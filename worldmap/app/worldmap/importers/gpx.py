"""GPX and KML (incl. Google ``gx:Track``) parsing with the stdlib XML parser.

External entities and DTDs are rejected before parsing (XXE / billion laughs).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET  # nosec B405 - input is checked for DTD/entities first

from ..timeparse import parse_ts

_FORBIDDEN = re.compile(r"<!DOCTYPE|<!ENTITY", re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(text: str):
    if _FORBIDDEN.search(text):  # anywhere in the file, not only at the start
        raise ValueError("XML with DOCTYPE/ENTITY declarations is not accepted")
    root = ET.fromstring(text)  # nosec B314 - DTD/entities rejected above
    kind = _local(root.tag).lower()
    if kind == "gpx":
        return "gpx", list(_gpx(root))
    if kind == "kml":
        return "kml", list(_kml(root))
    raise ValueError(f"unknown XML document <{kind}>")


def _gpx(root):
    for el in root.iter():
        if _local(el.tag) not in ("trkpt", "rtept", "wpt"):
            continue
        try:
            lat, lon = float(el.get("lat")), float(el.get("lon"))
        except (TypeError, ValueError):
            continue
        ts = None
        name = None
        for ch in el:
            t = _local(ch.tag)
            if t == "time":
                ts = parse_ts(ch.text)
            elif t == "name":
                name = ch.text
        yield ts, lat, lon, "gpx", None, name


def _kml(root):
    for pm in root.iter():
        tag = _local(pm.tag)
        if tag == "Track":  # gx:Track: <when> and <gx:coord> pairs
            whens = [parse_ts(c.text) for c in pm if _local(c.tag) == "when"]
            coords = [c.text for c in pm if _local(c.tag) == "coord"]
            for ts, c in zip(whens, coords, strict=False):
                parts = (c or "").split()
                if len(parts) >= 2:
                    yield ts, float(parts[1]), float(parts[0]), "kml", None, None
        elif tag == "Placemark":
            when = None
            for el in pm.iter():
                if _local(el.tag) in ("when", "begin"):
                    when = parse_ts(el.text)
                    break
            if when is None:
                continue
            for el in pm.iter():
                if _local(el.tag) == "coordinates" and el.text:
                    for tok in el.text.split():
                        parts = tok.split(",")
                        if len(parts) >= 2:
                            yield when, float(parts[1]), float(parts[0]), "kml", None, None
