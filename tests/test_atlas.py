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
    assert core["flights"] and len(core["flights"][0]) == 5 and 0 <= core["flights"][0][3] <= 1
    assert {f[4] for f in core["flights"]} == {0, 1}  # person index per flight
    assert len(core["trackP"]) == len(core["trackT"]) and set(core["trackP"]) <= {-1, 0, 1}
    assert len(core["dayP"]) == len(core["days"]) and any(m == 3 for m in core["dayP"])
    assert all(len(r) == 8 for r in core["days"])
    assert core["groups"] and core["groups"][0][1]


def test_tracks_and_cache(filled, tmp_path):
    at = A.Atlas(filled, str(tmp_path))
    tracks = load(at, "tracks")
    times = load(at, "core")["trackT"]
    assert len(times) == len(tracks) and all(0 <= a <= b <= 1 for a, b in times)
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


def test_regions_worldwide(engine, tmp_path):
    at = A.Atlas(engine, str(tmp_path))
    names = {r[0]: (r[1], r[2]) for r in json.loads((A.STATIC / "regions.json").read_text(encoding="utf-8"))["regions"]}
    assert names[at.region_at(47.0505, 8.3093)] == ("Kanton Luzern", "CHE")
    assert names[at.region_at(48.137, 11.575)][1] == "DEU"       # Bavaria
    assert names[at.region_at(34.05, -118.25)][1] == "USA"       # California
    assert at.region_at(0.0, -30.0) is None                      # Atlantic
    engine.import_points([(ts("2025-01-05T12:00:00"), 47.0505, 8.3093, "Alex", "t", None, None)])
    reg = load(at, "reg")
    assert any(r[2] == "2025-01-05" and r[1] == 0 for r in reg)


def test_groups_settings():
    from worldmap.settings import from_dict
    s = from_dict({"persons": [{"label": "Alex", "color": "#FF00AA"}, {"label": "Sam"}],
                   "groups": [{"name": "Paar", "members": "Alex, Sam, Nobody", "extra": 2, "color": "#00FF00"},
                              {"name": "bad", "color": "red"}]})
    assert s.groups[0] == {"name": "Paar", "members": ["Alex", "Sam"], "extra": 2, "color": "#00FF00"}
    assert s.groups[1]["color"] == "" and s.who_options == ["Paar", "bad"]
    assert s.colors() == {"Alex": "#FF00AA", "Paar": "#00FF00"}
    old = from_dict({"who_options": ["Familie", "Alex"], "persons": [{"label": "Alex"}], "routing": "osrm"})
    assert old.routing == "tiles" and [g["name"] for g in old.groups] == ["Familie"]
    assert old.groups == [{"name": "Familie", "members": [], "extra": 0, "color": ""}]


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


def test_gps_jumps_are_not_flights():
    a = {"ts": 0, "lat": 47.0, "lon": 8.0, "hint": None}
    assert A.mode_of_pair(a, {"ts": 20, "lat": 47.02, "lon": 8.0, "hint": None}, 2.2) == "jump"
    assert A.mode_of_pair(a, {"ts": 3600, "lat": 48.0, "lon": 8.0, "hint": None}, 111) == "road"


def test_estimate_km_without_gps():
    from worldmap.modes import estimate_km
    car = estimate_km(400, ["road"], 6)
    assert 1000 < car["road"] < 1300          # 2 x 400 x 1.25 + a week of local driving
    fly = estimate_km(2000, ["fly", "road"], 13)
    assert fly["fly"] == 4000 and 100 < fly["road"] < 500
    assert estimate_km(80, ["fly"], 0) == {"road": 235}  # too short to fly: by car
    ship = estimate_km(500, ["road", "ferry"], 7)
    assert ship["ferry"] == 250 and ship["road"] > 1250
    assert estimate_km(0, [], 0) == {"road": 35}


def test_regions_from_trips_without_gps(engine, tmp_path):
    at = A.Atlas(engine, str(tmp_path))
    engine.db.upsert_trip({"start_date": "2012-06-20", "end_date": "2012-06-27", "destination": "Sample Island", "who": "Alex",
                           "confidence": "bestätigt", "nights": 7, "lat": 35.24, "lon": 24.90, "radius_km": 40, "approx": 1,
                           "transport": "Flug", "source": "manual", "locked": 1})
    engine.touch()
    reg = load(at, "reg")
    crete = at.region_at(35.24, 24.90)
    assert any(r[0] == crete and r[1] == 0 and r[2] == "2012-06-20" and r[3] == 8 and r[4] == 1 for r in reg)
