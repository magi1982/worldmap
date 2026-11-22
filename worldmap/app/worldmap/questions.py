"""Suggest who was on a trip and phrase a short question with all the context."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
RANK = {"tief": 0, "mittel": 1, "hoch": 2, "bestätigt": 3}


@dataclass
class Suggestion:
    who: str
    confidence: str
    reason: str


def parse_ranges(ranges: list[str]) -> list[tuple[str, str]]:
    """'2026-07-04..2026-08-09' -> ('2026-07-04', '2026-08-09'); invalid entries are ignored."""
    out = []
    for r in ranges or []:
        parts = str(r).split("..")
        if len(parts) != 2:
            continue
        try:
            a, b = date.fromisoformat(parts[0].strip()), date.fromisoformat(parts[1].strip())
        except ValueError:
            continue
        out.append((min(a, b).isoformat(), max(a, b).isoformat()))
    return out


def in_holidays(start: str, end: str, holidays: list[tuple[str, str]]) -> bool:
    return any(not (end < a or start > b) for a, b in holidays)


def is_weekend_trip(start: str, end: str) -> bool:
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    return (e - s).days <= 3 and all((date.fromordinal(o).weekday() >= 4) for o in range(s.toordinal(), e.toordinal() + 1))


def options(persons: list[str], extra: list[str]) -> list[str]:
    seen, out = set(), []
    for o in [*persons, *extra]:
        if o and o not in seen:
            seen.add(o)
            out.append(o)
    return out


def suggest(present: set[str], tracked: set[str], at_home: set[str], overlap: float,
            holidays: bool, weekend: bool, hints: set[str], extra: list[str],
            keyword_map: dict[str, str]) -> Suggestion:
    text = " ".join(sorted(hints)).lower()
    for kw, who in (keyword_map or {}).items():
        if kw and kw.lower() in text:
            return Suggestion(who, "hoch", f"Hinweis «{kw}» im Ordner/Foto")
    group_family = next((o for o in extra if o.lower() in ("familie", "family")), None)
    group_couple = next((o for o in extra if o.lower() in ("paar", "couple")), None)
    if len(tracked) >= 2 and present >= tracked and overlap >= 0.6:
        if holidays and group_family:
            return Suggestion(group_family, "mittel", "alle gleichzeitig unterwegs, Schulferien")
        if group_couple and not holidays:
            return Suggestion(group_couple, "tief" if weekend else "mittel",
                              "alle gleichzeitig unterwegs" + (", Wochenende" if weekend else ""))
        if group_family:
            return Suggestion(group_family, "mittel", "alle gleichzeitig unterwegs")
    if len(present) == 1:
        who = next(iter(present))
        others = tracked - present
        if others and others <= at_home:
            return Suggestion(who, "hoch", "die anderen waren zu Hause")
        return Suggestion(who, "tief", "von den anderen fehlen Daten")
    if present:
        return Suggestion(" + ".join(sorted(present)), "tief", "teilweise gemeinsam unterwegs")
    return Suggestion("", "tief", "nur Fotos/Import ohne Person")


def fmt_range(start: str, end: str) -> str:
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    if s == e:
        return f"{WEEKDAYS[s.weekday()]} {s:%d.%m.%Y}"
    return f"{WEEKDAYS[s.weekday()]} {s:%d.%m.}–{WEEKDAYS[e.weekday()]} {e:%d.%m.%Y}"


def question_text(trip: dict, sug: Suggestion, holidays: bool, present: set[str]) -> str:
    n = trip.get("nights") or 0
    parts = [fmt_range(trip["start_date"], trip["end_date"]),
             "Tagesausflug" if n == 0 else f"{n} Nacht" if n == 1 else f"{n} Nächte"]
    place = trip.get("destination") or "unbekannter Ort"
    if trip.get("country"):
        place += f", {trip['country']}"
    if trip.get("max_km"):
        place += f" ({round(trip['max_km'])} km)"
    parts.append(place)
    if holidays:
        parts.append("Schulferien")
    if present:
        parts.append("unterwegs: " + ", ".join(sorted(present)))
    q = " · ".join(parts) + ". Wer war dabei?"
    if sug.who:
        q += f" Vorschlag: {sug.who} ({sug.reason})."
    return q


def needs_question(sug: Suggestion, ask_below: str) -> bool:
    return RANK.get(sug.confidence, 0) < RANK.get(ask_below, 2)
