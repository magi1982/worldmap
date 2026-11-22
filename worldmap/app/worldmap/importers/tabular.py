"""CSV / Excel with unknown columns: find latitude, longitude and time by name.

Works for iCloud exports, exiftool dumps (``-csv``), Google My Maps tables,
Strava/Garmin CSVs and hand-made lists. Column names in English and German.
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata

from ..geo import parse_coordinate
from ..timeparse import parse_ts

MAX_CELL = 10_000

LAT = ("gpslatitude", "latitude", "lat", "breitengrad", "breite", "latitudee7")
LON = ("gpslongitude", "longitude", "lon", "lng", "long", "laengengrad", "langengrad", "lange", "laenge", "longitudee7")
LATREF = ("gpslatituderef",)
LONREF = ("gpslongituderef",)
PAIR = ("gpsposition", "coordinates", "coordinate", "coords", "koordinaten", "location", "position", "latlng", "geo")
TIME = (
    "aufnahmeutc", "datetimeoriginal", "gpsdatetime", "gpszeitutc", "aufnahmelokal", "aufnahme", "createdate", "creationdate", "timestamp", "datetime", "datumzeit",
    "date", "datum", "starttime", "start", "begin", "time", "zeit", "recorded", "createdat",
)
TIME_ONLY = ("time", "zeit", "uhrzeit")
DATE_ONLY = ("date", "datum")
HINT = ("directory", "folder", "ordner", "album", "sourcefile", "filename", "name", "title", "titel", "place", "ort")
CAMERA = ("model", "cameramodel", "make", "geraet", "device")


def _norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def decode_text(data: bytes) -> str:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def read_csv(text: str) -> list[list[str]]:
    sample = text[:20000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    csv.field_size_limit(MAX_CELL * 10)
    return [row for row in csv.reader(io.StringIO(text), dialect)]


def read_xlsx(data: bytes):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - dependency is installed in the image
        raise ValueError("Excel support needs openpyxl") from exc
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    best, best_name = [], ""
    for ws in wb.worksheets:
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        if len(rows) > len(best):
            best, best_name = rows, ws.title
    wb.close()
    return best, best_name


def _find(header: list[str], names, exact: bool = False) -> int | None:
    normed = [_norm(h) for h in header]
    for n in names:  # priority order
        for i, h in enumerate(normed):
            if h == n:
                return i
    if exact:
        return None
    for n in names:
        if len(n) < 4:
            continue
        for i, h in enumerate(normed):
            if n in h:
                return i
    return None


def _header_index(rows) -> int:
    for i, row in enumerate(rows[:30]):
        cells = [_norm(c) for c in row if c is not None]
        if any(c in LAT or c in PAIR or c in ("gpslatitude",) for c in cells):
            return i
    return 0


def detect_columns(header: list) -> dict:
    header = ["" if h is None else str(h) for h in header]
    m = {
        "lat": _find(header, LAT),
        "lon": _find(header, LON),
        "pair": None,
        "time": _find(header, TIME),
        "date": None,
        "clock": None,
        "lat_ref": _find(header, LATREF),
        "lon_ref": _find(header, LONREF),
        "hint": _find(header, HINT),
        "camera": _find(header, CAMERA),
    }
    if m["lat_ref"] is not None and m["lat_ref"] == m["lat"]:
        m["lat_ref"] = None
    if m["lon_ref"] is not None and m["lon_ref"] == m["lon"]:
        m["lon_ref"] = None
    if m["lat"] is None or m["lon"] is None:
        m["pair"] = _find(header, PAIR)
    d, c = _find(header, DATE_ONLY, exact=True), _find(header, TIME_ONLY, exact=True)
    if d is not None and c is not None and d != c:
        m["date"], m["clock"] = d, c
    m["names"] = {k: header[v] for k, v in m.items() if isinstance(v, int)}
    return m


def _cell(row, i):
    if i is None or i >= len(row):
        return None
    v = row[i]
    if isinstance(v, str) and len(v) > MAX_CELL:
        return None
    return v


def parse_rows(rows: list, tz: str):
    if not rows:
        return {}, []
    hi = _header_index(rows)
    m = detect_columns(rows[hi])
    if m["lat"] is None and m["pair"] is None:
        return m["names"], []
    if m["time"] is None and m["date"] is None:
        return m["names"], []

    time_name = _norm(m["names"].get("time", ""))
    row_tz = "UTC" if "utc" in time_name or time_name == "gpsdatetime" else tz

    def gen():
        for row in rows[hi + 1:]:
            if m["pair"] is not None:
                raw = str(_cell(row, m["pair"]) or "")
                parts = re.split(r"\s*[,;]\s*(?=[+-]?\d)", raw.replace("geo:", ""), maxsplit=1)
                if len(parts) != 2:
                    yield None, 0, 0, "csv", None, None
                    continue
                lat, lon = parse_coordinate(parts[0]), parse_coordinate(parts[1])
            else:
                lat, lon = parse_coordinate(_cell(row, m["lat"])), parse_coordinate(_cell(row, m["lon"]))
            if lat is None or lon is None:
                yield None, 0, 0, "csv", None, None
                continue
            if abs(lat) > 1000:  # E7 integers
                lat, lon = lat / 1e7, lon / 1e7
            ref = str(_cell(row, m["lat_ref"]) or "").strip().upper()[:1]
            if ref == "S":
                lat = -abs(lat)
            ref = str(_cell(row, m["lon_ref"]) or "").strip().upper()[:1]
            if ref == "W":
                lon = -abs(lon)
            if m["date"] is not None:
                ts = parse_ts(f"{_cell(row, m['date'])} {_cell(row, m['clock'])}".strip(), tz)
            else:
                ts = parse_ts(_cell(row, m["time"]), row_tz)
            hint_parts = [str(_cell(row, m[k])) for k in ("hint", "camera") if _cell(row, m[k])]
            yield ts, lat, lon, "csv", None, " | ".join(hint_parts) or None

    return m["names"], gen()
