import base64
import csv
import io
import json
import sqlite3
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from conftest import HOME
from worldmap import asking, owntracks
from worldmap.db import Database
from worldmap.importers import detect_and_parse
from worldmap.server import upsert_trips

TZ = ZoneInfo("Europe/Zurich")


def sheet_csv(rows):
    b = io.StringIO()
    csv.writer(b).writerows([["Von", "Bis", "Hauptziel", "Land", "Wer", "Sicherheit", "Nächte", "Max. Entfernung (km)",
                              "Unterwegs mit", "Notiz", "Quelle"], *rows])
    return b.getvalue().encode()


def test_trip_list_import_finds_places():
    data = sheet_csv([["2009-10-01", "2009-10-08", "Korsika", "Frankreich", "Paar", "bestätigt", "", "625", "Auto · Schiff", "", ""],
                      ["03.06.2017", "12.06.2017", "Mallorca (Porto Cristo)", "Spanien", "Familie", "", "9", "1'028", "Flug", "", ""],
                      ["2016-07-13", "", "Sampletown that does not exist", "", "", "", "", "", "", "", ""]])
    r = detect_and_parse(data, "Reisen.csv")
    assert r.format == "trips-csv" and len(r.trips) == 3
    kors, mall, unknown = r.trips
    assert (kors["lat"], kors["radius_km"], kors["who"], kors["nights"]) == (42.15, 60, "Paar", 7)
    assert 39 < mall["lat"] < 40 and mall["max_km"] == 1028 and mall["confidence"] == "bestätigt"
    assert unknown["end_date"] == "2016-07-13" and unknown.get("lat") is None
    assert r.warnings  # one destination not found


def test_upsert_detects_duplicates(db):
    t = {"start_date": "2009-10-01", "end_date": "2009-10-08", "destination": "Korsika", "lat": 42.15, "lon": 9.1}
    assert upsert_trips(db, [t, dict(t)])["duplicates_in_file"] == 1
    res = upsert_trips(db, [{**t, "destination": "Corse (Corte)", "lat": 42.30, "lon": 9.15, "who": "Paar"}])
    assert res["trips_updated"] == 1 and len(db.trips()) == 1  # same dates, 17 km away -> same trip
    assert db.trips()[0]["who"] == "Paar"
    upsert_trips(db, [{**t, "who": ""}])
    assert db.trips()[0]["who"] == "Paar"  # an empty cell never blanks out data


def _day_trips(engine, n, dest=(47.37, 8.54), person="Alex", weekend=False):
    rows = []
    d = datetime(2025, 3, 3, tzinfo=TZ)
    made = 0
    while made < n:
        if (d.weekday() >= 5) == weekend:
            for h, p in ((8, HOME), (12, dest), (18, HOME)):
                rows.append((int(d.replace(hour=h).timestamp()), p[0], p[1], person, "t", None, None))
            made += 1
        d += timedelta(days=7 if made else 1) if False else timedelta(days=1)
    engine.import_points(rows)


def test_similar_trips_are_asked_once_and_rules_are_learned(engine):
    engine.s.routine_days = 0
    _day_trips(engine, 6)
    engine.rebuild()
    qs = engine.db.open_questions()
    group = [q for q in qs if q["kind"] == "group"]
    assert len(group) == 1 and len(group[0]["trip_ids"]) == 6
    assert asking.NO_TRIP in group[0]["options"] and asking.SPLIT in group[0]["options"]
    res = asking.answer(engine.db, group[0]["id"], asking.NO_TRIP, remember=True)
    assert res["trips"] == 6 and res["rule"]
    assert engine.db.trips() == [] and len(engine.db.trips(include_ignored=True)) == 6
    # new trips to the same place are handled by the rule – no new question
    rows = []
    d = datetime(2025, 9, 1, 8, tzinfo=TZ)
    rows += [(int(d.timestamp()), *HOME, "Alex", "t", None, None), (int(d.replace(hour=12).timestamp()), 47.37, 8.54, "Alex", "t", None, None),
             (int(d.replace(hour=18).timestamp()), *HOME, "Alex", "t", None, None)]
    engine.import_points(rows)
    engine.rebuild()
    assert engine.db.open_questions() == []
    assert engine.db.rules()[0]["hits"] >= 1


def test_split_and_merge(engine):
    engine.s.routine_days = 0
    _day_trips(engine, 3, weekend=True, dest=(46.5, 7.6))
    engine.rebuild()
    g = next(q for q in engine.db.open_questions() if q["kind"] == "group")
    asking.answer(engine.db, g["id"], asking.SPLIT)
    singles = engine.db.open_questions()
    assert len(singles) == 3 and all(q["kind"] == "who" for q in singles)
    with pytest.raises(ValueError):
        asking.answer(engine.db, singles[0]["id"], "nonsense")
    asking.answer(engine.db, singles[0]["id"], "Alex")
    assert any(t["who"] == "Alex" and t["confidence"] == "bestätigt" for t in engine.db.trips())


def test_old_database_is_migrated(tmp_path):
    p = tmp_path / "old.db"
    c = sqlite3.connect(p)
    c.executescript("CREATE TABLE trips (id INTEGER PRIMARY KEY, start_date TEXT NOT NULL, end_date TEXT NOT NULL,"
                    " destination TEXT NOT NULL DEFAULT '', country TEXT NOT NULL DEFAULT '', who TEXT NOT NULL DEFAULT '',"
                    " confidence TEXT NOT NULL DEFAULT 'tief', nights INTEGER NOT NULL DEFAULT 0, max_km REAL, lat REAL, lon REAL,"
                    " transport TEXT NOT NULL DEFAULT '', reason TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',"
                    " source TEXT NOT NULL DEFAULT '', locked INTEGER NOT NULL DEFAULT 0, updated_at INTEGER NOT NULL DEFAULT 0);"
                    "INSERT INTO trips (start_date, end_date, destination) VALUES ('2020-01-01', '2020-01-02', 'Old');")
    c.close()
    db = Database(str(p))
    t = db.trips()[0]
    assert t["status"] == "trip" and t["approx"] == 0 and "radius_km" in t
    db.close()


def test_owntracks_parse_and_auth(engine):
    body = json.dumps([{"_type": "location", "lat": 46.1, "lon": 7.2, "tst": 1751364000, "acc": 12, "m": "a"},
                       {"_type": "transition", "lat": 1, "lon": 1, "tst": 1}, {"_type": "location", "lat": 999, "lon": 1, "tst": 1751364000}])
    rows = owntracks.parse(body.encode(), "Alex")
    assert rows == [(1751364000, 46.1, 7.2, "Alex", "owntracks", 12.0, "IN_PASSENGER_VEHICLE")]
    engine.s.owntracks = [{"user": "alex", "password": "secret-123", "label": "Alex"}]
    srv = owntracks.serve(engine, "127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/pub"

    def post(user, pw, data=body.encode()):
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode())
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    try:
        assert post("alex", "wrong-pass")[0] == 401
        assert post("bob", "secret-123")[0] == 401
        st, raw = post("alex", "secret-123")
        assert st == 200 and raw == b"[]"
        assert engine.db.scalar("SELECT COUNT(*) FROM points WHERE source = 'owntracks'") == 1
        assert post("alex", "secret-123", b"{broken")[0] == 400
    finally:
        srv.shutdown()


def test_trip_list_with_coordinates_is_still_a_trip_list():
    from worldmap import importers
    csv = ("Von;Bis;Ziel;Land;Wer;Verkehrsmittel;Breitengrad;Längengrad\n"
           "2019-08-01;2019-08-10;Sample Bay;Frankreich;Paar;Auto · Schiff;42.15;9.10\n"
           "2020-02-01;2020-02-02;Somewhere;Schweiz;Alex;Zug;;\n").encode("utf-8-sig")
    r = importers.detect_and_parse(csv, "list.csv")
    assert r.format == "trips-csv" and len(r.trips) == 2
    assert r.trips[0]["lat"] == 42.15 and r.trips[0]["who"] == "Paar"
