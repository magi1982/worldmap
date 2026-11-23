import gzip
import json
import threading
import urllib.error
import urllib.request

import pytest

from worldmap.server import csv_safe, serve, validate_connectors, validate_trip


@pytest.fixture
def server(engine):
    httpd = serve(engine, host="127.0.0.1", port=0, allowed_ips={"127.0.0.1"})
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", engine
    httpd.shutdown()


def call(url, method="GET", body=None, ctype="application/json", headers=None):
    data = body if isinstance(body, bytes) or body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", ctype)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return r.status, raw, r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


def js(raw):
    return json.loads(raw)


def test_static_and_headers(server):
    url, _ = server
    st, raw, h = call(url + "/")
    assert st == 200 and b"atlas.js" in raw  # the maps are the start page
    st, raw, h = call(url + "/app.html")
    assert st == 200 and b"Worldmap" in raw
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert h["X-Content-Type-Options"] == "nosniff"
    st, raw, h = call(url + "/base.json", headers={"Accept-Encoding": "gzip"})
    assert st == 200 and h["Content-Encoding"] == "gzip" and "land" in js(raw)
    for bad in ("/../config.yaml", "/static/../server.py", "/%2e%2e/server.py", "/server.py"):
        assert call(url + bad)[0] == 404


def test_only_ingress_ip_allowed(engine):
    httpd = serve(engine, host="127.0.0.1", port=0, allowed_ips={"172.30.32.2"})
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        assert call(f"http://127.0.0.1:{httpd.server_address[1]}/api/trips")[0] == 403
    finally:
        httpd.shutdown()


def test_trip_crud_and_validation(server):
    url, eng = server
    st, raw, _ = call(url + "/api/trips", "POST", {"start_date": "2011-10-01", "end_date": "2011-10-08",
                                                    "destination": "Korsika", "who": "Paar", "confidence": "bestätigt",
                                                    "lat": 42.15, "lon": 9.1, "radius_km": 60, "approx": True, "source": "manual"})
    assert st == 201
    t = js(raw)
    assert (t["nights"], t["locked"], t["approx"], t["radius_km"]) == (7, 1, 1, 60)
    st, raw, _ = call(url + f"/api/trips/{t['id']}", "PATCH", {"note": "<script>alert(1)</script>"})
    assert st == 200 and js(raw)["note"] == "<script>alert(1)</script>"  # stored verbatim, escaped by the UI
    bad = [
        {"start_date": "2011-10-08", "end_date": "2011-10-01"},
        {"start_date": "nope", "end_date": "2011-10-01"},
        {"start_date": "2011-10-01", "end_date": "2011-10-02", "confidence": "sure"},
        {"start_date": "2011-10-01", "end_date": "2011-10-02", "lat": 99},
        {"start_date": "2011-10-01", "end_date": "2011-10-02", "note": "x" * 2000},
        {"start_date": "2011-10-01", "end_date": "2011-10-02", "radius_km": -1},
    ]
    for b in bad:
        assert call(url + "/api/trips", "POST", b)[0] == 400, b
    assert call(url + f"/api/trips/{t['id']}", "PATCH", {"end_date": "2000-01-01"})[0] == 400
    assert call(url + "/api/trips", "POST", b"{}", ctype="text/plain")[0] == 400  # CSRF guard
    assert call(url + "/api/trips/9999", "PATCH", {"note": "x"})[0] == 404
    assert call(url + f"/api/trips/{t['id']}", "DELETE")[0] == 200
    assert call(url + f"/api/trips/{t['id']}", "DELETE")[0] == 404


def test_import_preview_then_import_and_questions(server):
    url, eng = server
    rows = ["time,lat,lon"]
    for d in range(10, 13):
        rows += [f"2025-07-{d}T08:00:00Z,46.0,7.0", f"2025-07-{d}T20:00:00Z,46.0,7.0"]
    body = ("\n".join(rows) + "\n").encode()
    st, raw, _ = call(url + "/api/import?dry_run=1&person=Alex", "POST", body, "application/octet-stream", {"X-Filename": "../../x.csv"})
    r = js(raw)
    assert st == 200 and r["points"] == 6 and r["format"] == "csv"
    assert eng.db.scalar("SELECT COUNT(*) FROM points") == 0
    st, raw, _ = call(url + "/api/import?person=Alex", "POST", body, "application/octet-stream", {"X-Filename": "../../x.csv"})
    r = js(raw)
    assert r["new_points"] == 6 and r["rebuild"]["trips_created"] == 1
    assert eng.db.query("SELECT filename FROM imports")[0]["filename"] == ".._.._x.csv"
    assert call(url + "/api/import?person=Mallory", "POST", body, "application/octet-stream")[0] == 400
    assert call(url + "/api/import", "POST", b"garbage", "application/octet-stream")[0] == 422
    qs = js(call(url + "/api/questions")[1])
    assert len(qs) == 1
    assert call(url + f"/api/questions/{qs[0]['id']}/answer", "POST", {"answer": "nope"})[0] == 400
    assert call(url + f"/api/questions/{qs[0]['id']}/answer", "POST", {"answer": "Alex"})[0] == 200
    assert js(call(url + "/api/questions")[1]) == []


def test_upload_limit(server):
    url, eng = server
    eng.s.max_upload_mb = 1
    try:
        st, _, _ = call(url + "/api/import", "POST", b"x" * (1024 * 1024 + 10), "application/octet-stream")
    except urllib.error.URLError:  # server may close before the client finished sending
        st = 413
    assert st == 413
    assert eng.db.scalar("SELECT COUNT(*) FROM imports") == 0


def test_export_csv_neutralises_formulas(server):
    url, eng = server
    eng.db.upsert_trip({"start_date": "2020-01-01", "end_date": "2020-01-02", "destination": "=HYPERLINK(\"http://evil\")"})
    st, raw, h = call(url + "/api/export.csv")
    assert st == 200 and "attachment" in h["Content-Disposition"]
    assert "'=HYPERLINK" in raw.decode("utf-8-sig")
    assert csv_safe("+1") == "'+1" and csv_safe("ok") == "ok" and csv_safe(None) == ""


def test_places_config_tracks_stats(server):
    url, _ = server
    places = js(call(url + "/api/places?q=korsi")[1])
    assert places[0]["name"] == "Korsika" and places[0]["radius_km"]
    assert js(call(url + "/api/places?q=a")[1]) == []
    cfg = js(call(url + "/api/config")[1])
    assert cfg["persons"] == ["Alex", "Sam"] and cfg["home"] == [47.0, 8.0]
    assert "lines" in js(call(url + "/api/tracks?tol=abc")[1])
    assert js(call(url + "/api/stats")[1])["trips"] == 0
    conn = js(call(url + "/api/connectors")[1])
    assert conn["editable"] is False and conn["persons"][0]["label"] == "Alex"
    assert call(url + "/api/connectors", "POST", {"routing": "off"})[0] == 503  # no Supervisor in tests


def test_validators():
    ok = validate_connectors({"persons": [{"entity": "person.alex", "label": "Alex"}, {"entity": "", "label": "Sam"}],
                              "owntracks": [{"user": "alex", "password": "secret-123", "label": "Alex"}],
                              "notify_service": "notify.mobile_app_x", "school_holidays": ["2025-07-05..2025-08-10"],
                              "unknown_key": "ignored"})
    assert "unknown_key" not in ok and ok["owntracks"][0]["user"] == "alex" and "entity" not in ok["persons"][1]
    for bad in ({"persons": [{"entity": "light.x", "label": "A"}]},
                {"persons": [{"entity": "person.a", "label": "<b>"}]},
                {"owntracks": [{"user": "Alex Smith", "password": "secret-123", "label": "Alex"}]},
                {"owntracks": [{"user": "alex", "password": "short", "label": "Alex"}]},
                {"notify_service": "shell_command.x"}, {"routing": "maybe"},
                {"school_holidays": ["July"]}):
        with pytest.raises(ValueError):
            validate_connectors(bad)
    with pytest.raises(ValueError):
        validate_trip([], partial=True)
    assert validate_trip({"start_date": "2020-01-01", "end_date": "2020-01-03"}, partial=False)["nights"] == 2


def test_settings_endpoints(server):
    url, eng = server
    # trip list pasted from Excel: duplicates are recognised
    rows = [["Von", "Bis", "Ziel", "Land", "Wer"], ["01.08.2019", "10.08.2019", "Korsika", "Frankreich", "Paar"],
            ["01.08.2019", "10.08.2019", "Korsika", "Frankreich", "Paar"]]
    st, raw, _ = call(url + "/api/trips/bulk", "POST", {"rows": rows})
    r = js(raw)
    assert st == 200 and r["trips_created"] == 1 and r["duplicates_in_file"] == 1
    assert js(call(url + "/api/trips/bulk", "POST", {"rows": rows})[1])["trips_updated"] == 1
    assert call(url + "/api/trips/bulk", "POST", {"rows": "nope"})[0] == 400
    assert call(url + "/api/trips/bulk", "POST", {"rows": [["a", "b"]]})[0] == 400
    # import of a trip list file
    csvb = b"Von;Bis;Hauptziel;Land;Wer\n2017-06-03;2017-06-12;Mallorca;Spanien;Familie\n"
    st, raw, _ = call(url + "/api/import?dry_run=1", "POST", csvb, "application/octet-stream")
    assert js(raw)["kind"] == "trips" and js(raw)["located"] == 1
    st, raw, _ = call(url + "/api/import", "POST", csvb, "application/octet-stream", {"X-Filename": "list.csv"})
    assert js(raw)["trips_created"] == 1
    imports = js(call(url + "/api/connectors")[1])["imports"]
    assert imports and call(url + f"/api/imports/{imports[0]['id']}", "DELETE")[0] == 200
    assert call(url + "/api/imports/99999", "DELETE")[0] == 404
    assert js(call(url + "/api/rules")[1]) == []
    assert js(call(url + "/api/notify_services")[1]) == []  # no Home Assistant in tests
    assert call(url + "/api/notify_test", "POST", {})[0] == 503
    assert call(url + "/api/sync/photos", "POST", {})[0] == 404


def test_validate_groups_home_work():
    ok = validate_connectors({"persons": [{"label": "Alex", "color": "#112233"}, {"label": "Sam"}],
                              "groups": [{"name": "Paar", "members": ["Alex", "Sam"], "extra": 30, "color": "#00FF00"}],
                              "home_lat": "47.1", "home_lon": 8.2, "home_radius_m": 99999, "work_lat": None,
                              "work_radius_m": 10, "show_work": True})
    assert ok["groups"] == [{"name": "Paar", "members": "Alex, Sam", "extra": 20, "color": "#00FF00"}]
    assert ok["who_options"] == ["Paar"] and ok["persons"][0]["color"] == "#112233"
    assert ok["home_lat"] == 47.1 and ok["home_radius_m"] == 5000 and ok["work_lat"] is None and ok["work_radius_m"] == 50
    assert ok["show_work"] is True
    for bad in ({"groups": [{"name": "<x>"}]}, {"groups": [{"name": "A", "members": ["<b>"]}]},
                {"groups": [{"name": "A", "color": "red"}]}, {"home_lat": 91}, {"work_lon": "x"},
                {"persons": [{"label": "Alex"}], "groups": [{"name": "Alex"}]}):
        with pytest.raises(ValueError):
            validate_connectors(bad)


def test_worldmap_package_roundtrip(server, tmp_path, monkeypatch):
    url, eng = server
    pkg = {"worldmap": 1, "persons": ["Alex", "Sam"], "groups": [{"name": "Grossfamilie", "members": ["Alex", "Nobody"], "extra": 2}],
           "trips": [{"start_date": "2024-07-13", "end_date": "2024-07-20", "destination": "Sample Bay", "who": "Grossfamilie",
                      "country": "Kroatien", "transport": "Flug · Auto", "lat": 42.6, "lon": 18.1},
                     {"start_date": "2024-07-13", "end_date": "2024-07-20", "destination": "Sample Bay", "who": "Grossfamilie"},
                     {"destination": "no date"}],
           "points": [[1720850000, 47.0, 8.0, 0, "google", "IN_TRAIN"], [1720853600, 47.1, 8.1, 1, "google", None],
                      [1720857200, 999, 8.1, 0], ["bad"], [1720860000, 47.2, 8.2, 7]]}
    body = gzip.compress(json.dumps(pkg).encode())
    st, raw, _ = call(url + "/api/import?dry_run=1", "POST", body, "application/octet-stream", {"X-Filename": "x.worldmap.json.gz"})
    r = js(raw)
    assert st == 200 and r["kind"] == "package" and r["trips"] == 2 and r["points"] == 3 and r["skipped"] == 1
    assert "Grossfamilie" in r["missing"] and any("could not be read" in w for w in r["warnings"])
    st, raw, _ = call(url + "/api/import", "POST", body, "application/octet-stream", {"X-Filename": "x.worldmap.json.gz"})
    r = js(raw)
    assert st == 200 and r["new_points"] == 3 and r["trips_created"] == 1 and r["duplicates_in_file"] == 1
    people = {p["person"] for p in eng.db.points()}
    assert people == {"Alex", "Sam", ""}
    st, raw, hdr = call(url + "/api/export.worldmap.json.gz")
    back = json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
    assert st == 200 and back["worldmap"] == 1 and len(back["points"]) == 3
    assert any(t["destination"] == "Sample Bay" and t["who"] == "Grossfamilie" for t in back["trips"])


def test_gzip_bomb_is_refused(monkeypatch):
    from worldmap import importers
    monkeypatch.setattr(importers, "MAX_UNZIPPED", 1000)
    with pytest.raises(importers.UserImportError):
        importers.detect_and_parse(gzip.compress(b" " * 5000), "x.gz")
