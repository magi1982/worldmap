"""Trip lists (Excel/CSV/pasted text): one row per trip with dates and a destination.

Typical columns (German or English, any order): Von/Start, Bis/Ende, Ziel/Hauptziel/Ort,
Land, Wer, Sicherheit, Nächte, Verkehrsmittel/Unterwegs mit, Notiz, Quelle, Entfernung.
Destinations without coordinates are looked up in the bundled gazetteer (regions first).
"""
from __future__ import annotations

import re
from datetime import UTC, date, datetime

from .. import places
from ..db import CONFIDENCE
from ..timeparse import parse_ts
from .tabular import _find

START = ("von", "start", "startdatum", "beginn", "abreise", "from", "startdate", "datumvon", "anreise")
END = ("bis", "ende", "enddatum", "rueckkehr", "ruckkehr", "to", "enddate", "datumbis", "abreisedatum")
DEST = ("hauptziel", "ziel", "reiseziel", "destination", "ort", "place", "name", "titel", "title")
COUNTRY = ("land", "country", "staat")
WHO = ("wer", "who", "personen", "mitreisende")
CONF = ("sicherheit", "confidence")
NIGHTS = ("naechte", "nachte", "nights", "uebernachtungen")
TRANSPORT = ("unterwegsmit", "verkehrsmittel", "transport", "womit", "anreiseart")
NOTE = ("notiz", "note", "bemerkung", "kommentar", "comment")
SOURCE = ("quelle", "source")
KM = ("maxentfernungkm", "entfernungkm", "entfernung", "km", "distancekm", "distance")
LAT = ("lat", "latitude", "breite", "breitengrad")
LON = ("lon", "lng", "longitude", "laenge", "lange", "laengengrad")

COUNTRY_CC = {v.lower(): k for k, v in places.COUNTRY_DE.items()}
COUNTRY_CC.update({"grossbritannien": "GB", "vereinigtes königreich": "GB", "uk": "GB", "united kingdom": "GB",
                   "england": "GB", "schottland": "GB", "wales": "GB", "holland": "NL", "usa": "US"})


def looks_like_trip_list(header: list) -> bool:
    h = ["" if x is None else str(x) for x in header]
    return _find(h, START, exact=True) is not None and _find(h, DEST) is not None and _find(h, LAT, exact=True) is None


def _date(v) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    ts = parse_ts(v, "UTC")
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, UTC).date().isoformat()


def geocode(name: str, country: str = "") -> tuple[float, float, float | None] | None:
    """(lat, lon, radius_km) for a free-text destination like "Mallorca (Porto Cristo)"."""
    cc = COUNTRY_CC.get((country or "").strip().lower())
    cname = places.COUNTRY_DE.get(cc, country or "")
    parts = [name]
    parts += [p for p in re.split(r"\s+[–-]\s+|\s*[(),/]\s*|\s+bei\s+|\s+und\s+", name) if p]
    for part in parts:
        part = part.strip(" )·")
        if len(part) < 3:
            continue
        hits = places.search(part, limit=10)
        if cname:
            same = [h for h in hits if h.get("country") == cname]
            hits = same or ([] if hits and all(h.get("country") for h in hits) and cc else hits)
        exact = [h for h in hits if h["name"].lower() == part.lower()]
        h = (exact or hits or [None])[0]
        if h and h.get("lat") is not None:
            return h["lat"], h["lon"], h.get("radius_km")
    if cc:  # at least the country
        box = places.country_box(cc)
        if box:
            return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, None
    return None


def parse_rows(rows: list) -> tuple[dict, list[dict], int]:
    """-> (column names, trips, skipped rows)."""
    hi = next((i for i, r in enumerate(rows[:30]) if looks_like_trip_list(r)), None)
    if hi is None:
        return {}, [], 0
    header = ["" if x is None else str(x) for x in rows[hi]]
    col = {k: _find(header, names, exact=k in ("start", "end", "lat", "lon"))
           for k, names in (("start", START), ("end", END), ("dest", DEST), ("country", COUNTRY), ("who", WHO),
                            ("conf", CONF), ("nights", NIGHTS), ("transport", TRANSPORT), ("note", NOTE),
                            ("source", SOURCE), ("km", KM), ("lat", LAT), ("lon", LON))}
    names = {k: header[v] for k, v in col.items() if v is not None}

    def cell(row, k):
        i = col.get(k)
        return row[i] if i is not None and i < len(row) else None

    trips, skipped = [], 0
    for row in rows[hi + 1:]:
        a, b = _date(cell(row, "start")), _date(cell(row, "end"))
        dest = str(cell(row, "dest") or "").strip()[:120]
        if not a or not dest:
            skipped += 1 if any(c not in (None, "") for c in row) else 0
            continue
        b = b or a
        if b < a:
            a, b = b, a
        t = {"start_date": a, "end_date": b, "destination": dest,
             "country": str(cell(row, "country") or "").strip()[:60],
             "who": str(cell(row, "who") or "").strip()[:60],
             "transport": str(cell(row, "transport") or "").strip()[:80],
             "note": str(cell(row, "note") or "").strip()[:1000],
             "source": (str(cell(row, "source") or "").strip() or "Import")[:80],
             "nights": (date.fromisoformat(b) - date.fromisoformat(a)).days}
        conf = str(cell(row, "conf") or "").strip().lower()
        t["confidence"] = conf if conf in CONFIDENCE else ("bestätigt" if t["who"] else "tief")
        km = cell(row, "km")
        try:
            t["max_km"] = float(str(km).replace("'", "").replace("’", "").replace(",", ".")) if km not in (None, "") else None
        except ValueError:
            t["max_km"] = None
        try:
            lat, lon = float(cell(row, "lat")), float(cell(row, "lon"))
            t["lat"], t["lon"] = lat, lon
        except (TypeError, ValueError):
            g = geocode(dest, t["country"])
            if g:
                t["lat"], t["lon"] = round(g[0], 4), round(g[1], 4)
                if g[2]:
                    t["radius_km"] = g[2]
        trips.append(t)
    return names, trips, skipped
