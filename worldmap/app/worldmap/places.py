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
    "MV": "Malediven", "AE": "Vereinigte Arabische Emirate", "US": "USA", "CA": "Kanada",
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


@lru_cache(maxsize=1)
def _index():
    rows = json.loads(gzip.decompress(DATA.read_bytes()))
    grid: dict[tuple[int, int], list] = {}
    for name, lat, lon, cc in rows:
        grid.setdefault((math.floor(lat), math.floor(lon)), []).append((name, lat, lon, cc))
    return grid


def nearest(lat: float, lon: float, radius_km: float = 60.0):
    grid = _index()
    best, best_d = None, radius_km
    ci, cj = math.floor(lat), math.floor(lon)
    for i in (ci - 1, ci, ci + 1):
        for j in (cj - 1, cj, cj + 1):
            for p in grid.get((i, j), ()):
                d = haversine_km(lat, lon, p[1], p[2])
                if d < best_d:
                    best, best_d = p, d
    return (best, best_d) if best else (None, None)


def describe(lat: float | None, lon: float | None) -> tuple[str, str]:
    """(place name, country) – 'bei X' when the nearest town is more than 8 km away."""
    if lat is None or lon is None:
        return "", ""
    p, d = nearest(lat, lon)
    if not p:
        return f"{lat:.2f}, {lon:.2f}", ""
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
