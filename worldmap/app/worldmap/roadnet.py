"""Offline main roads, ferries and railways of the world (Natural Earth, public domain).

Used to draw the likely way of a trip without GPS: by car along motorways and main roads, by train along railways,
with ferries where the way crosses the sea. Nothing is downloaded; data/network.json.gz ships with the add-on.
"""
from __future__ import annotations

import gzip
import heapq
import json
import math
import threading
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).with_name("data") / "network.json.gz"
KX, KY = 111.32, 110.54  # km per degree
# cost factor per code: motorways first; trains may use a road only where the railway data has a hole
WEIGHTS = {
    "road": {"0": 0.62, "1": 0.8, "2": 1.0, "f": 1.6, "t": 0.8},
    "rail": {"a": 1.0, "t": 0.9, "f": 1.7, "0": 2.6, "1": 3.0, "2": 3.4},
}
STITCH_KM = 6.0      # loose ends closer than this are joined (simplified data: junctions, borders)
DENSE_KM = 2.0       # roads get a point at least this often, so a loose end finds the road it meets
# longer than this × the straight way (+ km): the coarse network lacks a road there (trains go around more)
MAX_DETOUR = {"road": 2.0, "rail": 2.2}  # mountains (Alps) need up to ~1.9×: below that the way is real
DETOUR_KM = 20.0
SNAP_KM = 25.0       # start / destination may be this far from the network (else: the land grid decides)
_lock = threading.Lock()


@lru_cache(maxsize=1)
def _load() -> dict:
    """{kind: [(code, coords tuple, bbox)]}; roads are also offered to trains (see WEIGHTS)."""
    try:
        raw = json.loads(gzip.decompress(DATA.read_bytes()))
    except (OSError, ValueError):
        return {"road": [], "rail": []}
    out = {}
    for kind, lines in raw.items():
        items = []
        for ln in lines:
            c = ln[1:]
            la, lo = c[0::2], c[1::2]
            items.append((ln[0], tuple(c), (min(la), min(lo), max(la), max(lo))))
        out[kind] = items
    return out


def _km(a, b, kx):
    return math.hypot((a[0] - b[0]) * KY, (a[1] - b[1]) * kx)


class _Graph:
    def __init__(self, lines, weights: dict, lat_ref: float):
        self.kx = KX * math.cos(math.radians(lat_ref))
        self.coord: list = []
        self.adj: list = []
        key: dict = {}

        def nid(p):
            i = key.get(p)
            if i is None:
                i = key[p] = len(self.coord)
                self.coord.append(p)
                self.adj.append([])
            return i

        for code, c in lines:
            w = weights[code]
            prev = None
            for k in range(0, len(c) - 1, 2):
                p = (c[k], c[k + 1])
                if prev is not None:  # long straight pieces get extra points, so loose ends find a road nearby
                    q = self.coord[prev]
                    steps = int(_km(q, p, self.kx) / DENSE_KM)
                    for s_ in range(1, steps + 1):
                        f = s_ / (steps + 1)
                        m = nid((round(q[0] + (p[0] - q[0]) * f, 5), round(q[1] + (p[1] - q[1]) * f, 5)))
                        d = _km(self.coord[prev], self.coord[m], self.kx)
                        self.adj[prev].append((m, d * w, code))
                        self.adj[m].append((prev, d * w, code))
                        prev = m
                i = nid(p)
                if prev is not None and prev != i:
                    d = _km(self.coord[prev], self.coord[i], self.kx)
                    self.adj[prev].append((i, d * w, code))
                    self.adj[i].append((prev, d * w, code))
                prev = i
        self.cell = 0.05
        self.grid = defaultdict(list)
        for i, (la, lo) in enumerate(self.coord):
            self.grid[(int(la / self.cell), int(lo / self.cell))].append(i)
        # join loose ends to the nearest other node (data has small holes at borders and junctions)
        for e, nb in enumerate(self.adj):
            if len(nb) != 1:
                continue
            reach = 25.0 if nb[0][2] in ("f", "t") else STITCH_KM  # ferry piers lie a bit away from the roads
            best, bd = None, reach
            own = self._line_of(e)
            for j in self._near(self.coord[e], reach):
                if j in own or (reach > STITCH_KM and all(x[2] in ("f", "t") for x in self.adj[j])):
                    continue
                d = _km(self.coord[e], self.coord[j], self.kx)
                if d < bd:
                    best, bd = j, d
            if best is not None:
                self.adj[e].append((best, bd * 1.2, "2"))
                self.adj[best].append((e, bd * 1.2, "2"))

    def _line_of(self, e, limit=400):
        """Nodes of the same line near e (walking along degree-2 nodes): a loose end never joins itself."""
        seen = {e}
        st = [e]
        while st and len(seen) < limit:
            u = st.pop()
            for v, _c, _code in self.adj[u]:
                if v not in seen and len(self.adj[v]) <= 2:
                    seen.add(v)
                    st.append(v)
                elif v not in seen:
                    seen.add(v)
        return seen

    def _near(self, p, radius_km):
        r = int(radius_km / (self.cell * KY)) + 1
        ci, cj = int(p[0] / self.cell), int(p[1] / self.cell)
        for i in range(ci - r, ci + r + 1):
            for j in range(cj - r, cj + r + 1):
                yield from self.grid.get((i, j), ())

    def near_sorted(self, p, max_km):
        out = [(_km(p, self.coord[j], self.kx), j) for j in self._near(p, max_km)]
        return sorted(x for x in out if x[0] <= max_km)

    def components(self):
        comp = [-1] * len(self.coord)
        for i in range(len(self.coord)):
            if comp[i] >= 0:
                continue
            comp[i] = i
            st = [i]
            while st:
                u = st.pop()
                for v, _c, _code in self.adj[u]:
                    if comp[v] < 0:
                        comp[v] = i
                        st.append(v)
        return comp

    def snap_pair(self, a, b, max_km):
        """Start and end node on the same connected network, as close to a and b as possible."""
        ca, cb = self.near_sorted(a, max_km), self.near_sorted(b, max_km)
        if not ca or not cb:
            return None
        comp = self.components()
        best_b: dict = {}
        for d, j in cb:
            best_b.setdefault(comp[j], (d, j))
        best = None
        for d, i in ca:
            hit = best_b.get(comp[i])
            if hit and (best is None or d + hit[0] < best[0]):
                best = (d + hit[0], i, hit[1])
        return (best[1], best[2]) if best else None

    def route(self, s: int, t: int, max_cost: float):
        tc = self.coord[t]
        minw = 0.62
        g = {s: 0.0}
        prev: dict = {s: (-1, "")}
        pq = [(0.0, s)]
        done = set()
        while pq:
            f, u = heapq.heappop(pq)
            if u in done:
                continue
            if u == t:
                path, codes = [], []
                while u != -1:
                    path.append(self.coord[u])
                    codes.append(prev[u][1])
                    u = prev[u][0]
                return path[::-1], codes[::-1]
            if f > max_cost:
                return None
            done.add(u)
            for v, c, code in self.adj[u]:
                nv = g[u] + c
                if nv < g.get(v, 1e18):
                    g[v] = nv
                    prev[v] = (u, code)
                    heapq.heappush(pq, (nv + _km(self.coord[v], tc, self.kx) * minw, v))
        return None


def route(kind: str, a: tuple, b: tuple) -> list | None:
    """Likely way from a to b: [[sea 0/1, [lat, lon, lat, lon, ...]], ...] (sea = ferry), or None if not found."""
    kind = "rail" if kind == "rail" else "road"
    net = _load()
    lines = net.get(kind, []) + (net.get("road", []) if kind == "rail" else [])
    if not lines:
        return None
    straight = math.hypot((a[0] - b[0]) * KY, (a[1] - b[1]) * KX * math.cos(math.radians((a[0] + b[0]) / 2)))
    pad = max(1.0, 0.35 * max(abs(a[0] - b[0]), abs(a[1] - b[1])))
    box = (min(a[0], b[0]) - pad, min(a[1], b[1]) - pad * 1.3, max(a[0], b[0]) + pad, max(a[1], b[1]) + pad * 1.3)
    sel = [(code, c) for code, c, bb in lines
           if bb[2] >= box[0] and bb[0] <= box[2] and bb[3] >= box[1] and bb[1] <= box[3]]
    if not sel:
        return None
    with _lock:
        g = _Graph(sel, WEIGHTS[kind], (a[0] + b[0]) / 2)
    pair = g.snap_pair(a, b, SNAP_KM)
    if not pair:
        return None
    s, t = pair
    res = g.route(s, t, straight * 3.2 + 150) if s != t else ([g.coord[s]], [""])
    if not res:
        return None
    path, codes = res
    total = sum(_km(p, q, g.kx) for p, q in zip([tuple(a)] + path, path + [tuple(b)], strict=False))
    ferry = sum(_km(p, q, g.kx) for p, q, c in zip(path, path[1:], codes[1:], strict=False) if c == "f")
    if total - ferry > (straight - ferry) * MAX_DETOUR[kind] + DETOUR_KM:
        return None  # the coarse network has no direct road there (hundreds of km around): not a plausible way
    runs: list = []
    cur = None
    pts = [tuple(a)] + path + [tuple(b)]
    flags = [0] + [1 if c == "f" else 0 for c in codes] + [0]  # flag of the edge that ends at this point
    for p, sea in zip(pts, flags, strict=True):
        if cur is None:
            cur = [sea, [round(p[0], 3), round(p[1], 3)]]
            runs.append(cur)
            continue
        if sea != cur[0]:
            last = cur[1][-2:]
            cur = [sea, last[:]]
            runs.append(cur)
        cur[1] += [round(p[0], 3), round(p[1], 3)]
    return [r for r in runs if len(r[1]) >= 4]
