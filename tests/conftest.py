"""Shared fixtures. All data is invented – fictional people "Alex" and "Sam"."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "worldmap" / "app"))

from worldmap.db import Database  # noqa: E402
from worldmap.engine import Engine  # noqa: E402
from worldmap.settings import from_dict  # noqa: E402

HOME = (47.0, 8.0)  # somewhere in central Switzerland, not a real address


class NoHA:
    available = False

    def state(self, *_):
        return None

    def history(self, *_):
        return []


@pytest.fixture
def db(tmp_path):
    d = Database(str(tmp_path / "t.db"))
    yield d
    d.close()


@pytest.fixture
def settings():
    return from_dict({
        "persons": [
            {"entity": "person.alex", "label": "Alex", "camera_models": "Phone A"},
            {"entity": "person.sam", "label": "Sam"},
        ],
        "who_options": ["Paar", "Familie"],
        "home_lat": HOME[0], "home_lon": HOME[1], "min_day_trip_km": 1, "route_service": "offline",
        "routing": "off",
        "school_holidays": ["2025-07-05..2025-08-10"],
    })


@pytest.fixture
def engine(db, settings):
    return Engine(db, settings, ha=NoHA())


@pytest.fixture(autouse=True)
def _no_supervisor(monkeypatch):
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    os.environ.pop("SUPERVISOR_TOKEN", None)


@pytest.fixture(autouse=True)
def _no_route_service(monkeypatch):
    """Tests never reach the online routing services."""
    from worldmap import routeservice

    def blocked(*a, **k):
        raise routeservice.RouteError("network blocked in tests")
    monkeypatch.setattr(routeservice, "_call", blocked)
