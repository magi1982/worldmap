"""Offline place names from the bundled GeoNames gazetteer (CC BY 4.0)."""
from __future__ import annotations

import gzip
import json
import math
from functools import lru_cache
from pathlib import Path

from .geo import haversine_km

DATA = Path(__file__).with_name("data") / "places.json.gz"

COUNTRY_DE = {
    "CH": "Schweiz", "DE": "Deutschland", "AT": "Österreich", "FR": "Frankreich", "IT": "Italien",
    "ES": "Spanien", "PT": "Portugal", "GB": "England", "IE": "Irland", "NL": "Niederlande",
    "BE": "Belgien", "LU": "Luxemburg", "LI": "Liechtenstein", "DK": "Dänemark", "SE": "Schweden",
    "NO": "Norwegen", "FI": "Finnland", "PL": "Polen", "CZ": "Tschechien", "SK": "Slowakei",
    "HU": "Ungarn", "SI": "Slowenien", "HR": "Kroatien", "BA": "Bosnien", "RS": "Serbien",
    "ME": "Montenegro", "AL": "Albanien", "GR": "Griechenland", "TR": "Türkei", "CY": "Zypern",
    "MT": "Malta", "EG": "Ägypten", "MA": "Marokko", "TN": "Tunesien", "KE": "Kenia",
    "MV": "Malediven", "AE": "Vereinigte Arabische Emirate", "US": "USA", "CA": "Kanada", "AU": "Australien",
    "NZ": "Neuseeland", "JP": "Japan", "CN": "China", "IN": "Indien", "ID": "Indonesien", "VN": "Vietnam",
    "BR": "Brasilien", "AR": "Argentinien", "MX": "Mexiko", "ZA": "Südafrika", "TZ": "Tansania", "MU": "Mauritius",
    "LK": "Sri Lanka", "SG": "Singapur", "MY": "Malaysia", "PH": "Philippinen", "KR": "Südkorea", "CU": "Kuba",
    "DO": "Dominikanische Republik", "CR": "Costa Rica", "PE": "Peru", "CL": "Chile", "JO": "Jordanien", "IL": "Israel",
    "TH": "Thailand", "IS": "Island", "MC": "Monaco", "SM": "San Marino", "VA": "Vatikan",
}


# Regions, islands and coasts people use for holidays: (name, lat, lon, country, radius_km)
REGIONS = [
    ("Korsika", 42.15, 9.10, "Frankreich", 60), ("Sardinien", 40.10, 9.05, "Italien", 90),
    ("Sizilien", 37.55, 14.20, "Italien", 110), ("Elba", 42.78, 10.27, "Italien", 15),
    ("Mallorca", 39.62, 2.98, "Spanien", 45), ("Menorca", 39.95, 4.10, "Spanien", 25),
    ("Ibiza", 38.98, 1.43, "Spanien", 18), ("Teneriffa", 28.29, -16.62, "Spanien", 35),
    ("Gran Canaria", 27.92, -15.55, "Spanien", 25), ("La Gomera", 28.10, -17.23, "Spanien", 12),
    ("Lanzarote", 29.04, -13.63, "Spanien", 25), ("Fuerteventura", 28.36, -14.05, "Spanien", 40),
    ("Kreta", 35.24, 24.90, "Griechenland", 90), ("Rhodos", 36.17, 27.92, "Griechenland", 30),
    ("Kos", 36.85, 27.20, "Griechenland", 20), ("Kykladen", 37.00, 25.20, "Griechenland", 70),
    ("Toskana", 43.40, 11.00, "Italien", 70), ("Ligurien", 44.30, 8.70, "Italien", 70),
    ("Südtirol", 46.60, 11.30, "Italien", 55), ("Gardasee", 45.64, 10.67, "Italien", 25),
    ("Lago Maggiore", 45.95, 8.65, "Italien", 30), ("Comer See", 46.00, 9.25, "Italien", 25),
    ("Adria (Emilia-Romagna)", 44.20, 12.40, "Italien", 50), ("Provence", 43.90, 5.40, "Frankreich", 70),
    ("Côte d'Azur", 43.55, 7.00, "Frankreich", 60), ("Bretagne", 48.15, -3.00, "Frankreich", 110),
    ("Normandie", 49.10, -0.40, "Frankreich", 100), ("Atlantikküste (Landes)", 44.00, -1.30, "Frankreich", 90),
    ("Elsass", 48.30, 7.45, "Frankreich", 50), ("Costa Brava", 41.90, 3.10, "Spanien", 45),
    ("Costa Daurada", 41.10, 1.10, "Spanien", 45), ("Algarve", 37.10, -8.20, "Portugal", 60),
    ("Istrien", 45.20, 13.90, "Kroatien", 40), ("Dalmatien", 43.50, 16.40, "Kroatien", 110),
    ("Tessin", 46.30, 8.85, "Schweiz", 40), ("Engadin", 46.60, 9.95, "Schweiz", 35),
    ("Wallis", 46.20, 7.60, "Schweiz", 55), ("Berner Oberland", 46.60, 7.80, "Schweiz", 35),
    ("Graubünden", 46.70, 9.60, "Schweiz", 60), ("Bodensee", 47.60, 9.40, "Deutschland", 30),
    ("Schwarzwald", 48.10, 8.20, "Deutschland", 60), ("Allgäu", 47.60, 10.30, "Deutschland", 40),
    ("Tirol", 47.25, 11.40, "Österreich", 70), ("Vorarlberg", 47.25, 9.90, "Österreich", 30),
    ("Westküste Schweden", 58.00, 11.60, "Schweden", 110), ("Cornwall", 50.40, -4.90, "England", 60),
    ("Schottland", 56.80, -4.20, "Schottland", 180), ("Lappland", 67.50, 25.50, "Finnland", 250),
    ("Malediven", 3.20, 73.20, "Malediven", 120), ("Rotes Meer (Ägypten)", 26.50, 34.00, "Ägypten", 120),
]


GRID = 0.2  # degrees


@lru_cache(maxsize=1)
def _index():
    rows = json.loads(gzip.decompress(DATA.read_bytes()))
    grid: dict[tuple[int, int], list] = {}
    for name, lat, lon, cc in rows:
        grid.setdefault((math.floor(lat / GRID), math.floor(lon / GRID)), []).append((name, lat, lon, cc))
    return grid


def nearest(lat: float, lon: float, radius_km: float = 60.0):
    """Closest town within ``radius_km`` – fast equirectangular search on a 0.2° grid."""
    grid = _index()
    kx = math.cos(math.radians(lat))
    ring_y = math.ceil(radius_km / (GRID * 111.2))
    ring_x = math.ceil(radius_km / (GRID * 111.2 * max(0.1, kx)))
    ci, cj = math.floor(lat / GRID), math.floor(lon / GRID)
    best, best_d2 = None, (radius_km / 111.2) ** 2
    for i in range(ci - ring_y, ci + ring_y + 1):
        for j in range(cj - ring_x, cj + ring_x + 1):
            for p in grid.get((i, j), ()):
                dy = p[1] - lat
                dx = (p[2] - lon) * kx
                d2 = dx * dx + dy * dy
                if d2 < best_d2:
                    best, best_d2 = p, d2
    if not best:  # outside the detailed (European) gazetteer: use world cities
        for n, la, lo, cc, _sr, _pop in _world():
            if abs(la - lat) > 3 or abs(lo - lon) > 4:
                continue
            dy, dx = la - lat, (lo - lon) * kx
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best, best_d2 = (n, la, lo, cc), d2
    if not best:
        return None, None
    return best, haversine_km(lat, lon, best[1], best[2])


def describe(lat: float | None, lon: float | None) -> tuple[str, str]:
    """(place name, country) – 'bei X' when the nearest town is more than 8 km away."""
    if lat is None or lon is None:
        return "", ""
    p, d = nearest(lat, lon)
    if not p:  # outside the detailed gazetteer (Europe): fall back to world cities
        city = major(lat, lon, radius_km=250)
        return (f"bei {city}" if city else f"{lat:.2f}, {lon:.2f}"), ""
    name = p[0] if d <= 8 else f"bei {p[0]}"
    return name, COUNTRY_DE.get(p[3], p[3])


def _fold(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


@lru_cache(maxsize=1)
def _names():
    rows = json.loads(gzip.decompress(DATA.read_bytes()))
    return [(_fold(n), n, lat, lon, cc) for n, lat, lon, cc in rows]


def search(query: str, limit: int = 10) -> list[dict]:
    """Regions first, then towns (prefix matches before substring matches)."""
    q = _fold(query)[:60]
    if len(q) < 2:
        return []
    starts, contains = [], []
    for key, name, lat, lon, cc in _names():
        if key.startswith(q):
            starts.append((len(key), name, lat, lon, cc))
        elif q in key:
            contains.append((len(key), name, lat, lon, cc))
        if len(starts) >= 200:
            break
    regions = [{"name": n, "lat": la, "lon": lo, "country": c, "kind": "region", "radius_km": r}
               for n, la, lo, c, r in REGIONS if _fold(n).startswith(q) or q in _fold(n)]
    out = regions + [{"name": n, "lat": la, "lon": lo, "country": COUNTRY_DE.get(cc, cc), "kind": "place"}
           for _, n, la, lo, cc in sorted(starts)[:limit] + sorted(contains)[:limit]][:limit]
    return out[:limit]


WORLD = Path(__file__).with_name("data") / "world_cities.json.gz"


@lru_cache(maxsize=1)
def _world():
    """Natural Earth populated places, worldwide (public domain): (name, lat, lon, cc, scalerank, population)."""
    try:
        return [tuple(r) for r in json.loads(gzip.decompress(WORLD.read_bytes()))]
    except (OSError, ValueError):
        return []


def _major():
    return [(n, sr, la, lo) for n, la, lo, _cc, sr, _pop in _world()]


def major(lat: float, lon: float, radius_km: float = 45.0) -> str | None:
    """Best-known city near a point (prefers low scale rank = more important)."""
    best, score = None, 1e9
    for n, sr, la, lo in _major():
        if abs(la - lat) > 1 or abs(lo - lon) > 1.5:
            continue
        d = haversine_km(lat, lon, la, lo)
        if d <= radius_km and d + sr * 6 < score:
            best, score = n, d + sr * 6
    return best


@lru_cache(maxsize=64)
def country_box(cc: str) -> tuple[float, float, float, float] | None:
    """Rough extent of a country from its towns (2nd–98th percentile, ignores far-away territories)."""
    lats, lons = [], []
    for rows in _index().values():
        for _n, la, lo, c in rows:
            if c == cc:
                lats.append(la)
                lons.append(lo)
    if len(lats) < 3:
        lats = [la for _n, la, _lo, c, _s, _p in _world() if c == cc]
        lons = [lo for _n, _la, lo, c, _s, _p in _world() if c == cc]
    if len(lats) < 3:
        return None
    lats.sort()
    lons.sort()
    q = lambda a, f: a[min(len(a) - 1, int(len(a) * f))]  # noqa: E731
    return q(lats, .02), q(lons, .02), q(lats, .98), q(lons, .98)


def home_region(lat: float, lon: float) -> dict:
    p, _d = nearest(lat, lon, radius_km=150)
    if not p:
        return {"cc": "", "name": "", "box": [lat - 1, lon - 1.5, lat + 1, lon + 1.5]}
    box = country_box(p[3]) or (lat - 1, lon - 1.5, lat + 1, lon + 1.5)
    return {"cc": p[3], "name": COUNTRY_DE.get(p[3], p[3]), "box": [round(v, 3) for v in box]}
