"""Read GPS positions from photo EXIF data in mounted folders (read-only)."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from .timeparse import parse_ts

log = logging.getLogger(__name__)

EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".heic", ".heif"}
GPS_IFD = 0x8825
EXIF_IFD = 0x8769
DATETIME_ORIGINAL = 0x9003
MODEL = 0x0110


def _ratio(v) -> float:
    try:
        return float(v)
    except TypeError:
        num, den = v
        return num / den if den else 0.0


def _dms(values, ref) -> float | None:
    try:
        d, m, s = (_ratio(x) for x in values)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    v = d + m / 60 + s / 3600
    if str(ref).upper().startswith(("S", "W")):
        v = -v
    return v


def read_exif(path: Path, tz: str):
    """(ts, lat, lon, model) or None. Requires Pillow (pillow-heif optional)."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return None
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            gps = exif.get_ifd(GPS_IFD)
            if not gps or 2 not in gps or 4 not in gps:
                return None
            lat = _dms(gps[2], gps.get(1, "N"))
            lon = _dms(gps[4], gps.get(3, "E"))
            sub = exif.get_ifd(EXIF_IFD)
            when = sub.get(DATETIME_ORIGINAL) or exif.get(0x0132)
            model = exif.get(MODEL)
    except Exception as exc:  # noqa: BLE001 - broken files are common; skip them
        log.debug("EXIF read failed for %s: %s", path.name, exc)
        return None
    ts = parse_ts(when, tz) if when else None
    if lat is None or lon is None or ts is None:
        return None
    return ts, lat, lon, (str(model).strip() if model else None)


def owner_for(model: str | None, persons: list[dict]) -> str:
    if not model:
        return ""
    m = model.lower()
    for p in persons:
        for token in str(p.get("camera_models") or "").split(","):
            token = token.strip().lower()
            if token and token in m:
                return p.get("label", "")
    return ""


def scan(roots: list[str], since_mtime: float, persons: list[dict], tz: str, max_files: int = 20000):
    """Yield points for photos changed after ``since_mtime``; never leaves the roots."""
    seen = 0
    for root in roots:
        base = Path(root).resolve()
        if not base.is_dir():
            log.warning("photo folder not found: %s", root)
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = [d for d in dirnames if not d.startswith((".", "@", "#"))]  # skip @eaDir etc.
            for fn in filenames:
                p = Path(dirpath) / fn
                if p.suffix.lower() not in EXTS or p.is_symlink():
                    continue
                try:
                    if p.stat().st_mtime <= since_mtime:
                        continue
                except OSError:
                    continue
                seen += 1
                if seen > max_files:
                    return
                r = read_exif(p, tz)
                if not r:
                    continue
                ts, lat, lon, model = r
                rel = p.parent.relative_to(base)
                hint = " / ".join(rel.parts[-2:]) if rel.parts else None
                if model:
                    hint = f"{hint} | {model}" if hint else model
                yield ts, lat, lon, owner_for(model, persons), "exif", None, hint
