import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from worldmap import routing
from worldmap.ha import HomeAssistant, Supervisor, list_trackers, position_from_state


def test_classify_gap():
    a = {"ts": 0, "lat": 47.0, "lon": 8.0}
    assert routing.classify_gap(a, {"ts": 3600, "lat": 47.001, "lon": 8.0}) is None          # tiny
    assert routing.classify_gap(a, {"ts": 3600, "lat": 46.5, "lon": 7.6}) == "road"          # ~60 km/h
    assert routing.classify_gap(a, {"ts": 7200, "lat": 41.9, "lon": 12.5}) == "flight"       # Rome in 2 h
    assert routing.classify_gap(a, {"ts": 3 * 86400, "lat": 46.5, "lon": 7.6}) is None       # data gap


def test_great_circle_endpoints():
    line = routing.great_circle((47.0, 8.0), (40.6, -73.8), 10)
    assert line[0] == pytest.approx([47.0, 8.0], abs=1e-4) and line[-1] == pytest.approx([40.6, -73.8], abs=1e-4)
    assert max(p[0] for p in line) > 50  # arcs north


def test_fill_gaps_flights_without_matcher(db):
    db.add_points([(0, 47.0, 8.0, "Alex", "t", None, None), (7200, 41.9, 12.5, "Alex", "t", None, None)])
    assert routing.fill_gaps(db, None) == 1
    assert [s["mode"] for s in db.segments()] == ["flight"]
    assert routing.fill_gaps(db, None) == 0


def test_position_from_state():
    st = {"attributes": {"latitude": 47.0, "longitude": 8.0, "gps_accuracy": 12}, "last_updated": "2025-07-01T10:00:00+00:00"}
    assert position_from_state(st)[:3] == (47.0, 8.0, 12)
    assert position_from_state({"attributes": {}}) is None
    assert position_from_state(None) is None


class FakeCore(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *a):
        pass

    def _reply(self, obj):
        raw = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        FakeCore.calls.append(("GET", self.path, self.headers.get("Authorization")))
        if self.path == "/api/states":
            return self._reply([{"entity_id": "person.alex", "attributes": {"latitude": 1, "longitude": 2, "friendly_name": "Alex"}},
                                {"entity_id": "light.kitchen", "attributes": {}}])
        if self.path.startswith("/api/states/"):
            return self._reply({"attributes": {"latitude": 47.0, "longitude": 8.0}, "last_updated": "2025-07-01T10:00:00+00:00"})
        if self.path == "/addons/self/info":
            return self._reply({"data": {"options": {"routing": "off"}}})
        self._reply(None)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        FakeCore.calls.append(("POST", self.path, json.loads(self.rfile.read(n))))
        self._reply([])


@pytest.fixture
def fake_core():
    srv = HTTPServer(("127.0.0.1", 0), FakeCore)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FakeCore.calls = []
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_ha_client(fake_core):
    ha = HomeAssistant(fake_core + "/api", token="t0k")
    assert ha.state("person.alex")["attributes"]["latitude"] == 47.0
    assert FakeCore.calls[-1][2] == "Bearer t0k"
    with pytest.raises(ValueError):
        ha.state("person.alex/../../config")
    assert ha.notify("notify.mobile_app_x", "T", "M", url="/x")
    assert FakeCore.calls[-1][:2] == ("POST", "/api/services/notify/mobile_app_x")
    with pytest.raises(ValueError):
        ha.notify("shell_command.boom", "T", "M")
    with pytest.raises(ValueError):
        ha.set_sensor("sensor.other", 1, {})
    ents = list_trackers(ha)
    assert [e["entity"] for e in ents] == ["person.alex"]
    sup = Supervisor(fake_core, token="t0k")
    assert sup.options() == {"routing": "off"}
    sup.set_options({"routing": "osrm"})
    assert FakeCore.calls[-1] == ("POST", "/addons/self/options", {"options": {"routing": "osrm"}})
