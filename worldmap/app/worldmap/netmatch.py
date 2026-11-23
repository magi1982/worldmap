"""Map matching: lay gaps between GPS points onto the real rail and road network.

The network comes from OpenStreetMap via OpenFreeMap vector tiles (zoom 12, layer
``transportation``). Only tile numbers are requested – no coordinates of the user leave
the house. Tiles are decoded once and cached in ``/data/tiles``.

For every gap a small graph of the surrounding tiles is built (cached per 0.25° region),
loose line ends are stitched, the two GPS points are snapped onto the network and the
shortest path is searched with A*. Paths that are much longer than the direct line are
rejected; such gaps stay open instead of becoming a straight line.
"""
from __future__ import annotations

import gzip
import heapq
import json
import logging
import math
import threading
import time
import urllib.error
import urllib.request
from collections import OrderedDict, defaultdict
from pathlib import Path

log = logging.getLogger(__name__)

Z = 12
REGION = 0.25        # degrees – one cached graph per region
MARGIN = 0.06        # degrees added around a region / gap
MAX_TILES = 400
# OpenMapTiles transportation classes -> one-letter codes
CLASS_CODE = {"rail": "a", "transit": "e", "motorway": "0", "trunk": "1", "primary": "2", "secondary": "3",
              "tertiary": "4", "minor": "5", "ferry": "f"}
# cost factor per code: prefer main lines / big roads
WEIGHTS = {"rail": {"a": 1.0, "e": 2.2}, "road": {"0": 0.75, "1": 0.85, "2": 1.0, "3": 1.1, "4": 1.25, "5": 1.5, "f": 1.3}}
SNAP_M = {"rail": 2500, "road": 300}
SLACK_M = {"rail": 4000, "road": 1500}
STITCH_M = 20
TILEJSON = "https://tiles.openfreemap.org/planet"


# ---------------------------------------------------------------- tiles
def tile_xy(lat: float, lon: float, z: int = Z) -> tuple[int, int]:
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    s = math.sin(math.radians(max(-85.0, min(85.0, lat))))
    y = int((0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n)
    return min(n - 1, max(0, x)), min(n - 1, max(0, y))


def tiles_for_bbox(lat0, lon0, lat1, lon1, z: int = Z) -> list[tuple[int, int]]:
    x0, y1 = tile_xy(lat0, lon0, z)
    x1, y0 = tile_xy(lat1, lon1, z)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def _unproject(px: float, py: float, z: int, x: int, y: int, extent: int) -> tuple[float, float]:
    n = 2 ** z
    lon = (x + px / extent) / n * 360 - 180
    yy = (y + py / extent) / n
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy))))
    return lat, lon


# ---------------------------------------------------------------- MVT decoding (protobuf, no dependency)
def _varint(b: bytes, i: int) -> tuple[int, int]:
    shift = res = 0
    while True:
        c = b[i]
        i += 1
        res |= (c & 0x7F) << shift
        if c < 0x80:
            return res, i
        shift += 7
        if shift > 70:
            raise ValueError("bad varint")


def _fields(b: bytes):
    i, n = 0, len(b)
    while i < n:
        key, i = _varint(b, i)
        f, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 2:
            ln, i = _varint(b, i)
            v = b[i:i + ln]
            i += ln
        elif wt == 1:
            v = b[i:i + 8]
            i += 8
        elif wt == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError("unsupported wire type")
        yield f, wt, v


def _packed(b: bytes) -> list[int]:
    out, i = [], 0
    while i < len(b):
        v, i = _varint(b, i)
        out.append(v)
    return out


def decode_mvt(data: bytes, z: int, x: int, y: int) -> list[tuple[str, list[tuple[float, float]]]]:
    """Lines of the ``transportation`` layer with a known class: [(code, [(lat, lon), ...]), ...]."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    out = []
    for f, _wt, layer in _fields(data):
        if f != 3:
            continue
        name, keys, values, feats, extent = None, [], [], [], 4096
        for lf, _lw, lv in _fields(layer):
            if lf == 1:
                name = lv.decode("utf-8", "replace")
            elif lf == 2:
                feats.append(lv)
            elif lf == 3:
                keys.append(lv.decode("utf-8", "replace"))
            elif lf == 4:
                val = None
                for vf, _vw, vv in _fields(lv):
                    if vf == 1:
                        val = vv.decode("utf-8", "replace")
                values.append(val)
            elif lf == 5:
                extent = lv
        if name != "transportation":
            continue
        try:
            kclass = keys.index("class")
        except ValueError:
            continue
        for feat in feats:
            tags, geom, gtype = [], [], 0
            for ff, _fw, fv in _fields(feat):
                if ff == 2:
                    tags = _packed(fv)
                elif ff == 3:
                    gtype = fv
                elif ff == 4:
                    geom = _packed(fv)
            if gtype != 2:  # LINESTRING
                continue
            cls = None
            for t in range(0, len(tags) - 1, 2):
                if tags[t] == kclass and tags[t + 1] < len(values):
                    cls = values[tags[t + 1]]
            code = CLASS_CODE.get(cls or "")
            if not code:
                continue
            for line in _geometry(geom):
                out.append((code, [_unproject(px, py, z, x, y, extent) for px, py in line]))
    return out


def _geometry(cmds: list[int]):
    i, px, py, line = 0, 0, 0, []
    while i < len(cmds):
        cmd, count = cmds[i] & 7, cmds[i] >> 3
        i += 1
        if cmd == 7:  # ClosePath
            continue
        for _ in range(count):
            dx, dy = cmds[i], cmds[i + 1]
            i += 2
            px += (dx >> 1) ^ -(dx & 1)
            py += (dy >> 1) ^ -(dy & 1)
            if cmd == 1:
                if len(line) >= 2:
                    yield line
                line = [(px, py)]
            else:
                line.append((px, py))
    if len(line) >= 2:
        yield line


# ---------------------------------------------------------------- tile sources
class TileSource:
    def lines(self, x: int, y: int) -> list | None:  # pragma: no cover - interface
        raise NotImplementedError


class OpenFreeMapTiles(TileSource):
    """Downloads zoom-12 vector tiles once and keeps the decoded lines on disk."""

    def __init__(self, cache_dir: str, tilejson: str = TILEJSON, timeout: float = 20.0, min_interval: float = 0.2,
                 allow_http: bool = False, z: int = Z):
        self.z = z  # 12 for map matching; 7 for long estimated car routes (motorways and main roads only)
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tilejson = tilejson
        self.timeout = timeout
        self.min_interval = min_interval
        self._url: str | None = None
        self._url_t = 0.0
        self._last = 0.0
        self._lock = threading.Lock()
        self.downloaded = 0
        self.allow_http = allow_http
        self.pause_until = 0.0  # back off when the tile server says "too many requests" or is down
        self.last_error = ""
        self._warned = 0.0

    def _template(self) -> str:
        if self._url and time.time() - self._url_t < 86400:
            return self._url
        with urllib.request.urlopen(self.tilejson, timeout=self.timeout) as r:  # nosec B310 - fixed https URL
            tj = json.loads(r.read(1_000_000))
        url = tj["tiles"][0]
        if not url.startswith("https://") and not (self.allow_http and url.startswith("http://")):
            raise ValueError("unexpected tile URL")
        self._url, self._url_t = url, time.time()
        return url

    def lines(self, x: int, y: int):
        f = self.dir / f"{self.z}-{x}-{y}.json.gz"
        if f.exists():
            try:
                return json.loads(gzip.decompress(f.read_bytes()))
            except (OSError, ValueError):
                pass
        if time.monotonic() < self.pause_until:
            return None
        with self._lock:
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
        try:
            url = self._template().replace("{z}", str(self.z)).replace("{x}", str(x)).replace("{y}", str(y))
            req = urllib.request.Request(url, headers={"User-Agent": "worldmap-home-assistant-addon"})
            with urllib.request.urlopen(req, timeout=self.timeout) as r:  # nosec B310 - https URL from TileJSON
                data = r.read(20_000_000)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:  # empty sea tile
                data = b""
            else:
                self._failed(exc, 300 if exc.code == 429 else 120)
                return None
        except (OSError, ValueError) as exc:
            self._failed(exc, 120)
            return None
        lines = decode_mvt(data, self.z, x, y) if data else []
        compact = [[c, [[round(a, 6), round(b, 6)] for a, b in pts]] for c, pts in lines]
        f.write_bytes(gzip.compress(json.dumps(compact, separators=(",", ":")).encode(), 6))
        self.downloaded += 1
        return compact

    def _failed(self, exc, pause_s: float) -> None:
        """Pause downloads for a while instead of hammering the server; tell the log once in a while why."""
        self.last_error = str(exc)[:200]
        self.pause_until = time.monotonic() + pause_s
        if time.monotonic() - self._warned > 600:
            self._warned = time.monotonic()
            log.warning("map tiles: download paused for %d s (%s)", pause_s, self.last_error)


class StaticLines(TileSource):
    """Lines from memory, bucketed into tiles (tests and offline use)."""

    def __init__(self, lines, z: int = Z):
        self.z = z
        self.buckets = defaultdict(list)
        for code, pts in lines:
            seen = set()
            for la, lo in pts:
                seen.add(tile_xy(la, lo, z))
            for t in seen:
                self.buckets[t].append([code, [list(p) for p in pts]])

    def lines(self, x, y):
        return self.buckets.get((x, y), [])


# ---------------------------------------------------------------- graph
KX = 111_320.0
KY = 110_540.0


class Graph:
    def __init__(self, lines, weights: dict, lat_ref: float, cell: float = 0.002, stitch_m: float = STITCH_M):
        self.stitch_m = stitch_m
        self.kx = KX * math.cos(math.radians(lat_ref))
        self.coord: list[tuple[float, float]] = []
        self.adj: list[list[tuple[int, float, float]]] = []
        key: dict = {}

        def nid(la, lo):
            k = (round(la * 1e5), round(lo * 1e5))
            i = key.get(k)
            if i is None:
                i = key[k] = len(self.coord)
                self.coord.append((la, lo))
                self.adj.append([])
            return i

        seen_edges = set()
        for code, pts in lines:
            w = weights.get(code)
            if w is None:
                continue
            prev = None
            for la, lo in pts:
                i = nid(la, lo)
                if prev is not None and prev != i and (prev, i) not in seen_edges:
                    seen_edges.add((prev, i))
                    seen_edges.add((i, prev))
                    d = self.dist(prev, i)
                    self.adj[prev].append((i, d * w, d))
                    self.adj[i].append((prev, d * w, d))
                prev = i
        # spatial grid for snapping and stitching
        self.cell = cell
        self.grid = defaultdict(list)
        for i, (la, lo) in enumerate(self.coord):
            self.grid[(int(la / self.cell), int(lo / self.cell))].append(i)
        self._stitch()

    def dist(self, i: int, j: int) -> float:
        a, b = self.coord[i], self.coord[j]
        return math.hypot((a[0] - b[0]) * KY, (a[1] - b[1]) * self.kx)

    def _near(self, la, lo, radius_m):
        r = int(radius_m / (self.cell * KY)) + 1
        ci, cj = int(la / self.cell), int(lo / self.cell)
        for i in range(ci - r, ci + r + 1):
            for j in range(cj - r, cj + r + 1):
                yield from self.grid.get((i, j), ())

    def _stitch(self) -> None:
        """Connect loose line ends to the nearest point of another line (tile seams, gaps in OSM).

        The nearest *segment* within STITCH_M is split at the projected point, like a real junction.
        """
        segs = defaultdict(list)  # cell -> [(u, v, w)], only cells that contain a loose end
        cell = max(0.002, self.stitch_m / KY * 1.2)
        ends = [i for i, nb in enumerate(self.adj) if len(nb) == 1]
        want = {(int(self.coord[e][0] / cell), int(self.coord[e][1] / cell)) for e in ends}
        coord = self.coord
        for u, nb in enumerate(self.adj):
            la0, lo0 = coord[u]
            cu0, cu1 = int(la0 / cell), int(lo0 / cell)
            for v, c, d in nb:
                if u < v:
                    la1, lo1 = coord[v]
                    cv0, cv1 = int(la1 / cell), int(lo1 / cell)
                    i0, i1 = min(cu0, cv0) - 1, max(cu0, cv0) + 1
                    j0, j1 = min(cu1, cv1) - 1, max(cu1, cv1) + 1
                    if (i1 - i0 + 1) * (j1 - j0 + 1) <= 9 and not any(
                            (i, j) in want for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)):
                        continue
                    w = c / d if d else 1.0
                    for i in range(i0, i1 + 1):
                        for j in range(j0, j1 + 1):
                            if (i, j) in want:
                                segs[(i, j)].append((u, v, w))
        for e in ends:
            la, lo = self.coord[e]
            ex, ey = lo * self.kx, la * KY
            best = None
            bd = self.stitch_m
            own = self.adj[e][0][0]
            for (u, v, w) in segs.get((int(la / cell), int(lo / cell)), ()):
                if e in (u, v) or own in (u, v) and (u == e or v == e):
                    continue
                if u == e or v == e:
                    continue
                ax, ay = self.coord[u][1] * self.kx, self.coord[u][0] * KY
                bx, by = self.coord[v][1] * self.kx, self.coord[v][0] * KY
                dx, dy = bx - ax, by - ay
                l2 = dx * dx + dy * dy
                t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((ex - ax) * dx + (ey - ay) * dy) / l2))
                px, py = ax + t * dx, ay + t * dy
                d = math.hypot(px - ex, py - ey)
                if d < bd and not (own in (u, v) and t in (0.0, 1.0)):
                    best, bd = (u, v, w, t, px, py), d
            if best is None:
                continue
            u, v, w, t, px, py = best
            if t <= 1e-6:
                n = u
            elif t >= 1 - 1e-6:
                n = v
            else:  # split u-v at the projection
                n = len(self.coord)
                self.coord.append((py / KY, px / self.kx))
                self.adj.append([])
                self.adj[u] = [x for x in self.adj[u] if x[0] != v]
                self.adj[v] = [x for x in self.adj[v] if x[0] != u]
                for a_, b_ in ((u, n), (n, v)):
                    d = self.dist(a_, b_)
                    self.adj[a_].append((b_, d * w, d))
                    self.adj[b_].append((a_, d * w, d))
                key = (int(self.coord[n][0] / cell), int(self.coord[n][1] / cell))
                segs[key].append((u, n, w))
                segs[key].append((n, v, w))
                self.grid[(int(self.coord[n][0] / self.cell), int(self.coord[n][1] / self.cell))].append(n)
            if n == e or n == own:
                continue
            d = max(bd, 0.1)
            self.adj[e].append((n, d, d))
            self.adj[n].append((e, d, d))

    def snap(self, la: float, lo: float, max_m: float) -> tuple[int, float] | None:
        best, bd = None, max_m
        for j in self._near(la, lo, max_m):
            a = self.coord[j]
            d = math.hypot((a[0] - la) * KY, (a[1] - lo) * self.kx)
            if d < bd:
                best, bd = j, d
        return (best, bd) if best is not None else None

    def route(self, s: int, t: int, max_cost: float) -> tuple[list[int], float] | None:
        """A* on cost; returns (node path, real length in metres)."""
        tc = self.coord[t]
        minw = 0.75

        def h(i):
            a = self.coord[i]
            return math.hypot((a[0] - tc[0]) * KY, (a[1] - tc[1]) * self.kx) * minw

        g = {s: 0.0}
        length = {s: 0.0}
        prev = {s: -1}
        pq = [(h(s), s)]
        done = set()
        while pq:
            f, u = heapq.heappop(pq)
            if u in done:
                continue
            if u == t:
                path = []
                while u != -1:
                    path.append(u)
                    u = prev[u]
                return path[::-1], length[t]
            if f > max_cost:
                return None
            done.add(u)
            gu = g[u]
            for v, c, d in self.adj[u]:
                nv = gu + c
                if nv < g.get(v, 1e18):
                    g[v] = nv
                    length[v] = length[u] + d
                    prev[v] = u
                    heapq.heappush(pq, (nv + h(v), v))
        return None


# ---------------------------------------------------------------- matcher
class Matcher:
    """Find network paths for gaps. Keeps a few region graphs in memory."""

    def __init__(self, source: TileSource, max_graphs: int = 6):
        self.source = source
        self.graphs: OrderedDict = OrderedDict()
        self.max_graphs = max_graphs
        self.stats = defaultdict(int)

    def _graph(self, kind: str, bbox: tuple[float, float, float, float]):
        key = (kind, *(round(v, 3) for v in bbox))
        g = self.graphs.get(key)
        if g is not None:
            self.graphs.move_to_end(key)
            return g
        tiles = tiles_for_bbox(*bbox)
        if len(tiles) > MAX_TILES:
            self.stats["too_large"] += 1
            return "too_large"
        lines = []
        codes = set(WEIGHTS[kind])
        for x, y in tiles:
            got = self.source.lines(x, y)
            if got is None:
                self.stats["tile_errors"] += 1
                return None  # network trouble: try again later
            lines.extend((c, p) for c, p in got if c in codes)
        g = Graph(lines, WEIGHTS[kind], (bbox[0] + bbox[2]) / 2)
        self.graphs[key] = g
        if len(self.graphs) > self.max_graphs:
            self.graphs.popitem(last=False)
        return g

    def region_bbox(self, a, b):
        """Cached region graph that holds both points (with margin), else a box around the gap."""
        mid_lat, mid_lon = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        r0, r1 = math.floor(mid_lat / REGION), math.floor(mid_lon / REGION)
        box = (r0 * REGION - MARGIN, r1 * REGION - MARGIN, (r0 + 1) * REGION + MARGIN, (r1 + 1) * REGION + MARGIN)
        inner = MARGIN / 2  # keep some network around the points
        if all(box[0] + inner <= p[0] <= box[2] - inner and box[1] + inner <= p[1] <= box[3] - inner for p in (a, b)):
            return box
        lo_lat, hi_lat = min(a[0], b[0]), max(a[0], b[0])
        lo_lon, hi_lon = min(a[1], b[1]), max(a[1], b[1])
        m = max(MARGIN, 0.15 * max(hi_lat - lo_lat, hi_lon - lo_lon))
        q = REGION / 2  # round outwards so neighbouring gaps share one graph
        return (math.floor((lo_lat - m) / q) * q, math.floor((lo_lon - m * 1.4) / q) * q,
                math.ceil((hi_lat + m) / q) * q, math.ceil((hi_lon + m * 1.4) / q) * q)

    def match(self, kind: str, a, b):
        """Path [[lat, lon], ...] from a to b on the network, or "none" (no plausible path), or None (no data)."""
        bbox = self.region_bbox(a, b)
        g = self._graph(kind, bbox)
        if g == "too_large":
            return "none"  # far too long for a ground path: leave the gap open
        if g is None:
            return None
        sa, sb = g.snap(a[0], a[1], SNAP_M[kind]), g.snap(b[0], b[1], SNAP_M[kind])
        if not sa or not sb:
            self.stats["no_snap"] += 1
            return "none"
        dd = math.hypot((a[0] - b[0]) * KY, (a[1] - b[1]) * g.kx)
        factor = 2.2 if dd < 6000 else 1.6
        limit = dd * factor + SLACK_M[kind]
        res = g.route(sa[0], sb[0], limit * 1.6)
        if not res or res[1] > limit:
            self.stats["rejected"] += 1
            return "none"
        self.stats["matched"] += 1
        path = [list(a)] + [[round(g.coord[i][0], 5), round(g.coord[i][1], 5)] for i in res[0]] + [list(b)]
        return path
