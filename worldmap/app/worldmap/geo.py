"""Small, dependency-free geo helpers."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

EARTH_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(min(1.0, math.sqrt(a)))


def valid_coord(lat: float, lon: float) -> bool:
    """True for a finite coordinate inside the WGS84 range (and not Null Island)."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return False
    if abs(lat) > 90 or abs(lon) > 180:
        return False
    return not (abs(lat) < 1e-6 and abs(lon) < 1e-6)


def _perp_sq(p: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    qx, qy = ax + t * dx, ay + t * dy
    return (px - qx) ** 2 + (py - qy) ** 2


def simplify(points: Sequence[Sequence[float]], tolerance: float) -> list[list[float]]:
    """Iterative Douglas-Peucker on (x, y) pairs; keeps first and last point."""
    n = len(points)
    if n < 3 or tolerance <= 0:
        return [list(p[:2]) for p in points]
    keep = [False] * n
    keep[0] = keep[-1] = True
    tol2 = tolerance * tolerance
    stack = [(0, n - 1)]
    while stack:
        s, e = stack.pop()
        best, idx = 0.0, -1
        for i in range(s + 1, e):
            d = _perp_sq(points[i], points[s], points[e])
            if d > best:
                best, idx = d, i
        if idx >= 0 and best > tol2:
            keep[idx] = True
            stack.append((s, idx))
            stack.append((idx, e))
    return [list(points[i][:2]) for i in range(n) if keep[i]]


def bbox(points: Iterable[Sequence[float]]) -> tuple[float, float, float, float] | None:
    """(min_lat, min_lon, max_lat, max_lon) of (lat, lon) points."""
    it = iter(points)
    try:
        la, lo = next(it)[:2]
    except StopIteration:
        return None
    a, b, c, d = la, lo, la, lo
    for la, lo in (p[:2] for p in it):
        a, b, c, d = min(a, la), min(b, lo), max(c, la), max(d, lo)
    return a, b, c, d


def parse_coordinate(value) -> float | None:
    """Parse decimal or exiftool DMS strings like ``47 deg 31' 12.00" N``."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    s = str(value).strip()
    if s.count(",") == 1 and "." not in s:  # European decimal comma: "47,52"
        s = s.replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    import re

    m = re.match(
        r"^\s*([+-]?\d+(?:\.\d+)?)\s*(?:deg|°)?\s*(?:(\d+(?:\.\d+)?)\s*['′])?\s*(?:(\d+(?:\.\d+)?)\s*(?:\"|″|''))?\s*([NSEWOnsewo])?\s*$",
        s,
    )
    if not m:
        return None
    deg = float(m.group(1))
    minutes = float(m.group(2) or 0)
    seconds = float(m.group(3) or 0)
    v = abs(deg) + minutes / 60 + seconds / 3600
    hemi = (m.group(4) or "").upper()
    if deg < 0 or hemi in ("S", "W"):
        v = -v
    return v
