"""Build the data of the five-view map ("atlas") from the database.

The output has the same shape the interactive map expects:

* ``core``   – trips, days, cells, places, groups, flights, est. areas, people/colours
* ``tracks`` – per day and transport mode: [day, cls, lat0*1e5, lon0*1e5, dlat, dlon, ...]
* ``labels`` – place names near the tracks
* ``reg``    – states, provinces and cantons worldwide: [region id, person index, first day, days, stayed]

Everything is computed from points, segments and trips and cached by a data fingerprint.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import logging
import math
import threading
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from . import airports, places
from .geo import haversine_km, simplify
from .modes import MIN_FLIGHT_KM, estimate_km, mode_of_pair, mode_of_text, modes_of_transport  # noqa: F401 - re-exported for tests
from .timeparse import local_date


@lru_cache(maxsize=1)
def _code_version() -> str:
    h = hashlib.sha256()
    here = Path(__file__).parent
    for name in ("atlas.py", "modes.py", "airports.py", "places.py", "roads.py", "importers/triplist.py",
                 "data/airports.json"):
        try:
            h.update((here / name).read_bytes())
        except OSError:
            pass
    return h.hexdigest()[:12]


def _rev(flat: list) -> list:
    """[lat, lon, lat, lon, ...] the other way round."""
    return [c for i in range(len(flat) - 2, -1, -2) for c in flat[i:i + 2]]


def _legs(raw) -> list:
    """Stops of a trip (JSON text from the database) → list of dicts; broken data → []."""
    if not raw:
        return []
    try:
        legs = json.loads(raw) if isinstance(raw, str) else raw
        return [x for x in legs if isinstance(x, dict) and isinstance(x.get("lat"), (int, float))
                and isinstance(x.get("lon"), (int, float))][:20]
    except (ValueError, TypeError):
        return []


@lru_cache(maxsize=4096)
def _net_route(kind: str, la1: float, lo1: float, la2: float, lo2: float):
    from . import roadnet

    try:
        return roadnet.route(kind, (la1, lo1), (la2, lo2))
    except (ValueError, KeyError, IndexError):
        return None


@lru_cache(maxsize=2048)
def _geocode(name: str, country: str, home: tuple, max_km):
    from .importers.triplist import geocode

    try:
        return geocode(name, country, home, max_km)
    except (ValueError, TypeError):
        return None

log = logging.getLogger(__name__)

MODES = ("fly", "rail", "road", "ferry", "foot")
TCLS = {"road": 0, "rail": 1, "foot": 2}
CELL = 0.02          # degrees latitude; longitude uses CELL * 1.4
FAR_KM = 150         # trips farther than this get a named destination group
GROUP_KM = 80        # destinations closer than this are merged into one label
STAY_M = 250         # radius of a stay
STAY_MIN_S = 20 * 60
WD = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
STATIC = Path(__file__).with_name("static")

def wd(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{WD[d.weekday()]} {d:%d.%m.%Y}"


GUESS_KM = 12.0  # a flight end recorded further than this from the airport: the airport is a guess


class Atlas:
    def __init__(self, engine, cache_dir: str | None = None):
        self.engine = engine
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._lock = threading.Lock()
        self._mem: dict = {}

    # ------------------------------------------------------------ public
    def fingerprint(self) -> str:
        db = self.engine.db
        parts = (
            db.scalar("SELECT COUNT(*) FROM points"), db.scalar("SELECT MAX(id) FROM points"),
            db.scalar("SELECT COUNT(*) FROM trips"), db.scalar("SELECT MAX(updated_at) FROM trips"),
            db.scalar("SELECT SUM(id) FROM trips"), db.scalar("SELECT COUNT(*) FROM segments"),
            json.dumps([self.engine.s.labels, self.engine.s.who_options, self.engine.home]),
        )
        # stable across restarts, and new with every add-on version (new code = new map data)
        return "a3-" + hashlib.sha256((json.dumps(parts, default=str) + _code_version()).encode()).hexdigest()[:16]

    def get(self, part: str) -> bytes:
        """gzip-compressed JSON of one part: core | tracks | labels | reg."""
        if part not in ("core", "tracks", "labels", "reg"):
            raise KeyError(part)
        fp = self.fingerprint()
        with self._lock:
            if self._mem.get("fp") != fp:
                self._mem = {"fp": fp, **self._load_or_build(fp, force=bool(self.__dict__.get("_force")))}
                self._force = False
            return self._mem[part]

    # ------------------------------------------------------------ cache
    def _load_or_build(self, fp: str, force: bool = False) -> dict:
        if self.cache_dir and not force:
            f = self.cache_dir / f"atlas-{fp}.json.gz"
            if f.exists():
                try:
                    data = json.loads(gzip.decompress(f.read_bytes()))
                    return {k: gzip.compress(json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode(), 6)
                            for k, v in data.items()}
                except (OSError, ValueError):
                    pass
        data = self.build()
        pending = self._roads_pending
        self._save_roads()
        if self.cache_dir and not pending:  # routes still missing (tiles not loaded yet): build again later
            try:
                for old in self.cache_dir.glob("atlas-*.json.gz"):
                    old.unlink()
                (self.cache_dir / f"atlas-{fp}.json.gz").write_bytes(
                    gzip.compress(json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode(), 6))
            except OSError as exc:
                log.warning("atlas cache not written: %s", exc)
        out = {k: gzip.compress(json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode(), 6)
               for k, v in data.items()}
        if pending:
            out["pending"] = True
            ev = getattr(self.engine, "routes_wanted", None)
            if ev is not None:
                ev.set()  # compute the missing road routes in the background
        return out

    # ------------------------------------------------------------ estimated car routes on real roads
    _roads_pending = False
    road_router = None

    def _router(self):
        if self.road_router is not None:
            return self.road_router
        if getattr(self.engine.s, "routing", "off") != "tiles" or not getattr(self.engine, "tile_dir", None):
            return None
        from .netmatch import Matcher, OpenFreeMapTiles
        from .roads import LONG_Z, RoadRouter

        short = getattr(self.engine, "matcher", None) or Matcher(OpenFreeMapTiles(self.engine.tile_dir))
        self.road_router = RoadRouter(OpenFreeMapTiles(self.engine.tile_dir, z=LONG_Z), short)
        return self.road_router

    def _roads(self) -> dict:
        c = self.__dict__.get("_road_cache")
        if c is None:
            c = {}
            if self.cache_dir:
                try:
                    c = json.loads(gzip.decompress((self.cache_dir / "est-roads.json.gz").read_bytes()))
                except (OSError, ValueError):
                    c = {}
            self._road_cache, self._road_dirty = c, False
        return c

    def _save_roads(self) -> None:
        if self.cache_dir and self.__dict__.get("_road_dirty"):
            try:
                (self.cache_dir / "est-roads.json.gz").write_bytes(
                    gzip.compress(json.dumps(self._road_cache, separators=(",", ":")).encode(), 6))
                self._road_dirty = False
            except OSError as exc:
                log.warning("road cache not written: %s", exc)

    @staticmethod
    def _road_key(p, q) -> str:
        return f"{p[0]:.2f},{p[1]:.2f}>{q[0]:.2f},{q[1]:.2f}"

    def _road_path(self, p, q):
        """Road path p → q from the cache: list of [lat, lon], "none", or None (queued for ``fill_roads``).

        Building the map never waits for the network; missing routes are computed in the background and the map is
        built again afterwards."""
        cache = self._roads()
        key = self._road_key(p, q)
        if key in cache:
            return cache[key]
        self.__dict__.setdefault("_road_todo", {})[key] = (tuple(p), tuple(q))
        self._roads_pending = True
        return None

    def fill_roads(self, budget_s: float = 300) -> int:
        """Compute queued road routes (background thread). Returns how many are new; then the map is rebuilt."""
        router = self._router()
        todo = self.__dict__.get("_road_todo") or {}
        if router is None or not todo:
            return 0
        cache, n, t0 = self._roads(), 0, time.monotonic()
        for key, (p, q) in list(todo.items()):
            if time.monotonic() - t0 > budget_s:
                break
            try:
                got = router.route(p, q)
            except Exception as exc:  # noqa: BLE001 - a broken tile must never break the map
                log.warning("road route failed: %s", exc)
                got = "none"
            if got is None:  # tiles not available right now: try again later
                break
            if isinstance(got, list):
                got = [[round(a, 4), round(b, 4)] for a, b in simplify(got, 0.003)]
            cache[key] = got
            todo.pop(key, None)
            self._road_dirty = True
            n += 1
        if n:
            self._save_roads()
            with self._lock:
                self._mem, self._force = {}, True  # build again with the new routes (not from the disk cache)
        return n

    def est_route(self, a: tuple, b: tuple, mode: str = "road") -> list:
        """Estimated way for a trip without GPS. Cars follow roads (motorways, main roads); where there is no way by
        land a ferry; without road data the coarse land grid of ``ground_route``."""
        runs = self.ground_route(a, b, mode)
        if mode != "road" or self._router() is None:
            return runs
        out = []
        for sea, flat in runs:
            if sea or len(flat) < 4:
                out.append([sea, flat])
                continue
            p, q = (flat[0], flat[1]), (flat[-2], flat[-1])
            path = self._road_path(p, q) if haversine_km(*p, *q) >= 8 else None
            if isinstance(path, list) and len(path) >= 2:
                path[0], path[-1] = [p[0], p[1]], [q[0], q[1]]  # the runs keep touching (ferry ↔ road)
                out.append([0, [round(c, 3) for pt in path for c in pt]])
            else:
                out.append([sea, flat])
        return out

    # ------------------------------------------------------------ build
    def build(self) -> dict:
        self._roads_pending = False
        self._road_todo = {}
        eng = self.engine
        s = eng.s
        tz = s.timezone
        home = eng.resolve_home() or (47.0, 8.0)
        trips_db = eng.db.trips()
        pts = eng.clean_points()
        segs = {(x["person"], x["t0"], x["t1"]): x for x in eng.db.segments()}

        # ---- days
        first_day = min((local_date(p["ts"], tz) for p in pts), default=None)
        last_day = max((local_date(p["ts"], tz) for p in pts), default=None)
        day_index: dict[str, int] = {}
        days: list[list] = []
        if first_day:
            d, end = date.fromisoformat(first_day), date.fromisoformat(last_day)
            while d <= end:
                day_index[d.isoformat()] = len(days)
                days.append([d.isoformat(), 0.0, 0.0, 0.0, 0.0, 0, -1, 0])
                d += timedelta(days=1)

        # ---- trips (ids are positions in the list)
        trip_rows = sorted(trips_db, key=lambda t: (t["start_date"], t["id"]))
        tid_of_day: dict[str, int] = {}
        # trips where a person said "no plane" (transport edited, e.g. Auto): fast GPS bits are not flights there
        no_fly: dict[int, str] = {}
        fly_only: set = set()  # … and trips where a person said "by plane" only: no long ways on the ground there
        for i, t in enumerate(trip_rows):
            ms = modes_of_transport(t["transport"])
            if (t["locked"] or t["source"] == "manual") and ms and "fly" not in ms:
                no_fly[i] = "rail" if "rail" in ms and "road" not in ms else "road"
            if (t["locked"] or t["source"] == "manual") and "fly" in ms and not set(ms) - {"fly", "foot"}:
                fly_only.add(i)
        for i, t in enumerate(trip_rows):
            d = date.fromisoformat(t["start_date"])
            while d.isoformat() <= t["end_date"]:
                if t["locked"] or t["source"] == "manual":
                    tid_of_day[d.isoformat()] = i  # what a person entered wins over a detected trip
                else:
                    tid_of_day.setdefault(d.isoformat(), i)
                d += timedelta(days=1)

        # ---- walk the points: tracks, km per day/mode, cells, flights
        tracks: list = []
        cells: dict = defaultdict(float)
        flights: list = []
        trip_km: dict = defaultdict(lambda: defaultdict(float))
        alltag_year: dict = defaultdict(lambda: defaultdict(float))
        hour_year: dict = {}
        who_idx = {w: i for i, w in enumerate(self.who_list(trip_rows))}
        p_idx = {w: i for i, w in enumerate(s.labels)}
        track_p: list = []
        used_ap: dict = {}
        gaps: list = []
        day_p = [0] * len(days)
        alltag_i = who_idx["Alltag"]

        def year_of(ts):
            hb = ts // 3600
            if hb not in hour_year:
                hour_year[hb] = local_date(ts, tz)
            return hour_year[hb]

        cur: list = []
        cur_key = None
        cur_t = [0, 0]
        cur_p = [-1]
        track_t: list = []
        offsets: dict = {}

        def tod(ts):  # share of the local day, 0..1
            hb = ts // 3600
            if hb not in offsets:
                offsets[hb] = int(datetime.fromtimestamp(ts, ZoneInfo(tz)).utcoffset().total_seconds())
            return ((ts + offsets[hb]) % 86400) / 86400

        def flush():
            nonlocal cur
            if cur_key is not None and len(cur) >= 2:
                di, mode = cur_key
                line = simplify(cur, 0.00004)
                tracks.append(_encode_track(di, TCLS.get(mode, 0), line))
                t0, t1 = tod(cur_t[0]), tod(cur_t[1])
                track_t.append([round(t0, 4), round(max(t0, t1 if cur_t[1] - cur_t[0] < 86400 else 1.0), 4)])
                track_p.append(cur_p[0])
            cur = []

        prev = None
        air = None  # the flight we are in while the plane has not landed: {"i": index in flights, "ts", "person"}
        for p in pts:
            day = year_of(p["ts"])
            di = day_index[day]
            days[di][7] = 1
            dist_home = haversine_km(home[0], home[1], p["lat"], p["lon"])
            days[di][5] = max(days[di][5], round(dist_home))
            pi = p_idx.get(p["person"], -1)
            if pi >= 0:
                day_p[di] |= 1 << min(pi, 30)
            if not p["person"]:
                # photos without an owner: count the day and the place, but never connect them with lines
                prev = None
                continue
            if prev is None or prev["person"] != p["person"]:
                flush()
                cur_key = None
                prev = p
                continue
            dkm = haversine_km(prev["lat"], prev["lon"], p["lat"], p["lon"])
            dt = p["ts"] - prev["ts"]
            seg = segs.get((p["person"], prev["ts"], p["ts"]))
            if dkm < 0.02:
                prev = p
                continue
            if dt > 12 * 3600 and not seg:
                flush()
                cur_key = None
                prev = p
                continue
            mode = mode_of_pair(prev, p, dkm)
            if seg and seg["mode"] == "flight":
                mode = "fly"
            if air and (air["person"] != p["person"] or prev["ts"] != air["ts"]
                        or (dt > 5400 and airports.snap(prev["lat"], prev["lon"], 25, 15))):
                air = None  # landed: a new piece after a long stop at an airport is a new flight
            if (air and mode != "fly" and dkm / max(1e-6, dt / 3600) >= 150
                    and not airports.snap(prev["lat"], prev["lon"], 25, 15)):
                mode = "fly"  # still in the air between two sparse points of the same flight
            tid = tid_of_day.get(day, -1)
            if tid in no_fly and mode in ("fly", "jump") and dkm >= 20:
                mode, air = no_fly[tid], None  # corrected by hand: by car / train, not a flight
            if tid in fly_only and mode in ("road", "rail", "ferry") and dkm >= 150:
                mode = "jump"  # corrected by hand: flown – a long way "on the ground" is a gap or a stray photo
            if mode == "jump":  # GPS jump: no line, no kilometres
                flush()
                cur_key = None
                prev = p
                continue
            km_idx = {"road": 1, "rail": 2, "foot": 3, "fly": 4, "ferry": 1}[mode]
            routed = bool(seg and seg["mode"] in ("road", "rail") and seg["geometry"])
            if routed:
                mode = seg["mode"]
            if mode != "fly":
                if routed:
                    geom = seg["geometry"]
                    dkm = sum(haversine_km(*geom[i], *geom[i + 1]) for i in range(len(geom) - 1))
                elif dkm > 3 and ((seg and seg["mode"] == "none") or dt > 3600 or dkm > 50):
                    # a long gap without a route: no solid line – the map shows it as a soft dotted link
                    if dkm <= 1500:
                        g = [di, TCLS.get(mode, 0), round(prev["lat"], 4), round(prev["lon"], 4),
                             round(p["lat"], 4), round(p["lon"], 4), pi]
                        if dkm >= 20 and mode in ("road", "rail"):  # long gaps follow the main roads / railways
                            via = _net_route(mode, g[2], g[3], g[4], g[5])
                            if via:
                                g.append([c for r in via for c in r[1]])
                        if len(g) > 7 or dkm <= 400:
                            gaps.append(g)
                    days[di][km_idx] += dkm
                    if tid >= 0:
                        trip_km[tid][mode] += dkm
                    else:
                        alltag_year[day[:4]][mode] += dkm
                    flush()
                    cur_key = None
                    prev = p
                    continue
            days[di][km_idx] += dkm
            if tid >= 0:
                trip_km[tid][mode] += dkm
            else:
                alltag_year[day[:4]][mode] += dkm
            if mode == "fly":
                flush()
                cur_key = None
                b_ap = airports.snap(p["lat"], p["lon"])
                b_pt = [b_ap[2], b_ap[3]] if b_ap else [round(p["lat"], 4), round(p["lon"], 4)]
                b_off = haversine_km(p["lat"], p["lon"], b_ap[2], b_ap[3]) if b_ap else None
                if air:  # one flight recorded in pieces (ZRH → over the Alps → HER): extend it, no stopovers
                    f = flights[air["i"]]
                    f[2], f[6], f[7][1] = b_pt, b_ap[0] if b_ap else "", b_off
                else:
                    a_ap = airports.snap(prev["lat"], prev["lon"])
                    a_off = haversine_km(prev["lat"], prev["lon"], a_ap[2], a_ap[3]) if a_ap else None
                    # [7]: how far the recorded point was from the airport – far means the airport is a guess
                    flights.append([day, [a_ap[2], a_ap[3]] if a_ap else [round(prev["lat"], 4), round(prev["lon"], 4)],
                                    b_pt, round(tod(prev["ts"]), 4), pi, a_ap[0] if a_ap else "", b_ap[0] if b_ap else "",
                                    [a_off, b_off]])
                # a next piece that starts right here belongs to this flight (sparse points while flying)
                air = {"i": air["i"] if air else len(flights) - 1, "ts": p["ts"], "person": p["person"]}
                prev = p
                continue
            key = (di, mode)
            if key != cur_key:
                flush()
                cur_key = key
                cur = [[prev["lat"], prev["lon"]]]
                cur_t[0] = prev["ts"]
                cur_p[0] = pi
            cur_t[1] = p["ts"]
            if routed:
                cur.extend(seg["geometry"][1:])
            else:
                cur.append([p["lat"], p["lon"]])
            speed = dkm / max(1e-6, dt / 3600)
            if dkm < 25 and (mode == "foot" or speed < 50):  # local movements become the "many short ways" areas
                w = who_idx.get(trip_rows[tid]["who"] or "", alltag_i) if tid >= 0 else alltag_i
                yr = int(day[:4])
                ca, cb = math.floor(p["lat"] / CELL), math.floor(p["lon"] / (CELL * 1.4))
                cells[(ca, cb, w, MODES.index(mode), yr)] += dkm
            prev = p
        flush()
        # pieces that start and end at the same airport (taxiing, holding patterns) are no flights
        flights[:] = [f for f in flights if not (f[5] and f[5] == f[6])
                      and haversine_km(*f[1], *f[2]) >= MIN_FLIGHT_KM * .6]
        # airports set by hand on a trip win: the end nearer home gets "from", the other end "to"
        for f in flights:
            tid = tid_of_day.get(f[0], -1)
            if tid < 0:
                continue
            t = trip_rows[tid]
            fa = airports.by_iata(t["ap_from"] or "")
            ta = airports.by_iata(t["ap_to"] or "") or next(  # the airport stop you set ("✈ HER, then 🚗")
                (airports.by_iata(x["ap"]) for x in _legs(t["legs"]) if x.get("ap") and not x.get("gps")), None)
            if not (fa or ta):
                continue
            near_a = haversine_km(home[0], home[1], *f[1]) <= haversine_km(home[0], home[1], *f[2])
            for end, code_i, is_home in ((1, 5, near_a), (2, 6, not near_a)):
                ap = fa if is_home else ta
                if ap:
                    f[end], f[code_i], f[7][end - 1] = [ap[2], ap[3]], ap[0], 0.0
        # an end recorded only later, away from any airport (first point at home after landing), is a guess: the
        # airport the trip or you really used nearby wins (out from ZRH, back to ZRH – not to the nearest one, FDH)
        sure: dict = {}
        for f in flights:
            for k, (code_i, pt_i) in enumerate(((5, 1), (6, 2))):
                tid = tid_of_day.get(f[0], -1)
                if tid >= 0 and f[code_i] and f[7][k] is not None and f[7][k] <= GUESS_KM:
                    sure.setdefault(tid, []).append((f[code_i], f[pt_i]))
        for f in flights:
            for k, (code_i, pt_i) in enumerate(((5, 1), (6, 2))):
                if not f[code_i] or f[7][k] is None or f[7][k] <= GUESS_KM:
                    continue
                pool = sure.get(tid_of_day.get(f[0], -1), [])  # only airports this same trip really used
                near = Counter(c for c, pt in pool if haversine_km(*f[pt_i], *pt) <= 120)
                if near:
                    ap = airports.by_iata(near.most_common(1)[0][0])
                    if ap:
                        f[pt_i], f[code_i] = [ap[2], ap[3]], ap[0]
        for f in flights:
            del f[7:]
        flights[:] = [f for f in flights if not (f[5] and f[5] == f[6])]
        for f in flights:
            for code in (f[5], f[6]):
                ap = airports.by_iata(code) if code else None
                if ap:
                    used_ap[code] = [ap[2], ap[3], ap[1]]
        for r in days:
            for i in (1, 2, 3, 4):
                r[i] = round(r[i], 1)
            r[6] = tid_of_day.get(r[0], -1)

        # ---- trips in the map format
        out_trips, est = [], []
        # home airport: the setting, else the airport most GPS flights near home start or end at, else the nearest large one
        h_ap = airports.by_iata(getattr(s, "home_airport", ""))
        if not h_ap:
            near = Counter(c for f in flights for c, pt in ((f[5], f[1]), (f[6], f[2]))
                           if c and haversine_km(home[0], home[1], *pt) <= 150)
            h_ap = airports.by_iata(near.most_common(1)[0][0]) if near else airports.snap(home[0], home[1], 150, 0)
        for i, t in enumerate(trip_rows):
            k = {m: round(v) for m, v in trip_km.get(i, {}).items() if v >= 1}
            modes = [m for m in MODES if m in k] or modes_of_transport(t["transport"]) or ["road"]
            for m in modes_of_transport(t["transport"]):
                if m not in modes:
                    modes.append(m)
            legs = _legs(t["legs"])
            for lg_ in (x for x in legs if not x.get("gps")):  # found in the recording: the GPS shows the modes
                for m in modes_of_transport(lg_["transport"]):
                    if m not in modes:
                        modes.append(m)
            lat, lon, nopos, approx, rad = t["lat"], t["lon"], 0, t["approx"], t["radius_km"]
            if (lat is None or lon is None) and legs:
                lat, lon = legs[0]["lat"], legs[0]["lon"]
            fixed = t["source"] == "manual" or t["locked"]
            hit = None
            if lat is None or lon is None or (not k and not fixed):
                hit = _geocode(t["destination"] or "", t["country"] or "", (round(home[0], 2), round(home[1], 2)),
                               t["max_km"])
            if lat is None or lon is None:  # trips without coordinates: find the place by its name (offline)
                if hit and hit[3] == "place":
                    lat, lon, approx, rad = hit[0], hit[1], 1, rad or hit[2]
                elif hit:  # only the country is known: no point on the map (its middle is not where we were)
                    lat, lon, nopos = home[0], home[1], 2
                else:  # unknown place: never pretend the trip was at home
                    lat, lon, nopos = home[0], home[1], 1
            elif hit and hit[3] == "country" and haversine_km(lat, lon, hit[0], hit[1]) < 3:
                lat, lon, nopos = home[0], home[1], 2  # imported before 0.7.2: the middle of the country was stored
            dist = t["max_km"] if t["max_km"] is not None else haversine_km(home[0], home[1], lat, lon)
            fl, gr, lg = [], None, None
            by_hand = any(not x.get("gps") for x in legs)  # stops found in the recording do not draw the estimate
            if not k and by_hand and (len(legs) > 1 or any(x.get("ap") for x in legs)):  # several stops or an airport: each leg its own way
                fl, gr, lg, k = self._leg_ways(home, h_ap, t, legs, used_ap)
                if rad and rad <= 250:
                    est.append([i, lat, lon, rad])
            elif not k:  # no GPS: estimate the distance there and back
                k = estimate_km(dist, modes, t["nights"] or 0)
                if "fly" in modes and not nopos:
                    # set by hand, else only the big airport of a city (London → LHR); no guessing beyond
                    d_ap = airports.by_iata(t["ap_to"] or "") or airports.snap(lat, lon, 60, 0)
                    if not d_ap:  # no big airport there (La Gomera): fly to the big one nearby, then ferry or road
                        d_ap = airports.nearest_large(lat, lon, 400)
                        if d_ap and haversine_km(d_ap[2], d_ap[3], lat, lon) >= 15:
                            gr = self.est_route((d_ap[2], d_ap[3]), (lat, lon), "road")
                            if any(r[0] for r in gr) and "ferry" not in modes:
                                modes.append("ferry")
                    o_ap = airports.by_iata(t["ap_from"] or "") or h_ap
                    ha = [o_ap[2], o_ap[3]] if o_ap else [home[0], home[1]]
                    da = [d_ap[2], d_ap[3]] if d_ap else [lat, lon]
                    hc, dc = (o_ap[0] if o_ap else ""), (d_ap[0] if d_ap else "")
                    for ap in (o_ap, d_ap):
                        if ap:
                            used_ap[ap[0]] = [ap[2], ap[3], ap[1]]
                    fl = [[ha, da, hc, dc], [da, ha, dc, hc]]
                if rad and not nopos and rad <= 250:  # a whole country is no "area you were in"
                    est.append([i, lat, lon, rad])
                if not nopos and "fly" not in modes and dist >= 30:
                    gr = self.est_route(home, (lat, lon), "rail" if "rail" in modes and "road" not in modes else "road")
            else:
                fl = [[f[1], f[2], f[5], f[6]] for f in flights if t["start_date"] <= f[0] <= t["end_date"]]
                if not fl and i in fly_only and not nopos and dist >= MIN_FLIGHT_KM:  # flown, but not recorded
                    d_ap = airports.by_iata(t["ap_to"] or "") or next(
                        (airports.by_iata(x["ap"]) for x in legs if x.get("ap") and not x.get("gps")), None) \
                        or airports.snap(lat, lon, 60, 0)
                    o_ap = airports.by_iata(t["ap_from"] or "") or h_ap
                    if d_ap and o_ap and d_ap[0] != o_ap[0]:
                        ha, da = [o_ap[2], o_ap[3]], [d_ap[2], d_ap[3]]
                        for ap in (o_ap, d_ap):
                            used_ap[ap[0]] = [ap[2], ap[3], ap[1]]
                        fl = [[ha, da, o_ap[0], d_ap[0]], [da, ha, d_ap[0], o_ap[0]]]
                        k = {**k, "fly": k.get("fly", 0) + round(haversine_km(*ha, *da) * 2)}
            name = t["destination"] or "Reise"
            out_trips.append({
                "id": i, "dbid": t["id"], "a": t["start_date"], "b": t["end_date"], "y": int(t["start_date"][:4]),
                "n": t["nights"], "w": t["who"] or "offen", "name": name, "c": t["country"], "m": modes, "g": None,
                "km": sum(k.values()), "dw": wd(t["start_date"]), "dwb": wd(t["end_date"]), "fl": fl, "k": k,
                "p": [round(lat, 4), round(lon, 4)], "conf": t["confidence"], "approx": approx, "nopos": nopos,
                "r": t["radius_km"], "fixed": 1 if fixed else 0,
                **({"gr": gr} if gr else {}),
                **({"lg": lg} if lg else {}),
                **({"st": [[x["lat"], x["lon"], x["name"]] + ([x["ap"]] if x.get("ap") else []) for x in legs]}
                   if len(legs) > 1 or any(x.get("ap") for x in legs) else {}),
            })

        groups = _groups(out_trips, home)
        place_list = self._places(pts, trip_rows, tid_of_day, home, tz, p_idx)
        reg = self._reg(pts, place_list, tz, p_idx, [t for t in out_trips if t["approx"] or t["fixed"]])
        labels = _labels(cells, pts)
        who = self.who_list(trip_rows)
        years = sorted({t["y"] for t in out_trips} | {int(d[0][:4]) for d in days[:1]} | {int(d[0][:4]) for d in days[-1:]})
        core = {
            "home": [round(home[0], 4), round(home[1], 4)],
            "who": who, "persons": s.labels, "groups_who": s.who_options, "groups_cfg": s.groups,
            "colors": s.colors(), "trackP": track_p, "dayP": day_p, "airports": used_ap, "gaps": gaps,
            "trips": out_trips, "days": days,
            "alltagYear": {y: {m: round(v) for m, v in ms.items()} for y, ms in alltag_year.items()},
            "flights": flights, "groups": groups, "places": place_list,
            "cells": [[a, b, w, m, y, round(v, 2)] for (a, b, w, m, y), v in cells.items()],
            "est": est, "years": years,
            "routed": sum(1 for x in segs.values() if x["mode"] in ("road", "rail")),
            "trackT": track_t,
            "region": places.home_region(*home),
            "has_reg": len(reg) > 0,
            "min_trip_km": s.min_trip_km,
            "since": min((local_date(p["ts"], tz) for p in pts if p["person"]), default=first_day),
        }
        return {"core": core, "tracks": tracks, "labels": labels, "reg": reg}

    def who_list(self, trip_rows) -> list[str]:
        out = []
        for w in [*self.engine.s.labels, *self.engine.s.who_options, *(t["who"] for t in trip_rows if t["who"])]:
            if w and w not in out and w != "Alltag":
                out.append(w)
        return [*out, "offen", "Alltag"] if any(not t["who"] for t in trip_rows) else [*out, "Alltag"]

    # ------------------------------------------------------------ places
    def _places(self, pts, trip_rows, tid_of_day, home, tz, p_idx):
        s = self.engine.s
        home_km = self.engine.home_radius_km() if hasattr(self.engine, "home_radius_km") else 0.3
        stays = []
        by_person = defaultdict(list)
        for p in pts:
            by_person[p["person"]].append(p)
        for plist in by_person.values():
            i = 0
            while i < len(plist):
                j = i
                a = plist[i]
                while j + 1 < len(plist) and haversine_km(a["lat"], a["lon"], plist[j + 1]["lat"], plist[j + 1]["lon"]) * 1000 < STAY_M:
                    j += 1
                dur = plist[j]["ts"] - a["ts"]
                if dur >= STAY_MIN_S:
                    run = plist[i:j + 1]
                    lat = sum(x["lat"] for x in run) / len(run)
                    lon = sum(x["lon"] for x in run) / len(run)
                    stays.append((lat, lon, a["ts"], plist[j]["ts"], a["person"]))
                i = j + 1
        grid = defaultdict(list)
        for st in stays:
            near = haversine_km(home[0], home[1], st[0], st[1]) < home_km
            grid["home" if near else (round(st[0] / 0.003), round(st[1] / 0.004))].append(st)
        work_hours: dict = defaultdict(float)
        out = []
        for key, v in grid.items():
            lat = sum(x[0] for x in v) / len(v)
            lon = sum(x[1] for x in v) / len(v)
            pmask = 0
            for x in v:
                if x[4] in p_idx:
                    pmask |= 1 << min(p_idx[x[4]], 30)
            hours = sum((x[3] - x[2]) / 3600 for x in v)
            dset = {local_date(x[2], tz) for x in v}
            for x in v:  # weekday stays within one day count towards "work"
                d0 = local_date(x[2], tz)
                if date.fromisoformat(d0).weekday() < 5 and d0 == local_date(x[3], tz):
                    work_hours[key] += (x[3] - x[2]) / 3600
            tids = Counter(tid_of_day.get(d, -1) for d in dset)
            tid = tids.most_common(1)[0][0]
            near_home = haversine_km(home[0], home[1], lat, lon) < home_km
            if near_home:
                name = "Zuhause"
            else:
                name, _ = places.describe(lat, lon)
            out.append([round(lat, 5), round(lon, 5), round(hours, 1), len(v), len(dset), min(dset), max(dset),
                        "Home" if near_home else "Unknown", tid, name, pmask, key])
        # the place with most weekday hours (not home, not on trips) is "Arbeit"
        if s.work_lat is not None:  # set in the settings
            for p in out:
                if p[7] != "Home" and haversine_km(s.work_lat, s.work_lon, p[0], p[1]) * 1000 <= s.work_radius_m:
                    p[7] = "Work"
                    p[9] = "Arbeit"
        else:
            cands = [p for p in out if p[7] != "Home" and p[8] < 0 and work_hours.get(p[11], 0) > 150]
            if cands:
                w = max(cands, key=lambda p: work_hours.get(p[11], 0))
                w[7] = "Work"
                w[9] = f"Arbeit · {w[9]}"
        if not s.show_work:
            out = [p for p in out if p[7] != "Work"]
        for p in out:
            p.pop()
        out.sort(key=lambda p: -p[2])
        return out[:1500]

    # ------------------------------------------------------------ regions (states, provinces, cantons)
    @staticmethod
    def _regions():
        if not hasattr(Atlas, "_REG"):
            grid = defaultdict(list)
            try:
                data = json.loads((STATIC / "regions.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {"regions": []}
            for rid, _name, _a3, _la, _lo, rings in data["regions"]:
                polys = []
                for r in rings:
                    x = y = 0
                    poly = []
                    for i in range(0, len(r), 2):
                        x += r[i]
                        y += r[i + 1]
                        poly.append((x / 1e3, y / 1e3))
                    polys.append(poly)
                for poly in polys:
                    xs = [q[0] for q in poly]
                    ys = [q[1] for q in poly]
                    bb = (min(xs), min(ys), max(xs), max(ys))
                    for gx in range(math.floor(bb[0]), math.floor(bb[2]) + 1):
                        for gy in range(math.floor(bb[1]), math.floor(bb[3]) + 1):
                            grid[(gx, gy)].append((rid, poly, bb))
            Atlas._REG = grid
        return Atlas._REG

    def region_at(self, la: float, lo: float):
        best = None
        for rid, poly, bb in self._regions().get((math.floor(lo), math.floor(la)), ()):
            if bb[0] <= lo <= bb[2] and bb[1] <= la <= bb[3] and _pip(lo, la, poly):
                return rid
            if best is None and bb[0] - 0.02 <= lo <= bb[2] + 0.02 and bb[1] - 0.02 <= la <= bb[3] + 0.02:
                best = rid  # coastline simplified away: take the region whose box is next to the point
        return best

    def on_land(self, la: float, lo: float) -> bool:
        return any(bb[0] <= lo <= bb[2] and bb[1] <= la <= bb[3] and _pip(lo, la, poly)
                   for _rid, poly, bb in self._regions().get((math.floor(lo), math.floor(la)), ()))

    def _leg_ways(self, home, h_ap, t, legs, used_ap):
        """Ways of a trip with several stops and no GPS, e.g. home ✈ Tenerife ⛴ La Gomera.

        Returns (flight arcs, ground runs, ordered legs for the film, estimated km by mode).
        Flights use the big airport near a stop (or the airports set by hand), ships the ferry lines of the
        network (else a straight line over the water), cars and trains the main roads / railways.
        """
        fl, gr, lg, km = [], [], [], defaultdict(float)
        prev, prev_home, prev_ap = (home[0], home[1]), True, None
        fly_idx = [n for n, x in enumerate(legs) if "fly" in modes_of_transport(x["transport"])
                   and "Wasserflugzeug" not in (x["transport"] or "")]
        for n, leg in enumerate(legs):
            ms = modes_of_transport(leg["transport"]) or ["road"]
            here = (leg["lat"], leg["lon"])
            d = haversine_km(*prev, *here)
            if "Wasserflugzeug" in (leg["transport"] or ""):  # seaplane: straight from where you are, no airport
                ca = prev_ap[0] if prev_ap else ""
                a, b = [round(prev[0], 4), round(prev[1], 4)], [round(here[0], 4), round(here[1], 4)]
                fl += [[a, b, ca, "", 1], [b, a, "", ca, 1]]
                lg.append(["fly", [a[0], a[1], b[0], b[1]], [ca, ""], 1])
                km["fly"] += d
            elif "fly" in ms:
                a_ap = prev_ap or (airports.by_iata(t["ap_from"] or "") if n == fly_idx[0] else None) or \
                    (h_ap if prev_home else airports.snap(prev[0], prev[1], 60, 0))
                b_ap = airports.by_iata(leg.get("ap") or "") or \
                    (airports.by_iata(t["ap_to"] or "") if n == fly_idx[-1] else None) or \
                    airports.snap(here[0], here[1], 60, 0)
                a = [a_ap[2], a_ap[3]] if a_ap else list(prev)
                b = [b_ap[2], b_ap[3]] if b_ap else list(here)
                ca, cb = (a_ap[0] if a_ap else ""), (b_ap[0] if b_ap else "")
                for ap in (a_ap, b_ap):
                    if ap:
                        used_ap[ap[0]] = [ap[2], ap[3], ap[1]]
                fl += [[a, b, ca, cb], [b, a, cb, ca]]
                lg.append(["fly", [round(a[0], 4), round(a[1], 4), round(b[0], 4), round(b[1], 4)], [ca, cb]])
                km["fly"] += d
                if haversine_km(b[0], b[1], *here) > 8:  # from the airport to the place by road
                    runs = [[r[0], r[1], "ferry" if r[0] else "road"] for r in self.ground_route((b[0], b[1]), here, "road")]
                    gr += runs
                    lg.append(["road", runs])
            else:
                mode = "ferry" if "ferry" in ms else "rail" if "rail" in ms and "road" not in ms else "road"
                if mode == "ferry":
                    runs = self._sea_way(prev, here)
                else:
                    runs = self.est_route(prev, here, mode) if d >= 2 else []
                runs = [[r[0], r[1], "ferry" if r[0] else mode] for r in runs]
                gr += runs
                lg.append([mode, runs])
                km[mode] += d
            prev, prev_home, prev_ap = here, False, airports.by_iata(leg.get("ap") or "")
        if not fly_idx and haversine_km(*prev, home[0], home[1]) > 30:  # round trip by land: the way back home
            first = modes_of_transport(legs[0]["transport"]) or ["road"]
            kind = "rail" if "rail" in first else "road"
            ships = [n for n, x in enumerate(lg) if x[0] == "ferry"]
            if ships:  # over the water: back the same way (Corsica ⛴ Piombino 🚗 home), not another ferry
                j = ships[-1] - (1 if ships[-1] == 1 else 0)  # the first land leg is retraced too
                back = [[r[0], _rev(r[1]), r[2]] for x in reversed(lg[j:]) for r in reversed(x[1])]
                if j > 0:  # from the port home: its own way
                    port = (back[-1][1][-2], back[-1][1][-1]) if back else prev
                    more = [[r[0], r[1], "ferry" if r[0] else kind] for r in self.est_route(port, (home[0], home[1]), kind)]
                    gr += more
                    back += more
            else:
                back = [[r[0], r[1], "ferry" if r[0] else kind]
                        for r in self.est_route(prev, (home[0], home[1]), kind)]
                gr += back
            lg.append(["back", back])
            km["road"] += haversine_km(*prev, home[0], home[1]) / 2
        return fl, gr, lg, {m: round(v * 2) for m, v in km.items() if v >= 1}

    def _sea_way(self, a, b) -> list:
        """Ship between two ports: over the water (around coasts), else straight."""
        grid = self._grid_route(a, b, by_ship=True) if haversine_km(*a, *b) < 1500 else None
        if grid and any(r[0] for r in grid):  # around the coasts, over the water: all of it is the ship
            pts: list = []
            for r in grid:
                pts += r[1][2:] if pts else r[1]
            return [[1, pts]]
        return [[1, [round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)]]]

    def _land_cell(self, la: float, lo: float) -> bool:
        cache = Atlas.__dict__.get("_LANDC")
        if cache is None:
            cache = Atlas._LANDC = {}
        k = (round(la, 3), round(lo, 3))
        v = cache.get(k)
        if v is None:
            v = cache[k] = self.on_land(la, lo)
            if len(cache) > 400000:
                cache.clear()
        return v

    def ground_route(self, a: tuple, b: tuple, kind: str = "road") -> list:
        """Estimated way by car or train for a trip without GPS: [[sea 0/1, [lat, lon, lat, lon, ...]], ...].

        First along the real main roads / railways (offline Natural Earth network, ferries included);
        only where that has no way, a path over a coarse land grid.
        """
        from . import roadnet

        try:
            via = roadnet.route(kind, a, b)
        except (ValueError, KeyError, IndexError):
            via = None
        return via or self._grid_route(a, b)

    def _grid_route(self, a: tuple, b: tuple, by_ship: bool = False) -> list:
        """Way over a coarse land grid: [[sea 0/1, [lat, lon, ...]], ...].

        A shortest path over a coarse land grid (offline, from the region polygons): it goes around bays and seas
        on land and only crosses water where there is no way by land (a ferry: Corsica, Mallorca, England).
        """
        import heapq

        d = haversine_km(a[0], a[1], b[0], b[1])
        if d > 3500:  # very far by car: just the straight way
            return [[0, [round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)]]]
        g = max(0.08, min(0.3, d / 1400))  # grid step in degrees
        pad = max(1.2, 0.3 * d / 111)
        la0, la1 = min(a[0], b[0]) - pad, max(a[0], b[0]) + pad
        lo0, lo1 = min(a[1], b[1]) - pad * 1.4, max(a[1], b[1]) + pad * 1.4
        ni, nj = int((la1 - la0) / g) + 1, int((lo1 - lo0) / g) + 1
        cell = lambda la, lo: (int((la - la0) / g), int((lo - lo0) / g))  # noqa: E731
        ctr = lambda i, j: (la0 + (i + .5) * g, lo0 + (j + .5) * g)  # noqa: E731
        start, goal = cell(*a), cell(*b)
        coslat = math.cos(math.radians((a[0] + b[0]) / 2))
        land = {}

        def is_land(c):
            if c in (start, goal):
                return True
            v = land.get(c)
            if v is None:
                v = land[c] = self._land_cell(*ctr(*c))
            return v

        def h(c):
            return math.hypot(c[0] - goal[0], (c[1] - goal[1]) * coslat)

        best = {start: 0.0}
        prev = {}
        pq = [(h(start), 0.0, start)]
        steps = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        while pq:
            _f, cost, c = heapq.heappop(pq)
            if c == goal:
                break
            if cost > best.get(c, 1e18):
                continue
            lc = is_land(c)
            for di, dj in steps:
                n = (c[0] + di, c[1] + dj)
                if not (0 <= n[0] < ni and 0 <= n[1] < nj):
                    continue
                ln = is_land(n)
                step = math.hypot(di, dj * coslat)
                if by_ship:  # a ship: over the water, land only to reach the port
                    nc = cost + step * (1.0 if not (lc and ln) else 2.5)
                else:
                    nc = cost + step * (1.0 if (lc and ln) else 3.0)  # water only where it saves a lot (a ferry)
                if nc < best.get(n, 1e18):
                    best[n] = nc
                    prev[n] = c
                    heapq.heappush(pq, (nc + h(n), nc, n))
        if goal not in prev and goal != start:
            return [[0, [round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)]]]
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()
        pts = [list(a)] + [list(ctr(*c)) for c in path[1:-1]] + [list(b)]
        flags = [True] + [is_land(c) for c in path[1:-1]] + [True]
        # short stretches of "water" between land are coasts, lakes or rivers, not a ferry
        k = 0
        while k < len(flags):
            if not flags[k]:
                e = k
                while e < len(flags) and not flags[e]:
                    e += 1
                if not by_ship and haversine_km(*pts[max(0, k - 1)], *pts[min(len(pts) - 1, e)]) < 35:
                    for q in range(k, e):
                        flags[q] = True
                k = e
            else:
                k += 1
        # pull the string tight: skip grid corners while the straight way stays on land (no stair steps)
        def clear(p, q, land_wanted):
            n = max(2, int(haversine_km(*p, *q) / (g * 40)))
            return all(self._land_cell(p[0] + (q[0] - p[0]) * t / n, p[1] + (q[1] - p[1]) * t / n) == land_wanted
                       for t in range(1, n))
        sp, sf, k = [pts[0]], [flags[0]], 0
        while k < len(pts) - 1:
            j = k + 1
            if flags[k] or by_ship:
                for m in range(min(len(pts) - 1, k + 40), k + 1, -1):
                    if all(f == flags[k] for f in flags[k:m + 1]) and clear(pts[k], pts[m], flags[k]):
                        j = m
                        break
            sp.append(pts[j])
            sf.append(flags[j])
            k = j
        pts, flags = sp, sf
        # smooth the path (Chaikin), keep where land and water change
        for _ in range(3):
            if len(pts) < 3:
                break
            np_, nf = [pts[0]], [flags[0]]
            for q in range(len(pts) - 1):
                p0, p1 = pts[q], pts[q + 1]
                np_ += [[p0[0] * .75 + p1[0] * .25, p0[1] * .75 + p1[1] * .25], [p0[0] * .25 + p1[0] * .75, p0[1] * .25 + p1[1] * .75]]
                nf += [flags[q], flags[q + 1]]
            np_.append(pts[-1])
            nf.append(flags[-1])
            pts, flags = np_, nf
        runs, cur = [], None
        for pt, fl in zip(pts, flags, strict=True):
            sea = 0 if fl else 1
            if cur is None or cur[0] != sea:
                if cur is not None:
                    cur[1] += [round(pt[0], 3), round(pt[1], 3)]  # the runs touch
                cur = [sea, []]
                runs.append(cur)
            cur[1] += [round(pt[0], 3), round(pt[1], 3)]
        return runs

    def _reg(self, pts, place_list, tz, p_idx, est_trips=()):
        first: dict = {}
        days: dict = defaultdict(set)
        cache: dict = {}
        air = _airborne(pts)
        for i, p in enumerate(pts):
            if i in air:  # over-flown on a plane: not a visit
                continue
            key = (round(p["lat"] / 0.01), round(p["lon"] / 0.01))
            if key not in cache:
                cache[key] = self.region_at(p["lat"], p["lon"])
            rid = cache[key]
            if rid is None:
                continue
            k = (rid, p_idx.get(p["person"], -1))
            day = local_date(p["ts"], tz)
            days[k].add(day)
            if k not in first or day < first[k]:
                first[k] = day
        # trips without GPS (by hand, trip lists): their destination region counts too
        groups = {g["name"]: g["members"] for g in self.engine.s.groups}
        for t in est_trips:
            rid = self.region_at(*t["p"])
            if rid is None:
                continue
            who = [t["w"]] if t["w"] in p_idx else groups.get(t["w"]) or [None]
            day = t["a"]
            for w in who:
                k = (rid, p_idx.get(w, -1))
                if k in first and len(days[k]) > 0 and first[k] <= day:
                    continue
                first[k] = min(first.get(k, day), day)
                days[k].update(f"{day}#{i}" for i in range((t["n"] or 0) + 1))
        stayed = {self.region_at(*t["p"]) for t in est_trips}
        for pl in place_list:
            rid = self.region_at(pl[0], pl[1])
            if rid is not None:
                stayed.add(rid)
        return [[k[0], k[1], first[k], len(days[k]), 1 if k[0] in stayed else 0] for k in sorted(first)]


AIR_KMH = 200.0


def _airborne(pts) -> set:
    """Indices of points recorded in a plane (fast to the neighbour point of the same person, or tagged as flying)."""
    out: set = set()
    last: dict = {}
    for i, p in enumerate(pts):
        if "FLY" in str(p.get("hint") or "").upper():
            out.add(i)
        j = last.get(p["person"])
        if j is not None:
            q = pts[j]
            dkm = haversine_km(q["lat"], q["lon"], p["lat"], p["lon"])
            dt_h = max(1 / 3600, (p["ts"] - q["ts"]) / 3600)
            if dkm > 5 and dkm / dt_h > AIR_KMH:
                out.add(i)
                out.add(j)
        last[p["person"]] = i
    return out


def _pip(x: float, y: float, poly) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _encode_track(day: int, cls: int, line) -> list:
    la0, lo0 = round(line[0][0] * 1e5), round(line[0][1] * 1e5)
    out = [day, cls, la0, lo0]
    pla, plo = la0, lo0
    for la, lo in line[1:]:
        a, b = round(la * 1e5), round(lo * 1e5)
        if a == pla and b == plo:
            continue
        out += [a - pla, b - plo]
        pla, plo = a, b
    if len(out) == 4:
        out += [0, 0]
    return out


def _groups(trips, home) -> list:
    """Named destinations for far trips; sets trip['g']."""
    far = [t for t in trips if haversine_km(home[0], home[1], *t["p"]) >= FAR_KM]
    groups: list = []
    for t in sorted(far, key=lambda t: t["a"]):
        g = next((g for g in groups if haversine_km(g["lat"], g["lon"], *t["p"]) < GROUP_KM), None)
        if not g:
            g = {"key": f"g{len(groups)}", "lat": t["p"][0], "lon": t["p"][1], "names": Counter(), "n": 0, "km": 0}
            groups.append(g)
        g["names"][t["name"].removeprefix("bei ")] += 10 if t.get("fixed") else 1
        g["n"] += 1
        g["km"] = max(g["km"], haversine_km(home[0], home[1], *t["p"]))
        t["g"] = g["key"]
    out = []
    for g in groups:
        name = g["names"].most_common(1)[0][0]
        if g["names"][name] < 10:  # automatic names are often suburbs: use the known city instead
            name = places.major(g["lat"], g["lon"]) or name
        anchor = "end" if g["lon"] < home[1] - 2 else "start"
        out.append([g["key"], name, round(g["lat"], 3), round(g["lon"], 3), anchor,
                    min(18, 13 + g["n"]), 1 if g["n"] >= 2 or g["km"] > 600 else 0, round(g["km"])])
    return out


def _labels(cells, pts) -> list:
    """Town names near visited cells (GeoNames), ranked by how much time was spent nearby."""
    weight: dict = Counter()
    for (a, b, *_rest), v in cells.items():
        weight[(a, b)] += v
    out, seen = [], set()
    for (a, b), _w in weight.most_common(25000):
        lat, lon = (a + 0.5) * CELL, (b + 0.5) * CELL * 1.4
        p, d = places.nearest(lat, lon, radius_km=6)
        if p and p[0] not in seen:
            seen.add(p[0])
            rank = 0 if len(out) < 60 else 1 if len(out) < 600 else 2 if len(out) < 4000 else 3
            out.append([p[0], rank, round(p[1], 4), round(p[2], 4)])
    return out
