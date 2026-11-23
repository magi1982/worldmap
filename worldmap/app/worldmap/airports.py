"""Airports with scheduled flights (OurAirports, public domain) – flights start and end at a real airport.

GPS points around a flight are often a bit off: the last point before take-off may be on the motorway, the first
after landing at the hotel. ``snap`` moves such an end to the airport nearby; large airports win over small ones.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from .geo import haversine_km

DATA = Path(__file__).parent / "data" / "airports.json"
LARGE_KM = 60.0
MEDIUM_KM = 35.0


@lru_cache(maxsize=1)
def _index():
    try:
        rows = json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rows = []
    grid: dict = {}
    for r in rows:
        grid.setdefault((math.floor(r[3]), math.floor(r[4])), []).append(r)
    return grid


def by_iata(code: str):
    """-> (IATA, name, lat, lon) for an IATA code, or None."""
    code = (code or "").strip().upper()
    for rows in _index().values():
        for r in rows:
            if r[0] == code:
                return (r[0], r[1], r[3], r[4])
    return None


def by_city(name: str):
    """-> (IATA, name, lat, lon) of the biggest airport serving a town ("Marsa Alam" → RMF), or None."""
    import unicodedata

    def fold(s):
        return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()

    key, best = fold(name or ""), None
    if len(key) < 3:
        return None
    for rows in _index().values():
        for r in rows:
            if fold(r[2] or "") == key and (best is None or r[5] > best[5]):
                best = r
    return (best[0], best[1], best[3], best[4]) if best else None


def snap(lat: float, lon: float, max_large: float = LARGE_KM, max_medium: float = MEDIUM_KM):
    """-> (IATA, name, lat, lon) of the airport this flight end belongs to, or None."""
    best, score = None, 1e9
    grid = _index()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for r in grid.get((math.floor(lat) + dy, math.floor(lon) + dx), ()):
                d = haversine_km(lat, lon, r[3], r[4])
                limit = max_large if r[5] == 2 else max_medium
                s = d if r[5] == 2 else d * 1.6
                if d <= limit and s < score:
                    best, score = r, s
    return (best[0], best[1], best[3], best[4]) if best else None
