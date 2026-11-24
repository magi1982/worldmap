"""Trip dates as people remember them: a day, a range of days, only a month or only a year.

``parse("Juli 2009", nights=7)`` → ``{"start_date": "2009-07-12", "end_date": "2009-07-19", "date_prec": "month",
"nights": 7}``. A month or a year is stored as a representative stay in its middle (mid-month / mid-year) so the map,
the film, sorting and statistics keep working; ``date_prec`` tells the screens to show only "Juli 2009" or "2009".
"""
from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

PRECISIONS = ("day", "month", "year")
MIN_YEAR, MAX_YEAR = 1900, 2100

MONTHS = {
    "jan": 1, "januar": 1, "january": 1, "jänner": 1, "janvier": 1,
    "feb": 2, "februar": 2, "february": 2, "février": 2,
    "mär": 3, "mar": 3, "märz": 3, "maerz": 3, "march": 3, "mars": 3,
    "apr": 4, "april": 4, "avril": 4,
    "mai": 5, "may": 5,
    "jun": 6, "juni": 6, "june": 6, "juin": 6,
    "jul": 7, "juli": 7, "july": 7, "juillet": 7,
    "aug": 8, "august": 8, "août": 8,
    "sep": 9, "sept": 9, "september": 9, "septembre": 9,
    "okt": 10, "oct": 10, "oktober": 10, "october": 10, "octobre": 10,
    "nov": 11, "november": 11, "novembre": 11,
    "dez": 12, "dec": 12, "dezember": 12, "december": 12, "décembre": 12,
}
_DASH = r"\s*(?:–|—|-|bis|to|au)\s*"
_FUZZY = re.compile(r"^(?:ca\.?|circa|etwa|ungefähr|um|~)\s*", re.I)


def _year(s: str) -> int:
    y = int(s)
    if len(s) == 2:
        y += 1900 if y >= 50 else 2000
    if not MIN_YEAR <= y <= MAX_YEAR:
        raise ValueError(f"Jahr {y} ausserhalb {MIN_YEAR}–{MAX_YEAR}")
    return y


def _day(d: str, m: str, y: str) -> date:
    try:
        return date(_year(y), int(m), int(d))
    except ValueError:
        raise ValueError(f"kein gültiges Datum: {d}.{m}.{y}") from None


def _month_name(s: str) -> int | None:
    return MONTHS.get(s.lower().rstrip("."))


def _centre(first: date, last: date, nights: int) -> tuple[date, date]:
    """A stay of ``nights`` in the middle of [first, last], never outside it if it fits."""
    span = (last - first).days
    nights = max(0, nights)
    if nights >= span:
        return first, first + timedelta(days=nights)
    mid = first + timedelta(days=span // 2)
    start = mid - timedelta(days=nights // 2)
    return start, start + timedelta(days=nights)


def _out(start: date, end: date, prec: str) -> dict:
    return {"start_date": start.isoformat(), "end_date": end.isoformat(), "date_prec": prec,
            "nights": (end - start).days}


def parse(text: str, nights: int | None = None) -> dict:
    """Read "13.07.2009", "13.–25.07.2009", "2009-07-13", "07.2009", "Juli 2009", "2009", "ca. 2009" …

    ``nights`` (the trip's current length) is kept when only a start day, a month or a year is given.
    Raises ValueError with a German message when the text is not a date.
    """
    s = _FUZZY.sub("", str(text or "").strip()).strip()
    s = re.sub(r"\s+", " ", s)
    if not s or len(s) > 60:
        raise ValueError("Datum fehlt")
    n = 0 if nights is None else max(0, min(3650, int(nights)))

    # ISO day or ISO range
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:" + _DASH + r"(\d{4})-(\d{1,2})-(\d{1,2}))?", s)
    if m:
        a = _day(m[3], m[2], m[1])
        b = _day(m[6], m[5], m[4]) if m[4] else a + timedelta(days=n)
        return _range(a, b)
    # 13.07.2009 – 25.07.2009 / 13.07.–25.07.2009 / 13.–25.07.2009 / 13.07.2009
    m = re.fullmatch(r"(\d{1,2})\.(?:(\d{1,2})\.(\d{2}|\d{4})?)?(?:" + _DASH + r"(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4}))?", s)
    if m and (m[3] or m[6]):
        y2, m2 = m[6] or m[3], m[5] or m[2]
        if m[4]:
            a = _day(m[1], m[2] or m2, m[3] or y2)
            b = _day(m[4], m2, y2)
            if b < a and not m[3] and m[2] and int(m[2]) > int(m2):  # 28.12.–03.01.2010: start in the year before
                a = a.replace(year=a.year - 1)
            return _range(a, b)
        a = _day(m[1], m[2], m[3])
        return _range(a, a + timedelta(days=n))
    # month: 07.2009 / 7/2009 / 2009-07 / Juli 2009 / Juli–August 2009
    m = re.fullmatch(r"(\d{1,2})\s*[./]\s*(\d{4})", s) or None
    if m:
        return _month(_year(m[2]), int(m[1]), int(m[1]), n)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", s)
    if m:
        return _month(_year(m[1]), int(m[2]), int(m[2]), n)
    m = re.fullmatch(r"([^\W\d_]+\.?)(?:" + _DASH + r"([^\W\d_]+\.?))?\s+(\d{4})", s)
    if m and _month_name(m[1]) and (not m[2] or _month_name(m[2])):
        a = _month_name(m[1])
        return _month(_year(m[3]), a, _month_name(m[2]) if m[2] else a, n)
    # year
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        y = _year(m[1])
        start, end = _centre(date(y, 1, 1), date(y, 12, 31), n)
        return _out(start, end, "year")
    raise ValueError("Datum als 13.07.2009, 13.–25.07.2009, Juli 2009 oder 2009")


def _range(a: date, b: date) -> dict:
    if b < a:
        raise ValueError("Ende liegt vor dem Anfang")
    if (b - a).days > 3650:
        raise ValueError("Reise länger als 10 Jahre")
    return _out(a, b, "day")


def _month(y: int, m1: int, m2: int, nights: int) -> dict:
    if not (1 <= m1 <= 12 and 1 <= m2 <= 12):
        raise ValueError("Monat 1–12")
    y2 = y if m2 >= m1 else y + 1
    first, last = date(y, m1, 1), date(y2, m2, calendar.monthrange(y2, m2)[1])
    start, end = _centre(first, last, nights)
    return _out(start, end, "month")


def label(start: str, end: str, prec: str) -> str:
    """How a trip's date reads in lists and exports: "13.–25.07.2009", "Juli 2009", "2009"."""
    a, b = date.fromisoformat(start), date.fromisoformat(end or start)
    if prec == "year":
        return str(a.year)
    if prec == "month":
        names = ("", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
                 "November", "Dezember")
        if (a.year, a.month) == (b.year, b.month):
            return f"{names[a.month]} {a.year}"
        if a.year == b.year:
            return f"{names[a.month]}–{names[b.month]} {a.year}"
        return f"{names[a.month]} {a.year}–{names[b.month]} {b.year}"
    if a == b:
        return f"{a:%d.%m.%Y}"
    if a.year == b.year and a.month == b.month:
        return f"{a:%d}.–{b:%d.%m.%Y}"
    if a.year == b.year:
        return f"{a:%d.%m.}–{b:%d.%m.%Y}"
    return f"{a:%d.%m.%Y}–{b:%d.%m.%Y}"
