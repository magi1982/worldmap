"""Build the data of the five-view map ("atlas") from the database.

The output has the same shape the interactive map expects:

* ``core``   – trips, days, cells, places, groups, flights, est. areas, people/colours
* ``tracks`` – per day and transport mode: [day, cls, lat0*1e5, lon0*1e5, dlat, dlon, ...]
* ``labels`` – place names near the tracks
* ``gem``    – Swiss municipalities: [id, first day, days, stayed]

Everything is computed from points, segments and trips and cached by a data fingerprint.
"""
from __future__ import annotations

import gzip
import json
import logging
import math
import threading
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from . import places
from .geo import haversine_km, simplify
from .routing import FLIGHT_KMH
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

# Google activity names and our transport words -> mode
ACTIVITY = (
    ("fly", ("FLYING", "flying", "Flug", "flight")),
    ("ferry", ("FERRY", "ferry", "Schiff", "boat", "SAILING")),
    ("rail", ("TRAIN", "SUBWAY", "TRAM", "BUS", "in train", "in subway", "in tram", "in bus", "Zug", "rail",
              "METRO", "in metro")),
    ("foot", ("WALKING", "RUNNING", "ON_FOOT", "CYCLING", "BICYCLE", "walking", "running", "cycling", "zu Fuss", "Velo")),
    ("road", ("VEHICLE", "DRIVING", "MOTORCYCLING", "passenger vehicle", "Auto", "Wohnmobil", "car", "driving")),
)


def mode_of_text(text: str | None) -> str | None:
    if not text:
        return None
    for mode, words in ACTIVITY:
        if any(w in text for w in words):
            return mode
    return None


def modes_of_transport(text: str | None) -> list[str]:
    out = []
    for part in (text or "").split("·"):
        m = mode_of_text(part.strip())
        if m and m not in out:
            out.append(m)
    return out


def mode_of_pair(a: dict, b: dict, dist_km: float) -> str:
    dt_h = max(1e-6, (b["ts"] - a["ts"]) / 3600)
    speed = dist_km / dt_h
    if speed >= FLIGHT_KMH or (dist_km > 800 and dt_h < 24):
        return "fly"
    hinted = mode_of_text(b.get("hint")) or mode_of_text(a.get("hint"))
    if hinted and hinted != "fly":
        return hinted
    if speed < 7:
        return "foot"
    return "road"


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
        """gzip-compressed JSON of one part: core | tracks | labels | gem."""
        if part not in ("core", "tracks", "labels", "gem"):
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
        alltag_i = who_idx["Alltag"]

        def year_of(ts):
            hb = ts // 3600
            if hb not in hour_year:
                hour_year[hb] = local_date(ts, tz)
            return hour_year[hb]

        cur: list = []
        cur_key = None

        def flush():
            nonlocal cur
            if cur_key is not None and len(cur) >= 2:
                di, mode = cur_key
                line = simplify(cur, 0.00004)
                tracks.append(_encode_track(di, TCLS.get(mode, 0), line))
            cur = []

        prev = None
        for p in pts:
            day = year_of(p["ts"])
            di = day_index[day]
            days[di][7] = 1
            dist_home = haversine_km(home[0], home[1], p["lat"], p["lon"])
            days[di][5] = max(days[di][5], round(dist_home))
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
            tid = tid_of_day.get(day, -1)
            km_idx = {"road": 1, "rail": 2, "foot": 3, "fly": 4, "ferry": 1}[mode]
            if mode != "fly":
                if seg and seg["mode"] == "road":
                    geom = seg["geometry"]
                    dkm = sum(haversine_km(*geom[i], *geom[i + 1]) for i in range(len(geom) - 1))
                elif dkm > 3 and dt > 3600 and not seg:
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
                flights.append([day, [round(prev["lat"], 4), round(prev["lon"], 4)], [round(p["lat"], 4), round(p["lon"], 4)]])
                prev = p
                continue
            key = (di, mode)
            if key != cur_key:
                flush()
                cur_key = key
                cur = [[prev["lat"], prev["lon"]]]
            if seg and seg["mode"] == "road":
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
                main = modes[0]
                k = {main: round(2 * dist * (1.0 if main == "fly" else 1.25))}
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
        place_list = self._places(pts, trip_rows, tid_of_day, home, tz)
        gem = self._gem(pts, place_list, tz)
        labels = _labels(cells, pts)
        who = self.who_list(trip_rows)
        years = sorted({t["y"] for t in out_trips} | {int(d[0][:4]) for d in days[:1]} | {int(d[0][:4]) for d in days[-1:]})
        core = {
            "home": [round(home[0], 4), round(home[1], 4)],
            "who": who, "persons": s.labels, "groups_who": s.who_options,
            "trips": out_trips, "days": days,
            "alltagYear": {y: {m: round(v) for m, v in ms.items()} for y, ms in alltag_year.items()},
            "flights": flights, "groups": groups, "places": place_list,
            "cells": [[a, b, w, m, y, round(v, 2)] for (a, b, w, m, y), v in cells.items()],
            "est": est, "cantons": _cantons(), "years": years,
            "routed": len(segs),
        }
        return {"core": core, "tracks": tracks, "labels": labels, "gem": gem}

    def who_list(self, trip_rows) -> list[str]:
        out = []
        for w in [*self.engine.s.labels, *self.engine.s.who_options, *(t["who"] for t in trip_rows if t["who"])]:
            if w and w not in out and w != "Alltag":
                out.append(w)
        return [*out, "offen", "Alltag"] if any(not t["who"] for t in trip_rows) else [*out, "Alltag"]

    # ------------------------------------------------------------ places
    def _places(self, pts, trip_rows, tid_of_day, home, tz):
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
                    stays.append((lat, lon, a["ts"], plist[j]["ts"]))
                i = j + 1
        grid = defaultdict(list)
        for st in stays:
            near = haversine_km(home[0], home[1], st[0], st[1]) < 0.35
            grid["home" if near else (round(st[0] / 0.003), round(st[1] / 0.004))].append(st)
        work_hours: dict = defaultdict(float)
        out = []
        for key, v in grid.items():
            lat = sum(x[0] for x in v) / len(v)
            lon = sum(x[1] for x in v) / len(v)
            mun = self._mun_at(lat, lon)
            hours = sum((x[3] - x[2]) / 3600 for x in v)
            dset = {local_date(x[2], tz) for x in v}
            for x in v:  # weekday stays within one day count towards "work"
                d0 = local_date(x[2], tz)
                if date.fromisoformat(d0).weekday() < 5 and d0 == local_date(x[3], tz):
                    work_hours[key] += (x[3] - x[2]) / 3600
            tids = Counter(tid_of_day.get(d, -1) for d in dset)
            tid = tids.most_common(1)[0][0]
            near_home = haversine_km(home[0], home[1], lat, lon) < 0.35
            if near_home:
                name = "Zuhause"
            elif mun:
                name = mun[1]
            else:
                name, _ = places.describe(lat, lon)
            out.append([round(lat, 5), round(lon, 5), round(hours, 1), len(v), len(dset), min(dset), max(dset),
                        "Home" if near_home else "Unknown", tid, name, mun[0] if mun else 0, key])
        # the place with most weekday hours (not home, not on trips) is "Arbeit"
        cands = [p for p in out if p[7] != "Home" and p[8] < 0 and work_hours.get(p[11], 0) > 150]
        if cands:
            w = max(cands, key=lambda p: work_hours.get(p[11], 0))
            w[7] = "Work"
            w[9] = f"Arbeit · {w[9]}"
        for p in out:
            p.pop()
        out.sort(key=lambda p: -p[2])
        return out[:1500]

    # ------------------------------------------------------------ Swiss municipalities
    @staticmethod
    def _ch():
        if not hasattr(Atlas, "_CH"):
            data = json.loads((STATIC / "ch.json").read_text(encoding="utf-8"))
            mun = []
            for mid, name, kt, _la, _lo, rings in data["mun"]:
                polys = []
                for r in rings:
                    x = y = 0
                    pts = []
                    for i in range(0, len(r), 2):
                        x += r[i]
                        y += r[i + 1]
                        pts.append((x / 1e4, y / 1e4))  # lon, lat
                    polys.append(pts)
                xs = [p[0] for poly in polys for p in poly]
                ys = [p[1] for poly in polys for p in poly]
                mun.append((mid, name, kt, polys, (min(xs), min(ys), max(xs), max(ys))))
            grid = defaultdict(list)
            for m in mun:
                b = m[4]
                for gx in range(math.floor(b[0] * 10), math.floor(b[2] * 10) + 1):
                    for gy in range(math.floor(b[1] * 10), math.floor(b[3] * 10) + 1):
                        grid[(gx, gy)].append(m)
            Atlas._CH = grid
        return Atlas._CH

    def _mun_at(self, la, lo):
        if not (45.8 <= la <= 47.9 and 5.9 <= lo <= 10.6):
            return None
        for m in self._ch().get((math.floor(lo * 10), math.floor(la * 10)), ()):
            b = m[4]
            if not (b[0] <= lo <= b[2] and b[1] <= la <= b[3]):
                continue
            inside = False
            for poly in m[3]:
                if _pip(lo, la, poly):
                    inside = not inside
            if inside:
                return (m[0], m[1])
        return None

    def _gem(self, pts, place_list, tz):
        first: dict = {}
        days: dict = defaultdict(set)
        cell_cache: dict = {}
        for p in pts:
            if not (45.8 <= p["lat"] <= 47.9 and 5.9 <= p["lon"] <= 10.6):
                continue
            key = (round(p["lat"] / 0.004), round(p["lon"] / 0.005))
            if key not in cell_cache:
                m = self._mun_at(p["lat"], p["lon"])
                cell_cache[key] = m[0] if m else None
            mid = cell_cache[key]
            if mid is None:
                continue
            day = local_date(p["ts"], tz)
            days[mid].add(day)
            if mid not in first or day < first[mid]:
                first[mid] = day
        stayed = {p[10] for p in place_list if p[10]}
        return [[mid, first[mid], len(days[mid]), 1 if mid in stayed else 0] for mid in sorted(first)]


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
    for (a, b), _w in weight.most_common(4000):
        lat, lon = (a + 0.5) * CELL, (b + 0.5) * CELL * 1.4
        p, d = places.nearest(lat, lon, radius_km=6)
        if p and p[0] not in seen:
            seen.add(p[0])
            rank = 1 if len(out) < 40 else 2 if len(out) < 300 else 3
            out.append([p[0], rank, round(p[1], 4), round(p[2], 4)])
    return out


def _cantons() -> dict:
    try:
        return json.loads((STATIC / "ch.json").read_text(encoding="utf-8"))["cantons"]
    except (OSError, ValueError, KeyError):
        return {}
