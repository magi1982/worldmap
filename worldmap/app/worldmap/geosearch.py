"""Online place search for "add a trip": OpenStreetMap (Nominatim) or Google Maps, plus Google Maps links.

Only the search word typed by the user is sent – never positions or trips. Results are checked and trimmed
before they reach the app. Without network the built-in offline list still works.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "worldmap-home-assistant-addon/1.0 (+https://github.com/magi1982/worldmap)"
TIMEOUT = 6
_lock = threading.Lock()
_last = [0.0]
_cache: dict = {}
CACHE_S = 24 * 3600


def _radius(south, north, west, east) -> int | None:
    try:
        h = abs(float(north) - float(south)) * 111
        w = abs(float(east) - float(west)) * 111 * math.cos(math.radians((float(north) + float(south)) / 2))
    except (TypeError, ValueError):
        return None
    r = math.hypot(h, w) / 2
    return int(max(2, min(1500, r))) if r > 0 else None


def _ok(lat, lon) -> bool:
    try:
        return -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
    except (TypeError, ValueError):
        return False


def _item(name, country, lat, lon, radius, source) -> dict | None:
    if not _ok(lat, lon) or not str(name or "").strip():
        return None
    return {"name": str(name).strip()[:80], "country": str(country or "").strip()[:60],
            "lat": round(float(lat), 5), "lon": round(float(lon), 5), "kind": "online",
            "radius_km": radius, "source": source}


API_HOSTS = ("nominatim.openstreetmap.org", "places.googleapis.com")


def _get(url: str, headers: dict, data: bytes | None = None):
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or u.hostname not in API_HOSTS:  # only the two search services, never file:// or others
        raise ValueError("search host not allowed")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # nosec B310 # noqa: S310 – https + fixed hosts checked above
        return json.loads(r.read(2_000_000))


def nominatim(q: str, lang: str = "de") -> list:
    """OpenStreetMap search; at most one request per second (Nominatim usage policy)."""
    with _lock:
        wait = 1.05 - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "jsonv2", "limit": 6, "addressdetails": 1, "accept-language": lang})
    out = []
    for r in _get(url, {}) or []:
        a = r.get("address") or {}
        bb = r.get("boundingbox") or [None] * 4
        name = r.get("name") or (r.get("display_name") or "").split(",")[0]
        it = _item(name, a.get("country"), r.get("lat"), r.get("lon"), _radius(*bb[:4]), "OpenStreetMap")
        if it:
            out.append(it)
    return out


def google(q: str, key: str, lang: str = "de") -> list:
    """Google Places API (New) text search with the user's own key."""
    body = json.dumps({"textQuery": q, "languageCode": lang, "pageSize": 6}).encode()
    res = _get("https://places.googleapis.com/v1/places:searchText",
               {"Content-Type": "application/json", "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": "places.displayName,places.location,places.viewport,places.addressComponents"},
               body)
    out = []
    for p in (res or {}).get("places", []):
        loc = p.get("location") or {}
        vp = p.get("viewport") or {}
        lo_, hi_ = vp.get("low") or {}, vp.get("high") or {}
        country = next((c.get("longText") for c in p.get("addressComponents") or [] if "country" in (c.get("types") or [])), "")
        it = _item((p.get("displayName") or {}).get("text"), country, loc.get("latitude"), loc.get("longitude"),
                   _radius(lo_.get("latitude"), hi_.get("latitude"), lo_.get("longitude"), hi_.get("longitude")),
                   "Google Maps")
        if it:
            out.append(it)
    return out


def search(q: str, provider: str, key: str = "") -> list:
    """Online results, cached for a day; [] on any error (the offline list still answers)."""
    q = (q or "").strip()[:120]
    if len(q) < 3 or provider not in ("osm", "google") or (provider == "google" and not key):
        return []
    ck = (provider, q.lower())
    hit = _cache.get(ck)
    if hit and time.time() - hit[0] < CACHE_S:
        return hit[1]
    try:
        res = google(q, key) if provider == "google" else nominatim(q)
    except Exception:  # noqa: BLE001 – network, quota, wrong key: the offline list still answers
        return []
    if len(_cache) > 500:
        _cache.clear()
    _cache[ck] = (time.time(), res)
    return res


# ---------------------------------------------------------------- Google Maps links
GMAPS_HOSTS = ("google.com", "google.ch", "google.de", "google.at", "maps.app.goo.gl", "goo.gl", "maps.google.com")
_AT = re.compile(r"@(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)")
_3D = re.compile(r"!3d(-?\d{1,2}\.\d+)!4d(-?\d{1,3}\.\d+)")
_Q = re.compile(r"[?&](?:q|query|ll|destination)=(-?\d{1,2}\.\d+)(?:,|%2C)\s*(-?\d{1,3}\.\d+)", re.I)
_PLACE = re.compile(r"/maps/(?:place|search)/([^/@?]+)")


def is_gmaps(text: str) -> bool:
    try:
        u = urllib.parse.urlparse((text or "").strip())
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    return u.scheme in ("http", "https") and any(host == h or host.endswith("." + h) for h in GMAPS_HOSTS)


def parse_gmaps(url: str) -> dict | None:
    """Place from a Google Maps link (name and coordinates are part of the address), or None."""
    m = _3D.search(url) or _AT.search(url) or _Q.search(url)
    if not m or not _ok(m.group(1), m.group(2)):
        return None
    name = ""
    pm = _PLACE.search(url)
    if pm:
        name = urllib.parse.unquote_plus(pm.group(1)).split(",")[0]
    return _item(name or f"{float(m.group(1)):.4f}, {float(m.group(2)):.4f}", "", m.group(1), m.group(2), None,
                 "Google-Maps-Link")


def resolve_gmaps(url: str) -> dict | None:
    """Like parse_gmaps; short links (maps.app.goo.gl) are followed – only to Google hosts."""
    url = (url or "").strip()[:2000]
    if not is_gmaps(url):
        return None
    hit = parse_gmaps(url)
    if hit:
        return hit
    try:
        for _ in range(4):  # follow redirects by hand so every hop is checked
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
            opener = urllib.request.build_opener(_NoRedirect)
            try:
                r = opener.open(req, timeout=TIMEOUT)
                url = r.geturl()
            except urllib.error.HTTPError as e:
                loc = e.headers.get("Location")
                if not loc:
                    return None
                url = urllib.parse.urljoin(url, loc)
            if not is_gmaps(url):
                return None
            hit = parse_gmaps(url)
            if hit:
                return hit
    except (OSError, ValueError):
        return None
    return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None
