"""Worldmap package: one file with everything – trips (with who was there) and GPS points (with whose phone).

Format (JSON, optionally gzip-compressed, file name ``*.worldmap.json`` or ``*.worldmap.json.gz``)::

    {
      "worldmap": 1,
      "persons": ["Alex", "Sam"],
      "groups": [{"name": "Familie", "members": ["Alex", "Sam"], "extra": 2}],
      "trips": [{"start_date": "2024-07-13", "end_date": "2024-07-25", "destination": "...", "who": "Familie",
                 "country": "...", "transport": "Flug · Auto", "lat": 42.6, "lon": 18.1, ...}],
      "points": [[ts, lat, lon, person_index, "google", "IN_TRAIN"], ...]
    }

Also read (written by other tools and AIs): ``"when": "Juli 2009"`` instead of start/end dates, ``"legs"`` (stations),
points as objects ``{"time": "2024-07-13T10:00:00Z", "lat": 46.9, "lon": 7.4, "person": "Alex"}`` and times in
milliseconds or ISO text.

``person_index`` points into ``persons`` (-1 = nobody, e.g. photos). Trips are validated again when they are stored.
"""
from __future__ import annotations

from ..settings import LABEL_RE
from ..timeparse import parse_ts

MAX_TRIPS = 20_000
TRIP_KEYS = ("start_date", "end_date", "destination", "country", "who", "confidence", "nights", "max_km", "transport",
             "note", "source", "lat", "lon", "radius_km", "reason", "date_prec", "legs", "when")


def _ts(v) -> int | None:
    """Unix seconds; also milliseconds and ISO text ("2024-07-13T10:00:00Z") – what other tools and AIs write."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        t = int(v / 1000) if abs(v) > 1e11 else int(v)
    else:
        t = parse_ts(str(v), "UTC")
        if t is None:
            return None
    return t if 315_532_800 <= t <= 4_102_444_800 else None  # 1980 … 2100


def is_package(obj) -> bool:
    return isinstance(obj, dict) and obj.get("worldmap") == 1 and isinstance(obj.get("points", []), list)


def parse(obj):
    """-> (points as (ts, lat, lon, src, acc, hint, person), trips, persons, groups, problems)"""
    problems: list[str] = []
    persons = [str(p).strip() for p in obj.get("persons") or [] if LABEL_RE.match(str(p).strip())][:50]
    groups = []
    for g in obj.get("groups") or []:
        if isinstance(g, dict) and LABEL_RE.match(str(g.get("name", "")).strip()):
            groups.append({"name": str(g["name"]).strip(),
                           "members": [m for m in g.get("members") or [] if m in persons],
                           "extra": max(0, min(20, int(g.get("extra") or 0)))})
    trips = []
    for t in (obj.get("trips") or [])[:MAX_TRIPS]:
        if isinstance(t, dict) and (t.get("start_date") or t.get("when")) and t.get("destination"):
            clean = {k: t[k] for k in TRIP_KEYS if k in t and t[k] not in (None, "")}
            if clean.get("start_date"):
                clean.setdefault("end_date", clean["start_date"])
                if clean.get("when"):  # exact dates win
                    del clean["when"]
            trips.append(clean)
    if len(obj.get("trips") or []) > MAX_TRIPS:
        problems.append(f"nur die ersten {MAX_TRIPS} Reisen gelesen")
    points = []
    bad = 0
    for p in obj.get("points") or []:
        try:
            if isinstance(p, dict):  # {"time": "2024-07-13T10:00:00Z", "lat": …, "lon": …, "person": "Alex"} – easy for an AI
                ts = _ts(p.get("time", p.get("ts")))
                lat, lon = float(p["lat"]), float(p.get("lon", p.get("lng")))
                who = str(p.get("person") or "").strip()
                if who and who not in persons and len(persons) < 50 and LABEL_RE.match(who):
                    persons.append(who)
                pi = persons.index(who) if who in persons else -1
                src = str(p.get("source") or "package")[:20]
                hint = str(p["hint"])[:200] if p.get("hint") else None
            else:
                ts, lat, lon = _ts(p[0]), float(p[1]), float(p[2])
                pi = int(p[3]) if len(p) > 3 and p[3] is not None else -1
                src = str(p[4])[:20] if len(p) > 4 and p[4] else "package"
                hint = str(p[5])[:200] if len(p) > 5 and p[5] else None
        except (TypeError, ValueError, IndexError, KeyError):
            bad += 1
            continue
        if ts is None:
            bad += 1
            continue
        person = persons[pi] if 0 <= pi < len(persons) else ""
        points.append((ts, lat, lon, src, None, hint, person))
    if bad:
        problems.append(f"{bad} Positionen unlesbar (Zeit oder Koordinaten fehlen) – übersprungen")
    return points, trips, persons, groups, problems
