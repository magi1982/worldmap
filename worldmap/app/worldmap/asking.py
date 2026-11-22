"""Smart questions – rule based, no AI needed.

* Similar trips (same area, same kind of day, same suggestion) are asked together:
  "9 day trips to Zurich on weekdays – who?" answers all of them at once.
* Every answer can become a *rule* (place + kind of day -> who / no trip), so the same
  question is never asked again and future trips there are filled in automatically.
* Besides the people and groups there are answers for "no trip (everyday life)",
  "merge with the trip before" and "ask me one by one".
"""
from __future__ import annotations

import json
from datetime import date

from . import questions as qn
from .geo import haversine_km

NO_TRIP = "Keine Reise (Alltag)"
MERGE = "Mit Reise davor zusammenlegen"
SPLIT = "Einzeln fragen"
GROUP_KM = 15.0
RULE_KM = 15.0


def day_kind(start: str, end: str) -> str:
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    wds = {date.fromordinal(o).weekday() for o in range(s.toordinal(), e.toordinal() + 1)}
    if wds <= {5, 6} or (wds <= {4, 5, 6} and len(wds) > 1):
        return "weekend"
    if wds <= {0, 1, 2, 3, 4}:
        return "weekday"
    return "all"


KIND_TEXT = {"weekend": "am Wochenende", "weekday": "unter der Woche", "all": ""}


def rule_for(rules: list[dict], lat: float | None, lon: float | None, start: str, end: str) -> dict | None:
    if lat is None or lon is None:
        return None
    kind = day_kind(start, end)
    best = None
    for r in rules:
        if r["days"] != "all" and r["days"] != kind:
            continue
        d = haversine_km(lat, lon, r["lat"], r["lon"])
        if d <= r["radius_km"] and (best is None or d < best[0]):
            best = (d, r)
    return best[1] if best else None


def who_options(settings) -> list[str]:
    return qn.options(settings.labels, settings.who_options)


def build(db, settings) -> int:
    """(Re)create all open questions. Returns the number of questions."""
    notified = {(k, v.replace(" ", "")) for k, v in db.clear_open_questions()}
    trips = db.trips()
    rank = qn.RANK.get(settings.ask_below, 2)
    todo = [t for t in trips if t["source"] == "auto" and not t["locked"] and t["status"] == "trip"
            and qn.RANK.get(t["confidence"], 0) < rank and t["lat"] is not None]
    groups: list[list[dict]] = []
    for t in sorted(todo, key=lambda t: t["start_date"]):
        kind = day_kind(t["start_date"], t["end_date"])
        g = next((g for g in groups if day_kind(g[0]["start_date"], g[0]["end_date"]) == kind
                  and (g[0]["who"] or "") == (t["who"] or "") and (g[0]["nights"] > 0) == (t["nights"] > 0)
                  and haversine_km(g[0]["lat"], g[0]["lon"], t["lat"], t["lon"]) <= GROUP_KM), None)
        if g is None:
            groups.append([t])
        else:
            g.append(t)
    base = who_options(settings)
    n = 0
    by_start = sorted(trips, key=lambda t: t["end_date"])
    for g in groups:
        first = g[0]
        if len(g) >= 2:
            ids = [t["id"] for t in g]
            opts = [*base, NO_TRIP, SPLIT]
            sug = first["who"] if first["who"] in base else None
            key = ("group", str(ids).replace(" ", ""))
            db.add_question(first["id"], "group", group_text(g, sug), opts, sug, ids, notified=1 if key in notified else 0)
        else:
            opts = [*base, NO_TRIP]
            prev = [t for t in by_start if t["id"] != first["id"] and t["end_date"] < first["start_date"]
                    and (date.fromisoformat(first["start_date"]) - date.fromisoformat(t["end_date"])).days <= 2]
            if prev:
                opts.append(MERGE)
            sug = first["who"] if first["who"] in base else None
            db.add_question(first["id"], "who", single_text(first, sug), opts, sug,
                            notified=1 if ("who", str(first["id"])) in notified else 0)
        n += 1
    return n


def single_text(t: dict, sug: str | None) -> str:
    n = t["nights"] or 0
    parts = [qn.fmt_range(t["start_date"], t["end_date"]), "Tagesausflug" if n == 0 else f"{n} Nacht" if n == 1 else f"{n} Nächte"]
    place = t["destination"] or "unbekannter Ort"
    if t["country"]:
        place += f", {t['country']}"
    if t["max_km"]:
        place += f" ({round(t['max_km'])} km)"
    parts.append(place)
    q = " · ".join(parts) + ". Wer war dabei?"
    if sug:
        q += f" Vorschlag: {sug}" + (f" ({t['reason']})." if t["reason"] else ".")
    return q


def group_text(g: list[dict], sug: str | None) -> str:
    t = g[0]
    kind = KIND_TEXT[day_kind(t["start_date"], t["end_date"])]
    years = sorted({x["start_date"][:4] for x in g})
    yr = years[0] if len(years) == 1 else f"{years[0]}–{years[-1]}"
    what = "Tagesausflüge" if all((x["nights"] or 0) == 0 for x in g) else "Reisen"
    dates = ", ".join(qn.fmt_range(x["start_date"], x["end_date"]) for x in g[:3]) + (" …" if len(g) > 3 else "")
    head = f"{len(g)} {what} nach {t['destination'] or 'demselben Ort'}"
    if kind:
        head += f" {kind}"
    q = f"{head} ({yr}, z. B. {dates}). Eine Antwort gilt für alle."
    if sug:
        q += f" Vorschlag: {sug}."
    return q


def answer(db, qid: int, ans: str, remember: bool = True) -> dict:
    """Apply an answer. Returns what happened (for the UI)."""
    rows = db.query("SELECT * FROM questions WHERE id = ?", (qid,))
    if not rows:
        raise LookupError("question not found")
    q = rows[0]
    options = json.loads(q["options"])
    if ans not in options:
        raise ValueError("answer is not one of the options")
    ids = json.loads(q["trip_ids"]) if q["trip_ids"] else [q["trip_id"]]
    trips = [t for t in (db.trip(i) for i in ids) if t]
    out = {"trips": len(trips), "rule": None}
    with db.tx() as c:
        c.execute("UPDATE questions SET answer = ?, answered_at = strftime('%s','now') WHERE id = ?", (ans, qid))
    if ans == SPLIT:
        for t in trips:
            db.add_question(t["id"], "who", single_text(t, q["suggestion"]), [o for o in options if o != SPLIT],
                            q["suggestion"])
        return {**out, "split": True}
    if ans == MERGE and trips:
        t = trips[0]
        prev = db.query("SELECT * FROM trips WHERE id != ? AND status = 'trip' AND end_date < ? ORDER BY end_date DESC LIMIT 1",
                        (t["id"], t["start_date"]))
        if prev:
            p = prev[0]
            nights = (date.fromisoformat(max(p["end_date"], t["end_date"])) - date.fromisoformat(p["start_date"])).days
            db.upsert_trip({"end_date": max(p["end_date"], t["end_date"]), "nights": nights, "locked": 1}, p["id"])
            db.delete_trip(t["id"])
            return {**out, "merged_into": p["id"]}
    for t in trips:
        if ans == NO_TRIP:
            db.upsert_trip({"status": "ignored", "locked": 1, "confidence": "bestätigt"}, t["id"])
        else:
            db.upsert_trip({"who": ans, "confidence": "bestätigt", "locked": 1, "status": "trip"}, t["id"])
    if remember and trips and ans not in (MERGE, SPLIT):
        lat = sum(t["lat"] for t in trips) / len(trips)
        lon = sum(t["lon"] for t in trips) / len(trips)
        kind = day_kind(trips[0]["start_date"], trips[0]["end_date"])
        action = "ignore" if ans == NO_TRIP else "who"
        label = f"{trips[0]['destination'] or 'Ort'} {KIND_TEXT[kind]}".strip()
        out["rule"] = db.add_rule(round(lat, 4), round(lon, 4), RULE_KM, kind, action, "" if action == "ignore" else ans, label)
    return out
