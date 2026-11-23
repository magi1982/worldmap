"""HTTP API + static UI, served behind Home Assistant Ingress.

Only the Ingress proxy (172.30.32.2) may connect; Home Assistant has already
authenticated the user. Everything else is refused.
"""
from __future__ import annotations

import csv
import functools
import gzip
import hashlib
import io
import json
import logging
import os
import re
import sys
import threading
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import airports, asking, geosearch, places
from .atlas import Atlas
from .db import CONFIDENCE
from .engine import Engine
from .ha import Supervisor, list_trackers
from .importers import UserImportError, detect_and_parse, package, triplist
from .settings import COLOR_RE, ENTITY_RE, LABEL_RE, SERVICE_RE, USER_RE, from_dict
from .style import StyleStore

log = logging.getLogger(__name__)

STATIC = Path(__file__).with_name("static")
STATIC_FILES = {
    "/": ("atlas.html", "text/html; charset=utf-8"),
    "/index.html": ("atlas.html", "text/html; charset=utf-8"),
    "/app.html": ("app.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/base.json": ("base.json", "application/json"),
    "/logo.svg": ("logo.svg", "image/svg+xml"),
    "/atlas.html": ("atlas.html", "text/html; charset=utf-8"),
    "/atlas.js": ("atlas.js", "text/javascript; charset=utf-8"),
    "/atlas.css": ("atlas.css", "text/css; charset=utf-8"),
    "/regions.json": ("regions.json", "application/json"),
    "/stylespec.js": ("stylespec.js", "text/javascript; charset=utf-8"),
}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self';"
                               " connect-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'",
    "Cache-Control": "no-store",
}
_STATIC_CACHE: dict = {}


class QuietServer(ThreadingHTTPServer):
    """A browser that closes the page mid-download is normal: no stack trace in the log for that."""

    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


@functools.lru_cache(maxsize=1)
def asset_version() -> str:
    """Short fingerprint of all static files: changes with every add-on update, so browsers never keep old files."""
    h = hashlib.sha256()
    for name in sorted({n for n, _ in STATIC_FILES.values()}):
        try:
            h.update((STATIC / name).read_bytes())
        except OSError:
            pass
    return h.hexdigest()[:10]
FILENAME_RE = re.compile(r"[^\w.\-]+")
MAX_JSON = 256 * 1024
CONNECTOR_KEYS = ("persons", "groups", "owntracks", "notify_service", "notify_mode", "who_options", "school_holidays",
                  "routing", "min_trip_km", "min_day_trip_km", "ask_below", "hint_keywords", "routine_days", "home_lat", "home_lon",
                  "home_radius_m", "work_lat", "work_lon", "work_radius_m", "show_work", "home_airport")
TEXT_LIMITS = {"destination": 120, "country": 60, "who": 60, "transport": 80, "reason": 300, "note": 1000, "source": 80}


def csv_safe(v) -> str:
    """Neutralise spreadsheet formulas in exported cells (CSV injection)."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


LEG_TRANSPORT = ("Auto", "Zug", "Bus", "Flug", "Schiff", "Wohnmobil", "Velo", "zu Fuss")


def validate_legs(raw) -> str:
    """Stops of a trip in order, e.g. Tenerife (by plane) → La Gomera (by ship). Stored as JSON text."""
    if raw in (None, "", []):
        return ""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError as e:
            raise ValueError("legs must be a list") from e
    if not isinstance(raw, list) or len(raw) > 20:
        raise ValueError("legs must be a list of at most 20 stops")
    out = []
    for leg in raw:
        if not isinstance(leg, dict):
            raise ValueError("every stop must be an object")
        code = str(leg.get("ap") or "").strip().upper()
        ap = None
        if code:  # an airport as stop: the plane lands exactly there
            if not re.fullmatch(r"[A-Z]{3}", code) or not (ap := airports.by_iata(code)):
                raise ValueError(f"unknown airport code: {code[:8]}")
            leg = {**leg, "lat": ap[2], "lon": ap[3], "name": leg.get("name") or ap[1]}
        try:
            la, lo = float(leg["lat"]), float(leg["lon"])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError("every stop needs lat and lon") from e
        if not (-90 <= la <= 90 and -180 <= lo <= 180):
            raise ValueError("stop coordinates out of range")
        name = str(leg.get("name") or "").strip()[:80]
        if not name:
            raise ValueError("every stop needs a name")
        tr = str(leg.get("transport") or ("Flug" if ap else "Auto"))
        if tr not in LEG_TRANSPORT:
            raise ValueError(f"unknown transport: {tr[:20]}")
        stop = {"name": name, "country": str(leg.get("country") or "").strip()[:60],
                "lat": round(la, 5), "lon": round(lo, 5), "transport": tr}
        if ap:
            stop["ap"] = ap[0]
        out.append(stop)
    return json.dumps(out, ensure_ascii=False)


def validate_trip(data: dict, partial: bool) -> dict:
    if not isinstance(data, dict):
        raise ValueError("body must be a JSON object")
    out: dict = {}
    for k in ("start_date", "end_date"):
        if k in data:
            out[k] = date.fromisoformat(str(data[k])).isoformat()
        elif not partial:
            raise ValueError(f"{k} is required")
    if "start_date" in out and "end_date" in out and out["end_date"] < out["start_date"]:
        raise ValueError("end_date is before start_date")
    for k, limit in TEXT_LIMITS.items():
        if k in data:
            v = "" if data[k] is None else str(data[k]).strip()
            if len(v) > limit:
                raise ValueError(f"{k} is too long (max {limit})")
            out[k] = v
    if "legs" in data:
        out["legs"] = validate_legs(data["legs"])
    for k in ("ap_from", "ap_to"):
        if k in data:
            code = str(data[k] or "").strip().upper()
            if code and not (len(code) == 3 and code.isalpha() and airports.by_iata(code)):
                raise ValueError(f"unknown airport code: {code[:8]}")
            out[k] = code
    if "confidence" in data:
        if data["confidence"] not in CONFIDENCE:
            raise ValueError("invalid confidence")
        out["confidence"] = data["confidence"]
    if "approx" in data:
        out["approx"] = 1 if data["approx"] else 0
    for k in ("max_km", "lat", "lon", "radius_km"):
        if k in data:
            out[k] = None if data[k] in (None, "") else float(data[k])
    if out.get("lat") is not None and not -90 <= out["lat"] <= 90:
        raise ValueError("lat out of range")
    if out.get("lon") is not None and not -180 <= out["lon"] <= 180:
        raise ValueError("lon out of range")
    if out.get("radius_km") is not None and not 0 <= out["radius_km"] <= 2000:
        raise ValueError("radius_km out of range")
    if "nights" in data:
        out["nights"] = max(0, min(3650, int(data["nights"])))
    elif "start_date" in out and "end_date" in out:
        out["nights"] = (date.fromisoformat(out["end_date"]) - date.fromisoformat(out["start_date"])).days
    out["locked"] = 1  # any human edit wins over automatic detection
    return out


def notify_services(ha) -> list[str]:
    """notify.* services of Home Assistant (mobile apps, groups …)."""
    if not ha.available:
        return []
    try:
        domains = ha._req("GET", "/services") or []
    except OSError:
        return []
    out = []
    for d in domains:
        if d.get("domain") == "notify":
            out += [f"notify.{name}" for name in (d.get("services") or {}) if SERVICE_RE.match(f"notify.{name}")]
    return sorted(out)


def _same_trip(a: dict, b: dict) -> bool:
    """Duplicate = same dates and the same place (same name or less than 30 km apart)."""
    if a["start_date"] != b["start_date"] or a["end_date"] != b["end_date"]:
        return False
    if (a.get("destination") or "").strip().lower() == (b.get("destination") or "").strip().lower():
        return True
    if None not in (a.get("lat"), a.get("lon"), b.get("lat"), b.get("lon")):
        from .geo import haversine_km

        return haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]) < 30
    return False


def upsert_trips(db, trips: list[dict]) -> dict:
    """Insert imported/pasted trips. Duplicates (also within the file) update the existing row."""
    created = updated = dup_in_file = 0
    existing = db.trips(include_ignored=True)
    seen: list[dict] = []
    for t in trips:
        clean = validate_trip(t, partial=False)
        clean["source"] = clean.get("source") or "Import"
        if any(_same_trip(clean, s) for s in seen):
            dup_in_file += 1
            continue
        seen.append(clean)
        match = next((e for e in existing if _same_trip(clean, e)), None)
        if match:
            keep = {k: v for k, v in clean.items() if v not in ("", None)}  # never blank out fields
            db.upsert_trip(keep, match["id"])
            updated += 1
        else:
            clean["id"] = db.upsert_trip(clean)
            existing.append(clean)
            created += 1
    return {"trips_created": created, "trips_updated": updated, "duplicates_in_file": dup_in_file}


def validate_connectors(data: dict) -> dict:
    """Whitelist + validate the connector settings that the UI may change."""
    if not isinstance(data, dict):
        raise ValueError("body must be a JSON object")
    out: dict = {}
    for k in CONNECTOR_KEYS:
        if k not in data:
            continue
        v = data[k]
        if k == "persons":
            persons = []
            for p in v or []:
                ent, label = str(p.get("entity", "") or ""), str(p.get("label", "")).strip()
                if (ent and not ENTITY_RE.match(ent)) or not LABEL_RE.match(label):
                    raise ValueError(f"invalid person entry: {ent!r} / {label!r}")
                color = str(p.get("color") or "")
                if color and not COLOR_RE.match(color):
                    raise ValueError("invalid colour")
                row = {"entity": ent, "label": label, "camera_models": str(p.get("camera_models") or "")[:200], "color": color}
                persons.append({k2: v2 for k2, v2 in row.items() if v2 or k2 == "label"})  # Supervisor rejects "" for match()
            if len(persons) > 10:
                raise ValueError("at most 10 persons")
            out[k] = persons
        elif k == "groups":
            groups = []
            for g in v or []:
                name = str(g.get("name", "")).strip()
                members = g.get("members") or []
                color = str(g.get("color") or "")
                if not LABEL_RE.match(name) or not isinstance(members, list) or (color and not COLOR_RE.match(color)):
                    raise ValueError(f"invalid group {name!r}")
                if not all(isinstance(m, str) and LABEL_RE.match(m) for m in members):
                    raise ValueError("invalid group member")
                row = {"name": name, "members": ", ".join(members), "extra": max(0, min(20, int(g.get("extra") or 0))),
                       "color": color}
                groups.append({k2: v2 for k2, v2 in row.items() if v2 or k2 == "name"})
            if len({g["name"] for g in groups}) != len(groups) or {g["name"] for g in groups} & {
                    str(p.get("label", "")).strip() for p in (data.get("persons") or [])}:
                raise ValueError("names of people and groups must be unique")
            out[k] = groups[:20]
            out["who_options"] = [g["name"] for g in groups]
        elif k == "owntracks":
            users = []
            for o in v or []:
                user, pw, label = str(o.get("user", "")), str(o.get("password", "")), str(o.get("label", "")).strip()
                if not USER_RE.match(user) or len(pw) < 8 or len(pw) > 128 or not LABEL_RE.match(label):
                    raise ValueError("OwnTracks: user 2–32 characters (a-z 0-9 . _ -), password at least 8 characters, label = person")
                users.append({"user": user, "password": pw, "label": label})
            if len({u["user"] for u in users}) != len(users):
                raise ValueError("OwnTracks users must be unique")
            out[k] = users[:10]
        elif k == "notify_service":
            if v and not SERVICE_RE.match(str(v)):
                raise ValueError("notify_service must look like notify.mobile_app_phone")
            out[k] = str(v or "")
        elif k == "notify_mode":
            if v not in ("off", "instant", "daily", "weekly"):
                raise ValueError("invalid notify_mode")
            out[k] = v
        elif k == "routing":
            if v not in ("tiles", "off"):
                raise ValueError("invalid routing")
            out[k] = v
        elif k == "ask_below":
            if v not in ("mittel", "hoch", "bestätigt"):
                raise ValueError("invalid ask_below")
            out[k] = v
        elif k in ("home_lat", "home_lon", "work_lat", "work_lon"):
            if v in (None, ""):
                out[k] = None
                continue
            f = float(v)
            limit = 90 if k.endswith("lat") else 180
            if not -limit <= f <= limit:
                raise ValueError(f"{k} out of range")
            out[k] = round(f, 6)
        elif k in ("home_radius_m", "work_radius_m"):
            out[k] = max(0 if k == "home_radius_m" else 50, min(5000, int(v)))
        elif k == "show_work":
            out[k] = bool(v)
        elif k == "home_airport":
            code = str(v or "").strip().upper()
            if code and not (len(code) == 3 and code.isalpha()):
                raise ValueError("home_airport must be a 3-letter IATA code")
            out[k] = code
        elif k in ("min_trip_km", "min_day_trip_km"):
            out[k] = max(1.0, min(2000.0, float(v)))
        elif k == "routine_days":
            out[k] = max(0, min(3650, int(v)))
        elif k in ("who_options", "school_holidays", "hint_keywords"):
            items = [str(x).strip()[:80] for x in v or [] if str(x).strip()][:50]
            if k == "who_options" and not all(LABEL_RE.match(x) for x in items):
                raise ValueError("invalid who option")
            if k == "school_holidays" and not all(re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}", x) for x in items):
                raise ValueError("school holidays must look like 2026-07-04..2026-08-09")
            out[k] = items
    return out


class App:
    def __init__(self, engine: Engine, allowed_ips: set[str]):
        self.engine = engine
        self.allowed_ips = allowed_ips
        self.busy = threading.Lock()
        self.supervisor = Supervisor()
        self.atlas = getattr(engine, "atlas", None) or Atlas(engine, os.environ.get("WORLDMAP_DATA"))
        self.style = StyleStore(os.environ.get("WORLDMAP_DATA"))
        self.sync_state: dict = {}

    def changed(self) -> None:
        """Data changed: invalidate caches and rebuild the map data in the background."""
        self.engine.touch()
        self.run_bg("atlas", lambda: len(self.atlas.get("core")))

    def run_bg(self, name: str, fn) -> bool:
        if self.sync_state.get(name) == "running":
            return False
        self.sync_state[name] = "running"

        def job():
            try:
                res = fn()
                self.sync_state[name] = f"ok: {res}"
            except Exception as exc:  # noqa: BLE001 - reported to the UI, never crashes the server
                log.exception("%s failed", name)
                self.sync_state[name] = f"error: {type(exc).__name__}"
        threading.Thread(target=job, daemon=True, name=f"sync-{name}").start()
        return True


def make_handler(app: App):
    eng = app.engine

    def connectors_status() -> dict:
        last = {r["person"]: r["t"] for r in eng.db.query("SELECT person, MAX(ts) AS t FROM points GROUP BY person")}
        by_src = {r["source"]: r["n"] for r in eng.db.query("SELECT source, COUNT(*) AS n FROM points GROUP BY source")}
        imports = eng.db.query("SELECT id, filename, format, points, created_at FROM imports ORDER BY id DESC LIMIT 20")
        return {
            "persons": [{**p, "last_point": last.get(p["label"])} for p in eng.s.persons],
            "trackers": list_trackers(eng.ha),
            "owntracks": [{"user": o["user"], "label": o["label"], "password_set": bool(o["password"]),
                           "last_point": eng.db.scalar("SELECT MAX(ts) FROM points WHERE source = 'owntracks' AND person = ?",
                                                       (o["label"],))} for o in eng.s.owntracks],
            "tiles": len(list(Path(eng.tile_dir).glob("*.json.gz"))) if Path(eng.tile_dir).is_dir() else 0,
            "segments": {r["mode"]: r["n"] for r in eng.db.query("SELECT mode, COUNT(*) AS n FROM segments GROUP BY mode")},
            "notify_service": eng.s.notify_service, "notify_mode": eng.s.notify_mode,
            "who_options": eng.s.who_options, "groups": eng.s.groups, "school_holidays": eng.s.school_holidays,
            "routing": eng.s.routing, "min_trip_km": eng.s.min_trip_km, "min_day_trip_km": eng.s.min_day_trip_km, "ask_below": eng.s.ask_below,
            "routine_days": eng.s.routine_days,
            "home": {"zone": eng.s.home_zone, "lat": eng.s.home_lat, "lon": eng.s.home_lon, "radius_m": eng.s.home_radius_m,
                     "resolved": eng.resolve_home(), "radius_used_m": round(eng.home_radius_km() * 1000),
                     "airport": eng.s.home_airport},
            "work": {"lat": eng.s.work_lat, "lon": eng.s.work_lon, "radius_m": eng.s.work_radius_m, "show": eng.s.show_work},
            "hint_keywords": [f"{k}={v}" for k, v in eng.s.hint_keywords.items()],
            "points_by_source": by_src, "imports": imports,
            "editable": app.supervisor.available, "sync": app.sync_state,
        }

    class Handler(BaseHTTPRequestHandler):
        server_version = "worldmap"
        sys_version = ""

        def log_message(self, fmt, *args):  # route to logging, never print bodies
            log.debug("%s %s", self.address_string(), fmt % args)

        # ---------------------------------------------------- helpers
        def _allowed(self) -> bool:
            if self.client_address[0] in app.allowed_ips:
                return True
            self._send(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
            return False

        def _send(self, status, body, ctype="application/json", extra=None):
            raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
            headers = {**SECURITY_HEADERS, **(extra or {})}
            if len(raw) > 1400 and "gzip" in (self.headers.get("Accept-Encoding") or "") and not ctype.startswith("image/png"):
                raw = gzip.compress(raw, 5)
                headers["Content-Encoding"] = "gzip"
                headers["Vary"] = "Accept-Encoding"
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(raw)))
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(raw)

        def _static(self, path: str, versioned: bool = False):
            name, ctype = STATIC_FILES[path]
            if name not in _STATIC_CACHE:
                raw = (STATIC / name).read_bytes().replace(b"__WMV__", asset_version().encode())
                _STATIC_CACHE[name] = (raw, gzip.compress(raw, 9))
            raw, gz = _STATIC_CACHE[name]
            use_gz = "gzip" in (self.headers.get("Accept-Encoding") or "")
            body = gz if use_gz else raw
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in SECURITY_HEADERS.items():
                if k != "Cache-Control":
                    self.send_header(k, v)
            # files asked for with ?v=<fingerprint> never change; pages are always fetched fresh, so an update shows at once
            self.send_header("Cache-Control", "public, max-age=31536000, immutable" if versioned
                             else "no-store" if name.endswith(".html") else "no-cache")
            if use_gz:
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _gz_json(self, gz: bytes):
            use_gz = "gzip" in (self.headers.get("Accept-Encoding") or "")
            body = gz if use_gz else gzip.decompress(gz)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for k, v in SECURITY_HEADERS.items():
                self.send_header(k, v)
            if use_gz:
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _body(self, limit: int) -> bytes:
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
            if n < 0 or n > limit:
                self.close_connection = True  # do not read the oversized body
                raise OverflowError
            return self.rfile.read(n) if n else b""

        def _json(self):
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                raise ValueError("Content-Type must be application/json")
            return json.loads(self._body(MAX_JSON) or b"{}")

        def _route(self):
            u = urlparse(self.path)
            return u.path.rstrip("/") or "/", parse_qs(u.query)

        # ---------------------------------------------------- GET
        def do_GET(self):  # noqa: N802
            if not self._allowed():
                return
            path, q = self._route()
            if path in STATIC_FILES:
                return self._static(path, versioned=q.get("v") == [asset_version()])
            if path == "/api/trips":
                return self._send(HTTPStatus.OK, eng.db.trips(include_ignored=q.get("all", ["0"])[0] == "1"))
            if path == "/api/questions":
                return self._send(HTTPStatus.OK, eng.db.open_questions())
            if path == "/api/stats":
                return self._send(HTTPStatus.OK, {**eng.stats(), "routes": eng.route_progress,
                                                  "routing": eng.s.routing})
            if path == "/api/config":
                return self._send(HTTPStatus.OK, {
                    "persons": eng.s.labels, "who_options": eng.s.who_options, "colors": eng.s.colors(),
                    "home": eng.home, "routing": eng.s.routing, "max_upload_mb": eng.s.max_upload_mb,
                    "place_search": eng.s.place_search if eng.s.place_search != "google" or eng.s.google_maps_api_key else "offline",
                })
            m = re.fullmatch(r"/api/atlas/(core|tracks|labels|reg)", path)
            if m:
                return self._gz_json(app.atlas.get(m.group(1)))
            if path == "/api/rules":
                return self._send(HTTPStatus.OK, eng.db.rules())
            if path == "/api/style":
                return self._send(HTTPStatus.OK, app.style.get())
            if path == "/api/notify_services":
                return self._send(HTTPStatus.OK, notify_services(eng.ha))
            if path == "/api/airports":  # airports of your own flights first, any IATA code on request
                code = q.get("code", [""])[0].strip().upper()[:3]
                text = q.get("q", [""])[0].strip()[:80]
                if text:  # search by town, airport name or code – nobody has to know the codes
                    return self._send(HTTPStatus.OK, airports.search(text))
                if code:
                    ap = airports.by_iata(code)
                    return self._send(HTTPStatus.OK, {"code": ap[0], "name": ap[1]} if ap else {})
                try:
                    used = json.loads(gzip.decompress(app.atlas.get("core"))).get("airports", {})
                except (ValueError, OSError):
                    used = {}
                return self._send(HTTPStatus.OK, sorted(({"code": c, "name": v[2]} for c, v in used.items()),
                                                        key=lambda x: x["code"]))
            if path == "/api/places":
                text = q.get("q", [""])[0][:2000]
                if geosearch.is_gmaps(text):  # a Google Maps link pasted into the search
                    hit = geosearch.resolve_gmaps(text)
                    return self._send(HTTPStatus.OK, [hit] if hit else [])
                local = places.search(text)
                online = geosearch.search(text, eng.s.place_search, eng.s.google_maps_api_key) if q.get("online") else []
                return self._send(HTTPStatus.OK, local + online)
            if path == "/api/connectors":
                return self._send(HTTPStatus.OK, connectors_status())
            if path == "/api/tracks":
                try:
                    tol = float(q.get("tol", ["0.002"])[0])
                except ValueError:
                    tol = 0.002
                return self._send(HTTPStatus.OK, eng.tracks(min(0.5, max(0.00002, tol))))
            if path == "/api/export.worldmap.json.gz":
                persons = eng.s.labels
                pidx = {p: i for i, p in enumerate(persons)}
                pkg = {"worldmap": 1, "persons": persons,
                       "groups": [{"name": g["name"], "members": g["members"], "extra": g["extra"]} for g in eng.s.groups],
                       "trips": [{k: t[k] for k in package.TRIP_KEYS if t.get(k) not in (None, "")} for t in eng.db.trips()],
                       "points": [[r["ts"], round(r["lat"], 6), round(r["lon"], 6), pidx.get(r["person"], -1), r["source"], r["hint"]]
                                  for r in eng.db.query("SELECT ts, lat, lon, person, source, hint FROM points ORDER BY ts")]}
                body = gzip.compress(json.dumps(pkg, ensure_ascii=False, separators=(",", ":")).encode(), 6)
                return self._send(HTTPStatus.OK, body, "application/gzip",
                                  {"Content-Disposition": 'attachment; filename="worldmap-backup.worldmap.json.gz"'})
            if path == "/api/export.csv":
                buf = io.StringIO()
                w = csv.writer(buf, delimiter=";")
                cols = ["start_date", "end_date", "destination", "country", "who", "confidence", "nights",
                        "max_km", "transport", "reason", "note", "source"]
                w.writerow(cols)
                for t in eng.db.trips():
                    w.writerow([csv_safe(t[c]) for c in cols])
                return self._send(HTTPStatus.OK, ("﻿" + buf.getvalue()).encode(), "text/csv; charset=utf-8",
                                  {"Content-Disposition": 'attachment; filename="worldmap-trips.csv"'})
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

        do_HEAD = do_GET  # noqa: N815 - name required by BaseHTTPRequestHandler

        # ---------------------------------------------------- POST/PATCH/DELETE
        def do_POST(self):  # noqa: N802
            if not self._allowed():
                return
            path, q = self._route()
            try:
                if path == "/api/import":
                    return self._import(q)
                if path == "/api/trips":
                    tid = eng.db.upsert_trip(validate_trip(self._json(), partial=False))
                    app.changed()
                    return self._send(HTTPStatus.CREATED, eng.db.trip(tid))
                m = re.fullmatch(r"/api/questions/(\d+)/answer", path)
                if m:
                    body = self._json()
                    try:
                        res = asking.answer(eng.db, int(m.group(1)), str(body.get("answer", "")), bool(body.get("remember", False)))
                    except LookupError:
                        return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    app.changed()
                    eng.publish_sensors()
                    return self._send(HTTPStatus.OK, {"ok": True, **res})
                if path == "/api/style":
                    body = self._json()
                    return self._send(HTTPStatus.OK, app.style.save(body.get("style"), str(body.get("note", ""))))
                m = re.fullmatch(r"/api/style/versions/(\d+)/restore", path)
                if m:
                    try:
                        return self._send(HTTPStatus.OK, app.style.restore(int(m.group(1))))
                    except LookupError:
                        return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                if path == "/api/trips/bulk":
                    body = self._json()
                    rows = body.get("rows")
                    if not isinstance(rows, list) or len(rows) > 5000:
                        raise ValueError("rows must be a list (max 5000)")
                    _names, trips, skipped = triplist.parse_rows([[None if c is None else str(c)[:1000] for c in r][:30]
                                                                 for r in rows if isinstance(r, list)])
                    if not trips:
                        raise ValueError("no row with a start date and a destination (first row = column names)")
                    res = upsert_trips(eng.db, trips)
                    app.changed()
                    return self._send(HTTPStatus.OK, {**res, "skipped": skipped})
                if path == "/api/notify_test":
                    self._json()
                    if not eng.ha.available:
                        return self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Home Assistant not reachable"})
                    title, msg = "Worldmap", "Test: so sehen die Fragen zu deinen Reisen aus."
                    ok = (eng.ha.notify(eng.s.notify_service, title, msg, url=eng.ingress_url) if eng.s.notify_service
                          else (eng.ha.persistent(title, msg) or True))
                    return self._send(HTTPStatus.OK if ok else HTTPStatus.BAD_GATEWAY, {"ok": bool(ok)})
                if path == "/api/connectors":
                    body = self._json()
                    if isinstance(body, dict) and isinstance(body.get("owntracks"), list):
                        known = {o["user"]: o["password"] for o in eng.s.owntracks}
                        for o in body["owntracks"]:  # an empty password field keeps the stored one
                            if isinstance(o, dict) and not o.get("password") and o.get("user") in known:
                                o["password"] = known[o["user"]]
                            if isinstance(o, dict):
                                o.pop("keep_password", None)
                    new = validate_connectors(body)
                    if not app.supervisor.available:
                        return self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Supervisor API not available"})
                    opts = app.supervisor.options()
                    opts.update(new)
                    app.supervisor.set_options(opts)
                    eng.s = from_dict(opts)
                    app.changed()
                    return self._send(HTTPStatus.OK, connectors_status())
                m = re.fullmatch(r"/api/sync/(ha|routes|rebuild)", path)
                if m:
                    self._json()
                    what = m.group(1)
                    fn = {"ha": eng.backfill_history, "routes": lambda: eng.routes_wanted.set() or "started", "rebuild": eng.rebuild}[what]
                    started = app.run_bg(what, fn)
                    return self._send(HTTPStatus.ACCEPTED if started else HTTPStatus.CONFLICT,
                                      {"started": started, "state": app.sync_state})
                if path == "/api/rebuild":
                    self._json()  # require JSON content type (CSRF guard)
                    if not app.busy.acquire(blocking=False):
                        return self._send(HTTPStatus.CONFLICT, {"error": "already running"})
                    try:
                        res = eng.rebuild()
                    finally:
                        app.busy.release()
                    return self._send(HTTPStatus.OK, res)
            except OverflowError:
                return self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "body too large"})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                return self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)[:300]})
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_PATCH(self):  # noqa: N802
            if not self._allowed():
                return
            path, _ = self._route()
            m = re.fullmatch(r"/api/trips/(\d+)", path)
            if not m:
                return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            tid = int(m.group(1))
            if not eng.db.trip(tid):
                return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            try:
                data = validate_trip(self._json(), partial=True)
                cur = eng.db.trip(tid)
                if data.get("end_date", cur["end_date"]) < data.get("start_date", cur["start_date"]):
                    raise ValueError("end_date is before start_date")
            except OverflowError:
                return self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "body too large"})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                return self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)[:300]})
            eng.db.upsert_trip(data, tid)
            app.changed()
            return self._send(HTTPStatus.OK, eng.db.trip(tid))

        def do_DELETE(self):  # noqa: N802
            if not self._allowed():
                return
            path, _ = self._route()
            m = re.fullmatch(r"/api/trips/(\d+)", path)
            if m and eng.db.delete_trip(int(m.group(1))):
                app.changed()
                return self._send(HTTPStatus.OK, {"ok": True})
            m = re.fullmatch(r"/api/rules/(\d+)", path)
            if m and eng.db.delete_rule(int(m.group(1))):
                return self._send(HTTPStatus.OK, {"ok": True})
            m = re.fullmatch(r"/api/imports/(\d+)", path)
            if m:
                with eng.db.tx() as c:
                    gone = c.execute("DELETE FROM imports WHERE id = ?", (int(m.group(1)),)).rowcount
                if gone:
                    return self._send(HTTPStatus.OK, {"ok": True})
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

        # ---------------------------------------------------- import
        def _import_trips(self, res, filename, dry):
            found = sum(1 for t in res.trips if t.get("lat") is not None)
            summary = {"format": res.format, "kind": "trips", "trips": len(res.trips), "located": found,
                       "skipped": res.skipped, "columns": res.columns, "warnings": res.warnings,
                       "first": min(t["start_date"] for t in res.trips), "last": max(t["end_date"] for t in res.trips),
                       "sample": [t["destination"] for t in res.trips[:5]]}
            if dry:
                return self._send(HTTPStatus.OK, summary)
            summary.update(upsert_trips(eng.db, res.trips))
            with eng.db.tx() as c:
                c.execute("INSERT INTO imports (filename, format, points) VALUES (?, ?, ?)", (filename, res.format, len(res.trips)))
            app.changed()
            return self._send(HTTPStatus.OK, summary)

        def _import_package(self, res, filename, dry):
            ok_trips, bad = [], 0  # check every trip before anything is written
            for t in res.trips:
                try:
                    validate_trip(t, partial=False)
                    ok_trips.append(t)
                except ValueError:
                    bad += 1
            res.trips = ok_trips
            if bad:
                res.warnings.append(f"{bad} trips could not be read and were left out")
            known = set(eng.s.labels) | {g["name"] for g in eng.s.groups}
            needed = sorted({p[3] for p in res.points if p[3]} | {t.get("who") for t in res.trips if t.get("who")})
            missing = [n for n in needed if n not in known]
            summary = {"format": "worldmap", "kind": "package", "points": len(res.points), "trips": len(res.trips),
                       "skipped": res.skipped, "warnings": res.warnings, "persons": res.persons,
                       "groups": [g["name"] for g in res.groups], "missing": missing,
                       "first": min([p[0] for p in res.points] or [0]), "last": max([p[0] for p in res.points] or [0]),
                       "sample": [t["destination"] for t in res.trips[:5]]}
            if missing:
                summary["warnings"] = [*res.warnings, "not set up yet under People & groups: " + ", ".join(missing)]
            if dry:
                return self._send(HTTPStatus.OK, summary)
            summary["new_points"] = eng.import_points(res.points) if res.points else 0
            eng.routes_wanted.set()
            if res.trips:
                summary.update(upsert_trips(eng.db, res.trips))
            with eng.db.tx() as c:
                c.execute("INSERT INTO imports (filename, format, points) VALUES (?, ?, ?)",
                          (filename, "worldmap", summary["new_points"] + len(res.trips)))
            if app.busy.acquire(blocking=False):
                try:
                    summary["rebuild"] = eng.rebuild()
                finally:
                    app.busy.release()
            app.changed()
            return self._send(HTTPStatus.OK, summary)

        def _import(self, q):
            if "application/octet-stream" not in (self.headers.get("Content-Type") or ""):
                raise ValueError("Content-Type must be application/octet-stream")
            person = (q.get("person", [""])[0] or "").strip()
            if person and person not in eng.s.labels:
                raise ValueError("unknown person")
            dry = q.get("dry_run", ["0"])[0] == "1"
            filename = FILENAME_RE.sub("_", self.headers.get("X-Filename", "upload"))[:120]
            data = self._body(eng.s.max_upload_mb * 1024 * 1024)
            try:
                res = detect_and_parse(data, filename, person, eng.s.timezone)
            except UserImportError as exc:
                return self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
            if res.format == "worldmap":
                return self._import_package(res, filename, dry)
            if res.trips:
                return self._import_trips(res, filename, dry)
            if not person:  # photos: the camera tells whose they are
                cams = [(tok.strip().lower(), p["label"]) for p in eng.s.persons
                        for tok in str(p.get("camera_models") or "").split(",") if tok.strip()]
                if cams:
                    res.points = [pt if pt[3] or not pt[6] else
                                  (*pt[:3], next((lab for tok, lab in cams if tok in pt[6].lower()), ""), *pt[4:])
                                  for pt in res.points]
            summary = {
                "format": res.format, "points": len(res.points), "skipped": res.skipped,
                "columns": res.columns, "warnings": res.warnings,
                "first": min(p[0] for p in res.points), "last": max(p[0] for p in res.points),
                "sample": [p[:3] for p in res.points[:5]],
            }
            if dry:
                return self._send(HTTPStatus.OK, summary)
            new = eng.import_points(res.points)
            eng.routes_wanted.set()
            with eng.db.tx() as c:
                c.execute("INSERT INTO imports (filename, format, points) VALUES (?, ?, ?)", (filename, res.format, new))
            summary["new_points"] = new
            if app.busy.acquire(blocking=False):
                try:
                    summary["rebuild"] = eng.rebuild()
                finally:
                    app.busy.release()
            app.changed()
            return self._send(HTTPStatus.OK, summary)

    return Handler


def serve(engine: Engine, host: str = "0.0.0.0", port: int = 8099, allowed_ips: set[str] | None = None):  # nosec B104 - container network, IP allow-list below
    ips = allowed_ips or set(filter(None, os.environ.get("WORLDMAP_ALLOWED_IPS", "172.30.32.2,127.0.0.1").split(",")))
    httpd = QuietServer((host, port), make_handler(App(engine, ips)))
    httpd.daemon_threads = True
    return httpd
