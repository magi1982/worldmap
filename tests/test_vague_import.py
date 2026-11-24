"""0.14.0: trips known only by month or year, and imports of messy files. Invented sample data only."""
import gzip
import json
import math

import pytest

from worldmap import vague
from worldmap.importers import UserImportError, detect_and_parse
from worldmap.server import validate_trip


# ---------------------------------------------------------------- vague dates
@pytest.mark.parametrize("text,nights,start,end,prec", [
    ("13.07.2009", None, "2009-07-13", "2009-07-13", "day"),
    ("13.07.2009", 5, "2009-07-13", "2009-07-18", "day"),
    ("13.–25.07.2009", None, "2009-07-13", "2009-07-25", "day"),
    ("13.07.–25.07.2009", None, "2009-07-13", "2009-07-25", "day"),
    ("13.07.2009 - 25.07.2009", None, "2009-07-13", "2009-07-25", "day"),
    ("28.12.–03.01.2010", None, "2009-12-28", "2010-01-03", "day"),
    ("2009-07-13 bis 2009-07-25", None, "2009-07-13", "2009-07-25", "day"),
    ("13.7.09", 2, "2009-07-13", "2009-07-15", "day"),
    ("07.2009", 7, "2009-07-13", "2009-07-20", "month"),
    ("7/2009", 0, "2009-07-16", "2009-07-16", "month"),
    ("2009-07", 7, "2009-07-13", "2009-07-20", "month"),
    ("Juli 2009", 7, "2009-07-13", "2009-07-20", "month"),
    ("Jul. 2009", 7, "2009-07-13", "2009-07-20", "month"),
    ("july 2009", 7, "2009-07-13", "2009-07-20", "month"),
    ("ca. Juli 2009", 7, "2009-07-13", "2009-07-20", "month"),
    ("Juli–August 2009", 10, "2009-07-26", "2009-08-05", "month"),
    ("Juli 2009", 40, "2009-07-01", "2009-08-10", "month"),   # longer than the month: starts on the 1st
    ("2009", 14, "2009-06-25", "2009-07-09", "year"),
    ("~2003", 0, "2003-07-02", "2003-07-02", "year"),
])
def test_parse(text, nights, start, end, prec):
    got = vague.parse(text, nights)
    assert (got["start_date"], got["end_date"], got["date_prec"]) == (start, end, prec)
    assert got["nights"] == (0 if nights is None and prec == "day" and start == end else got["nights"])


@pytest.mark.parametrize("bad", ["", "Sommer", "Juli", "31.02.2009", "1850", "2009-13", "13.13.2009",
                                 "25.–13.07.2009", "x" * 80, "2009-07-13 – 2021-07-13"])
def test_parse_rejects(bad):
    with pytest.raises(ValueError):
        vague.parse(bad)


def test_labels():
    assert vague.label("2009-07-13", "2009-07-25", "day") == "13.–25.07.2009"
    assert vague.label("2009-07-13", "2009-07-13", "day") == "13.07.2009"
    assert vague.label("2009-06-28", "2009-07-05", "day") == "28.06.–05.07.2009"
    assert vague.label("2009-12-28", "2010-01-03", "day") == "28.12.2009–03.01.2010"
    assert vague.label("2009-07-13", "2009-07-20", "month") == "Juli 2009"
    assert vague.label("2009-07-26", "2009-08-05", "month") == "Juli–August 2009"
    assert vague.label("2009-12-29", "2010-01-03", "month") == "Dezember 2009–Januar 2010"
    assert vague.label("2009-06-25", "2009-07-09", "year") == "2009"


def test_validate_trip_when():
    t = validate_trip({"when": "Juli 2009", "nights": 10, "destination": "Toskana"}, partial=False)
    assert t["date_prec"] == "month" and t["nights"] == 10 and t["start_date"].startswith("2009-07")
    t = validate_trip({"when": "2009"}, partial=True, cur={"nights": 7})          # keeps the trip's length
    assert t["date_prec"] == "year" and t["nights"] == 7
    t = validate_trip({"when": "13.–25.07.2009"}, partial=True, cur={"nights": 3})
    assert (t["start_date"], t["end_date"], t["date_prec"], t["nights"]) == ("2009-07-13", "2009-07-25", "day", 12)
    with pytest.raises(ValueError):
        validate_trip({"date_prec": "decade"}, partial=True)


def test_api_when_and_migration(engine):
    db = engine.db
    # trips from the old wizard: year = 15 July, month = from the 1st, marked approx
    a = db.upsert_trip({"start_date": "2005-07-15", "end_date": "2005-07-22", "destination": "Rom", "approx": 1,
                        "source": "manual", "nights": 7})
    b = db.upsert_trip({"start_date": "2006-08-01", "end_date": "2006-08-08", "destination": "Wien", "approx": 1,
                        "source": "manual", "nights": 7})
    c = db.upsert_trip({"start_date": "2007-08-01", "end_date": "2007-08-08", "destination": "GPS", "approx": 0,
                        "source": "gps", "nights": 7})
    db._conn.execute("DELETE FROM meta WHERE key='date_prec'")
    assert db.migrate_date_prec() == 2
    assert [db.trip(x)["date_prec"] for x in (a, b, c)] == ["year", "month", "day"]
    assert db.migrate_date_prec() == 0                                          # once only


# ---------------------------------------------------------------- trip lists
def test_triplist_with_vague_dates():
    csv = ("Wann;Ziel;Land;Nächte;Wer\n"
           "13.–25.07.2009;Toskana;Italien;;Alex\n"
           "Juli 2010;Kreta;Griechenland;10;Sam\n"
           "2003;Rom;Italien;5;\n"
           ";ohne Datum;Italien;;\n"
           "\n").encode()
    r = detect_and_parse(csv, "reisen.csv")
    got = {t["destination"]: (t["date_prec"], t["nights"]) for t in r.trips}
    assert got == {"Toskana": ("day", 12), "Kreta": ("month", 10), "Rom": ("year", 5)}
    assert r.skipped == 1


def test_triplist_von_bis_mixed_and_own_export_roundtrip():
    csv = ("Von,Bis,Ziel\n"
           "13.07.2009,25.07.2009,Toskana\n"
           "07.2010,,Kreta\n"
           "2011-05-01,2011-04-28,Rückwärts\n").encode()
    r = detect_and_parse(csv, "reisen.csv")
    got = {t["destination"]: (t["start_date"], t["end_date"], t["date_prec"]) for t in r.trips}
    assert got["Toskana"] == ("2009-07-13", "2009-07-25", "day")
    assert got["Kreta"][2] == "month"
    assert got["Rückwärts"][:2] == ("2011-04-28", "2011-05-01")              # swapped dates are put in order
    # our own CSV export: stand-in days + "when" – the month survives the round trip
    own = ("start_date;end_date;destination;nights;when\n"
           "2009-07-13;2009-07-20;Toskana;7;Juli 2009\n"
           "2009-07-13;2009-07-25;Elba;12;13.–25.07.2009\n").encode()
    r = detect_and_parse(own, "worldmap-trips.csv")
    got = {t["destination"]: (t["start_date"], t["end_date"], t["date_prec"]) for t in r.trips}
    assert got == {"Toskana": ("2009-07-13", "2009-07-20", "month"), "Elba": ("2009-07-13", "2009-07-25", "day")}


# ---------------------------------------------------------------- GPS files
def test_gps_csv_messy():
    csv = ("Zeit;Breite;Länge\n"
           "2024-05-10 11:40:02;38,7139;-9,1334\n"     # comma decimals
           "2024-05-10 12:00:00;;\n"                    # no position
           "2024-05-10 12:10:00;123,0;9,0\n"            # out of range
           "kein Datum;38,7;-9,1\n"
           "2024-05-10 12:20:00;0;0\n"                  # Null Island
           "2024-05-10 12:30:00;38,7110;-9,1390\n").encode()
    r = detect_and_parse(csv, "gps.csv")
    assert len(r.points) == 2 and r.skipped == 4
    assert all(-90 <= p[1] <= 90 and -180 <= p[2] <= 180 for p in r.points)


def test_exiftool_csv():
    csv = (b"SourceFile,GPSLatitude,GPSLongitude,DateTimeOriginal\n"
           b"IMG_0001.HEIC,38.7139,-9.1334,2024:05:10 11:40:02\n"
           b"IMG_0002.JPG,,,2024:05:10 12:00:00\n")
    r = detect_and_parse(csv, "fotos.csv")
    assert len(r.points) == 1 and r.skipped == 1 and r.columns["time"] == "DateTimeOriginal"


def test_only_rubbish_is_a_clear_error():
    with pytest.raises(UserImportError) as e:
        detect_and_parse(b"Name;Farbe\nA;rot\n", "x.csv")
    assert "keine brauchbaren Positionen" in str(e.value)
    with pytest.raises(UserImportError) as e:
        detect_and_parse(b'{"foo": 1}', "x.json")
    assert "nicht erkannt" in str(e.value)
    with pytest.raises(UserImportError) as e:
        detect_and_parse(b'{"worldmap": 1, "trips": [], "points": [', "x.json")
    assert "kein gültiges JSON" in str(e.value)


# ---------------------------------------------------------------- Worldmap package from other tools / an AI
def test_package_as_an_ai_writes_it():
    pkg = {"worldmap": 1, "persons": ["Alex"], "groups": [],
           "trips": [{"when": "Juli 2009", "nights": 10, "destination": "Toskana", "who": "Alex"},
                     {"start_date": "2024-05-10", "end_date": "2024-05-14", "destination": "Lissabon",
                      "legs": [{"name": "Lissabon", "lat": 38.72, "lon": -9.14, "transport": "Flug", "ap": "LIS"}]},
                     {"destination": "ohne Datum"}],
           "points": [{"time": "2024-05-10T09:15:00Z", "lat": 38.7742, "lon": -9.1342, "person": "Alex"},
                      {"time": 1715334000000, "lat": 38.7, "lon": -9.1, "person": "Sam"},       # ms, new person
                      {"time": "gestern", "lat": 38.7, "lon": -9.1},
                      {"time": "2024-05-10T10:00:00Z", "lat": math.nan, "lon": 1},
                      [1715594400, 38.7139, -9.1334, 0],
                      [1715594400, 95.0, 0.5, 0]]}
    r = detect_and_parse(gzip.compress(json.dumps(pkg).encode()), "x.worldmap.json.gz")
    assert r.format == "worldmap" and len(r.trips) == 2
    assert {p[3] for p in r.points} == {"Alex", "Sam"} and len(r.points) == 3
    assert r.skipped == 2 and any("unlesbar" in w for w in r.warnings)
    trips = [validate_trip(dict(t), partial=False) for t in r.trips]
    assert trips[0]["date_prec"] == "month" and '"ap": "LIS"' in trips[1]["legs"]


def test_sample_file_in_the_app_is_valid():
    from pathlib import Path
    p = Path(__file__).parents[1] / "worldmap/app/worldmap/static/beispiel.worldmap.json"
    r = detect_and_parse(p.read_bytes(), p.name)
    assert len(r.trips) == 3 and len(r.points) == 4 and not r.skipped and not r.warnings
    precs = [validate_trip(dict(t), partial=False).get("date_prec", "day") for t in r.trips]
    assert precs == ["day", "month", "year"]
