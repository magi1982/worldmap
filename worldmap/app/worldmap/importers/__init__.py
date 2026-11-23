"""Import location data from any file the user drops in.

Every importer yields ``Point`` tuples. ``detect_and_parse`` sniffs the format
from the content (never trusts the file name alone).
"""
from __future__ import annotations

import gzip
import io
import json
from dataclasses import dataclass, field

from ..geo import valid_coord
from . import google, gpx, package, tabular, triplist

# (ts, lat, lon, person, source, accuracy, hint)
Point = tuple

MAX_POINTS = 5_000_000


@dataclass
class ImportResult:
    format: str
    points: list = field(default_factory=list)
    skipped: int = 0
    columns: dict | None = None  # column mapping for tabular data (shown in the preview)
    warnings: list = field(default_factory=list)
    trips: list = field(default_factory=list)  # trip lists: one dict per trip
    persons: list = field(default_factory=list)  # Worldmap package: persons and groups it was made with
    groups: list = field(default_factory=list)


class UserImportError(ValueError):
    """Raised for input the user can fix (unknown format, no coordinates, ...)."""


def _clean(points, person: str, result: ImportResult) -> None:
    for p in points:
        ts, lat, lon, src, acc, hint = p
        if ts is None or not valid_coord(lat, lon):
            result.skipped += 1
            continue
        if len(result.points) >= MAX_POINTS:
            result.warnings.append(f"stopped after {MAX_POINTS} points")
            return
        hint = (str(hint)[:200] if hint else None)
        result.points.append((int(ts), float(lat), float(lon), person, src, acc, hint))


MAX_UNZIPPED = 1024 * 1024 * 1024


def _gunzip(data: bytes) -> bytes:
    out = bytearray()
    d = gzip.GzipFile(fileobj=io.BytesIO(data))
    while chunk := d.read(1 << 20):
        out += chunk
        if len(out) > MAX_UNZIPPED:  # zip bomb guard
            raise UserImportError("file too large after unpacking")
    return bytes(out)


def detect_and_parse(data: bytes, filename: str = "", person: str = "", tz: str = "Europe/Zurich") -> ImportResult:
    if data[:2] == b"\x1f\x8b":
        try:
            data = _gunzip(data)
        except (OSError, EOFError) as exc:
            raise UserImportError(f"invalid gzip file: {exc}") from exc
        filename = (filename or "").removesuffix(".gz")
    name = (filename or "").lower()
    head = data[:4096].lstrip()
    if data[:2] == b"PK" or name.endswith((".xlsx", ".xlsm")):
        rows, sheet = tabular.read_xlsx(data)
        trip_res = _trips(rows, "xlsx")
        if trip_res:
            return trip_res
        res = ImportResult(format="xlsx")
        mapping, pts = tabular.parse_rows(rows, tz)
        res.columns = mapping
        _clean(pts, person, res)
        _require(res)
        return res
    if head.startswith(b"<"):
        text = data.decode("utf-8", errors="replace")
        kind, pts = gpx.parse_xml(text)
        res = ImportResult(format=kind)
        _clean(pts, person, res)
        _require(res)
        return res
    if head[:1] in (b"{", b"["):
        try:
            obj = json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise UserImportError(f"invalid JSON: {exc}") from exc
        if package.is_package(obj):
            pts, trips, persons, groups, problems = package.parse(obj)
            res = ImportResult(format="worldmap", trips=trips, persons=persons, groups=groups, warnings=problems)
            for ts, lat, lon, src, acc, hint, who in pts:
                if valid_coord(lat, lon) and len(res.points) < MAX_POINTS:
                    res.points.append((ts, lat, lon, who, src, acc, hint))
                else:
                    res.skipped += 1
            if not res.points and not res.trips:
                raise UserImportError("the Worldmap package is empty")
            return res
        kind, pts = google.parse(obj, tz)
        if kind is None:
            raise UserImportError("JSON format not recognised (expected a Google Timeline export)")
        res = ImportResult(format=kind)
        _clean(pts, person, res)
        _require(res)
        return res
    text = tabular.decode_text(data)
    rows = tabular.read_csv(text)
    trip_res = _trips(rows, "trips-csv")
    if trip_res:
        return trip_res
    mapping, pts = tabular.parse_rows(rows, tz)
    res = ImportResult(format="csv", columns=mapping)
    _clean(pts, person, res)
    _require(res)
    return res


def _trips(rows, fmt):
    names, trips, skipped = triplist.parse_rows(rows)
    if not names:
        return None
    if not trips:
        raise UserImportError("trip list recognised, but no row has a start date and a destination")
    res = ImportResult(format=fmt, columns=names, skipped=skipped, trips=trips)
    missing = sum(1 for t in trips if t.get("lat") is None)
    if missing:
        res.warnings.append(f"{missing} destinations not found on the map – edit them in the list")
    return res


def _require(res: ImportResult) -> None:
    if not res.points:
        raise UserImportError(
            f"no usable coordinates found (format: {res.format}, skipped rows: {res.skipped})"
        )


__all__ = ["detect_and_parse", "ImportResult", "UserImportError", "Point"]
