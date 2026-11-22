"""Add-on options (written by the Supervisor to /data/options.json)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ENTITY_RE = re.compile(r"^(person|device_tracker)\.[a-z0-9_]+$")
SERVICE_RE = re.compile(r"^notify\.[a-z0-9_]+$")
LABEL_RE = re.compile(r"^[\w .+\-äöüÄÖÜéèàç]{1,40}$")


@dataclass
class Settings:
    persons: list = field(default_factory=list)          # [{entity, label, camera_models}]
    who_options: list = field(default_factory=lambda: ["Paar", "Familie"])
    hint_keywords: dict = field(default_factory=dict)    # {"keyword": "who option"}
    home_zone: str = "zone.home"
    home_lat: float | None = None
    home_lon: float | None = None
    timezone: str = "Europe/Zurich"
    min_trip_km: float = 30.0
    routine_days: int = 20                                # places visited on this many days are not trips (0 = off)
    poll_interval_min: int = 5
    history_days_on_start: int = 10
    routing: str = "osrm"                                 # osrm | off
    osrm_url: str = "https://router.project-osrm.org"
    photo_folders: list = field(default_factory=list)
    photo_scan_hours: int = 24
    notify_service: str = ""
    notify_mode: str = "weekly"                           # off | instant | daily | weekly
    ask_below: str = "hoch"
    school_holidays: list = field(default_factory=list)
    max_upload_mb: int = 200
    log_level: str = "info"

    @property
    def labels(self) -> list[str]:
        return [p["label"] for p in self.persons]


def _list(v):
    return v if isinstance(v, list) else []


def load(path: str | Path) -> Settings:
    p = Path(path)
    return from_dict(json.loads(p.read_text()) if p.exists() else {})


def from_dict(raw: dict) -> Settings:
    s = Settings()
    for k, v in raw.items():
        if hasattr(s, k) and v is not None:
            setattr(s, k, v)
    s.persons = [
        {"entity": str(x.get("entity", "")), "label": str(x.get("label", "")).strip(),
         "camera_models": str(x.get("camera_models") or "")}
        for x in _list(s.persons) if isinstance(x, dict) and LABEL_RE.match(str(x.get("label", "")).strip())
        and ENTITY_RE.match(str(x.get("entity", "")))
    ][:10]
    s.who_options = [str(o).strip() for o in _list(s.who_options) if LABEL_RE.match(str(o).strip())]
    kws = {}
    if isinstance(s.hint_keywords, list):  # HA options UI: ["keyword=who", ...]
        for item in s.hint_keywords:
            if "=" in str(item):
                k, v = str(item).split("=", 1)
                kws[k.strip()] = v.strip()
    elif isinstance(s.hint_keywords, dict):
        kws = {str(k): str(v) for k, v in s.hint_keywords.items()}
    s.hint_keywords = kws
    s.photo_folders = [str(f) for f in _list(s.photo_folders) if str(f).startswith(("/media", "/share"))]
    s.school_holidays = [str(x) for x in _list(s.school_holidays)]
    s.min_trip_km = max(1.0, float(s.min_trip_km))
    s.poll_interval_min = max(1, int(s.poll_interval_min))
    s.routine_days = max(0, min(3650, int(s.routine_days)))
    s.max_upload_mb = min(2000, max(1, int(s.max_upload_mb)))
    if s.notify_service and not SERVICE_RE.match(str(s.notify_service)):
        s.notify_service = ""
    for k in ("home_lat", "home_lon"):
        v = getattr(s, k)
        try:
            setattr(s, k, None if v in (None, "") else float(v))
        except (TypeError, ValueError):
            setattr(s, k, None)
    if s.home_lat is not None and not (-90 <= s.home_lat <= 90 and -180 <= (s.home_lon or 0) <= 180):
        s.home_lat = s.home_lon = None
    if s.routing not in ("osrm", "off"):
        s.routing = "off"
    if s.notify_mode not in ("off", "instant", "daily", "weekly"):
        s.notify_mode = "weekly"
    return s
