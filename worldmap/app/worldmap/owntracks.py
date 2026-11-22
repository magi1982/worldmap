"""Local live source for phones: the OwnTracks app in HTTP mode.

The app records positions on the phone, keeps them while the phone cannot reach the house and
sends them (with their real timestamps) as soon as it is back in the home network. Home Assistant
does not need to be reachable from the internet – no Nabu Casa, no open port.

Only ``POST`` with HTTP Basic auth of a configured user is accepted; nothing else is served.
"""
from __future__ import annotations

import base64
import hmac
import json
import logging
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .geo import valid_coord

log = logging.getLogger(__name__)
MAX_BODY = 1_000_000


def parse(body: bytes, label: str) -> list[tuple]:
    """OwnTracks JSON (one message or a list) -> point rows."""
    data = json.loads(body or b"null")
    msgs = data if isinstance(data, list) else [data]
    rows = []
    for m in msgs:
        if not isinstance(m, dict) or m.get("_type") != "location":
            continue
        try:
            lat, lon, tst = float(m["lat"]), float(m["lon"]), int(m["tst"])
        except (KeyError, TypeError, ValueError):
            continue
        if not valid_coord(lat, lon) or not 946684800 <= tst <= time.time() + 86400:
            continue
        acc = m.get("acc")
        hint = {"w": "WALKING", "r": "RUNNING", "a": "IN_PASSENGER_VEHICLE", "c": "CYCLING"}.get(str(m.get("m", "")), None)
        rows.append((tst, lat, lon, label, "owntracks", float(acc) if isinstance(acc, (int, float)) else None, hint))
    return rows


def make_handler(engine):
    class Handler(BaseHTTPRequestHandler):
        server_version = "worldmap"
        sys_version = ""

        def log_message(self, fmt, *args):
            log.debug("owntracks %s", fmt % args)

        def _reply(self, status, body=b"[]"):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if status == HTTPStatus.UNAUTHORIZED:
                self.send_header("WWW-Authenticate", 'Basic realm="worldmap"')
            self.end_headers()
            self.wfile.write(body)

        def _user(self):
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Basic "):
                return None
            try:
                user, _, pw = base64.b64decode(auth[6:], validate=True).decode("utf-8").partition(":")
            except (ValueError, UnicodeDecodeError):
                return None
            found = None
            for o in engine.s.owntracks:  # compare every entry in constant time
                ok_user = hmac.compare_digest(o["user"].encode(), user.encode())
                ok_pw = hmac.compare_digest(o["password"].encode(), pw.encode())
                if ok_user and ok_pw:
                    found = o
            return found

        def do_GET(self):  # noqa: N802
            self._reply(HTTPStatus.METHOD_NOT_ALLOWED, b"{}")

        def do_POST(self):  # noqa: N802
            if not engine.s.owntracks:
                return self._reply(HTTPStatus.NOT_FOUND, b"{}")
            user = self._user()
            if not user:
                time.sleep(0.5)  # slow down guessing
                return self._reply(HTTPStatus.UNAUTHORIZED, b"{}")
            try:
                n = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                n = -1
            if n < 0 or n > MAX_BODY:
                self.close_connection = True
                return self._reply(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, b"{}")
            try:
                rows = parse(self.rfile.read(n), user["label"])
            except ValueError:
                return self._reply(HTTPStatus.BAD_REQUEST, b"{}")
            if rows:
                engine.import_points(rows)
            return self._reply(HTTPStatus.OK)

    return Handler


def serve(engine, host: str = "0.0.0.0", port: int = 8098):  # nosec B104 - LAN endpoint, Basic auth required
    httpd = ThreadingHTTPServer((host, port), make_handler(engine))
    httpd.daemon_threads = True
    return httpd
