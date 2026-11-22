"""Fill gaps between GPS points with real routes (OSRM) or flight arcs."""
from __future__ import annotations

import json
import logging
import math
import time
import urllib.parse
import urllib.request

from .geo import haversine_km

log = logging.getLogger(__name__)

MIN_GAP_KM = 3.0
MAX_GAP_H = 12.0
FLIGHT_KMH = 220.0


def classify_gap(a: dict, b: dict) -> str | None:
    """'road', 'flight' or None (no line should be drawn)."""
    d = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
    dt_h = max(1e-6, (b["ts"] - a["ts"]) / 3600)
    if d < MIN_GAP_KM:
        return None
    speed = d / dt_h
    if speed >= FLIGHT_KMH or (d > 800 and dt_h < 24):
        return "flight"
    if dt_h > MAX_GAP_H or speed < 6:
        return None
    return "road"


def great_circle(a: tuple, b: tuple, n: int = 32) -> list[list[float]]:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2
                                + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
    if d == 0:
        return [list(a), list(b)]
    out = []
    for i in range(n + 1):
        f = i / n
        wa = math.sin((1 - f) * d) / math.sin(d)
        wb = math.sin(f * d) / math.sin(d)
        x = wa * math.cos(la1) * math.cos(lo1) + wb * math.cos(la2) * math.cos(lo2)
        y = wa * math.cos(la1) * math.sin(lo1) + wb * math.cos(la2) * math.sin(lo2)
        z = wa * math.sin(la1) + wb * math.sin(la2)
        out.append([round(math.degrees(math.atan2(z, math.hypot(x, y))), 5), round(math.degrees(math.atan2(y, x)), 5)])
    return out


class OsrmRouter:
    def __init__(self, base_url: str, min_interval_s: float = 1.1, timeout_s: float = 15.0):
        parsed = urllib.parse.urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("osrm_url must be an http(s) URL")
        self.base = base_url.rstrip("/")
        self.min_interval = min_interval_s
        self.timeout = timeout_s
        self._last = 0.0

    def route(self, a: tuple, b: tuple) -> list[list[float]] | None:
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        coords = f"{a[1]:.5f},{a[0]:.5f};{b[1]:.5f},{b[0]:.5f}"
        url = f"{self.base}/route/v1/driving/{coords}?overview=full&geometries=geojson"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as r:  # nosec B310 - scheme checked in __init__
                if r.status != 200:
                    return None
                data = json.loads(r.read(5_000_000))
        except (OSError, ValueError) as exc:
            log.debug("OSRM request failed: %s", exc)
            return None
        routes = data.get("routes") or []
        if data.get("code") != "Ok" or not routes:
            return None
        coords = routes[0].get("geometry", {}).get("coordinates", [])
        line = [[round(c[1], 5), round(c[0], 5)] for c in coords]
        dist = routes[0].get("distance", 0) / 1000
        direct = haversine_km(a[0], a[1], b[0], b[1])
        if direct > 0 and dist > direct * 2.5 + 5:  # implausible detour (ferry, wrong snap)
            return None
        return line


def fill_gaps(db, router: OsrmRouter | None, limit: int = 500) -> int:
    """Create missing segments. Returns the number of new segments."""
    done = {(s["person"], s["t0"], s["t1"]) for s in db.query("SELECT person, t0, t1 FROM segments")}
    new = 0
    prev = None
    for p in db.query("SELECT ts, lat, lon, person FROM points ORDER BY person, ts"):
        if prev and prev["person"] == p["person"] and (p["person"], prev["ts"], p["ts"]) not in done:
            kind = classify_gap(prev, p)
            geom = None
            if kind == "flight":
                geom = great_circle((prev["lat"], prev["lon"]), (p["lat"], p["lon"]))
            elif kind == "road" and router is not None:
                geom = router.route((prev["lat"], prev["lon"]), (p["lat"], p["lon"]))
            if geom:
                db.add_segment(p["person"], prev["ts"], p["ts"], kind, geom)
                new += 1
                if new >= limit:
                    return new
        prev = p
    return new
