"""Add-on options (written by the Supervisor to /data/options.json)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ENTITY_RE = re.compile(r"^(person|device_tracker)\.[a-z0-9_]+$")
SERVICE_RE = re.compile(r"^notify\.[a-z0-9_]+$")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
USER_RE = re.compile(r"^[a-z0-9_.-]{2,32}$")
LABEL_RE = re.compile(r"^[\w .+\-äöüÄÖÜéèàç]{1,40}$")


@dataclass
class Settings:
    persons: list = field(default_factory=list)          # [{entity, label, camera_models}]
    who_options: list = field(default_factory=lambda: ["Paar", "Familie"])
    groups: list = field(default_factory=list)            # [{name, members: [labels], extra, color}]
    hint_keywords: dict = field(default_factory=dict)    # {"keyword": "who option"}
    home_zone: str = "zone.home"
    home_lat: float | None = None
    home_lon: float | None = None
    home_radius_m: int = 0                                # 0 = radius of the home zone
    work_lat: float | None = None                         # empty = detect the workplace automatically
    work_lon: float | None = None
    work_radius_m: int = 300
    show_work: bool = False                               # show the workplace on the map
    timezone: str = "Europe/Zurich"
    min_trip_km: float = 30.0
    routine_days: int = 20                                # places visited on this many days are not trips (0 = off)
    poll_interval_min: int = 5
    history_days_on_start: int = 10
    routing: str = "tiles"                                # tiles | off
    owntracks: list = field(default_factory=list)         # [{user, password, label}] – local live source
    notify_service: str = ""
    notify_mode: str = "weekly"                           # off | instant | daily | weekly
    ask_below: str = "hoch"
    school_holidays: list = field(default_factory=list)
    max_upload_mb: int = 200
    log_level: str = "info"

    @property
    def labels(self) -> list[str]:
        return [p["label"] for p in self.persons]

    def colors(self) -> dict:
        out = {p["label"]: p["color"] for p in self.persons if p.get("color")}
        out.update({g["name"]: g["color"] for g in self.groups if g.get("color")})
        return out


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
         "camera_models": str(x.get("camera_models") or ""),
         "color": str(x.get("color") or "") if COLOR_RE.match(str(x.get("color") or "")) else ""}
        for x in _list(s.persons) if isinstance(x, dict) and LABEL_RE.match(str(x.get("label", "")).strip())
        and (not x.get("entity") or ENTITY_RE.match(str(x.get("entity", ""))))
    ][:10]
    s.who_options = [str(o).strip() for o in _list(s.who_options) if LABEL_RE.match(str(o).strip())]
    labels = set(s.labels)
    groups = []
    for g in _list(s.groups):
        if not isinstance(g, dict) or not LABEL_RE.match(str(g.get("name", "")).strip()):
            continue
        members = g.get("members") or []
        if isinstance(members, str):  # HA options UI: "Alex, Sam"
            members = [m.strip() for m in members.split(",")]
        groups.append({"name": str(g["name"]).strip(), "members": [m for m in members if m in labels],
                       "extra": max(0, min(20, int(g.get("extra") or 0))),
                       "color": str(g.get("color") or "") if COLOR_RE.match(str(g.get("color") or "")) else ""})
    if groups:
        s.groups = groups[:20]
        s.who_options = [g["name"] for g in s.groups]
    else:  # older configuration: plain group names
        s.groups = [{"name": n, "members": [], "extra": 0, "color": ""} for n in s.who_options if n not in labels]
        s.who_options = [g["name"] for g in s.groups]
    kws = {}
    if isinstance(s.hint_keywords, list):  # HA options UI: ["keyword=who", ...]
        for item in s.hint_keywords:
            if "=" in str(item):
                k, v = str(item).split("=", 1)
                kws[k.strip()] = v.strip()
    elif isinstance(s.hint_keywords, dict):
        kws = {str(k): str(v) for k, v in s.hint_keywords.items()}
    s.hint_keywords = kws
    s.owntracks = [
        {"user": str(o.get("user", "")), "password": str(o.get("password", "")), "label": str(o.get("label", "")).strip()}
        for o in _list(s.owntracks) if isinstance(o, dict) and USER_RE.match(str(o.get("user", "")))
        and len(str(o.get("password", ""))) >= 8 and LABEL_RE.match(str(o.get("label", "")).strip())
    ][:10]
    s.school_holidays = [str(x) for x in _list(s.school_holidays)]
    s.min_trip_km = max(1.0, float(s.min_trip_km))
    s.poll_interval_min = max(1, int(s.poll_interval_min))
    s.routine_days = max(0, min(3650, int(s.routine_days)))
    s.max_upload_mb = min(2000, max(1, int(s.max_upload_mb)))
    if s.notify_service and not SERVICE_RE.match(str(s.notify_service)):
        s.notify_service = ""
    s.home_radius_m = max(0, min(5000, int(s.home_radius_m or 0)))
    s.work_radius_m = max(50, min(5000, int(s.work_radius_m or 300)))
    s.show_work = s.show_work is True or str(s.show_work).lower() == "true"
    for k in ("home_lat", "home_lon", "work_lat", "work_lon"):
        v = getattr(s, k)
        try:
            setattr(s, k, None if v in (None, "") else float(v))
        except (TypeError, ValueError):
            setattr(s, k, None)
    if s.home_lat is not None and not (-90 <= s.home_lat <= 90 and -180 <= (s.home_lon or 0) <= 180):
        s.home_lat = s.home_lon = None
    if s.work_lat is None or s.work_lon is None or not (-90 <= s.work_lat <= 90 and -180 <= s.work_lon <= 180):
        s.work_lat = s.work_lon = None
    if s.routing not in ("tiles", "off"):
        s.routing = "tiles"
    if s.notify_mode not in ("off", "instant", "daily", "weekly"):
        s.notify_mode = "weekly"
    return s
