"""Online routes for trips without GPS: OpenStreetMap routing (FOSSGIS OSRM) or the Google Routes API.

Used only for estimated car / camper / bus legs (trips entered by hand or from stations). Each leg is asked once
and kept in the map cache. Only two rounded coordinates are sent (about 2 km, so never the exact home), never
names, dates or people. The Google key travels in a request header and is never logged.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from .geo import haversine_km

log = logging.getLogger(__name__)

UA = "worldmap-home-assistant-addon/1.0 (+https://github.com/magi1982/worldmap)"
TIMEOUT = 15
SERVICES = ("offline", "osm", "google")
API_HOSTS = ("routing.openstreetmap.de", "routes.googleapis.com")
OSRM_URL = "https://routing.openstreetmap.de/routed-car/route/v1/driving/"
GOOGLE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUND = 0.02          # degrees (~2 km): what leaves the add-on
MAX_DETOUR = 3.0      # an answer longer than straight × this + MAX_EXTRA_KM is not believed
MAX_EXTRA_KM = 60.0
MAX_POINTS = 5000

_lock = threading.Lock()
_last = [0.0]


class RouteError(Exception):
    """The service could not answer right now (network, quota, bad key): try again later, use the offline way."""


def coarse(p) -> tuple:
    """Round a position to the ~2 km grid that is sent."""
    return (round(round(float(p[0]) / ROUND) * ROUND, 4), round(round(float(p[1]) / ROUND) * ROUND, 4))


def _ok(lat, lon) -> bool:
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and -90 <= lat <= 90 and -180 <= lon <= 180


def _wait() -> None:
    """At most one request a second (light use of a free service)."""
    with _lock:
        wait = 1.05 - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def _call(url: str, headers: dict, data: bytes | None = None):
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or u.hostname not in API_HOSTS:  # only the two routing services, never file:// or others
        raise ValueError("routing host not allowed")
    _wait()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # nosec B310 # noqa: S310 – https + fixed hosts checked above
            return json.loads(r.read(5_000_000))
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 404):  # OSRM answers "no route" with 400 and a JSON body
            try:
                return json.loads(exc.read(100_000))
            except (OSError, ValueError):
                return {}
        raise RouteError(f"{u.hostname}: HTTP {exc.code}") from None
    except (OSError, ValueError) as exc:
        raise RouteError(f"{u.hostname}: {type(exc).__name__}") from None


def decode_polyline(s: str) -> list:
    """Google's encoded polyline → [[lat, lon], …]."""
    out, i, lat, lon = [], 0, 0, 0
    n = len(s)
    while i < n:
        vals = []
        for _ in range(2):
            shift = res = 0
            while True:
                if i >= n:
                    return out
                b = ord(s[i]) - 63
                i += 1
                res |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            vals.append(~(res >> 1) if res & 1 else res >> 1)
        lat += vals[0]
        lon += vals[1]
        out.append([lat / 1e5, lon / 1e5])
        if len(out) > MAX_POINTS:
            break
    return out


def _clean(path, p, q):
    pts = [[float(a), float(b)] for a, b in path[:MAX_POINTS] if _ok(a, b)]
    if len(pts) < 2:
        return "none"
    km = sum(haversine_km(*pts[i - 1], *pts[i]) for i in range(1, len(pts)))
    if km > haversine_km(*p, *q) * MAX_DETOUR + MAX_EXTRA_KM:
        return "none"  # a far detour is worse than the offline estimate
    return pts


def osrm(p, q):
    a, b = coarse(p), coarse(q)
    url = (OSRM_URL + f"{a[1]:.4f},{a[0]:.4f};{b[1]:.4f},{b[0]:.4f}"
           + "?overview=simplified&geometries=geojson&alternatives=false&steps=false")
    got = _call(url, {}) or {}
    code = got.get("code")
    if code in ("NoRoute", "NoSegment", "InvalidQuery", "InvalidValue"):
        return "none"
    if code != "Ok":
        raise RouteError(f"osm: {str(code)[:40]}")
    routes = got.get("routes") or []
    coords = ((routes[0] if routes else {}).get("geometry") or {}).get("coordinates") or []
    return _clean([(c[1], c[0]) for c in coords if isinstance(c, list) and len(c) >= 2], p, q)


def google(p, q, key: str):
    if not key:
        raise RouteError("google: no key")
    a, b = coarse(p), coarse(q)
    body = {"origin": {"location": {"latLng": {"latitude": a[0], "longitude": a[1]}}},
            "destination": {"location": {"latLng": {"latitude": b[0], "longitude": b[1]}}},
            "travelMode": "DRIVE", "routingPreference": "TRAFFIC_UNAWARE"}  # TRAFFIC_UNAWARE = the Essentials price
    got = _call(GOOGLE_URL, {"Content-Type": "application/json", "X-Goog-Api-Key": key,
                             "X-Goog-FieldMask": "routes.polyline.encodedPolyline"},
                json.dumps(body).encode()) or {}
    if got.get("error"):
        raise RouteError(f"google: {str((got['error'] or {}).get('status', 'error'))[:40]}")
    routes = got.get("routes") or []
    enc = ((routes[0] if routes else {}).get("polyline") or {}).get("encodedPolyline")
    if not isinstance(enc, str) or not enc:
        return "none"
    return _clean(decode_polyline(enc[:200_000]), p, q)


def route(service: str, p, q, key: str = ""):
    """Car way p → q: list of [lat, lon], "none" (no way / not believable) or RouteError (try later)."""
    if service == "osm":
        return osrm(p, q)
    if service == "google":
        return google(p, q, key)
    raise RouteError("offline")


def active(s) -> str:
    """The service in use: google needs a key, otherwise nothing leaves the add-on."""
    svc = getattr(s, "route_service", "offline")
    if svc == "google" and not getattr(s, "google_maps_api_key", ""):
        return "offline"
    return svc if svc in SERVICES else "offline"


__all__ = ["RouteError", "active", "coarse", "decode_polyline", "google", "osrm", "route"]
