from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from conftest import HOME
from worldmap import questions as Q  # noqa: N812
from worldmap import trips as T  # noqa: N812

TZ = "Europe/Zurich"


def ts(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(TZ)).timestamp())


def P(when, lat, lon, person, hint=None):
    return {"ts": ts(when), "lat": lat, "lon": lon, "person": person, "hint": hint}


def holiday_points(person, start_day=10, days=3, lat=46.0, lon=7.0):
    pts = [P(f"2025-07-{start_day - 1:02d}T20:00:00", *HOME, person)]
    for d in range(start_day, start_day + days):
        pts += [P(f"2025-07-{d:02d}T10:00:00", lat, lon, person), P(f"2025-07-{d:02d}T22:00:00", lat, lon, person)]
    pts.append(P(f"2025-07-{start_day + days:02d}T18:00:00", *HOME, person))
    return pts


def test_days_away_and_grouping_single_person():
    days = T.days_away(holiday_points("Alex"), HOME, 30, TZ)
    assert [d.day for d in days] == ["2025-07-10", "2025-07-11", "2025-07-12"]
    trips = T.group_trips(days)
    assert len(trips) == 1
    t = trips[0]
    assert (t.start, t.end, t.nights, t.persons) == ("2025-07-10", "2025-07-12", 2, {"Alex"})
    assert t.max_km > 100


def test_overlapping_trips_of_two_people_are_merged():
    days = T.days_away(holiday_points("Alex") + holiday_points("Sam", start_day=11, days=2), HOME, 30, TZ)
    trips = T.group_trips(days)
    assert len(trips) == 1
    assert trips[0].persons == {"Alex", "Sam"}
    assert 0 < T.overlap_share(trips[0], "Alex", "Sam") < 1


def test_separate_trips_stay_separate_and_short_hops_ignored():
    pts = holiday_points("Alex") + holiday_points("Alex", start_day=20, days=1) + [P("2025-07-25T12:00:00", 47.05, 8.05, "Alex")]
    trips = T.group_trips(T.days_away(pts, HOME, 30, TZ))
    assert [t.start for t in trips] == ["2025-07-10", "2025-07-20"]


def test_suggest_rules():
    tracked = {"Alex", "Sam"}
    extra = ["Paar", "Familie"]
    s = Q.suggest({"Alex", "Sam"}, tracked, set(), 1.0, True, False, set(), extra, {})
    assert (s.who, s.confidence) == ("Familie", "mittel")
    s = Q.suggest({"Alex", "Sam"}, tracked, set(), 1.0, False, True, set(), extra, {})
    assert (s.who, s.confidence) == ("Paar", "tief")
    s = Q.suggest({"Alex"}, tracked, {"Sam"}, 0, False, False, set(), extra, {})
    assert (s.who, s.confidence) == ("Alex", "hoch")
    s = Q.suggest({"Alex"}, tracked, set(), 0, False, False, set(), extra, {})
    assert s.confidence == "tief"
    s = Q.suggest(set(), tracked, set(), 0, False, False, {"2019_Dad weekend"}, extra, {"Dad": "Dad + kids"})
    assert (s.who, s.confidence) == ("Dad + kids", "hoch")


def test_question_text_and_helpers():
    trip = {"start_date": "2025-07-11", "end_date": "2025-07-13", "nights": 2, "destination": "Sampletown",
            "country": "Schweiz", "max_km": 123.4}
    sug = Q.Suggestion("Paar", "tief", "alle gleichzeitig unterwegs")
    text = Q.question_text(trip, sug, True, {"Alex", "Sam"})
    assert text.startswith("Fr 11.07.–So 13.07.2025 · 2 Nächte · Sampletown, Schweiz (123 km)")
    assert "Schulferien" in text and "Vorschlag: Paar" in text
    assert Q.is_weekend_trip("2025-07-11", "2025-07-13")
    assert not Q.is_weekend_trip("2025-07-09", "2025-07-13")
    assert Q.parse_ranges(["2025-08-10..2025-07-05", "junk"]) == [("2025-07-05", "2025-08-10")]
    assert Q.needs_question(sug, "hoch") and not Q.needs_question(Q.Suggestion("x", "hoch", ""), "hoch")
    assert Q.options(["Alex", "Sam"], ["Paar", "Alex"]) == ["Alex", "Sam", "Paar"]


def test_engine_rebuild_creates_trip_and_question(engine):
    rows = [(p["ts"], p["lat"], p["lon"], p["person"], "test", None, None)
            for p in holiday_points("Alex") + holiday_points("Sam")]
    engine.import_points(rows)
    res = engine.rebuild()
    assert res["trips_created"] == 1
    trip = engine.db.trips()[0]
    assert trip["who"] == "Familie"  # in the configured school holidays
    assert trip["destination"] and trip["country"] == "Schweiz"
    qs = engine.db.open_questions()
    assert len(qs) == 1 and "Familie" in qs[0]["options"]
    engine.db.answer_question(qs[0]["id"], "Paar")
    t = engine.db.trip(trip["id"])
    assert (t["who"], t["confidence"], t["locked"]) == ("Paar", "bestätigt", 1)
    # locked trips are never overwritten by a new detection
    engine.rebuild()
    assert engine.db.trip(trip["id"])["who"] == "Paar"
    with pytest.raises(ValueError):
        engine.db.answer_question(qs[0]["id"], "Not an option")


def test_tracks_and_stats(engine):
    pts = holiday_points("Alex") + [P("2025-07-10T08:00:00", *HOME, "Alex")]
    rows = [(p["ts"], p["lat"], p["lon"], p["person"], "test", None, None) for p in pts]
    engine.import_points(rows)
    tr = engine.tracks(0.001)
    assert any(k.startswith("Alex|2025") for k in tr["lines"])
    st = engine.stats()
    assert st["points"] == len(rows) and st["km_total"] > 0


def test_notify_open_sends_once(engine):
    sent = []

    class HA:
        available = True

        def notify(self, service, title, msg, url=None):
            sent.append((service, title, url))
            return True

        def persistent(self, *a, **k):
            sent.append(("persistent",))

        def set_sensor(self, *a, **k):
            pass

        def state(self, *_):
            return None

    engine.ha = HA()
    engine.s.notify_mode = "instant"
    engine.s.notify_service = "notify.mobile_app_test"
    rows = [(p["ts"], p["lat"], p["lon"], p["person"], "test", None, None) for p in holiday_points("Alex")]
    engine.import_points(rows)
    engine.rebuild()
    assert engine.notify_open() == 1
    assert sent[0][0] == "notify.mobile_app_test" and sent[0][2] == engine.ingress_url
    assert engine.notify_open() == 0  # already notified
