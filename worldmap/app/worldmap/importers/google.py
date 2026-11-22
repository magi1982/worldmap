"""Google location history in all known shapes.

* Takeout ``Records.json``                    -> {"locations": [...latitudeE7...]}
* Takeout Semantic Location History          -> {"timelineObjects": [...]}
* On-device Timeline export, Android         -> {"semanticSegments": [...], "rawSignals": [...]}
* On-device Timeline export, iOS             -> [{"startTime", "visit"|"activity"|"timelinePath"}]
"""
from __future__ import annotations

import re

from ..timeparse import parse_ts

SRC = "google"
_LATLNG = re.compile(r"(-?\d+(?:\.\d+)?)\s*°?\s*,\s*(-?\d+(?:\.\d+)?)")


def _latlng(value):
    """'geo:47.1,9.2' | '47.1°, 9.2°' | {'latLng': ...} | {'latitudeE7':..}"""
    if value is None:
        return None
    if isinstance(value, dict):
        if "latitudeE7" in value and "longitudeE7" in value:
            return value["latitudeE7"] / 1e7, value["longitudeE7"] / 1e7
        if "latE7" in value and "lngE7" in value:
            return value["latE7"] / 1e7, value["lngE7"] / 1e7
        for k in ("latLng", "LatLng", "placeLocation", "point"):
            if k in value:
                return _latlng(value[k])
        return None
    m = _LATLNG.search(str(value))
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


def _records(obj, tz):
    for loc in obj.get("locations", []):
        ll = _latlng(loc)
        if not ll:
            continue
        ts = parse_ts(loc.get("timestamp") or loc.get("timestampMs"), tz)
        yield ts, ll[0], ll[1], SRC, loc.get("accuracy"), None


def _semantic(obj, tz):
    for o in obj.get("timelineObjects", []):
        if "placeVisit" in o:
            pv = o["placeVisit"]
            ll = _latlng(pv.get("location", {}))
            dur = pv.get("duration", {})
            name = pv.get("location", {}).get("name")
            for key in ("startTimestamp", "endTimestamp", "startTimestampMs", "endTimestampMs"):
                if ll and dur.get(key):
                    yield parse_ts(dur[key], tz), ll[0], ll[1], SRC, None, name
        if "activitySegment" in o:
            a = o["activitySegment"]
            dur = a.get("duration", {})
            act = a.get("activityType")
            s = _latlng(a.get("startLocation", {}))
            e = _latlng(a.get("endLocation", {}))
            if s:
                yield parse_ts(dur.get("startTimestamp") or dur.get("startTimestampMs"), tz), s[0], s[1], SRC, None, act
            for p in (a.get("simplifiedRawPath") or {}).get("points", []):
                ll = _latlng(p)
                if ll:
                    yield parse_ts(p.get("timestamp") or p.get("timestampMs"), tz), ll[0], ll[1], SRC, None, act
            if e:
                yield parse_ts(dur.get("endTimestamp") or dur.get("endTimestampMs"), tz), e[0], e[1], SRC, None, act


def _segment(seg, tz):
    start = seg.get("startTime")
    t0 = parse_ts(start, tz)
    t1 = parse_ts(seg.get("endTime"), tz)
    visit = seg.get("visit")
    if visit:
        ll = _latlng((visit.get("topCandidate") or {}).get("placeLocation"))
        if ll:
            for t in (t0, t1):
                yield t, ll[0], ll[1], SRC, None, None
    act = seg.get("activity")
    if act:
        kind = (act.get("topCandidate") or {}).get("type")
        s, e = _latlng(act.get("start")), _latlng(act.get("end"))
        if s:
            yield t0, s[0], s[1], SRC, None, kind
        if e:
            yield t1, e[0], e[1], SRC, None, kind
    for p in seg.get("timelinePath", []) or []:
        ll = _latlng(p.get("point"))
        if not ll:
            continue
        if p.get("time"):
            ts = parse_ts(p["time"], tz)
        elif t0 is not None and p.get("durationMinutesOffsetFromStartTime") is not None:
            try:
                ts = t0 + int(float(p["durationMinutesOffsetFromStartTime"]) * 60)
            except (TypeError, ValueError):
                ts = None
        else:
            ts = t0
        yield ts, ll[0], ll[1], SRC, None, None


def _device(obj, tz):
    segs = obj["semanticSegments"] if isinstance(obj, dict) else obj
    for seg in segs:
        if isinstance(seg, dict):
            yield from _segment(seg, tz)
    if isinstance(obj, dict):
        for sig in obj.get("rawSignals", []):
            pos = sig.get("position")
            if pos:
                ll = _latlng(pos)
                if ll:
                    yield parse_ts(pos.get("timestamp"), tz), ll[0], ll[1], SRC, pos.get("accuracyMeters"), None


def parse(obj, tz: str = "UTC"):
    """Return (format_name, iterator) or (None, None)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("locations"), list):
            return "google-records", _records(obj, tz)
        if isinstance(obj.get("timelineObjects"), list):
            return "google-semantic", _semantic(obj, tz)
        if isinstance(obj.get("semanticSegments"), list):
            return "google-device", _device(obj, tz)
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "startTime" in obj[0]:
        return "google-device-ios", _device(obj, tz)
    return None, None


__all__ = ["parse"]
