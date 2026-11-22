"""Minimal Home Assistant Core API client (through the Supervisor proxy)."""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime

log = logging.getLogger(__name__)

ENTITY_RE = re.compile(r"^(person|device_tracker|zone)\.[a-z0-9_]+$")
SERVICE_RE = re.compile(r"^notify\.[a-z0-9_]+$")


class HomeAssistant:
    def __init__(self, base: str | None = None, token: str | None = None, timeout: float = 15.0):
        self.base = (base or os.environ.get("WORLDMAP_HA_URL") or "http://supervisor/core/api").rstrip("/")
        self.token = token if token is not None else os.environ.get("SUPERVISOR_TOKEN", "")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.token)

    def _req(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)  # nosec B310 - fixed base URL
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:  # nosec B310
            raw = r.read(50_000_000)
        return json.loads(raw) if raw else None

    def state(self, entity_id: str) -> dict | None:
        if not ENTITY_RE.match(entity_id):
            raise ValueError(f"invalid entity id: {entity_id!r}")
        try:
            return self._req("GET", f"/states/{entity_id}")
        except OSError as exc:
            log.warning("could not read %s: %s", entity_id, exc)
            return None

    def history(self, entity_id: str, since: datetime) -> list[dict]:
        """State history incl. attributes (latitude/longitude) since ``since``."""
        if not ENTITY_RE.match(entity_id):
            raise ValueError(f"invalid entity id: {entity_id!r}")
        start = urllib.parse.quote(since.astimezone(UTC).isoformat())
        path = f"/history/period/{start}?filter_entity_id={entity_id}&significant_changes_only=0"
        try:
            data = self._req("GET", path) or []
        except OSError as exc:
            log.warning("history for %s failed: %s", entity_id, exc)
            return []
        return data[0] if data else []

    def notify(self, service: str, title: str, message: str, url: str | None = None,
               actions: list[dict] | None = None) -> bool:
        if not SERVICE_RE.match(service):
            raise ValueError(f"invalid notify service: {service!r}")
        domain, name = service.split(".", 1)
        payload: dict = {"title": title[:120], "message": message[:1000]}
        data: dict = {}
        if url:
            data["url"] = url
            data["clickAction"] = url
        if actions:
            data["actions"] = actions[:3]
        if data:
            payload["data"] = data
        try:
            self._req("POST", f"/services/{domain}/{name}", payload)
            return True
        except OSError as exc:
            log.warning("notify failed: %s", exc)
            return False

    def persistent(self, title: str, message: str, notification_id: str = "worldmap") -> None:
        try:
            self._req("POST", "/services/persistent_notification/create",
                      {"title": title[:120], "message": message[:4000], "notification_id": notification_id})
        except OSError as exc:
            log.warning("persistent notification failed: %s", exc)

    def set_sensor(self, entity_id: str, state, attributes: dict) -> None:
        if not re.match(r"^sensor\.worldmap_[a-z0-9_]+$", entity_id):
            raise ValueError("only sensor.worldmap_* may be written")
        try:
            self._req("POST", f"/states/{entity_id}", {"state": state, "attributes": attributes})
        except OSError as exc:
            log.debug("sensor update failed: %s", exc)


def position_from_state(st: dict | None) -> tuple[float, float, float | None, int] | None:
    """(lat, lon, accuracy, ts) from a person/device_tracker state."""
    if not st:
        return None
    a = st.get("attributes") or {}
    lat, lon = a.get("latitude"), a.get("longitude")
    if lat is None or lon is None:
        return None
    ts_raw = st.get("last_updated") or st.get("last_changed")
    try:
        ts = int(datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None
    return float(lat), float(lon), a.get("gps_accuracy"), ts


def list_trackers(ha: HomeAssistant) -> list[dict]:
    """person.* and device_tracker.* entities that report GPS coordinates."""
    if not ha.available:
        return []
    try:
        states = ha._req("GET", "/states") or []
    except OSError as exc:
        log.warning("could not list entities: %s", exc)
        return []
    out = []
    for st in states:
        eid = st.get("entity_id", "")
        if not ENTITY_RE.match(eid) or eid.startswith("zone."):
            continue
        a = st.get("attributes") or {}
        out.append({
            "entity": eid,
            "name": str(a.get("friendly_name") or eid)[:80],
            "has_gps": a.get("latitude") is not None,
            "last_updated": st.get("last_updated"),
        })
    return sorted(out, key=lambda e: (not e["has_gps"], e["entity"]))


class Supervisor:
    """Read/write this add-on's own options (needs ``hassio_api: true``)."""

    def __init__(self, base: str | None = None, token: str | None = None, timeout: float = 15.0):
        self.base = (base or os.environ.get("WORLDMAP_SUPERVISOR_URL") or "http://supervisor").rstrip("/")
        self.token = token if token is not None else os.environ.get("SUPERVISOR_TOKEN", "")
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.token)

    def _req(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)  # nosec B310 - fixed base URL
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:  # nosec B310
            return json.loads(r.read(5_000_000) or b"null")

    def info(self) -> dict:
        return (self._req("GET", "/addons/self/info") or {}).get("data", {})

    def options(self) -> dict:
        return self.info().get("options", {})

    def ingress_path(self) -> str:
        """Sidebar URL of this add-on, e.g. /hassio/ingress/abcd1234_worldmap."""
        try:
            slug = self.info().get("slug") or "worldmap"
        except (OSError, ValueError):
            slug = "worldmap"
        return f"/hassio/ingress/{slug}"

    def set_options(self, options: dict) -> None:
        self._req("POST", "/addons/self/options", {"options": options})
