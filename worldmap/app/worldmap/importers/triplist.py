"""Trip lists (Excel/CSV/pasted text): one row per trip with dates and a destination.

Typical columns (German or English, any order): Von/Start, Bis/Ende, Ziel/Hauptziel/Ort,
Land, Wer, Sicherheit, Nächte, Verkehrsmittel/Unterwegs mit, Notiz, Quelle, Entfernung.
Destinations without coordinates are looked up in the bundled gazetteer (regions first).
"""
from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime

from .. import airports, places
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
STATIONS = ("stationen", "stations", "route", "etappen")
LAT = ("lat", "latitude", "breite", "breitengrad")
LON = ("lon", "lng", "longitude", "laenge", "lange", "laengengrad", "langengrad")

COUNTRY_CC = {v.lower(): k for k, v in places.COUNTRY_DE.items()}
COUNTRY_CC.update({"grossbritannien": "GB", "vereinigtes königreich": "GB", "uk": "GB", "united kingdom": "GB",
                   "england": "GB", "schottland": "GB", "wales": "GB", "holland": "NL", "usa": "US"})


def looks_like_trip_list(header: list) -> bool:
    h = ["" if x is None else str(x) for x in header]
    if _find(h, START, exact=True) is None or _find(h, DEST) is None:
        return False
    # a list with coordinates is still a trip list when it has an end date column (point exports have none)
    return _find(h, LAT, exact=True) is None or _find(h, END, exact=True) is not None


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


def _fold(s: str) -> str:
    return places._fold(s)


def geocode(name: str, country: str = "", home: tuple | None = None,
            max_km: float | None = None) -> tuple[float, float, float | None, str] | None:
    """(lat, lon, radius_km, kind) for a free-text destination like "Mallorca (Porto Cristo)".

    ``kind`` is "place" (a town, region or airport town) or "country" – then only the country is known and the
    coordinates are just its middle. A country is never a place on the map: the middle of Greece is the Cyclades,
    the middle of "France & Spain" is somewhere in Spain.

    With ``home`` and ``max_km`` (how far the trip went) the place that fits the distance wins:
    Brühl near Cologne instead of Brühl near Mannheim, London in England instead of London in Canada.
    """
    cc = COUNTRY_CC.get((country or "").strip().lower())
    cname = places.COUNTRY_DE.get(cc, country or "")
    parts = [name]
    parts += [p for p in re.split(r"\s+[–-]\s+|\s*[(),/&]\s*|\s+bei\s+|\s+und\s+", name) if p]
    words = [w for w in re.split(r"[\s(),/&–-]+", name) if len(w) >= 4 and w[:1].isupper()]
    fits = None
    if home and max_km and max_km > 0:
        from ..geo import haversine_km

        def off(h):  # how badly a place fits the distance of the trip
            return abs(haversine_km(home[0], home[1], h["lat"], h["lon"]) - max_km)

        def fits(h):
            return off(h) <= max(60.0, max_km * .35)
    for n, part in enumerate(parts + words):
        part = part.strip(" )·")
        if len(part) < 3:
            continue
        hits = [h for h in places.search(part, limit=10) if h.get("lat") is not None]
        if cname:
            same = [h for h in hits if h.get("country") == cname]
            hits = same or ([] if hits and all(h.get("country") for h in hits) and cc else hits)
        exact = [h for h in hits if h["name"].lower() == part.lower()]
        if n >= len(parts):  # single words: exact names only
            hits = exact
        if fits:
            good = [h for h in exact if fits(h)] or [h for h in hits if fits(h)]  # exact names first
            if not good:
                continue
            h = min(good, key=off)
        elif home:  # distance unknown: only names that match exactly (no guessing "Gommer See" → somewhere)
            h = (exact or [x for x in hits if x.get("kind") == "region" and _fold(x["name"]) == _fold(part)] or [None])[0]
        else:
            h = (exact or hits or [None])[0]
        if h:  # a country found by name is still only a country, not a place on the map
            return h["lat"], h["lon"], h.get("radius_km"), "country" if h.get("kind") == "country" else "place"
    for part in parts:  # a holiday town with its own airport ("Marsa Alam")
        ap = airports.by_city(part.strip(" )·"))
        if ap:
            return ap[2], ap[3], None, "place"
    for part in parts:  # a country as destination ("Kenia", "Kroatien")
        pc = COUNTRY_CC.get(part.strip(" )·").lower())
        if pc and pc != cc:
            box = places.country_box(pc)
            if box:
                return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, None, "country"
    if cc:  # at least the country
        box = places.country_box(cc)
        if box:
            return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, None, "country"
    return None


TRANSPORT_WORDS = ("Auto", "Zug", "Bus", "Flug", "Wasserflugzeug", "Schiff", "Wohnmobil", "Velo", "zu Fuss")


def stations_text(legs: list) -> str:
    """Stops as one cell: "✈ DXB [Flug] → Abu Dhabi [Auto]" – readable, and read back by ``parse_stations``."""
    out = []
    for x in legs or []:
        name = f"✈ {x['ap']}" if x.get("ap") else str(x.get("name") or "")
        out.append(f"{name} [{x.get('transport') or 'Auto'}]")
    return " → ".join(out)


def parse_stations(text: str, country: str = "") -> list[dict]:
    """A "Stationen" cell back into stops; places are looked up offline, unknown ones keep only their name."""
    out: list[dict] = []
    for part in re.split(r"\s*(?:→|->|>)\s*", text or "")[:20]:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.*?)\s*[\[(]([^\])]*)[\])]\s*$", part)
        name, tr = (m.group(1).strip(), m.group(2).strip()) if m else (part, "")
        parts = [w.strip() for w in tr.split("·") if w.strip() in TRANSPORT_WORDS]
        tr = " · ".join(parts) or "Auto"
        code = re.match(r"^✈\s*([A-Za-z]{3})$", name)
        ap = airports.by_iata(code.group(1)) if code else None
        if ap:
            out.append({"name": ap[1], "country": "", "lat": ap[2], "lon": ap[3], "transport": tr, "ap": ap[0]})
            continue
        g = geocode(name[:80], country)
        if g and g[3] == "place":
            out.append({"name": name[:80], "country": country, "lat": round(g[0], 4), "lon": round(g[1], 4),
                        "transport": tr})
        else:  # not found offline: a stop without a point, it gets the "where exactly?" question
            out.append({"name": name[:80], "country": country, "lat": None, "lon": None, "transport": tr})
    return out


def parse_rows(rows: list) -> tuple[dict, list[dict], int]:
    """-> (column names, trips, skipped rows)."""
    hi = next((i for i, r in enumerate(rows[:30]) if looks_like_trip_list(r)), None)
    if hi is None:
        return {}, [], 0
    header = ["" if x is None else str(x) for x in rows[hi]]
    col = {k: _find(header, names, exact=k in ("start", "end", "lat", "lon"))
           for k, names in (("start", START), ("end", END), ("dest", DEST), ("country", COUNTRY), ("who", WHO),
                            ("conf", CONF), ("nights", NIGHTS), ("transport", TRANSPORT), ("note", NOTE),
                            ("source", SOURCE), ("km", KM), ("lat", LAT), ("lon", LON), ("stations", STATIONS))}
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
            if g and g[3] == "place":  # only the country known: no point (it would be the middle of the country)
                t["lat"], t["lon"] = round(g[0], 4), round(g[1], 4)
                if g[2]:
                    t["radius_km"] = g[2]
        legs = parse_stations(str(cell(row, "stations") or ""), t["country"])
        if legs:
            t["legs"] = json.dumps(legs, ensure_ascii=False)
        trips.append(t)
    return names, trips, skipped
