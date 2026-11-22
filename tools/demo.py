"""Create a demo database with invented people and trips (for screenshots and local testing).

    python tools/demo.py /tmp/demo && WORLDMAP_DATA=/tmp/demo WORLDMAP_ALLOWED_IPS=127.0.0.1 \
        PYTHONPATH=worldmap/app python -m worldmap

Everything here is invented: the people "Alex" and "Sam", their home (a public square in a
Swiss city), work place and trips.
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

HOME = (47.0505, 8.3093)   # public square, Lucerne
WORK = (47.3779, 8.5403)   # main station area, Zurich
TZ = ZoneInfo("Europe/Zurich")
AIRPORT = (47.4582, 8.5555)
# (start, nights, lat, lon, who, how)
TRIPS = [
    ("2023-02-11", 6, 46.80, 9.84, "both", "car"),
    ("2023-07-08", 13, 43.70, 7.26, "both", "car"),
    ("2023-10-14", 3, 48.86, 2.35, "Alex", "train"),
    ("2024-04-06", 2, 46.01, 8.96, "both", "train"),
    ("2024-07-13", 12, 42.65, 18.09, "both", "fly"),
    ("2024-09-20", 1, 47.56, 7.59, "Sam", "train"),
    ("2025-05-29", 3, 45.44, 12.33, "both", "car"),
    ("2025-08-02", 14, 57.70, 11.95, "both", "fly"),
]
OUTINGS = [(46.9480, 7.4474), (46.6863, 7.8632), (47.5596, 7.5886), (46.8508, 9.5320), (47.4245, 9.3767), (46.1670, 8.7943)]
AIRPORTS = {(42.65, 18.09): (42.5614, 18.2682), (57.70, 11.95): (57.6628, 12.2798)}


def path(a, b, t0, minutes, step, rnd, wiggle=0.15, hint=None):
    """Points from a to b along a gently curved line."""
    n = max(2, int(minutes / step))
    dx, dy = b[0] - a[0], b[1] - a[1]
    bend = rnd.uniform(-wiggle, wiggle)
    out = []
    for i in range(n + 1):
        f = i / n
        off = math.sin(f * math.pi) * bend + math.sin(f * math.pi * 3) * bend * 0.25
        lat = a[0] + dx * f - dy * off
        lon = a[1] + dy * f + dx * off
        out.append((int((t0 + timedelta(minutes=f * minutes)).timestamp()), lat, lon, hint))
    return out


def main(out: str) -> None:
    Path(out).mkdir(parents=True, exist_ok=True)
    opts = {"persons": [{"entity": "person.alex", "label": "Alex"}, {"entity": "person.sam", "label": "Sam"}],
            "who_options": ["Paar", "Familie"], "home_lat": HOME[0], "home_lon": HOME[1], "routing": "off",
            "school_holidays": ["2023-07-08..2023-08-13", "2024-07-06..2024-08-11", "2025-07-05..2025-08-10"]}
    Path(out, "options.json").write_text(json.dumps(opts))
    db = Database(str(Path(out) / "worldmap.db"))
    rnd = random.Random(7)
    rows = []
    trip_days = set()
    for start, nights, *_ in TRIPS:
        d0 = datetime.fromisoformat(start)
        for i in range(nights + 1):
            trip_days.add((d0 + timedelta(days=i)).date())

    def add(person, pts):
        rows.extend((ts, la, lo, person, "demo", 15, h) for ts, la, lo, h in pts)

    day = datetime(2023, 1, 2, tzinfo=TZ)
    while day.date() <= datetime(2025, 10, 31).date():
        if day.date() not in trip_days:
            for person in ("Alex", "Sam"):
                add(person, [(int(day.replace(hour=7).timestamp()), HOME[0], HOME[1], None)])
                if person == "Alex" and day.weekday() < 5:
                    add(person, path(HOME, WORK, day.replace(hour=7, minute=10), 55, 4, rnd, 0.08, "IN_TRAIN"))
                    add(person, path(WORK, (WORK[0] + .004, WORK[1] - .006), day.replace(hour=12), 15, 3, rnd, .3, "WALKING"))
                    add(person, path(WORK, HOME, day.replace(hour=17, minute=30), 55, 4, rnd, 0.08, "IN_TRAIN"))
                elif day.weekday() >= 5 and rnd.random() < .12:
                    dest = rnd.choice(OUTINGS)
                    add(person, path(HOME, dest, day.replace(hour=10), 70, 5, rnd, .2, "IN_PASSENGER_VEHICLE"))
                    add(person, path(dest, HOME, day.replace(hour=16), 70, 5, rnd, .2, "IN_PASSENGER_VEHICLE"))
                elif rnd.random() < .5:
                    shop = (HOME[0] + rnd.uniform(-.03, .03), HOME[1] + rnd.uniform(-.04, .04))
                    add(person, path(HOME, shop, day.replace(hour=15), 20, 2, rnd, .3, "WALKING"))
                add(person, [(int(day.replace(hour=22).timestamp()), HOME[0], HOME[1], None)])
        day += timedelta(days=1)

    for start, nights, lat, lon, who, how in TRIPS:
        people = ["Alex", "Sam"] if who == "both" else [who]
        t0 = datetime.fromisoformat(start).replace(hour=7, tzinfo=TZ)
        back = t0 + timedelta(days=nights, hours=3)
        dest = (lat, lon)
        for person in people:
            if how == "fly":
                ap = AIRPORTS[dest]
                add(person, path(HOME, AIRPORT, t0, 60, 5, rnd, .05, "IN_PASSENGER_VEHICLE"))
                add(person, [(int((t0 + timedelta(hours=4)).timestamp()), ap[0], ap[1], None)])
                add(person, path(ap, dest, t0 + timedelta(hours=4, minutes=30), 40, 5, rnd, .1, "IN_PASSENGER_VEHICLE"))
            else:
                hint = "IN_TRAIN" if how == "train" else "IN_PASSENGER_VEHICLE"
                hours = max(1.5, math.dist(HOME, dest) * 1.4)
                add(person, path(HOME, dest, t0, hours * 60, 6, rnd, .12, hint))
            for d in range(nights + 1):
                for h in (9, 13, 18, 22):
                    ts = t0 + timedelta(days=d, hours=h - 7)
                    if ts < back:
                        add(person, [(int(ts.timestamp()), lat + rnd.uniform(-.05, .05), lon + rnd.uniform(-.05, .05), None)])
            if how == "fly":
                ap = AIRPORTS[dest]
                add(person, path(dest, ap, back, 40, 5, rnd, .1, "IN_PASSENGER_VEHICLE"))
                add(person, [(int((back + timedelta(hours=4)).timestamp()), AIRPORT[0], AIRPORT[1], None)])
                add(person, path(AIRPORT, HOME, back + timedelta(hours=4, minutes=20), 60, 5, rnd, .05, "IN_PASSENGER_VEHICLE"))
            else:
                hours = max(1.5, math.dist(HOME, dest) * 1.4)
                add(person, path(dest, HOME, back, hours * 60, 6, rnd, .12, "IN_TRAIN" if how == "train" else "IN_PASSENGER_VEHICLE"))
    db.add_points(rows)
    db.upsert_trip({"start_date": "2009-10-03", "end_date": "2009-10-10", "destination": "Korsika", "country": "Frankreich",
                    "who": "Paar", "confidence": "bestätigt", "nights": 7, "lat": 42.15, "lon": 9.10, "radius_km": 60,
                    "approx": 1, "transport": "Auto · Schiff", "source": "manual", "reason": "von Hand erfasst", "locked": 1})
    db.upsert_trip({"start_date": "2012-06-20", "end_date": "2012-07-04", "destination": "Kreta", "country": "Griechenland",
                    "who": "Paar", "confidence": "bestätigt", "nights": 14, "lat": 35.24, "lon": 24.90, "radius_km": 40,
                    "approx": 1, "transport": "Flug", "source": "manual", "reason": "von Hand erfasst", "locked": 1})
    eng = Engine(db, from_dict(opts), ha=type("NoHA", (), {"available": False})())
    print(len(rows), "points", eng.rebuild())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/worldmap-demo")
