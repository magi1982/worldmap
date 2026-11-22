import pytest

from worldmap.geo import haversine_km, parse_coordinate, simplify, valid_coord
from worldmap.timeparse import local_date, parse_ts


def test_haversine_known_distance():
    # Zurich HB -> Bern HB is about 95 km
    assert 94 < haversine_km(47.378, 8.540, 46.949, 7.439) < 97


@pytest.mark.parametrize("raw,expected", [
    ("47.5", 47.5), ("47,5", 47.5), (8, 8.0),
    ("47 deg 31' 12.00\" N", 47.52), ("8 deg 30' 0.00\" W", -8.5), ("-33.9", -33.9), ("", None), ("abc", None),
])
def test_parse_coordinate(raw, expected):
    v = parse_coordinate(raw)
    assert (v is None and expected is None) or v == pytest.approx(expected, abs=1e-4)


def test_valid_coord():
    assert valid_coord(47, 8)
    assert not valid_coord(0, 0)
    assert not valid_coord(91, 8)
    assert not valid_coord(float("nan"), 8)
    assert not valid_coord("x", 8)


def test_simplify_keeps_ends_and_drops_collinear():
    line = [[0, 0], [1, 0.0001], [2, 0], [3, 0]]
    out = simplify(line, 0.01)
    assert out[0] == [0, 0] and out[-1] == [3, 0] and len(out) == 2


@pytest.mark.parametrize("raw", ["2025:07:15 12:00:00", "2025-07-15T12:00:00", "15.07.2025 12:00", 1752573600, "1752573600000"])
def test_parse_ts_formats(raw):
    ts = parse_ts(raw, "Europe/Zurich")
    assert ts is not None
    assert local_date(ts, "Europe/Zurich") == "2025-07-15"


def test_parse_ts_offset_and_invalid():
    assert parse_ts("2025-07-15T10:00:00Z") == parse_ts("2025-07-15T12:00:00+02:00")
    assert parse_ts("not a date") is None
    assert parse_ts("") is None
