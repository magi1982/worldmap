"""Estimated ways must be plausible: no huge detours, no straight lines over the Alps, no stray points as flights."""

from worldmap import roadnet
from worldmap.geo import haversine_km
from worldmap.modes import drop_spikes


def length(runs):
    f = [c for r in runs for c in r[1]]
    return sum(haversine_km(f[i], f[i + 1], f[i + 2], f[i + 3]) for i in range(0, len(f) - 2, 2))


def test_motorways_are_connected_where_the_data_has_small_holes():
    zrh, bern = (47.378, 8.538), (46.948, 7.439)
    r = roadnet.route("road", zrh, bern)
    assert r and length(r) < 1.45 * haversine_km(*zrh, *bern)          # the A1, not over the Klausen pass


def test_no_big_loop_north_on_the_way_to_the_atlantic():
    allier, correze = (46.50, 3.36), (45.28, 1.57)
    r = roadnet.route("road", allier, correze)
    assert r and length(r) < 1.4 * haversine_km(*allier, *correze)
    assert max(r[0][1][0::2]) < 46.6                                    # no detour far to the north


def test_alpine_roads_are_followed_not_crossed():
    zrh, garda = (47.37, 8.54), (45.60, 10.60)
    r = roadnet.route("road", zrh, garda)
    assert r and sum(len(x[1]) for x in r) > 40                         # a real road over a pass, not a line


def test_hopeless_detours_are_refused():
    # Hossegor → Toulouse is ~250 km; a "way" five times as long is never offered
    a, b = (43.66, -1.43), (43.60, 1.44)
    r = roadnet.route("road", a, b)
    assert r is None or length(r) <= roadnet.MAX_DETOUR["road"] * haversine_km(*a, *b) + roadnet.DETOUR_KM


def P(ts, lat, lon, hint=None, person="Alex"):
    return {"ts": ts, "lat": lat, "lon": lon, "hint": hint, "person": person}


H = 3600


def test_one_stray_point_at_home_in_a_holiday_is_dropped():
    island, home = (39.52, 3.31), (47.37, 8.54)
    pts = [P(0, *island), P(30 * H, *home), P(39 * H, *island), P(45 * H, *island)]
    assert [p["ts"] for p in drop_spikes(pts)] == [0, 39 * H, 45 * H]


def test_impossible_photo_position_is_dropped_but_real_flights_stay():
    a, far = (47.37, 8.54), (55.0, 20.0)
    assert len(drop_spikes([P(0, *a), P(60, *far), P(120, *a)])) == 2       # 1000 km in a minute
    trip = [P(0, *a), P(2 * H, *far, "flying"), P(30 * H, *far), P(33 * H, *a, "flying")]
    assert len(drop_spikes(trip)) == 4                                     # a real day trip by plane
    near = [P(0, *a), P(3 * H, 47.0, 9.5), P(6 * H, *a)]
    assert len(drop_spikes(near)) == 3                                     # a short trip is no spike


def test_protected_points_stay():
    a, b = (47.37, 8.54), (52.37, 4.90)
    pts = [P(0, *a), P(5 * H, *b), P(20 * H, *a)]
    assert len(drop_spikes(pts, keep=lambda p: p["lat"] > 50)) == 3        # a trip went there: keep it


def test_a_flight_end_recorded_at_home_uses_the_airport_the_trip_flew_from(engine, tmp_path):
    import json as _j
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from worldmap import atlas as A  # noqa: N812

    def ts(s):
        return int(datetime.fromisoformat(s).replace(tzinfo=ZoneInfo("Europe/Zurich")).timestamp())

    zrh, pmi, town = (47.4581, 8.5481), (39.5517, 2.7388), (39.55, 3.30)
    near_fdh = (47.45, 9.30)   # first point after landing: at home, closer to another airport than to ZRH
    pts = [(ts("2017-06-03T08:00:00"), *zrh, "flying"), (ts("2017-06-03T10:00:00"), *pmi, "flying"),
           (ts("2017-06-03T12:00:00"), *town, None), (ts("2017-06-10T12:00:00"), *town, None),
           (ts("2017-06-12T14:00:00"), *pmi, None), (ts("2017-06-12T16:00:00"), *near_fdh, "flying"),
           (ts("2017-06-12T20:00:00"), 47.45, 9.31, None)]
    engine.import_points([(t, la, lo, "Alex", "t", h, None) for t, la, lo, h in pts])
    engine.db.upsert_trip({"start_date": "2017-06-03", "end_date": "2017-06-12", "destination": "Inselort",
                           "transport": "Flug", "lat": 39.55, "lon": 3.30, "locked": 1, "source": "manual"})
    core = _j.loads(__import__("gzip").decompress(A.Atlas(engine, str(tmp_path)).get("core")))
    t = next(x for x in core["trips"] if x["name"] == "Inselort")
    assert [f[2:4] for f in t["fl"]] == [["ZRH", "PMI"], ["PMI", "ZRH"]]
