"""Stops can be airports: one search for places and airports, and old airport fields move into the stops."""

import json

import pytest

from test_atlas import load  # noqa: F401 – shared helper
from worldmap import airports
from worldmap import atlas as A  # noqa: N812
from worldmap.db import Database
from worldmap.server import validate_legs


def test_airports_are_found_without_knowing_the_codes():
    codes = lambda q: [x["code"] for x in airports.search(q)]  # noqa: E731
    assert codes("Dubai")[:2] == ["DXB", "DWC"]           # the town: its airports, the big one first
    assert codes("dxb") == ["DXB"]                        # the code itself
    assert "MXP" in codes("Malpensa")                     # a part of the airport name
    assert {"MXP", "LIN"} <= set(codes("Mailand"))        # the German name of the town
    assert {"TFS", "TFN"} <= set(codes("Teneriffa"))      # an island: the airports on it
    assert airports.search("x") == []


def test_an_airport_stop_is_stored_with_the_airport_position():
    legs = json.loads(validate_legs([{"ap": "dxb"}, {"name": "Strandhotel", "lat": 25.08, "lon": 55.14}]))
    assert legs[0]["ap"] == "DXB" and legs[0]["name"].startswith("Dubai") and legs[0]["transport"] == "Flug"
    assert abs(legs[0]["lat"] - 25.25) < .01                     # the airport, whatever the browser sent
    assert "ap" not in legs[1] and legs[1]["transport"] == "Auto"
    with pytest.raises(ValueError):
        validate_legs([{"ap": "QQQ"}])                           # unknown code
    with pytest.raises(ValueError):
        validate_legs([{"ap": "<script>"}])


def test_the_plane_lands_at_the_airport_stop(engine, tmp_path):
    engine.db.upsert_trip({"start_date": "2016-02-06", "end_date": "2016-02-14", "destination": "Wüstenhotel",
                           "who": "Alex", "confidence": "bestätigt", "nights": 8, "transport": "Flug · Auto",
                           "source": "manual", "locked": 1, "ap_from": "BSL",
                           "legs": validate_legs([{"ap": "DWC"}, {"name": "Wüstenhotel", "lat": 24.80,
                                                                 "lon": 55.40, "transport": "Auto"}])})
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert t["lg"][0][0] == "fly" and t["lg"][0][2] == ["BSL", "DWC"]   # from the chosen departure to the stop
    assert t["lg"][1][0] == "road"                                      # then by car to the hotel
    assert t["st"][0][3] == "DWC" and len(t["st"][1]) == 3


def test_a_single_airport_stop_is_enough(engine, tmp_path):
    engine.db.upsert_trip({"start_date": "2016-03-05", "end_date": "2016-03-09", "destination": "Dubai",
                           "who": "Sam", "confidence": "bestätigt", "nights": 4, "transport": "Flug",
                           "source": "manual", "locked": 1, "legs": validate_legs([{"ap": "DXB"}])})
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert t["lg"][0][2][1] == "DXB" and t["fl"]


def _old_db(path, trips):
    db = Database(str(path))
    for t in trips:
        db.upsert_trip(t)
    db._conn.execute("DELETE FROM meta WHERE key='airport_stations'")   # as before the update
    db.close()
    return Database(str(path))                                           # opening it runs the migration once


def test_old_airport_fields_become_stops(tmp_path):
    base = {"who": "Alex", "confidence": "hoch", "nights": 7, "source": "manual"}
    db = _old_db(tmp_path / "w.db", [
        {**base, "start_date": "2018-06-01", "end_date": "2018-06-08", "destination": "Inselhotel", "country": "",
         "lat": 35.30, "lon": 25.40, "transport": "Flug", "ap_from": "ZRH", "ap_to": "HER"},
        {**base, "start_date": "2018-07-01", "end_date": "2018-07-08", "destination": "Hafen", "transport": "Flug",
         "ap_to": "TFS", "legs": validate_legs([{"name": "Teneriffa", "lat": 28.29, "lon": -16.62, "transport": "Flug"},
                                                {"name": "Nachbarinsel", "lat": 28.10, "lon": -17.11,
                                                 "transport": "Schiff"}])},
        {**base, "start_date": "2018-08-01", "end_date": "2018-08-08", "destination": "Nirgendwo", "transport": "Flug",
         "ap_to": "QQQ"},
        {**base, "start_date": "2018-09-01", "end_date": "2018-09-08", "destination": "Flughafenhotel",
         "lat": 25.25, "lon": 55.37, "transport": "Flug", "ap_to": "DXB"},
    ])
    t1, t2, t3, t4 = db.trips()                                            # ordered by date
    l1 = json.loads(t1["legs"])
    assert [x.get("ap") for x in l1] == ["HER", None] and l1[1]["name"] == "Inselhotel"
    assert l1[1]["transport"] == "Auto" and t1["ap_to"] is None and t1["ap_from"] == "ZRH"   # departure stays
    l2 = json.loads(t2["legs"])
    assert [x.get("ap") for x in l2] == ["TFS", None, None] and l2[1]["transport"] == "Auto"
    assert l2[2]["transport"] == "Schiff"                                   # the ship stays a ship
    assert t3["ap_to"] == "QQQ" and not t3["legs"]                         # unknown: left alone
    assert [x.get("ap") for x in json.loads(t4["legs"])] == ["DXB"]       # hotel at the airport: one stop
    db._conn.execute("UPDATE trips SET ap_to='HER' WHERE id=?", (t4["id"],))
    db.close()
    db = Database(str(tmp_path / "w.db"))                                  # runs only once
    assert next(t for t in db.trips() if t["id"] == t4["id"])["ap_to"] == "HER"
