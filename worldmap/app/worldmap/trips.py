"""Turn raw points into trips.

A *day away* is a local calendar day on which a person was at least
``min_trip_km`` from home. Consecutive days away (or a day away followed by a
night away) form a trip. Trips of different people that overlap are merged
so that the who-question can see who travelled together.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .geo import haversine_km
from .timeparse import local_date


@dataclass
class DayAway:
    day: str
    person: str
    max_km: float
    far_lat: float
    far_lon: float
    overnight: bool  # last point of the day was away from home
    hints: set = field(default_factory=set)


@dataclass
class TripCandidate:
    start: str
    end: str
    persons: set
    max_km: float
    lat: float
    lon: float
    nights: int
    hints: set
    days_by_person: dict

    @property
    def key(self) -> tuple:
        return (self.start, self.end)


def days_away(points: list[dict], home: tuple[float, float], min_km: float, tz: str) -> list[DayAway]:
    by = defaultdict(list)
    for p in points:
        by[(p["person"], local_date(p["ts"], tz))].append(p)
    out = []
    for (person, day), pts in by.items():
        pts.sort(key=lambda p: p["ts"])
        best, far = -1.0, None
        hints = set()
        for p in pts:
            d = haversine_km(home[0], home[1], p["lat"], p["lon"])
            if d > best:
                best, far = d, p
            if p.get("hint"):
                hints.add(p["hint"])
        if best >= min_km:
            last = pts[-1]
            overnight = haversine_km(home[0], home[1], last["lat"], last["lon"]) >= min_km
            out.append(DayAway(day, person, best, far["lat"], far["lon"], overnight, hints))
    return sorted(out, key=lambda d: (d.day, d.person))


def group_trips(days: list[DayAway], gap_days: int = 1) -> list[TripCandidate]:
    """Group per person, then merge overlapping trips of different persons."""
    per_person = defaultdict(list)
    for d in days:
        per_person[d.person].append(d)
    runs = []
    for person, ds in per_person.items():
        ds.sort(key=lambda d: d.day)
        cur = [ds[0]]
        for d in ds[1:]:
            prev = cur[-1]
            gap = (date.fromisoformat(d.day) - date.fromisoformat(prev.day)).days
            # continue if the next day follows, or a short gap while the person never came home
            if gap == 1 or (gap <= gap_days + 1 and prev.overnight):
                cur.append(d)
            else:
                runs.append((person, cur))
                cur = [d]
        runs.append((person, cur))

    runs.sort(key=lambda r: r[1][0].day)
    merged: list[TripCandidate] = []
    for person, ds in runs:
        start, end = ds[0].day, ds[-1].day
        far = max(ds, key=lambda d: d.max_km)
        hints = set().union(*(d.hints for d in ds))
        cand = TripCandidate(start, end, {person}, far.max_km, far.far_lat, far.far_lon, 0,
                             hints, {person: [d.day for d in ds]})
        for m in merged:
            if not (cand.end < m.start or cand.start > m.end):
                m.start, m.end = min(m.start, cand.start), max(m.end, cand.end)
                m.persons |= cand.persons
                m.hints |= cand.hints
                m.days_by_person.update(cand.days_by_person)
                if cand.max_km > m.max_km:
                    m.max_km, m.lat, m.lon = cand.max_km, cand.lat, cand.lon
                m.nights = (date.fromisoformat(m.end) - date.fromisoformat(m.start)).days
                break
        else:
            merged.append(cand)
    for m in merged:
        m.nights = (date.fromisoformat(m.end) - date.fromisoformat(m.start)).days
    return sorted(merged, key=lambda m: m.start)


def overlap_share(cand: TripCandidate, a: str, b: str) -> float:
    """Share of days on which both persons were away (0..1)."""
    da, db = set(cand.days_by_person.get(a, [])), set(cand.days_by_person.get(b, []))
    if not da or not db:
        return 0.0
    return len(da & db) / len(da | db)
