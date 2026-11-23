from pathlib import Path

import yaml

ADDON = Path(__file__).resolve().parents[1] / "worldmap"


def test_security_rating_settings():
    """Ingress (+2) and an own AppArmor profile (+1) give the highest rating Home Assistant hands out (8)."""
    cfg = yaml.safe_load((ADDON / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["ingress"] is True and cfg.get("apparmor", True) is not False
    for risky in ("host_network", "host_pid", "full_access", "docker_api", "privileged", "auth_api", "devices"):
        assert not cfg.get(risky), risky
    assert cfg.get("hassio_role", "default") == "default"
    profile = (ADDON / "apparmor.txt").read_text(encoding="utf-8")
    assert "profile " in profile and "/data/{,**} rwkm," in profile
    assert "deny mount," in profile and "capability sys_admin" not in profile
    assert "\nfile," not in profile and "  file,\n" not in profile  # no blanket file access


def test_owntracks_locks_out_password_guessing():
    from worldmap.owntracks import LOCK_AFTER, LOCK_FOR_S, Guard

    g = Guard()
    for _ in range(LOCK_AFTER - 1):
        g.fail("192.168.1.50", now=1000)
    assert not g.locked("192.168.1.50", now=1000)
    g.fail("192.168.1.50", now=1001)
    assert g.locked("192.168.1.50", now=1002)                  # locked …
    assert not g.locked("192.168.1.51", now=1002)              # … only that address
    assert not g.locked("192.168.1.50", now=1002 + LOCK_FOR_S)  # and only for a while
    g2 = Guard()
    for i in range(LOCK_AFTER * 2):                            # slow guessing spread over hours is not a burst
        g2.fail("10.0.0.9", now=i * 700)
    assert not g2.locked("10.0.0.9", now=LOCK_AFTER * 2 * 700)


def test_servers_close_stalled_connections():
    from worldmap import owntracks, server

    assert 0 < owntracks.make_handler(None).timeout <= 60
    for k in ("Permissions-Policy", "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy",
              "X-Content-Type-Options", "Content-Security-Policy"):
        assert k in server.SECURITY_HEADERS
    assert "frame-ancestors 'self'" in server.SECURITY_HEADERS["Content-Security-Policy"]


def test_xml_with_entities_is_refused_anywhere_in_the_file():
    import pytest as _pt

    from worldmap.importers.gpx import parse_xml

    late = "<!-- " + "x" * 70000 + " -->\n<!DOCTYPE gpx [<!ENTITY a 'b'>]><gpx></gpx>"
    with _pt.raises(ValueError):
        parse_xml(late)


def test_google_links_are_only_followed_over_https(monkeypatch):
    import urllib.request

    from worldmap import geosearch

    seen = []

    class FakeResp:
        def __init__(self, url):
            self.url = url

        def geturl(self):
            return self.url

    class Opener:
        def open(self, req, timeout=None):
            seen.append(req.full_url)
            return FakeResp("http://www.google.com/maps/place/x")   # a hop down to plain http

    monkeypatch.setattr(urllib.request, "build_opener", lambda *a: Opener())
    assert geosearch.resolve_gmaps("http://maps.app.goo.gl/abc") is None
    assert seen == ["https://maps.app.goo.gl/abc"]                    # upgraded before the first request
