"""Create a demo database with invented people and trips (for screenshots and local testing).

    python tools/demo.py /tmp/demo && WORLDMAP_DATA=/tmp/demo WORLDMAP_ALLOWED_IPS=127.0.0.1 \
        PYTHONPATH=worldmap/app python -m worldmap
"""
import json
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "worldmap" / "app"))
from worldmap.db import Database  # noqa: E402
from worldmap.engine import Engine  # noqa: E402
from worldmap.settings import from_dict  # noqa: E402

HOME = (47.05, 8.31)  # a public square in a Swiss city – not anybody's address
TZ = ZoneInfo("Europe/Zurich")
TRIPS = [  # (start, nights, lat, lon, who)
    ("2023-02-11", 6, 46.80, 9.84, "both"),
    ("2023-07-08", 13, 43.70, 7.26, "both"),
    ("2023-10-14", 3, 48.86, 2.35, "Alex"),
    ("2024-04-06", 2, 46.01, 8.96, "both"),
    ("2024-07-13", 12, 42.65, 18.09, "both"),
    ("2024-09-20", 1, 47.56, 7.59, "Sam"),
    ("2025-05-29", 3, 45.44, 12.33, "both"),
    ("2025-08-02", 14, 57.70, 11.95, "both"),
]


def main(out: str) -> None:
    Path(out).mkdir(parents=True, exist_ok=True)
    opts = {"persons": [{"entity": "person.alex", "label": "Alex"}, {"entity": "person.sam", "label": "Sam"}],
            "who_options": ["Paar", "Familie"], "home_lat": HOME[0], "home_lon": HOME[1], "routing": "off",
            "school_holidays": ["2023-07-08..2023-08-13", "2024-07-06..2024-08-11", "2025-07-05..2025-08-10"]}
    Path(out, "options.json").write_text(json.dumps(opts))
    db = Database(str(Path(out) / "worldmap.db"))
    rnd = random.Random(1)
    rows = []
    for start, nights, lat, lon, who in TRIPS:
        people = ["Alex", "Sam"] if who == "both" else [who]
        t0 = datetime.fromisoformat(start).replace(hour=7, tzinfo=TZ)
        for person in people:
            steps = 40
            for i in range(steps + 1):  # outbound
                f = i / steps
                la = HOME[0] + (lat - HOME[0]) * f + math.sin(f * math.pi) * 0.3
                lo = HOME[1] + (lon - HOME[1]) * f
                rows.append((int((t0 + timedelta(minutes=8 * i)).timestamp()), la, lo, person, "demo", 10, None))
            for d in range(nights + 1):
                for h in (9, 13, 18, 22):
                    ts = t0 + timedelta(days=d, hours=h - 7)
                    rows.append((int(ts.timestamp()), lat + rnd.uniform(-.08, .08), lon + rnd.uniform(-.08, .08), person, "demo", 20, None))
            back = t0 + timedelta(days=nights, hours=10)
            for i in range(steps + 1):
                f = i / steps
                rows.append((int((back + timedelta(minutes=8 * i)).timestamp()), lat + (HOME[0] - lat) * f, lon + (HOME[1] - lon) * f, person, "demo", 10, None))
    db.add_points(rows)
    db.upsert_trip({"start_date": "2009-10-03", "end_date": "2009-10-10", "destination": "Korsika", "country": "Frankreich",
                    "who": "Paar", "confidence": "bestätigt", "nights": 7, "lat": 42.15, "lon": 9.10, "radius_km": 60,
                    "approx": 1, "transport": "Auto · Schiff", "source": "manual", "reason": "von Hand erfasst", "locked": 1})
    eng = Engine(db, from_dict(opts), ha=type("NoHA", (), {"available": False})())
    print(eng.rebuild())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/worldmap-demo")
