import gzip

import pytest

from worldmap import netmatch as N  # noqa: N812
from worldmap import routing


# ---- minimal protobuf / MVT writer for the tests
def varint(v):
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        out.append(b | (0x80 if v else 0))
        if not v:
            return bytes(out)


def field(num, wt, payload):
    key = varint((num << 3) | wt)
    if wt == 0:
        return key + varint(payload)
    return key + varint(len(payload)) + payload


def zz(v):
    return (v << 1) ^ (v >> 31)


def line_geom(pts):
    cmds, px, py = [], 0, 0
    cmds.append((1 & 7) | (1 << 3))
    cmds += [zz(pts[0][0] - px), zz(pts[0][1] - py)]
    px, py = pts[0]
    cmds.append((2 & 7) | ((len(pts) - 1) << 3))
    for x, y in pts[1:]:
        cmds += [zz(x - px), zz(y - py)]
        px, py = x, y
    return b"".join(varint(c) for c in cmds)


def tile(features, layer="transportation"):
    keys = [b"class"]
    values = sorted({c for c, _ in features})
    body = field(1, 2, layer.encode()) + field(5, 0, 4096)
    for c, pts in features:
        tags = varint(0) + varint(values.index(c))
        feat = field(2, 2, tags) + field(3, 0, 2) + field(4, 2, line_geom(pts))
        body += field(2, 2, feat)
    body += b"".join(field(3, 2, k) for k in keys)
    body += b"".join(field(4, 2, field(1, 2, v.encode())) for v in values)
    return field(3, 2, body)


def test_decode_mvt_lines_and_classes():
    z, x, y = 12, 2149, 1438
    data = tile([("rail", [(0, 0), (4096, 4096)]), ("path", [(0, 0), (10, 10)]), ("motorway", [(100, 100), (200, 100), (300, 300)])])
    lines = N.decode_mvt(gzip.compress(data), z, x, y)
    codes = sorted(c for c, _ in lines)
    assert codes == ["0", "a"]  # "path" is ignored
    rail = next(p for c, p in lines if c == "a")
    tx, ty = N.tile_xy(*rail[0], z)
    assert (tx, ty) == (x, y)
    assert N.decode_mvt(tile([("rail", [(0, 0), (5, 5)])], layer="water"), z, x, y) == []


def straight(a, b, n=20):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


@pytest.fixture
def network():
    # two rail lines that meet at a tile seam with a small gap, plus a road loop
    a, m, b = (47.00, 8.00), (47.00, 8.10), (47.05, 8.20)
    seam = (m[0] + 0.00008, m[1] + 0.00005)  # ~10 m off
    rail = [("a", straight(a, m)), ("a", straight(seam, b))]
    road = [("0", straight(a, (47.10, 8.10))), ("0", straight((47.10, 8.10), b))]
    return N.StaticLines(rail + road)


def test_graph_stitches_and_routes(network):
    m = N.Matcher(network)
    path = m.match("rail", (47.001, 8.0), (47.049, 8.2))
    assert isinstance(path, list) and len(path) > 10
    assert all(abs(la - 47.0) < 0.06 for la, _ in path)  # stays on the rail, not on the road loop
    road = m.match("road", (47.0, 8.0), (47.05, 8.2))
    assert isinstance(road, list) and max(la for la, _ in road) > 47.09  # follows the only road
    assert m.match("rail", (46.5, 7.0), (46.51, 7.01)) == "none"  # nothing nearby


def test_detours_are_rejected():
    # the only line makes a huge detour -> no straight line, no silly path
    detour = [("a", straight((47.0, 8.0), (47.5, 8.0)) + straight((47.5, 8.0), (47.0, 8.03))[1:])]
    m = N.Matcher(N.StaticLines(detour))
    assert m.match("rail", (47.0, 8.0), (47.0, 8.03)) == "none"


def test_fill_gaps_uses_matcher(db, network):
    db.add_points([(0, 47.001, 8.0, "Alex", "t", None, "in train"), (1800, 47.049, 8.2, "Alex", "t", None, "in train"),
                   (2400, 47.0491, 8.2001, "Alex", "t", None, None)])
    n = routing.fill_gaps(db, N.Matcher(network))
    segs = db.segments()
    assert n == 1 and segs[0]["mode"] == "rail" and len(segs[0]["geometry"]) > 10
    assert routing.fill_gaps(db, N.Matcher(network)) == 0


def test_tiles_for_bbox_and_region():
    assert len(N.tiles_for_bbox(47.0, 8.0, 47.0, 8.0)) == 1
    m = N.Matcher(N.StaticLines([]))
    small = m.region_bbox((47.01, 8.01), (47.02, 8.02))
    assert small[2] - small[0] == pytest.approx(N.REGION + 2 * N.MARGIN)


def test_openfreemap_download_and_cache(tmp_path):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    calls = []
    body = tile([("rail", [(0, 0), (4096, 4096)])])

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            calls.append(self.path)
            if self.path == "/planet":
                raw = json.dumps({"tiles": [f"http://127.0.0.1:{srv.server_address[1]}/t/{{z}}/{{x}}/{{y}}.pbf"]}).encode()
            elif self.path.endswith("/1/1.pbf"):
                self.send_response(404)
                self.end_headers()
                return
            else:
                raw = body
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        src = N.OpenFreeMapTiles(str(tmp_path), f"http://127.0.0.1:{srv.server_address[1]}/planet", min_interval=0, allow_http=True)
        got = src.lines(2149, 1438)
        assert got and got[0][0] == "a"
        assert src.lines(2149, 1438) == got and src.downloaded == 1  # second call from the disk cache
        assert src.lines(1, 1) == []  # 404 = empty tile
        strict = N.OpenFreeMapTiles(str(tmp_path / "s"), f"http://127.0.0.1:{srv.server_address[1]}/planet", min_interval=0)
        assert strict.lines(5, 5) is None  # plain http tile URLs are refused in production
    finally:
        srv.shutdown()


def test_tile_server_backoff(tmp_path, monkeypatch):
    import urllib.error

    from worldmap import netmatch
    src = netmatch.OpenFreeMapTiles(str(tmp_path), min_interval=0)
    src._url, src._url_t = "https://tiles.example/{z}/{x}/{y}.pbf", 9e18
    calls = []

    def boom(req, timeout=0):
        calls.append(1)
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)
    monkeypatch.setattr(netmatch.urllib.request, "urlopen", boom)
    assert src.lines(1, 2) is None and src.pause_until > 0 and "429" in src.last_error
    assert src.lines(1, 3) is None and len(calls) == 1  # paused: no second request


def test_forbidden_means_long_growing_pauses_and_a_real_user_agent(tmp_path, monkeypatch):
    import time
    import urllib.error

    from worldmap import __version__, netmatch
    src = netmatch.OpenFreeMapTiles(str(tmp_path), min_interval=0)
    src._url, src._url_t = "https://tiles.example/{z}/{x}/{y}.pbf", 9e18
    seen = []

    def no(req, timeout=0):
        seen.append(req.get_header("User-agent"))
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
    monkeypatch.setattr(netmatch.urllib.request, "urlopen", no)
    pauses = []
    for _ in range(4):
        src.pause_until = 0
        assert src.lines(1, 2) is None
        pauses.append(round(src.pause_until - time.monotonic()))
    assert pauses[0] >= 3590 and pauses[1] >= 6 * 3600 - 10 and pauses[2] >= 24 * 3600 - 10 and pauses[3] == pauses[2]
    assert __version__ in seen[0] and "github.com/magi1982/worldmap" in seen[0]
    assert N.Matcher(src).paused() > 3000


def test_fill_gaps_stops_while_the_map_server_pauses(db):
    class Paused(N.TileSource):
        calls = 0

        def lines(self, x, y):
            Paused.calls += 1
            return None

        def paused(self):
            return 600.0
    pts = []
    for i in range(50):  # 49 rail gaps of ~15 km
        pts.append((i * 1800, 47.0 + i * 0.13, 8.0, "Alex", "t", None, "in train"))
    db.add_points(pts)
    assert routing.fill_gaps(db, N.Matcher(Paused())) == 0 and Paused.calls == 0  # nothing asked, nothing looped


def test_version_matches_the_addon():
    import re
    from pathlib import Path

    from worldmap import __version__
    cfg = (Path(__file__).resolve().parents[1] / "worldmap" / "config.yaml").read_text(encoding="utf-8")
    assert re.search(r'^version: "([^"]+)"', cfg, re.M).group(1) == __version__


def test_every_user_sees_worldmap():
    from pathlib import Path

    import yaml
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "worldmap" / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["panel_admin"] is False and cfg["ingress"] is True
