"""Airports with scheduled flights (OurAirports, public domain) – flights start and end at a real airport.

GPS points around a flight are often a bit off: the last point before take-off may be on the motorway, the first
after landing at the hotel. ``snap`` moves such an end to the airport nearby; large airports win over small ones.
"""
from __future__ import annotations

import json
import logging
import math
from functools import lru_cache
from pathlib import Path

from .geo import haversine_km

log = logging.getLogger(__name__)
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


def _fold(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def search(query: str, limit: int = 8, near: tuple | None = None) -> list[dict]:
    """Airports for a free text: a code ("DXB"), an airport name ("Malpensa") or a town ("Dubai", "Mailand").

    Nobody has to know the codes. ``near`` (lat, lon) of a town that was found adds the airports around it.
    Big airports come first. -> [{"code", "name", "city", "lat", "lon", "size"}]
    """
    q = _fold(query)
    if len(q) < 2:
        return []
    keys = {q}
    found: dict = {}
    near_km = LARGE_KM
    try:  # other-language town names: "mailand" → "milan"
        from . import places

        alias = places._exonyms().get(q)
        if alias:
            keys.add(_fold(alias[0]))
            near = near or (alias[1], alias[2])
        if near is None and len(q) >= 3:  # an island, region or country ("Teneriffa", "Malediven"): its airports
            hits = places.search(query, limit=3)
            land = next((h for h in hits if h.get("kind") == "country" and h.get("cc")), None)
            if land and _fold(land["name"]) == q:
                box = places.country_box(land["cc"])
                if box:
                    in_box = [r for rows in _index().values() for r in rows
                              if box[0] <= r[3] <= box[2] and box[1] <= r[4] <= box[3]]
                    for r in in_box:
                        found.setdefault(r[0], (2 if r[5] == 2 else 5, r))
            hit = next((h for h in hits if h.get("lat") is not None and h.get("kind") != "country"), None)
            if hit:
                near = (hit["lat"], hit["lon"])
                near_km = max(LARGE_KM, min(float(hit.get("radius_km") or 0), 250.0))
    except Exception:  # noqa: BLE001 – the search works without the town list too
        log.debug("airport search without town names", exc_info=True)
    for rows in _index().values():
        for r in rows:
            if len(q) == 3 and r[0].lower() == q:
                found[r[0]] = (0, r)
                continue
            name, city = _fold(r[1]), _fold(r[2] or "")
            for k in keys:
                if len(k) < 3:
                    continue
                if city == k or city.startswith(k + " ") or city.startswith(k + "("):
                    best = 0.5 if k in name else 1  # "Dubai International" before "Al Maktoum (Dubai)"
                    found.setdefault(r[0], (best if r[5] == 2 else 2, r))
                elif k in name.replace("-", " ") or (len(k) >= 4 and k in city):
                    found.setdefault(r[0], (1.5 if r[5] == 2 else 4, r))
    if near:
        for rows in _index().values():
            for r in rows:
                d = haversine_km(near[0], near[1], r[3], r[4])
                if r[0] not in found and d <= (near_km if r[5] == 2 else MEDIUM_KM):
                    found[r[0]] = (2 if r[5] == 2 else 5, r)
    ranked = sorted(found.values(), key=lambda x: (x[0], -x[1][5], x[1][1]))
    return [{"code": r[0], "name": r[1], "city": r[2] or "", "lat": r[3], "lon": r[4], "size": r[5]}
            for _, r in ranked[:limit]]
