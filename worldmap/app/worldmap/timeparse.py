"""Tolerant timestamp parsing for the many formats found in exports."""
from __future__ import annotations

import re
from datetime import UTC, datetime, timezone
from zoneinfo import ZoneInfo

_EXIF = re.compile(r"^(\d{4})[:\-./](\d{2})[:\-./](\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?\s*(Z|[+-]\d{2}:?\d{2})?$")
_DMY = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:[ ,]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$")
_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def parse_ts(value, tz: str = "UTC") -> int | None:
    """Return unix seconds (UTC) or None. Naive times are read in ``tz``."""
    if value is None or value == "":
        return None
    zone = ZoneInfo(tz)
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=zone)
        return int(dt.timestamp())
    if isinstance(value, (int, float)):
        v = float(value)
        if v > 1e14:      # microseconds
            v /= 1e6
        elif v > 1e11:    # milliseconds
            v /= 1e3
        return int(v) if 0 < v < 4e9 else None
    s = str(value).strip()
    if s.isdigit():
        return parse_ts(int(s), tz)
    m = _EXIF.match(s)
    if m:
        y, mo, d, h, mi, se, off = m.groups()
        dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(se or 0))
        if off:
            if off == "Z":
                dt = dt.replace(tzinfo=UTC)
            else:
                off = off.replace(":", "")
                sign = 1 if off[0] == "+" else -1
                from datetime import timedelta

                dt = dt.replace(tzinfo=timezone(sign * timedelta(hours=int(off[1:3]), minutes=int(off[3:5]))))
        else:
            dt = dt.replace(tzinfo=zone)
        return int(dt.timestamp())
    m = _DMY.match(s)
    if m:
        d, mo, y, h, mi, se = m.groups()
        dt = datetime(int(y), int(mo), int(d), int(h or 12), int(mi or 0), int(se or 0), tzinfo=zone)
        return int(dt.timestamp())
    m = _DATE.match(s)
    if m:
        return int(datetime(*map(int, m.groups()), 12, tzinfo=zone).timestamp())
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zone)
    return int(dt.timestamp())


def local_date(ts: int, tz: str) -> str:
    return datetime.fromtimestamp(ts, ZoneInfo(tz)).date().isoformat()
