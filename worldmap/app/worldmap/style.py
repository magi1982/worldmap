"""Map style (colours, line types, areas, base map) with versions.

Stored in ``<data>/style.json``::

    {"current": {...}, "versions": [{"id": 3, "ts": 1700000000, "note": "...", "style": {...}}, ...]}

Every save creates a version; the last ``MAX_VERSIONS`` are kept so the user can go back.
Everything is validated against a fixed schema – unknown keys are dropped, values are clamped.
"""
from __future__ import annotations

import copy
import json
import os
import re
import tempfile
import threading
import time
from pathlib import Path

MODES = ("road", "rail", "fly", "ferry", "foot")
DASHES = ("solid", "dashed", "dotted", "longdash", "dashdot", "sparse")
PALETTES = ("neon", "classic", "pastel", "earth", "contrast", "mono")
BASEMAPS = ("standard", "paper", "mono", "earth")
LOOKS = ("classic", "stars", "crystal", "medals")
PRESETS = 3
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_VERSIONS = 20

# every setting of every map: (type, default, ...) – the browser can only send what is listed here
B, N, E, C = "bool", "num", "enum", "color"
SCHEMA: dict = {
    "areas": {  # semi-transparent areas around places (Trips map)
        "show": (B, True), "opacity": (N, 1.0, 0.1, 1.0), "size": (N, 1.0, 0.5, 3.0), "outline": (B, True),
        "shape": (E, "organic", ("organic", "circles")), "connect": (N, 1.0, 0.0, 3.0), "smooth": (N, 1.0, 0.3, 2.5),
        "outline_width": (N, 1.4, 0.0, 6.0), "outline_color": (E, "fill", ("fill", "darker", "white", "none")),
    },
    "map": {
        "rivers": (B, True), "provinces": (B, True), "labels": (E, "normal", ("many", "normal", "few", "off")),
        "theme": (E, "auto", ("auto", "light", "dark")), "palette": (E, "neon", PALETTES),
        "basemap": (E, "standard", BASEMAPS), "gaps": (E, "dotted", ("dotted", "straight", "open")),
        "look": (E, "classic", LOOKS),  # how places and flights are drawn: classic dots and lines, or a game look
    },
    "est": {  # estimated way for trips without GPS (car, train, ferry)
        "show": (B, True), "dash": (E, "solid", DASHES), "opacity": (N, 0.7, 0.2, 1.0), "ferry": (B, True),
        "curve": (N, 1.0, 0.0, 2.5),
    },
    "anim": {
        "on": (B, True), "planes": (B, True), "trains": (B, True), "cars": (B, True), "ferries": (B, True),
        "hide_line": (B, True), "speed": (N, 1.0, 0.25, 4.0), "size": (N, 1.0, 0.5, 2.0),
        "plane_speed": (N, 1.0, 0.25, 4.0),
        "min_km_plane": (N, 0, 0, 5000), "min_km_train": (N, 0, 0, 2000), "min_km_car": (N, 150, 0, 2000),
        "min_km_ferry": (N, 0, 0, 2000), "max_count": (N, 60, 5, 300),
    },
    "trips": {  # Trips map
        "arc_height": (N, 1.0, 0.3, 2.5), "line_width": (N, 1.0, 0.5, 3.0), "airports": (B, True),
        "labels": (E, "normal", ("all", "normal", "few", "off")), "dot_size": (N, 1.0, 0.5, 2.5),
        "label_size": (N, 1.0, 0.7, 1.8),
    },
    "tracks": {  # Tracks map
        "width": (N, 1.0, 0.4, 3.0), "opacity": (N, 1.0, 0.2, 1.0), "everyday_opacity": (N, 0.7, 0.1, 1.0),
        "glow": (B, False), "airports": (B, True),
    },
    "places": {  # Places & days map
        "size_min": (N, 3.0, 1.0, 12.0), "size_max": (N, 16.0, 4.0, 40.0),
        "size_by": (E, "days", ("days", "visits", "same")), "style": (E, "filled", ("filled", "ring", "glow")),
        "color_by": (E, "person", ("person", "year", "days")), "names": (E, "big", ("none", "big", "all")),
        "name_size": (N, 1.0, 0.6, 2.0), "name_min_days": (N, 2, 0, 60), "collide": (B, True),
        "opacity": (N, 0.85, 0.2, 1.0),
    },
    "regions": {  # Regions map
        "border_color": (C, ""), "border_width": (N, 1.0, 0.0, 4.0), "border_opacity": (N, 0.6, 0.0, 1.0),
        "borders": (E, "visited", ("visited", "all", "none")), "country_width": (N, 1.8, 0.0, 5.0),
        "fill_by": (E, "first", ("first", "days", "stay")), "fill_opacity": (N, 0.8, 0.1, 1.0),
        "names": (B, True),
    },
    "timelapse": {  # the travel film
        "cinema": (B, True), "skip_everyday": (B, True), "glow": (B, True), "speed": (N, 1.0, 0.25, 4.0),
        "cards": (B, True), "chapters": (B, True), "counters": (B, True), "min_km": (N, 0, 0, 3000),
        "pause": (N, 1.0, 0.0, 3.0),
    },
}

DEFAULT: dict = {
    "modes": {
        "road": {"color": "#0A7CFF", "dash": "solid", "width": 1.0},
        "rail": {"color": "#12A84F", "dash": "solid", "width": 1.0},
        "fly": {"color": "#FF3D9A", "dash": "dashed", "width": 1.0},
        "ferry": {"color": "#00BFB3", "dash": "solid", "width": 1.0},
        "foot": {"color": "#FF8A00", "dash": "solid", "width": 1.0},
    },
    **{sec: {k: v[1] for k, v in keys.items()} for sec, keys in SCHEMA.items()},
}


def _clamp(v, lo: float, hi: float, default: float) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    return round(max(lo, min(hi, f)), 2)


def _bool(v, default: bool) -> bool:
    return v if isinstance(v, bool) else default


def _value(spec, v):
    kind, default = spec[0], spec[1]
    if kind == B:
        return _bool(v, default)
    if kind == N:
        return _clamp(default if v is None else v, spec[2], spec[3], default)
    if kind == E:
        return v if v in spec[2] else default
    return v.upper() if isinstance(v, str) and COLOR_RE.match(v) else default  # colour ("" = automatic)


def validate(raw) -> dict:
    """A complete, safe style from whatever the browser sent (missing parts fall back to the defaults)."""
    raw = raw if isinstance(raw, dict) else {}
    out = copy.deepcopy(DEFAULT)
    modes = raw.get("modes") if isinstance(raw.get("modes"), dict) else {}
    for m in MODES:
        src = modes.get(m) if isinstance(modes.get(m), dict) else {}
        d = out["modes"][m]
        if COLOR_RE.match(str(src.get("color", ""))):
            d["color"] = src["color"].upper()
        if src.get("dash") in DASHES:
            d["dash"] = src["dash"]
        d["width"] = _clamp(src.get("width", d["width"]), 0.5, 3.0, d["width"])
    for sec, keys in SCHEMA.items():
        src = raw.get(sec) if isinstance(raw.get(sec), dict) else {}
        if sec == "anim" and src.get("vehicles") is False:  # styles saved before 0.7: one switch for trains and cars
            src = {"trains": False, "cars": False, **src}
        for k, spec in keys.items():
            out[sec][k] = _value(spec, src.get(k))
    return out


class StyleStore:
    def __init__(self, data_dir: str | None):
        self.path = Path(data_dir or "/data") / "style.json"
        self.lock = threading.Lock()

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("versions"), list):
                data["current"] = validate(data.get("current"))
                data["versions"] = [v for v in data["versions"] if isinstance(v, dict) and isinstance(v.get("id"), int)]
                data["presets"] = _presets(data.get("presets"))
                data["preset_default"] = _slot(data.get("preset_default"), -1)
                return data
        except (OSError, ValueError):
            pass
        return {"current": validate({}), "versions": [], "presets": _presets(None), "preset_default": -1}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".style-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, self.path)  # atomic: a crash never leaves a half-written file

    def get(self) -> dict:
        with self.lock:
            data = self._load()
        return self.get_unlocked(data)

    def preset(self, slot, action: str, name=None, style=None) -> dict:
        """Preset 1–3: save the given style into a slot, rename it, make it the default at start, or load it."""
        i = _slot(slot, None)
        if i is None or i < 0:
            raise LookupError("no such preset")
        if action == "load":
            with self.lock:
                p = self._load()["presets"][i]
            return self.save(p["style"], f"{p['name']} geladen")
        with self.lock:
            data = self._load()
            p = data["presets"][i]
            if action == "save":
                p["style"] = validate(style)
                if name is not None:
                    p["name"] = _name(name, i)
            elif action == "rename":
                p["name"] = _name(name, i)
            elif action == "default":
                data["preset_default"] = -1 if data["preset_default"] == i else i  # tap again: no default
            else:
                raise ValueError("unknown action")
            self._write(data)
            return self.get_unlocked(data)

    def save(self, style, note: str = "") -> dict:
        clean = validate(style)
        note = re.sub(r"[\x00-\x1f]", " ", str(note or ""))[:80].strip()
        with self.lock:
            data = self._load()
            if data["versions"] and data["versions"][-1].get("style") == clean and data["current"] == clean:
                return self.get_unlocked(data)
            nid = max((v["id"] for v in data["versions"]), default=0) + 1
            data["versions"].append({"id": nid, "ts": int(time.time()), "note": note or "Gespeichert", "style": clean})
            data["versions"] = data["versions"][-MAX_VERSIONS:]
            data["current"] = clean
            self._write(data)
            return self.get_unlocked(data)

    def restore(self, vid: int) -> dict:
        with self.lock:
            data = self._load()
            v = next((v for v in data["versions"] if v["id"] == vid), None)
        if not v:
            raise LookupError("version not found")
        when = time.strftime("%d.%m.%Y %H:%M", time.localtime(v.get("ts", 0)))
        return self.save(v.get("style"), f"Zurück zu {when}")

    @staticmethod
    def get_unlocked(data: dict) -> dict:
        return {"style": data["current"], "default": validate({}),
                "versions": [{"id": v["id"], "ts": v.get("ts", 0), "note": v.get("note", "")} for v in reversed(data["versions"])],
                "presets": data.get("presets") or _presets(None), "preset_default": data.get("preset_default", -1)}


def _name(v, i: int) -> str:
    """A safe preset name: no control characters, at most 24 characters, never empty."""
    t = re.sub(r"[\x00-\x1f<>]", "", str(v or "")).strip()[:24]
    return t or f"Preset {i + 1}"


def _slot(v, default):
    return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v < PRESETS else default


def _presets(raw) -> list:
    """Always exactly three presets; the first one is today's map, the others show the new looks."""
    starts = [{}, {"map": {"basemap": "earth", "look": "stars"}}, {"map": {"theme": "dark", "look": "crystal"}}]
    raw = raw if isinstance(raw, list) else []
    out = []
    for i in range(PRESETS):
        src = raw[i] if i < len(raw) and isinstance(raw[i], dict) else {}
        out.append({"name": _name(src.get("name"), i), "style": validate(src.get("style", starts[i]))})
    return out
