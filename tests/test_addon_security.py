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
    assert "profile " in profile and "/data/{,**} rwk," in profile
    assert "deny mount," in profile and "capability sys_admin" not in profile
    assert "\nfile," not in profile and "  file,\n" not in profile  # no blanket file access
