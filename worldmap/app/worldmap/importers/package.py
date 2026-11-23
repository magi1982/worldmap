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

``person_index`` points into ``persons`` (-1 = nobody, e.g. photos). Trips are validated again when they are stored.
"""
from __future__ import annotations

from ..settings import LABEL_RE

MAX_TRIPS = 20_000
TRIP_KEYS = ("start_date", "end_date", "destination", "country", "who", "confidence", "nights", "max_km", "transport",
             "note", "source", "lat", "lon", "radius_km", "reason")


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
        if isinstance(t, dict) and t.get("start_date") and t.get("destination"):
            clean = {k: t[k] for k in TRIP_KEYS if k in t and t[k] not in (None, "")}
            clean.setdefault("end_date", clean["start_date"])
            trips.append(clean)
    if len(obj.get("trips") or []) > MAX_TRIPS:
        problems.append(f"only the first {MAX_TRIPS} trips were read")
    points = []
    bad = 0
    for p in obj.get("points") or []:
        try:
            ts, lat, lon = int(p[0]), float(p[1]), float(p[2])
            pi = int(p[3]) if len(p) > 3 and p[3] is not None else -1
            src = str(p[4])[:20] if len(p) > 4 and p[4] else "package"
            hint = str(p[5])[:200] if len(p) > 5 and p[5] else None
        except (TypeError, ValueError, IndexError):
            bad += 1
            continue
        person = persons[pi] if 0 <= pi < len(persons) else ""
        points.append((ts, lat, lon, src, None, hint, person))
    if bad:
        problems.append(f"{bad} points could not be read")
    return points, trips, persons, groups, problems
