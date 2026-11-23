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
    reach = max(max_large, max_medium)
    ny = int(reach / 111) + 1
    nx = int(reach / (111 * max(0.05, math.cos(math.radians(lat))))) + 1
    for dy in range(-ny, ny + 1):
        for dx in range(-min(nx, 180), min(nx, 180) + 1):
            for r in grid.get((math.floor(lat) + dy, math.floor(lon) + dx), ()):
                d = haversine_km(lat, lon, r[3], r[4])
                limit = max_large if r[5] == 2 else max_medium
                s = d if r[5] == 2 else d * 1.6
                if d <= limit and s < score:
                    best, score = r, s
    return (best[0], best[1], best[3], best[4]) if best else None


def nearest_large(lat: float, lon: float, max_km: float = 400.0):
    """-> (IATA, name, lat, lon) of the nearest large airport within max_km, or None.

    For a holiday island without big airport (La Gomera) the trip flies to the big one nearby (Tenerife) and goes on
    by ferry or road from there.
    """
    best, bd = None, max_km
    grid = _index()
    r = int(max_km / 80) + 1  # cells are 1° (≈ 80–111 km)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            for row in grid.get((math.floor(lat) + dy, math.floor(lon) + dx), ()):
                if row[5] != 2:
                    continue
                d = haversine_km(lat, lon, row[3], row[4])
                if d < bd:
                    best, bd = row, d
    return (best[0], best[1], best[3], best[4]) if best else None
