"""HTTP API + static UI, served behind Home Assistant Ingress.

Only the Ingress proxy (172.30.32.2) may connect; Home Assistant has already
authenticated the user. Everything else is refused.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import logging
import os
import re
import threading
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import places
from .atlas import Atlas
from .db import CONFIDENCE
from .engine import Engine
from .ha import Supervisor, list_trackers
from .importers import UserImportError, detect_and_parse
from .settings import ENTITY_RE, LABEL_RE, SERVICE_RE, from_dict

log = logging.getLogger(__name__)

STATIC = Path(__file__).with_name("static")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/base.json": ("base.json", "application/json"),
    "/logo.svg": ("logo.svg", "image/svg+xml"),
    "/atlas.html": ("atlas.html", "text/html; charset=utf-8"),
    "/atlas.js": ("atlas.js", "text/javascript; charset=utf-8"),
    "/atlas.css": ("atlas.css", "text/css; charset=utf-8"),
    "/ch.json": ("ch.json", "application/json"),
}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self';"
                               " connect-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'",
    "Cache-Control": "no-store",
}
_STATIC_CACHE: dict = {}
FILENAME_RE = re.compile(r"[^\w.\-]+")
MAX_JSON = 256 * 1024
CONNECTOR_KEYS = ("persons", "photo_folders", "notify_service", "notify_mode", "who_options",
                  "school_holidays", "routing", "min_trip_km", "ask_below", "hint_keywords", "routine_days")
TEXT_LIMITS = {"destination": 120, "country": 60, "who": 60, "transport": 80, "reason": 300, "note": 1000, "source": 80}


def csv_safe(v) -> str:
    """Neutralise spreadsheet formulas in exported cells (CSV injection)."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


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
                ent, label = str(p.get("entity", "")), str(p.get("label", "")).strip()
                if not ENTITY_RE.match(ent) or not LABEL_RE.match(label):
                    raise ValueError(f"invalid person entry: {ent!r} / {label!r}")
                persons.append({"entity": ent, "label": label, "camera_models": str(p.get("camera_models") or "")[:200]})
            if len(persons) > 10:
                raise ValueError("at most 10 persons")
            out[k] = persons
        elif k == "photo_folders":
            folders = [str(f).strip() for f in v or [] if str(f).strip()]
            for f in folders:
                if not re.fullmatch(r"/(media|share)(/[\w .\-äöüÄÖÜ]+)*", f) or "/.." in f:
                    raise ValueError(f"photo folder must be below /media or /share: {f!r}")
            out[k] = folders
        elif k == "notify_service":
            if v and not SERVICE_RE.match(str(v)):
                raise ValueError("notify_service must look like notify.mobile_app_phone")
            out[k] = str(v or "")
        elif k == "notify_mode":
            if v not in ("off", "instant", "daily", "weekly"):
                raise ValueError("invalid notify_mode")
            out[k] = v
        elif k == "routing":
            if v not in ("osrm", "off"):
                raise ValueError("invalid routing")
            out[k] = v
        elif k == "ask_below":
            if v not in ("mittel", "hoch", "bestätigt"):
                raise ValueError("invalid ask_below")
            out[k] = v
        elif k == "min_trip_km":
            out[k] = max(1.0, min(1000.0, float(v)))
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
        imports = eng.db.query("SELECT filename, format, points, created_at FROM imports ORDER BY id DESC LIMIT 10")
        return {
            "persons": [{**p, "last_point": last.get(p["label"])} for p in eng.s.persons],
            "trackers": list_trackers(eng.ha),
            "photo_folders": eng.s.photo_folders,
            "photo_scan_mtime": eng.db.get_meta("photo_scan_mtime"),
            "notify_service": eng.s.notify_service, "notify_mode": eng.s.notify_mode,
            "who_options": eng.s.who_options, "school_holidays": eng.s.school_holidays,
            "routing": eng.s.routing, "min_trip_km": eng.s.min_trip_km, "ask_below": eng.s.ask_below,
            "routine_days": eng.s.routine_days,
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

        def _static(self, path: str):
            name, ctype = STATIC_FILES[path]
            if name not in _STATIC_CACHE:
                raw = (STATIC / name).read_bytes()
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
            # data file changes only with a new add-on version; HTML must revalidate
            self.send_header("Cache-Control", "max-age=86400" if name in ("base.json", "ch.json") else "no-cache")
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
                return self._static(path)
            if path == "/api/trips":
                return self._send(HTTPStatus.OK, eng.db.trips())
            if path == "/api/questions":
                return self._send(HTTPStatus.OK, eng.db.open_questions())
            if path == "/api/stats":
                return self._send(HTTPStatus.OK, eng.stats())
            if path == "/api/config":
                return self._send(HTTPStatus.OK, {
                    "persons": eng.s.labels, "who_options": eng.s.who_options,
                    "home": eng.home, "routing": eng.s.routing, "max_upload_mb": eng.s.max_upload_mb,
                })
            m = re.fullmatch(r"/api/atlas/(core|tracks|labels|gem)", path)
            if m:
                return self._gz_json(app.atlas.get(m.group(1)))
            if path == "/api/places":
                return self._send(HTTPStatus.OK, places.search(q.get("q", [""])[0]))
            if path == "/api/connectors":
                return self._send(HTTPStatus.OK, connectors_status())
            if path == "/api/tracks":
                try:
                    tol = float(q.get("tol", ["0.002"])[0])
                except ValueError:
                    tol = 0.002
                return self._send(HTTPStatus.OK, eng.tracks(min(0.5, max(0.00002, tol))))
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
                    res = eng.db.answer_question(int(m.group(1)), str(body.get("answer", "")))
                    if res is None:
                        return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    app.changed()
                    eng.publish_sensors()
                    return self._send(HTTPStatus.OK, {"ok": True})
                if path == "/api/connectors":
                    new = validate_connectors(self._json())
                    if not app.supervisor.available:
                        return self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Supervisor API not available"})
                    opts = app.supervisor.options()
                    opts.update(new)
                    app.supervisor.set_options(opts)
                    eng.s = from_dict(opts)
                    app.changed()
                    return self._send(HTTPStatus.OK, connectors_status())
                m = re.fullmatch(r"/api/sync/(ha|photos|routes|rebuild)", path)
                if m:
                    self._json()
                    what = m.group(1)
                    fn = {"ha": eng.backfill_history, "photos": eng.scan_photos,
                          "routes": eng.fill_routes, "rebuild": eng.rebuild}[what]
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
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

        # ---------------------------------------------------- import
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
            summary = {
                "format": res.format, "points": len(res.points), "skipped": res.skipped,
                "columns": res.columns, "warnings": res.warnings,
                "first": min(p[0] for p in res.points), "last": max(p[0] for p in res.points),
                "sample": [p[:3] for p in res.points[:5]],
            }
            if dry:
                return self._send(HTTPStatus.OK, summary)
            new = eng.import_points(res.points)
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
    httpd = ThreadingHTTPServer((host, port), make_handler(App(engine, ips)))
    httpd.daemon_threads = True
    return httpd
