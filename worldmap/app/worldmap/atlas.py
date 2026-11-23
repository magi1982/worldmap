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
import json
import logging
import math
import threading
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import places
from .geo import haversine_km, simplify
from .modes import estimate_km, mode_of_pair, mode_of_text, modes_of_transport  # noqa: F401 - re-exported for tests
from .timeparse import local_date

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
        return "a2-" + str(abs(hash(parts)) % 10**12)

    def get(self, part: str) -> bytes:
        """gzip-compressed JSON of one part: core | tracks | labels | reg."""
        if part not in ("core", "tracks", "labels", "reg"):
            raise KeyError(part)
        fp = self.fingerprint()
        with self._lock:
            if self._mem.get("fp") != fp:
                self._mem = {"fp": fp, **self._load_or_build(fp)}
            return self._mem[part]

    # ------------------------------------------------------------ cache
    def _load_or_build(self, fp: str) -> dict:
        if self.cache_dir:
            f = self.cache_dir / f"atlas-{fp}.json.gz"
            if f.exists():
                try:
                    data = json.loads(gzip.decompress(f.read_bytes()))
                    return {k: gzip.compress(json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode(), 6)
                            for k, v in data.items()}
                except (OSError, ValueError):
                    pass
        data = self.build()
        if self.cache_dir:
            try:
                for old in self.cache_dir.glob("atlas-*.json.gz"):
                    old.unlink()
                (self.cache_dir / f"atlas-{fp}.json.gz").write_bytes(
                    gzip.compress(json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode(), 6))
            except OSError as exc:
                log.warning("atlas cache not written: %s", exc)
        return {k: gzip.compress(json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode(), 6) for k, v in data.items()}

    # ------------------------------------------------------------ build
    def build(self) -> dict:
        eng = self.engine
        s = eng.s
        tz = s.timezone
        home = eng.resolve_home() or (47.0, 8.0)
        trips_db = eng.db.trips()
        pts = eng.db.points()
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
        for i, t in enumerate(trip_rows):
            d = date.fromisoformat(t["start_date"])
            while d.isoformat() <= t["end_date"]:
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
            if mode == "jump":  # GPS jump: no line, no kilometres
                flush()
                cur_key = None
                prev = p
                continue
            tid = tid_of_day.get(day, -1)
            km_idx = {"road": 1, "rail": 2, "foot": 3, "fly": 4, "ferry": 1}[mode]
            routed = bool(seg and seg["mode"] in ("road", "rail") and seg["geometry"])
            if routed:
                mode = seg["mode"]
            if mode != "fly":
                if routed:
                    geom = seg["geometry"]
                    dkm = sum(haversine_km(*geom[i], *geom[i + 1]) for i in range(len(geom) - 1))
                elif dkm > 3 and ((seg and seg["mode"] == "none") or dt > 3600 or dkm > 50):
                    # a long gap without a route: do not draw a straight line
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
                flights.append([day, [round(prev["lat"], 4), round(prev["lon"], 4)], [round(p["lat"], 4), round(p["lon"], 4)],
                                round(tod(prev["ts"]), 4), pi])
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
        for r in days:
            for i in (1, 2, 3, 4):
                r[i] = round(r[i], 1)
            r[6] = tid_of_day.get(r[0], -1)

        # ---- trips in the map format
        out_trips, est = [], []
        for i, t in enumerate(trip_rows):
            k = {m: round(v) for m, v in trip_km.get(i, {}).items() if v >= 1}
            modes = [m for m in MODES if m in k] or modes_of_transport(t["transport"]) or ["road"]
            for m in modes_of_transport(t["transport"]):
                if m not in modes:
                    modes.append(m)
            lat = t["lat"] if t["lat"] is not None else home[0]
            lon = t["lon"] if t["lon"] is not None else home[1]
            dist = t["max_km"] if t["max_km"] is not None else haversine_km(home[0], home[1], lat, lon)
            fl = []
            if not k:  # no GPS: estimate the distance there and back
                k = estimate_km(dist, modes, t["nights"] or 0)
                if "fly" in modes and t["lat"] is not None:
                    fl = [[[home[0], home[1]], [lat, lon]], [[lat, lon], [home[0], home[1]]]]
                if t["radius_km"]:
                    est.append([i, lat, lon, t["radius_km"]])
            else:
                fl = [[f[1], f[2]] for f in flights if t["start_date"] <= f[0] <= t["end_date"]]
            name = t["destination"] or "Reise"
            out_trips.append({
                "id": i, "dbid": t["id"], "a": t["start_date"], "b": t["end_date"], "y": int(t["start_date"][:4]),
                "n": t["nights"], "w": t["who"] or "offen", "name": name, "c": t["country"], "m": modes, "g": None,
                "km": sum(k.values()), "dw": wd(t["start_date"]), "dwb": wd(t["end_date"]), "fl": fl, "k": k,
                "p": [round(lat, 4), round(lon, 4)], "conf": t["confidence"], "approx": t["approx"],
                "r": t["radius_km"], "fixed": 1 if (t["source"] == "manual" or t["locked"]) else 0,
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
            "colors": s.colors(), "trackP": track_p, "dayP": day_p,
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
