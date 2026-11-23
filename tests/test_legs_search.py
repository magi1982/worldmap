"""Trips with several stops, online place search and Google Maps links – all with invented sample data."""
import json

import pytest

from test_atlas import load  # noqa: F401 – shared helper
from worldmap import atlas as A  # noqa: N812
from worldmap import geosearch, places
from worldmap.server import validate_legs, validate_trip


def test_legs_are_validated():
    ok = json.loads(validate_legs([{"name": " Teneriffa ", "lat": 28.29, "lon": -16.62, "transport": "Flug"},
                                   {"name": "La Gomera", "country": "Spanien", "lat": "28.1", "lon": -17.11,
                                    "transport": "Schiff"}]))
    assert [x["name"] for x in ok] == ["Teneriffa", "La Gomera"] and ok[1]["lat"] == 28.1
    assert validate_legs([]) == "" and validate_legs(None) == ""
    for bad in ([{"name": "x", "lat": 99, "lon": 0}], [{"name": "", "lat": 1, "lon": 1}],
                [{"name": "x", "lat": 1, "lon": 1, "transport": "Rakete"}], [{"lat": 1}], "nope", [1] * 3,
                [{"name": "x", "lat": 1, "lon": 1}] * 21):
        with pytest.raises(ValueError):
            validate_legs(bad)
    assert "legs" in validate_trip({"legs": [{"name": "Oslo", "lat": 59.9, "lon": 10.7}]}, partial=True)


def _trip(engine, legs, transport):
    engine.db.upsert_trip({"start_date": "2015-04-02", "end_date": "2015-04-16", "destination": "Sample trip",
                           "who": "Alex", "confidence": "bestätigt", "nights": 14, "lat": legs[0][1], "lon": legs[0][2],
                           "transport": transport, "source": "manual", "locked": 1,
                           "legs": validate_legs([{"name": n, "lat": la, "lon": lo, "transport": t}
                                                  for n, la, lo, t in legs])})


def test_plane_then_ship_to_an_island(engine, tmp_path):
    _trip(engine, [("Teneriffa", 28.29, -16.62, "Flug"), ("La Gomera", 28.10, -17.11, "Schiff")], "Flug · Schiff")
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert [x[0] for x in t["lg"]] == ["fly", "road", "ferry"]          # plane, from the airport by road, ship
    assert t["lg"][0][2][1] == "TFS"                                   # lands on Tenerife's big airport
    assert all(r[0] == 1 for r in t["lg"][2][1])                        # the ship goes over the water
    assert {"fly", "ferry"} <= set(t["m"]) and [s[2] for s in t["st"]] == ["Teneriffa", "La Gomera"]


def test_road_trip_follows_roads_on_another_continent(engine, tmp_path):
    _trip(engine, [("Sydney", -33.87, 151.21, "Flug"), ("Canberra", -35.28, 149.13, "Wohnmobil"),
                   ("Melbourne", -37.81, 144.96, "Zug")], "Flug · Wohnmobil · Zug")
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert [x[0] for x in t["lg"]] == ["fly", "road", "road", "rail"]   # airport → city by road first
    road, rail = t["lg"][2][1], t["lg"][3][1]
    assert sum(len(r[1]) for r in road) > 40 and sum(len(r[1]) for r in rail) > 60   # real lines, not straight
    assert t["k"]["fly"] > 30000 and t["k"]["road"] > 300


def test_round_trip_by_car_gets_the_way_back(engine, tmp_path):
    _trip(engine, [("Lyon", 45.76, 4.84, "Auto"), ("Marseille", 43.30, 5.37, "Auto")], "Auto")
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert [x[0] for x in t["lg"]] == ["road", "road", "back"] and not t["fl"]


def test_search_finds_places_all_over_the_world():
    for q, want in (("Sydney", "Austral"), ("Kenia", "Kenia"), ("Melbourne", "Austral"), ("Wien", "")):
        hits = places.search(q)
        assert hits, q
        assert want in (hits[0].get("country") or "") or not want, (q, hits[0])


def test_google_maps_links():
    p = geosearch.parse_gmaps("https://www.google.com/maps/place/Playa+de+las+Am%C3%A9ricas/@28.0573,-16.7311,15z")
    assert p["name"] == "Playa de las Américas" and (p["lat"], p["lon"]) == (28.0573, -16.7311)
    p = geosearch.parse_gmaps("https://www.google.com/maps/place/X/data=!3d-33.8568!4d151.2153")
    assert (p["lat"], p["lon"]) == (-33.8568, 151.2153)
    assert geosearch.parse_gmaps("https://maps.google.com/?q=40.7128,-74.0060")["lon"] == -74.006
    assert geosearch.is_gmaps("https://maps.app.goo.gl/abc") and not geosearch.is_gmaps("https://evil.example/maps")
    assert not geosearch.is_gmaps("https://google.com.evil.example/maps/@1.0,2.0")
    assert geosearch.resolve_gmaps("https://evil.example/@1.5,2.5") is None   # never followed
    assert geosearch.parse_gmaps("https://www.google.com/maps/@95.1,10.0,5z") is None


def test_online_search_parses_and_never_breaks(monkeypatch):
    def fake_get(url, headers, data=None):
        if "nominatim" in url:
            assert "q=La+Gomera" in url and headers == {}
            return [{"name": "La Gomera", "lat": "28.1", "lon": "-17.11", "address": {"country": "Spanien"},
                     "boundingbox": ["27.99", "28.22", "-17.35", "-17.09"]},
                    {"name": "<b>bad</b>", "lat": "999", "lon": "0"}]
        assert headers["X-Goog-Api-Key"] == "k" and json.loads(data)["textQuery"] == "Uluru"
        return {"places": [{"displayName": {"text": "Uluru"}, "location": {"latitude": -25.34, "longitude": 131.04},
                            "addressComponents": [{"longText": "Australien", "types": ["country"]}]}]}
    monkeypatch.setattr(geosearch, "_get", fake_get)
    monkeypatch.setattr(geosearch, "_last", [0.0])
    geosearch._cache.clear()
    osm = geosearch.search("La Gomera", "osm")
    assert len(osm) == 1 and osm[0]["country"] == "Spanien" and 10 < osm[0]["radius_km"] < 40
    assert geosearch.search("Uluru", "google", "k")[0]["country"] == "Australien"
    assert geosearch.search("Uluru", "google", "") == [] and geosearch.search("x", "osm") == []
    assert geosearch.search("La", "offline") == []

    def boom(*a, **k):
        raise OSError("no network")
    monkeypatch.setattr(geosearch, "_get", boom)
    geosearch._cache.clear()
    assert geosearch.search("Somewhere", "osm") == []


def test_island_by_car_and_ferry_goes_back_the_same_way(engine, tmp_path):
    # car to the port, ferry to the island: the way home is the same ferry, not a second one to another port
    _trip(engine, [("Hafenstadt", 42.93, 10.53, "Auto"), ("Insel", 42.15, 9.10, "Schiff")], "Auto · Schiff")
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][-1]
    assert [x[0] for x in t["lg"]] == ["road", "ferry", "back"]
    ferry_out = [r for r in t["lg"][1][1] if r[0]]
    ferry_back = [r for r in t["lg"][2][1] if r[0]]
    assert len(ferry_out) == 1 and len(ferry_back) == 1
    assert ferry_back[0][1] == A._rev(ferry_out[0][1])                  # the same crossing, the other way
    back_end = t["lg"][2][1][-1][1]
    assert abs(back_end[-2] - t["lg"][0][1][0][1][0]) < .01              # ends at home, where the trip started
    assert sum(1 for r in t["gr"] if r[0]) == 1                          # one ship line on the map, not two


def test_reverse_of_a_line():
    assert A._rev([1, 2, 3, 4, 5, 6]) == [5, 6, 3, 4, 1, 2]
