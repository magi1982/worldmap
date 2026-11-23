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
BASEMAPS = ("standard", "paper", "mono")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_VERSIONS = 20

DEFAULT: dict = {
    "modes": {
        "road": {"color": "#0A7CFF", "dash": "solid", "width": 1.0},
        "rail": {"color": "#12A84F", "dash": "solid", "width": 1.0},
        "fly": {"color": "#FF3D9A", "dash": "dashed", "width": 1.0},
        "ferry": {"color": "#00BFB3", "dash": "solid", "width": 1.0},
        "foot": {"color": "#FF8A00", "dash": "solid", "width": 1.0},
    },
    "areas": {"show": True, "opacity": 1.0, "size": 1.0, "outline": True},
    "map": {"rivers": True, "provinces": True, "labels": "normal", "theme": "auto", "palette": "neon", "basemap": "standard"},
    "anim": {"on": True, "planes": True, "vehicles": True, "hide_line": True, "speed": 1.0, "size": 1.0},
    "timelapse": {"cinema": True, "skip_everyday": True, "glow": True},
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
    areas = raw.get("areas") if isinstance(raw.get("areas"), dict) else {}
    a = out["areas"]
    a["show"] = _bool(areas.get("show"), a["show"])
    a["outline"] = _bool(areas.get("outline"), a["outline"])
    a["opacity"] = _clamp(areas.get("opacity", a["opacity"]), 0.1, 1.0, a["opacity"])
    a["size"] = _clamp(areas.get("size", a["size"]), 0.5, 3.0, a["size"])
    mp = raw.get("map") if isinstance(raw.get("map"), dict) else {}
    b = out["map"]
    b["rivers"] = _bool(mp.get("rivers"), b["rivers"])
    b["provinces"] = _bool(mp.get("provinces"), b["provinces"])
    if mp.get("labels") in ("many", "normal", "few", "off"):
        b["labels"] = mp["labels"]
    if mp.get("theme") in ("auto", "light", "dark"):
        b["theme"] = mp["theme"]
    if mp.get("palette") in PALETTES:
        b["palette"] = mp["palette"]
    if mp.get("basemap") in BASEMAPS:
        b["basemap"] = mp["basemap"]
    an = raw.get("anim") if isinstance(raw.get("anim"), dict) else {}
    c = out["anim"]
    for k in ("on", "planes", "vehicles", "hide_line"):
        c[k] = _bool(an.get(k), c[k])
    c["speed"] = _clamp(an.get("speed", c["speed"]), 0.25, 4.0, c["speed"])
    c["size"] = _clamp(an.get("size", c["size"]), 0.5, 2.0, c["size"])
    tl = raw.get("timelapse") if isinstance(raw.get("timelapse"), dict) else {}
    d = out["timelapse"]
    for k in ("cinema", "skip_everyday", "glow"):
        d[k] = _bool(tl.get(k), d[k])
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
                return data
        except (OSError, ValueError):
            pass
        return {"current": validate({}), "versions": []}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".style-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, self.path)  # atomic: a crash never leaves a half-written file

    def get(self) -> dict:
        with self.lock:
            data = self._load()
        return {"style": data["current"], "default": validate({}),
                "versions": [{"id": v["id"], "ts": v.get("ts", 0), "note": v.get("note", "")} for v in reversed(data["versions"])]}

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
                "versions": [{"id": v["id"], "ts": v.get("ts", 0), "note": v.get("note", "")} for v in reversed(data["versions"])]}
