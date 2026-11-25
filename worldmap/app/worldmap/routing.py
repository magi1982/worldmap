"""Fill gaps between GPS points with paths on the rail/road network or flight arcs."""
from __future__ import annotations

import logging
import math
import time

from .geo import haversine_km
from .modes import FLIGHT_KMH, mode_of_pair

log = logging.getLogger(__name__)

MIN_GAP_KM = 3.0      # gaps shorter than this may be drawn straight
MIN_MATCH_KM = 0.4    # map matching on the tile network starts at this length
MAX_GAP_H = 12.0


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


def fill_gaps(db, matcher=None, limit: int = 200_000, budget_s: float | None = None, progress: dict | None = None) -> int:
    """Create missing segments: flight arcs and rail/road paths on the network (``matcher``).

    Everything is computed locally. Gaps without a plausible path are stored as mode ``none``
    so the map leaves them open instead of drawing a straight line.
    """
    t_end = time.monotonic() + budget_s if budget_s else None
    done = {(s["person"], s["t0"], s["t1"]) for s in db.query("SELECT person, t0, t1 FROM segments")}
    gaps, prev = [], None
    for p in db.query("SELECT ts, lat, lon, person, hint FROM points ORDER BY person, ts"):
        if prev and p["person"] and prev["person"] == p["person"] and (p["person"], prev["ts"], p["ts"]) not in done:
            d = haversine_km(prev["lat"], prev["lon"], p["lat"], p["lon"])
            dt_h = (p["ts"] - prev["ts"]) / 3600
            if d >= MIN_MATCH_KM and dt_h <= MAX_GAP_H:
                mode = mode_of_pair(prev, p, d)
                if mode == "fly" and d >= MIN_GAP_KM:
                    gaps.append(("flight", prev, p, d))
                elif mode in ("rail", "road"):
                    gaps.append((mode, prev, p, d))
        prev = p
    if matcher is not None:  # neighbouring gaps share cached region graphs
        gaps.sort(key=lambda g: (g[0], matcher.region_bbox((g[1]["lat"], g[1]["lon"]), (g[2]["lat"], g[2]["lon"]))))
    new = 0
    if progress is not None:
        progress["todo"] = len(gaps)
        progress["done_total"] = len(done)
    for mode, a, b, d in gaps:
        if new >= limit or (t_end and time.monotonic() > t_end):
            break
        if matcher is not None and mode != "flight" and matcher.paused():
            break  # the map server asked us to wait: stop now instead of failing every remaining gap
        pa, pb = (a["lat"], a["lon"]), (b["lat"], b["lon"])
        geom = None
        if mode == "flight":
            geom = great_circle(pa, pb)
        elif matcher is not None:
            geom = matcher.match(mode, pa, pb)
            if geom == "none" and mode == "rail" and d < 10:
                # trams, buses and city tunnels: follow the streets instead
                geom = matcher.match("road", pa, pb)
        if geom is None:
            continue  # no data yet (network) – try again later
        if geom == "none":
            db.add_segment(b["person"], a["ts"], b["ts"], "none", [])
        else:
            db.add_segment(b["person"], a["ts"], b["ts"], mode, geom)
        new += 1
    return new
