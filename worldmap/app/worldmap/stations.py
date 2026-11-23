"""Stations of a trip from recorded positions (Google Timeline, OwnTracks, Home Assistant, photos, GPX …).

The places where you slept become the stations, in order; several nights at the same place are one station.
The transport to a station is what the positions show on the way there: a flight lands at a real airport (the
airport becomes a station of its own when the place is further away), ships, trains, cars and walking are taken
from the movement between the points. Short stops on the way (petrol, lunch) are no stations.
"""
from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import airports, places
from .geo import haversine_km
from .modes import mode_of_pair, mode_of_text

SAME_PLACE_KM = 25.0      # nights closer than this are the same station
AIRPORT_OWN_KM = 15.0     # an airport further away from the place than this is a station of its own
WORD = {"fly": "Flug", "rail": "Zug", "ferry": "Schiff", "road": "Auto", "foot": "zu Fuss"}
MIN_KM = {"fly": 150.0, "rail": 20.0, "ferry": 3.0, "road": 10.0}


def _ts(day: date, hour: int, tz: ZoneInfo) -> int:
    return int(datetime.combine(day, time(hour), tz).timestamp())


def _night_spot(pts: list[dict], ts: list[int], t0: int, t1: int):
    """Median position of the points between t0 and t1, or None."""
    a, b = bisect_left(ts, t0), bisect_right(ts, t1)
    if b - a < 1:
        return None
    sel = pts[a:b]
    la = sorted(p["lat"] for p in sel)[len(sel) // 2]
    lo = sorted(p["lon"] for p in sel)[len(sel) // 2]
    return la, lo


def _transport(pts: list[dict], ts: list[int], t0: int, t1: int,
               home: tuple[float, float]) -> tuple[list[str], tuple | None]:
    """Transport words for the way between t0 and t1, and where a flight landed (lat, lon) if there was one."""
    a, b = bisect_left(ts, t0), bisect_right(ts, t1)
    km: dict = {}
    landed = None
    for p, q in zip(pts[a:b - 1], pts[a + 1:b], strict=True):
        d = haversine_km(p["lat"], p["lon"], q["lat"], q["lon"])
        if d < 0.2:
            continue
        if q["ts"] - p["ts"] > 3 * 3600:  # a gap in the recording: only a long one tells something (a flight)
            m = "fly" if d >= 700 else None
        else:
            m = mode_of_pair(p, q, d)
        if m in (None, "jump"):
            continue
        km[m] = km.get(m, 0.0) + d
        if m == "fly" and haversine_km(home[0], home[1], q["lat"], q["lon"]) > \
                haversine_km(home[0], home[1], p["lat"], p["lon"]):
            landed = (q["lat"], q["lon"])  # going away from home: this is where the plane landed
    words = [WORD[m] for m in ("fly", "ferry", "rail", "road") if km.get(m, 0) >= MIN_KM[m]]
    if not words:
        words = ["zu Fuss"] if km and max(km, key=km.get) == "foot" and sum(km.values()) < 15 else ["Auto"]
    return words, (landed if "Flug" in words else None)


def _name(lat: float, lon: float) -> tuple[str, str]:
    name, country = places.describe(lat, lon)
    city = places.major(lat, lon, radius_km=15)
    if city and name.startswith("bei "):
        name = city
    return name or f"{lat:.2f}, {lon:.2f}", country


def from_points(points: list[dict], start: str, end: str, tz: str, home: tuple[float, float],
                home_km: float = 30.0) -> list[dict]:
    """Stations of the trip from ``start`` to ``end`` (local dates), from points sorted by time. [] if unclear."""
    zone = ZoneInfo(tz)
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    lo_ts, hi_ts = _ts(d0, 0, zone) - 6 * 3600, _ts(d1 + timedelta(days=1), 0, zone)
    ts_all = [p["ts"] for p in points]
    pts = points[bisect_left(ts_all, lo_ts):bisect_right(ts_all, hi_ts)]
    if len(pts) < 2:
        return []
    ts = [p["ts"] for p in pts]
    stays: list[dict] = []  # {lat, lon, nights, first (ts of the first evening), last (ts of the last morning)}
    d = d0
    while d < d1:
        spot = (_night_spot(pts, ts, _ts(d, 22, zone), _ts(d + timedelta(days=1), 6, zone))
                or _night_spot(pts, ts, _ts(d, 18, zone), _ts(d + timedelta(days=1), 10, zone)))
        if spot and haversine_km(home[0], home[1], *spot) > home_km:
            cur = stays[-1] if stays else None
            if cur and haversine_km(cur["lat"], cur["lon"], *spot) <= SAME_PLACE_KM:
                n = cur["nights"]
                cur["lat"] = (cur["lat"] * n + spot[0]) / (n + 1)
                cur["lon"] = (cur["lon"] * n + spot[1]) / (n + 1)
                cur["nights"] += 1
                cur["last"] = _ts(d + timedelta(days=1), 10, zone)
            else:
                stays.append({"lat": spot[0], "lon": spot[1], "nights": 1, "first": _ts(d, 18, zone),
                              "last": _ts(d + timedelta(days=1), 10, zone)})
        d += timedelta(days=1)
    if stays:  # the last nights close to home on the way back from far away are no station (Sulgen after Mallorca)
        far = max(haversine_km(home[0], home[1], x["lat"], x["lon"]) for x in stays)
        stays = [x for x in stays if haversine_km(home[0], home[1], x["lat"], x["lon"]) >= max(home_km, far * .12)]
    out: list[dict] = []
    prev_end = lo_ts
    for st in stays:
        words, landed = _transport(pts, ts, prev_end, st["first"] + 6 * 3600, home)
        before = out[-1] if out else {"lat": home[0], "lon": home[1]}
        if words == ["zu Fuss"] and haversine_km(before["lat"], before["lon"], st["lat"], st["lon"]) >= 15:
            words = ["Auto"]  # too far to have walked: the recording is just thin
        name, country = _name(st["lat"], st["lon"])
        ap = airports.snap(landed[0], landed[1]) if landed else None
        if ap and haversine_km(ap[2], ap[3], st["lat"], st["lon"]) > AIRPORT_OWN_KM:
            out.append({"name": ap[1], "country": "", "lat": ap[2], "lon": ap[3], "transport": "Flug",
                        "ap": ap[0], "auto": 1, "gps": 1})
            words = [w for w in words if w != "Flug"] or ["Auto"]
        elif ap:
            words = ["Flug"] + [w for w in words if w != "Flug"]
        out.append({"name": name[:80], "country": country, "lat": round(st["lat"], 4), "lon": round(st["lon"], 4),
                    "transport": " · ".join(words) or "Auto", "auto": 1, "gps": 1, "n": st["nights"]})
        prev_end = st["last"]
    return out[:20]


LEG_WORDS = ("Auto", "Zug", "Bus", "Flug", "Wasserflugzeug", "Schiff", "Wohnmobil", "Velo", "zu Fuss")


def words(transport: str | None) -> list[str]:
    """Free transport text → the words of the stations ("Auto · Fähre" → Auto, Schiff; "U-Bahn" → Zug)."""
    out: list[str] = []
    for part in re.split(r"\s*[·,/+]\s*", transport or ""):
        part = re.sub(r"\s+via\s+.*$", "", part.strip(), flags=re.I)
        w = part if part in LEG_WORDS else {"fly": "Flug", "rail": "Zug", "ferry": "Schiff", "road": "Auto",
                                             "foot": "zu Fuss"}.get(mode_of_text(part) or "")
        if w and w not in out:
            out.append(w)
    return out


def from_fields(name: str, country: str, lat, lon, transport: str | None) -> list[dict]:
    """Stations from the old fields of a trip: "Flug via Dubai · Wasserflugzeug" to a resort becomes
    ✈ DXB → ✈ MLE → 🛩 resort; anything else one station with clean transport words."""
    ws = words(transport)
    stops: list[dict] = []
    for city in re.findall(r"via\s+([^·,/+]+)", transport or "", flags=re.I)[:3]:  # a stopover by plane
        ap = next((a for a in airports.search(city.strip()) if a["size"] == 2), None)
        if ap:
            stops.append({"name": ap["name"], "country": "", "lat": ap["lat"], "lon": ap["lon"], "transport": "Flug",
                          "ap": ap["code"], "auto": 1})
    dest_tr = [w for w in ws if not (stops and w == "Flug")] or ws
    if "Wasserflugzeug" in ws and lat is not None and not airports.snap(lat, lon, 60, 0):
        hub = airports.nearest_large(lat, lon, 400)  # the island has no big airport: land there, then seaplane
        if hub:
            stops.append({"name": hub[1], "country": "", "lat": hub[2], "lon": hub[3], "transport": "Flug",
                          "ap": hub[0], "auto": 1})
            dest_tr = ["Wasserflugzeug"]
    stops.append({"name": (name or country or "Ziel")[:80] if lat is not None else (country or name or "Ziel")[:80],
                  "country": country or "", "lat": lat, "lon": lon, "transport": " · ".join(dest_tr), "auto": 1})
    return stops
