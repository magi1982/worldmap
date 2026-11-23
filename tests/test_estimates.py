"""0.7.2: estimates for trips without GPS – no point in the middle of a country, islands without a big airport are
reached by plane + ferry, cars follow roads. All places are public tourist places, no personal data."""
import gzip
import json

from worldmap import airports
from worldmap import atlas as A  # noqa: N812
from worldmap import netmatch as N  # noqa: N812
from worldmap.importers.triplist import geocode, parse_rows
from worldmap.roads import LONG_Z, RoadRouter

HOME = (47.0, 8.0)  # sample home (central Switzerland), not a real address


def load(atlas, part):
    return json.loads(gzip.decompress(atlas.get(part)))


def trip(**kw):
    t = {"start_date": "2015-07-01", "end_date": "2015-07-10", "who": "Alex", "confidence": "bestätigt",
         "nights": 9, "source": "Import"}
    t.update(kw)
    return t


# ---------------------------------------------------------------- only a country
def test_a_country_is_no_place():
    assert geocode("Griechenland", "", HOME, None)[3] == "country"
    assert geocode("Frankreich & Spanien", "", HOME, None)[3] == "country"
    assert geocode("Wien", "", HOME, 600)[3] == "place"
    names, rows, _ = parse_rows([["Start", "Ende", "Ziel", "Land"],
                                 ["2015-07-01", "2015-07-10", "Griechenland", "Griechenland"],
                                 ["2016-07-01", "2016-07-10", "Wien", "Österreich"]])
    assert rows[0].get("lat") is None and rows[0].get("lon") is None       # no point in the Cyclades
    assert rows[1]["lat"] is not None


def test_country_only_trips_get_no_point_on_the_map(engine, tmp_path):
    engine.db.upsert_trip(trip(destination="Griechenland", country="Griechenland", transport="Flug"))
    g = geocode("Frankreich & Spanien", "", None, None)  # stored like 0.7.1 did: the middle of a country
    engine.db.upsert_trip(trip(start_date="2016-07-01", end_date="2016-07-10", destination="Frankreich & Spanien",
                               transport="Auto", lat=round(g[0], 4), lon=round(g[1], 4)))
    engine.touch()
    core = load(A.Atlas(engine, str(tmp_path)), "core")
    for t in core["trips"]:
        assert t["nopos"] == 2 and not t["fl"] and "gr" not in t
    assert core["est"] == []


# ---------------------------------------------------------------- islands without a big airport
def test_island_without_big_airport_plane_then_ferry(engine, tmp_path):
    assert airports.nearest_large(28.12, -17.24)[0] == "TFS"
    engine.db.upsert_trip(trip(destination="La Gomera", country="Spanien", transport="Flug"))
    engine.touch()
    t = load(A.Atlas(engine, str(tmp_path)), "core")["trips"][0]
    assert t["fl"][0][3] == "TFS" and t["fl"][1][2] == "TFS"              # the plane lands on Tenerife
    assert any(r[0] == 1 for r in t["gr"]) and "ferry" in t["m"]           # and the ferry goes on to the island


# ---------------------------------------------------------------- cars follow roads
def _net():
    """An invented motorway in two pieces (a tile seam 150 m apart) plus a side road – zoom-7 sample data."""
    mw1 = [(47.0, 8.1), (46.5, 7.6), (46.0, 7.0)]
    mw2 = [(46.0013, 6.9995), (45.5, 6.0), (45.0, 5.0)]
    side = [(45.5, 6.0), (45.3, 6.6)]
    return N.StaticLines([["0", mw1], ["0", mw2], ["2", side]], z=LONG_Z)


def test_road_router_follows_the_motorway():
    r = RoadRouter(_net(), None)
    path = r.route((47.02, 8.12), (45.02, 5.02))
    assert isinstance(path, list) and path[0] == [47.02, 8.12] and path[-1] == [45.02, 5.02]
    assert any(abs(p[0] - 45.5) < 1e-6 and abs(p[1] - 6.0) < 1e-6 for p in path)   # over the motorway junction
    assert r.route((47.02, 8.12), (30.0, -30.0)) == "none"                          # nowhere near a road


def test_road_router_waits_for_tiles():
    class Offline(N.TileSource):
        def lines(self, x, y):
            return None
    assert RoadRouter(Offline(), None).route((47.0, 8.1), (45.0, 5.0)) is None


def test_estimated_car_route_uses_the_roads(engine, tmp_path):
    at = A.Atlas(engine, str(tmp_path))
    at.road_router = RoadRouter(_net(), None)
    first = at.est_route((47.02, 8.12), (45.02, 5.02), "road")           # the map never waits for the network:
    assert first == at.ground_route((47.02, 8.12), (45.02, 5.02))         # rough estimate first, route queued
    assert at.fill_roads() == 1                                            # computed in the background
    runs = at.est_route((47.02, 8.12), (45.02, 5.02), "road")
    assert len(runs) == 1 and runs[0][0] == 0
    flat = runs[0][1]
    pts = list(zip(flat[::2], flat[1::2], strict=True))
    assert pts[0] == (47.02, 8.12) and pts[-1] == (45.02, 5.02)
    assert (46.5, 7.6) in pts and len(pts) >= 4                                      # on the motorway, not the land grid
    assert (tmp_path / "est-roads.json.gz").exists()                                 # computed once, then cached
    assert at.est_route((47.02, 8.12), (45.02, 5.02), "rail") == at.ground_route((47.02, 8.12), (45.02, 5.02))


def test_atlas_retries_when_tiles_were_missing(engine, tmp_path):
    class Offline(N.TileSource):
        def lines(self, x, y):
            return None
    engine.db.upsert_trip(trip(destination="Wien", country="Österreich", transport="Auto", max_km=600))
    engine.touch()
    at = A.Atlas(engine, str(tmp_path))
    at.road_router = RoadRouter(Offline(), None)
    t = load(at, "core")["trips"][0]
    assert t["gr"]                                                   # the coarse estimate is shown meanwhile
    assert at._mem.get("pending") and not list(tmp_path.glob("atlas-*.json.gz"))   # not cached on disk
    assert engine.routes_wanted.is_set()                             # the background worker is woken up
    assert at.fill_roads() == 0                                      # still offline: nothing new, try again later
    at.road_router = RoadRouter(_net(), None)
    assert at.fill_roads() == 1 and at._mem == {}                    # tiles back: route computed, map built again
    assert load(at, "core")["trips"][0]["gr"]


# ---------------------------------------------------------------- the place question
def test_place_question_puts_the_trip_on_the_map(engine, tmp_path):
    from worldmap import asking
    tid = engine.db.upsert_trip(trip(destination="Griechenland", country="Griechenland", transport="Flug"))
    engine.db.upsert_trip(trip(start_date="2016-07-01", end_date="2016-07-10", destination="Wien", country="Österreich",
                               lat=48.21, lon=16.37))
    asking.build(engine.db, engine.s)
    qs = [q for q in engine.db.open_questions() if q["kind"] == "place"]
    assert len(qs) == 1 and qs[0]["trip_id"] == tid and "Wo genau" in qs[0]["text"]
    import pytest
    with pytest.raises(ValueError):
        asking.answer(engine.db, qs[0]["id"], "Xyzzyqwert")                       # unknown name: try again
    res = asking.answer(engine.db, qs[0]["id"], "Santorini")
    t = engine.db.trip(tid)
    assert res["place"] and 36 < t["lat"] < 37 and t["destination"] == "Santorini" and t["locked"]
    asking.build(engine.db, engine.s)
    assert not [q for q in engine.db.open_questions() if q["kind"] == "place"]      # answered: not asked again
    engine.touch()
    core = load(A.Atlas(engine, str(tmp_path)), "core")
    assert [x for x in core["trips"] if x["dbid"] == tid][0]["nopos"] == 0


def test_place_question_can_be_skipped(engine):
    from worldmap import asking
    tid = engine.db.upsert_trip(trip(destination="Frankreich & Spanien", transport="Auto"))
    asking.build(engine.db, engine.s)
    q = [q for q in engine.db.open_questions() if q["kind"] == "place"][0]
    asking.answer(engine.db, q["id"], asking.PLACE_UNKNOWN)
    asking.build(engine.db, engine.s)
    assert not [q for q in engine.db.open_questions() if q["kind"] == "place"] and engine.db.trip(tid)["lat"] is None
