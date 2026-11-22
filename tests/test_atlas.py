import gzip
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from conftest import HOME
from worldmap import atlas as A  # noqa: N812
from worldmap import trips as T  # noqa: N812

TZ = ZoneInfo("Europe/Zurich")


def ts(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp())


def line(a, b, t0, minutes, n, person, hint=None):
    return [(t0 + int(minutes * 60 * i / n), a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, person, "t", None, hint)
            for i in range(n + 1)]


@pytest.fixture
def filled(engine):
    rows = []
    # a train day trip to a (made-up) place 60 km away and back
    rows += line(HOME, (46.6, 7.7), ts("2025-03-01T08:00:00"), 60, 12, "Alex", "IN_TRAIN")
    rows += line((46.6, 7.7), HOME, ts("2025-03-01T17:00:00"), 60, 12, "Alex", "IN_TRAIN")
    # a flight holiday of both
    for p in ("Alex", "Sam"):
        rows.append((ts("2025-07-10T08:00:00"), *HOME, p, "t", None, None))
        rows.append((ts("2025-07-10T11:00:00"), 41.8, 12.25, p, "t", None, None))   # ~720 km in 3 h -> flight
        for d in range(10, 15):
            rows.append((ts(f"2025-07-{d}T18:00:00"), 41.9, 12.5, p, "t", None, None))
        rows.append((ts("2025-07-15T09:00:00"), 41.8, 12.25, p, "t", None, None))
        rows.append((ts("2025-07-15T12:00:00"), *HOME, p, "t", None, None))
    engine.import_points(rows)
    engine.db.upsert_trip({"start_date": "2010-05-01", "end_date": "2010-05-08", "destination": "Sample Island",
                           "country": "Frankreich", "who": "Paar", "lat": 42.15, "lon": 9.1, "radius_km": 60,
                           "transport": "Auto · Schiff", "source": "manual", "locked": 1, "approx": 1, "nights": 7})
    engine.rebuild()
    return engine


def load(atlas, part):
    return json.loads(gzip.decompress(atlas.get(part)))


def test_core_shape(filled, tmp_path):
    at = A.Atlas(filled, str(tmp_path))
    core = load(at, "core")
    assert core["home"] == [47.0, 8.0]
    assert core["who"][:2] == ["Alex", "Sam"] and core["who"][-1] == "Alltag"
    assert {t["name"] for t in core["trips"]} >= {"Sample Island"}
    manual = next(t for t in core["trips"] if t["name"] == "Sample Island")
    assert manual["m"] == ["road", "ferry"] and manual["k"]["road"] > 0 and manual["approx"] == 1
    assert core["est"][0][3] == 60
    holiday = next(t for t in core["trips"] if t["a"] == "2025-07-10")
    assert "fly" in holiday["m"] and holiday["fl"] and holiday["g"]
    day_trip = next(t for t in core["trips"] if t["a"] == "2025-03-01")
    assert day_trip["m"][0] == "rail"
    assert core["flights"] and len(core["flights"][0]) == 3
    assert all(len(r) == 8 for r in core["days"])
    assert core["groups"] and core["groups"][0][1]


def test_tracks_and_cache(filled, tmp_path):
    at = A.Atlas(filled, str(tmp_path))
    tracks = load(at, "tracks")
    assert tracks and all(len(t) >= 6 and len(t) % 2 == 0 for t in tracks)
    assert {t[1] for t in tracks} >= {1}  # rail
    assert list(tmp_path.glob("atlas-*.json.gz"))
    fp = at.fingerprint()
    at2 = A.Atlas(filled, str(tmp_path))
    assert at2.fingerprint() == fp and load(at2, "core")["trips"]
    filled.db.upsert_trip({"start_date": "2011-01-01", "end_date": "2011-01-02", "destination": "X"})
    assert at.fingerprint() != fp
    with pytest.raises(KeyError):
        at.get("../etc")


def test_swiss_municipalities(engine, tmp_path):
    at = A.Atlas(engine, str(tmp_path))
    assert at._mun_at(47.0505, 8.3093)[1] == "Luzern"
    assert at._mun_at(48.86, 2.35) is None
    engine.import_points([(ts("2025-01-05T12:00:00"), 47.0505, 8.3093, "Alex", "t", None, None)])
    gem = load(at, "gem")
    assert any(g[1] == "2025-01-05" for g in gem)


def test_mode_detection():
    assert A.mode_of_text("IN_TRAIN") == "rail"
    assert A.mode_of_text("in passenger vehicle") == "road"
    assert A.mode_of_text("WALKING") == "foot"
    assert A.mode_of_text(None) is None
    assert A.modes_of_transport("Auto · Schiff") == ["road", "ferry"]
    a = {"ts": 0, "lat": 47.0, "lon": 8.0, "hint": None}
    assert A.mode_of_pair(a, {"ts": 3600, "lat": 47.02, "lon": 8.0, "hint": None}, 2.2) == "foot"
    assert A.mode_of_pair(a, {"ts": 3600, "lat": 41.9, "lon": 12.5, "hint": None}, 700) == "fly"
    assert A.mode_of_pair(a, {"ts": 3600, "lat": 46.5, "lon": 8.0, "hint": "IN_TRAIN"}, 55) == "rail"


def test_routine_places_are_not_trips(engine):
    work = (47.37, 8.54)  # ~60 km from the test home
    rows = []
    start = datetime(2025, 1, 6, tzinfo=TZ)
    for i in range(30):
        d = start + timedelta(days=i)
        rows += line(HOME, work, int(d.replace(hour=7).timestamp()), 50, 5, "Alex")
        rows += line(work, HOME, int(d.replace(hour=17).timestamp()), 50, 5, "Alex")
    engine.import_points(rows)
    assert engine.rebuild()["trips_created"] == 0
    pts = engine.db.points()
    assert T.routine_cells(pts, "Europe/Zurich", 20)
    engine.s.routine_days = 0
    assert engine.rebuild()["trips_created"] > 20
