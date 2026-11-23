"""A trip = a name + stations. Old data moves into stations, imports and GPS fill them in. All data invented."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from conftest import HOME
from test_atlas import load  # noqa: F401 – shared helper
from worldmap import atlas as A  # noqa: N812
from worldmap import stations
from worldmap.db import Database
from worldmap.importers import triplist
from worldmap.server import validate_legs

TZ = "Europe/Zurich"


def ts(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(TZ)).timestamp())


def legs(t):
    return json.loads(t["legs"])


def test_every_trip_gets_a_station_from_its_old_fields(db):
    a = db.upsert_trip({"start_date": "2019-05-01", "end_date": "2019-05-05", "destination": "Seehotel",
                        "country": "Italien", "lat": 45.9, "lon": 8.6, "transport": "Auto · Schiff"})
    b = db.upsert_trip({"start_date": "2019-06-01", "end_date": "2019-06-09", "destination": "Kenia",
                        "country": "Kenia", "transport": "Flug"})
    s1, s2 = legs(db.trip(a)), legs(db.trip(b))
    assert s1 == [{"name": "Seehotel", "country": "Italien", "lat": 45.9, "lon": 8.6, "transport": "Auto · Schiff",
                   "auto": 1}]
    assert s2[0]["name"] == "Kenia" and s2[0]["lat"] is None          # only a country: a stop without a point
    t = db.trip(a)
    assert (t["destination"], t["country"], t["transport"]) == ("Seehotel", "Italien", "Auto · Schiff")


def test_the_trip_follows_its_stations(db):
    i = db.upsert_trip({"start_date": "2019-05-01", "end_date": "2019-05-05", "destination": "Sommer am Meer"})
    db.upsert_trip({"legs": validate_legs([
        {"ap": "PMI"}, {"name": "Hafenort", "country": "Spanien", "lat": 39.57, "lon": 3.2, "transport": "Auto"},
        {"name": "Nachbarinsel", "country": "Spanien", "lat": 39.9, "lon": 4.1, "transport": "Schiff"}])}, i)
    t = db.trip(i)
    assert t["destination"] == "Sommer am Meer"                          # the name stays the name
    assert t["country"] == "Spanien" and t["transport"] == "Flug · Auto · Schiff"
    assert (t["lat"], t["lon"]) == (39.57, 3.2)                          # the first place, not the airport
    db.upsert_trip({"lat": 39.6, "lon": 3.3}, i)                         # several stops: they decide
    assert db.trip(i)["lat"] == 39.57


def test_one_station_follows_answers_and_refreshes(db):
    i = db.upsert_trip({"start_date": "2019-05-01", "end_date": "2019-05-05", "destination": "Kenia",
                        "country": "Kenia"})
    db.upsert_trip({"lat": -2.0, "lon": 40.9}, i)
    s = legs(db.trip(i))
    assert len(s) == 1 and (s[0]["lat"], s[0]["lon"]) == (-2.0, 40.9)


def test_old_databases_are_migrated_once(tmp_path):
    db = Database(str(tmp_path / "w.db"))
    db._conn.execute("INSERT INTO trips (start_date, end_date, destination, country, lat, lon, transport) "
                     "VALUES ('2010-01-01', '2010-01-08', 'Skiort', 'Schweiz', 46.5, 9.8, 'Zug')")
    db._conn.execute("DELETE FROM meta WHERE key='stations_v2'")
    db.close()
    db = Database(str(tmp_path / "w.db"))
    t = db.trips()[0]
    assert legs(t)[0]["name"] == "Skiort" and legs(t)[0]["transport"] == "Zug" and t["destination"] == "Skiort"
    assert db.migrate_stations() == 0                                     # only once


def test_seaplane_flies_straight_to_the_island(engine, tmp_path):
    engine.db.upsert_trip({"start_date": "2018-03-03", "end_date": "2018-03-17", "destination": "Atoll",
                           "who": "Alex", "confidence": "bestätigt", "nights": 14, "source": "manual", "locked": 1,
                           "legs": validate_legs([{"ap": "MLE"}, {"name": "Inselresort", "lat": 3.9, "lon": 72.9,
                                                                  "transport": "Wasserflugzeug"}])})
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert t["lg"][1][0] == "fly" and t["lg"][1][2] == ["MLE", ""] and t["lg"][1][3] == 1   # no airport at the end
    assert [f[4] for f in t["fl"] if len(f) > 4] == [1, 1] and "fly" in t["m"]


def test_station_cell_for_excel_round_trip():
    stops = json.loads(validate_legs([{"ap": "DXB"}, {"name": "Abu Dhabi", "lat": 24.47, "lon": 54.37}]))
    text = triplist.stations_text(stops)
    assert text == "✈ DXB [Flug] → Abu Dhabi [Auto]"
    back = triplist.parse_stations(text)
    assert back[0]["ap"] == "DXB" and back[1]["name"] == "Abu Dhabi" and back[1]["lat"] is not None
    odd = triplist.parse_stations("Xqzvwy (Schiff) > Bern [Zug · Wohnmobil]")
    assert odd[0]["lat"] is None and odd[0]["transport"] == "Schiff"
    assert odd[1]["transport"] == "Zug · Wohnmobil"


def P(when, lat, lon):
    return {"ts": ts(when), "lat": lat, "lon": lon, "person": "Alex", "hint": None}


def _flight_holiday():
    """Fly to an island airport, drive to a hotel, two nights, then a second place, then home. Invented."""
    pts = [P("2024-05-04T06:00:00", *HOME), P("2024-05-04T07:00:00", 47.46, 8.55)]
    pts += [P("2024-05-04T09:30:00", 39.55, 2.74), P("2024-05-04T10:10:00", 39.60, 2.90),
            P("2024-05-04T11:00:00", 39.70, 3.30)]
    for d in (4, 5):
        pts += [P(f"2024-05-{d:02d}T23:00:00", 39.70, 3.30), P(f"2024-05-{d + 1:02d}T03:00:00", 39.70, 3.30)]
    pts += [P("2024-05-06T12:00:00", 39.80, 3.00), P("2024-05-06T23:00:00", 39.86, 2.80),
            P("2024-05-07T03:00:00", 39.86, 2.80)]
    pts += [P("2024-05-07T15:00:00", 39.55, 2.74), P("2024-05-07T17:30:00", 47.46, 8.55), P("2024-05-07T19:00:00", *HOME)]
    return pts


def test_stations_from_a_recording():
    st = stations.from_points(_flight_holiday(), "2024-05-04", "2024-05-07", TZ, HOME)
    assert [x.get("ap") for x in st] == ["PMI", None, None]                # landed at the real airport
    assert st[1]["n"] == 2 and st[2]["n"] == 1                              # two nights, then one
    assert st[1]["transport"] == "Auto" and st[0]["transport"] == "Flug"
    assert all(x["auto"] for x in st)
    assert stations.from_points([], "2024-05-04", "2024-05-07", TZ, HOME) == []


def test_detection_adds_stations_but_never_over_hand_made_ones(engine):
    rows = [(p["ts"], p["lat"], p["lon"], p["person"], "test", None, None) for p in _flight_holiday()]
    engine.import_points(rows)
    engine.rebuild()
    t = engine.db.trips()[0]
    assert [x.get("ap") for x in legs(t)][:1] == ["PMI"] and len(legs(t)) == 3
    hand = validate_legs([{"name": "Mein Hotel", "lat": 39.7, "lon": 3.3, "transport": "Flug"}])
    engine.db.upsert_trip({"legs": hand}, t["id"])
    engine.rebuild()
    assert legs(engine.db.trip(t["id"]))[0]["name"] == "Mein Hotel"        # yours stays yours


def test_old_transport_words_become_stations():
    assert stations.words("Auto · Fähre") == ["Auto", "Schiff"]
    assert stations.words("Flug · U-Bahn · unknown") == ["Flug", "Zug"]
    st = stations.from_fields("Inselresort (Atoll)", "Malediven", 3.95, 72.83, "Flug via Dubai · Wasserflugzeug")
    assert [(x.get("ap"), x["transport"]) for x in st] == [("DXB", "Flug"), ("MLE", "Flug"), (None, "Wasserflugzeug")]
    one = stations.from_fields("Seehotel", "Italien", 45.9, 8.6, "Auto · Fähre")
    assert len(one) == 1 and one[0]["transport"] == "Auto · Schiff"


def test_seaplane_trip_from_old_fields_on_the_map(engine, tmp_path):
    engine.db.upsert_trip({"start_date": "2007-06-30", "end_date": "2007-07-10", "destination": "Inselresort (Atoll)",
                           "country": "Malediven", "lat": 3.95, "lon": 72.83, "nights": 10, "locked": 1,
                           "transport": "Flug via Dubai · Wasserflugzeug", "source": "Fotos", "who": "Alex"})
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert [x[0] for x in t["lg"]] == ["fly", "fly", "fly"]
    assert [x[2] for x in t["lg"]] == [["ZRH", "DXB"], ["DXB", "MLE"], ["MLE", ""]]   # via Dubai, then the seaplane
    assert not t.get("gr")                                                            # no ferry over the sea
    assert t["p"] == [3.95, 72.83]


def test_migration_v3_cleans_old_stations(tmp_path):
    db = Database(str(tmp_path / "w.db"))
    i = db.upsert_trip({"start_date": "2010-01-01", "end_date": "2010-01-08", "destination": "Hafen",
                        "lat": 43.0, "lon": 9.4, "transport": "Auto · Fähre"})
    db._conn.execute("UPDATE trips SET legs = ? WHERE id = ?", (json.dumps(
        [{"name": "Hafen", "country": "", "lat": 43.0, "lon": 9.4, "transport": "Auto · Fähre", "auto": 1}]), i))
    db._conn.execute("DELETE FROM meta WHERE key='stations_v3'")
    db.close()
    db = Database(str(tmp_path / "w.db"))
    t = db.trip(i)
    assert legs(t)[0]["transport"] == "Auto · Schiff" and t["transport"] == "Auto · Schiff" and t["lat"] == 43.0
