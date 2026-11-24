"""0.13.0: real roads from a routing service for trips without GPS. Services are mocked – no network in tests.
All positions are public places (cities), no personal data."""
import io
import json
import urllib.error

import pytest

from worldmap import atlas as A  # noqa: N812
from worldmap import routeservice as R  # noqa: N812
from worldmap.settings import from_dict

ZURICH, BERN = (47.37, 8.54), (46.95, 7.44)


def encode(points):
    """Google polyline encoder (for the test only)."""
    out, plat, plon = [], 0, 0
    for lat, lon in points:
        for v, prev in ((round(lat * 1e5), plat), (round(lon * 1e5), plon)):
            d = v - prev
            d = ~(d << 1) if d < 0 else d << 1
            while d >= 0x20:
                out.append(chr((0x20 | (d & 0x1F)) + 63))
                d >>= 5
            out.append(chr(d + 63))
        plat, plon = round(lat * 1e5), round(lon * 1e5)
    return "".join(out)


class Fake:
    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def __call__(self, url, headers, data=None):
        self.calls.append((url, headers, data))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def osrm_answer(points):
    return {"code": "Ok", "routes": [{"geometry": {"coordinates": [[lon, lat] for lat, lon in points]}}]}


WAY = [ZURICH, (47.2, 8.1), (47.0, 7.7), BERN]


# ---------------------------------------------------------------- the services
def test_osrm_route_and_what_is_sent(monkeypatch):
    f = Fake(osrm_answer(WAY))
    monkeypatch.setattr(R, "_call", f)
    got = R.route("osm", (47.3712, 8.5417), BERN)
    assert got[0] == list(ZURICH) and got[-1] == list(BERN) and len(got) == 4
    url = f.calls[0][0]
    assert url.startswith("https://routing.openstreetmap.de/routed-car/route/v1/driving/")
    assert "8.5400,47.3800" in url and "8.5417" not in url          # rounded to ~2 km, never the exact place


def test_osrm_no_route_and_errors(monkeypatch):
    monkeypatch.setattr(R, "_call", Fake({"code": "NoRoute"}))
    assert R.route("osm", ZURICH, BERN) == "none"
    monkeypatch.setattr(R, "_call", Fake({"code": "TooBig"}))
    with pytest.raises(R.RouteError):
        R.route("osm", ZURICH, BERN)


def test_a_far_detour_is_not_believed(monkeypatch):
    monkeypatch.setattr(R, "_call", Fake(osrm_answer([ZURICH, (52.5, 13.4), BERN])))   # via Berlin
    assert R.route("osm", ZURICH, BERN) == "none"


def test_google_route_key_in_header_only(monkeypatch):
    f = Fake({"routes": [{"polyline": {"encodedPolyline": encode(WAY)}}]})
    monkeypatch.setattr(R, "_call", f)
    got = R.route("google", ZURICH, BERN, "SECRET-KEY")
    assert [round(a, 2) for a in got[1]] == [47.2, 8.1] and len(got) == 4
    url, headers, data = f.calls[0]
    assert url == R.GOOGLE_URL and "SECRET-KEY" not in url and headers["X-Goog-Api-Key"] == "SECRET-KEY"
    body = json.loads(data)
    assert body["travelMode"] == "DRIVE" and body["routingPreference"] == "TRAFFIC_UNAWARE"
    assert "SECRET-KEY" not in data.decode()
    monkeypatch.setattr(R, "_call", Fake({}))
    assert R.route("google", ZURICH, BERN, "SECRET-KEY") == "none"
    with pytest.raises(R.RouteError):
        R.route("google", ZURICH, BERN, "")


def test_polyline_decoder_known_value():
    # the example from Google's polyline documentation
    pts = R.decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    assert [[round(a, 3), round(b, 3)] for a, b in pts] == [[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]]
    assert R.decode_polyline("_p~i") == []                     # broken input never raises


def test_only_https_to_the_two_hosts(monkeypatch):
    monkeypatch.undo()                                          # the real _call, without the test block
    for url in ("http://routing.openstreetmap.de/x", "https://evil.example/x", "file:///etc/passwd"):
        with pytest.raises(ValueError):
            R._call(url, {})


def test_http_errors_never_show_the_key(monkeypatch):
    monkeypatch.undo()
    monkeypatch.setattr(R, "_wait", lambda: None)

    def boom(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, io.BytesIO(b"{}"))
    monkeypatch.setattr(R.urllib.request, "urlopen", boom)
    with pytest.raises(R.RouteError) as exc:
        R.google(ZURICH, BERN, "SECRET-KEY")
    assert "SECRET-KEY" not in str(exc.value) and "403" in str(exc.value)


def test_active_service():
    assert R.active(from_dict({})) == "osm"                    # default
    assert R.active(from_dict({"route_service": "google"})) == "offline"       # google without a key: nothing sent
    assert R.active(from_dict({"route_service": "google", "google_maps_api_key": "k"})) == "google"
    assert R.active(from_dict({"route_service": "nonsense"})) == "osm"


# ---------------------------------------------------------------- in the map
def test_atlas_asks_once_and_caches(engine, tmp_path, monkeypatch):
    engine.s.route_service = "osm"
    f = Fake(osrm_answer(WAY))
    monkeypatch.setattr(R, "_call", f)
    at = A.Atlas(engine, str(tmp_path))
    first = at.est_route(ZURICH, BERN, "road")
    assert first == at.ground_route(ZURICH, BERN)             # never waits: offline estimate first, leg queued
    assert at.fill_roads() == 1 and len(f.calls) == 1
    runs = at.est_route(ZURICH, BERN, "road")
    pts = list(zip(runs[0][1][::2], runs[0][1][1::2], strict=True))
    assert pts[0] == ZURICH and pts[-1] == BERN and (47.2, 8.1) in pts
    assert at.fill_roads() == 0 and len(f.calls) == 1        # asked only once
    at2 = A.Atlas(engine, str(tmp_path))                       # after a restart: from the disk cache
    at2.est_route(ZURICH, BERN, "road")
    assert at2.fill_roads() == 0 and len(f.calls) == 1
    assert at.est_route(ZURICH, BERN, "rail") == at.ground_route(ZURICH, BERN, "rail")   # trains: not asked


def test_atlas_falls_back_when_the_service_is_down(engine, tmp_path, monkeypatch):
    engine.s.route_service = "osm"
    f = Fake(R.RouteError("down"))
    monkeypatch.setattr(R, "_call", f)
    at = A.Atlas(engine, str(tmp_path))
    legs = [(ZURICH, BERN), ((46.2, 6.15), (46.52, 6.63)), ((47.56, 7.59), (47.05, 8.31)), ((46.0, 8.95), (46.17, 9.0))]
    for a, b in legs:
        at.est_route(a, b, "road")
    at.fill_roads()
    assert len(f.calls) == 3                                    # three errors: stop asking for now
    assert not at.__dict__.get("_road_todo")
    for a, b in legs:                                           # offline estimate, nothing queued again
        assert at.est_route(a, b, "road") == at.ground_route(a, b)
    assert not at.__dict__.get("_road_todo")
    assert not (tmp_path / "est-roads.json.gz").exists()       # failures are never stored


def test_reset_and_service_change(engine, tmp_path, monkeypatch):
    engine.s.route_service = "osm"
    monkeypatch.setattr(R, "_call", Fake(osrm_answer(WAY)))
    at = A.Atlas(engine, str(tmp_path))
    at.est_route(ZURICH, BERN, "road")
    at.fill_roads()
    fp = at.fingerprint()
    engine.s.route_service = "offline"
    assert at.fingerprint() != fp                               # another service: the map is built again
    assert at.est_route(ZURICH, BERN, "road") == at.ground_route(ZURICH, BERN)   # offline, no tiles: coarse estimate
    engine.s.route_service = "osm"
    assert at.reset_roads() == 1
    at.est_route(ZURICH, BERN, "road")
    assert at.__dict__.get("_road_todo")                        # asked again
