"""SQLite storage. All queries are parameterised."""
from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Any

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS points (
    id INTEGER PRIMARY KEY,
    ts INTEGER NOT NULL,              -- unix seconds, UTC
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    person TEXT NOT NULL DEFAULT '',  -- label of the tracked person ('' = unknown)
    source TEXT NOT NULL,             -- google, icloud, exif, gpx, ha, csv ...
    accuracy REAL,
    hint TEXT,                        -- e.g. photo folder name, camera model
    UNIQUE (ts, lat, lon, person)
);
CREATE INDEX IF NOT EXISTS points_ts ON points (ts);
CREATE INDEX IF NOT EXISTS points_person_ts ON points (person, ts);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY,
    start_date TEXT NOT NULL,         -- ISO date, local
    end_date TEXT NOT NULL,
    destination TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    who TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT 'tief',   -- tief | mittel | hoch | bestätigt
    nights INTEGER NOT NULL DEFAULT 0,
    max_km REAL,
    lat REAL,
    lon REAL,
    transport TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    radius_km REAL,                            -- estimated area for trips without GPS
    approx INTEGER NOT NULL DEFAULT 0,         -- 1 = dates/place are estimates
    locked INTEGER NOT NULL DEFAULT 0,         -- 1 = edited by a human, never overwritten
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
CREATE INDEX IF NOT EXISTS trips_start ON trips (start_date);

CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY,
    person TEXT NOT NULL,
    t0 INTEGER NOT NULL,
    t1 INTEGER NOT NULL,
    mode TEXT NOT NULL,               -- road | flight | straight
    geometry TEXT NOT NULL,           -- JSON [[lat, lon], ...]
    UNIQUE (person, t0, t1)
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,               -- who | merge | place
    text TEXT NOT NULL,
    options TEXT NOT NULL,            -- JSON list of strings
    suggestion TEXT,
    answer TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    answered_at INTEGER,
    notified INTEGER NOT NULL DEFAULT 0,
    UNIQUE (trip_id, kind)
);

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    format TEXT NOT NULL,
    points INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    radius_km REAL NOT NULL,
    days TEXT NOT NULL DEFAULT 'all',      -- all | weekday | weekend
    action TEXT NOT NULL,                  -- who | ignore
    value TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    hits INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
"""

# columns added after 0.1.0 – CREATE TABLE IF NOT EXISTS does not add them to old databases
MIGRATIONS = (
    ("trips", "radius_km", "REAL"),
    ("trips", "approx", "INTEGER NOT NULL DEFAULT 0"),
    ("trips", "status", "TEXT NOT NULL DEFAULT 'trip'"),
    ("questions", "trip_ids", "TEXT"),
    ("trips", "ap_from", "TEXT"),   # IATA code set by hand: airport the flights start from (home side)
    ("trips", "ap_to", "TEXT"),     # … and the airport at the destination
    ("trips", "legs", "TEXT"),      # JSON: stops of a trip in order [{name, country, lat, lon, transport}]
    ("trips", "date_prec", "TEXT NOT NULL DEFAULT 'day'"),  # day | month | year: how exactly the date is known
)

TRIP_FIELDS = (
    "start_date", "end_date", "destination", "country", "who", "confidence", "nights",
    "max_km", "lat", "lon", "transport", "reason", "note", "source", "locked", "radius_km", "approx", "status",
    "ap_from", "ap_to", "legs", "date_prec",
)
CONFIDENCE = ("tief", "mittel", "hoch", "bestätigt")
# writing one of these keeps the stations and the trip in step
STATION_KEYS = {"destination", "country", "lat", "lon", "transport", "legs"}


class Database:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)
        for table, col, decl in MIGRATIONS:
            cols = {r[1] for r in self._conn.execute(f"PRAGMA table_info({table})")}  # nosec B608 - constant names
            if col not in cols:
                self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")  # nosec B608 - constant names
        self._migrate_airport_stations()
        self.migrate_stations()
        self.migrate_stations_v3()
        self.migrate_date_prec()

    def migrate_date_prec(self) -> int:
        """0.14.0: trips from the "Reise von Hand" wizard that only knew the year or the month say so.

        The wizard stored a year as 15 July and a month as starting on the 1st, marked ``approx``.
        """
        with self._lock:
            if self._conn.execute("SELECT 1 FROM meta WHERE key='date_prec'").fetchone():
                return 0
            with self.tx() as c:
                hand = "approx = 1 AND source = 'manual' AND date_prec = 'day'"
                n = c.execute(f"UPDATE trips SET date_prec = 'year' WHERE {hand} AND substr(start_date, 6) = '07-15'").rowcount  # nosec B608 - constant
                n += c.execute(f"UPDATE trips SET date_prec = 'month' WHERE {hand} AND substr(start_date, 9) = '01'").rowcount  # nosec B608 - constant
                c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('date_prec', '1')")
            return n

    def _migrate_airport_stations(self) -> None:
        """0.11.0: the airport at the destination (``ap_to``) becomes an airport stop in ``legs``.

        "✈ HER, then 🚗 to the hotel" instead of a separate airport field. Runs once; nothing is lost: a trip without
        stops gets [airport, destination], a trip with stops gets the airport before its last flight's stop.
        The departure airport (``ap_from``) stays as it is ("Abflug ab").
        """
        with self._lock:
            done = self._conn.execute("SELECT value FROM meta WHERE key='airport_stations'").fetchone()
            if done:
                return
            from . import airports
            from .geo import haversine_km
            rows = self._conn.execute(
                "SELECT id, destination, country, lat, lon, transport, legs, ap_to FROM trips "
                "WHERE ap_to IS NOT NULL AND ap_to != ''").fetchall()
            self._conn.execute("BEGIN")
            try:
                for r in rows:
                    ap = airports.by_iata(r["ap_to"])
                    if not ap:
                        continue  # unknown code: leave it as it is
                    stop = {"name": ap[1], "country": "", "lat": ap[2], "lon": ap[3], "transport": "Flug", "ap": ap[0]}
                    try:
                        legs = json.loads(r["legs"]) if r["legs"] else []
                    except ValueError:
                        legs = []
                    if legs:
                        fly = [i for i, x in enumerate(legs) if "Flug" in str(x.get("transport") or "")]
                        if fly and not legs[fly[-1]].get("ap"):
                            i = fly[-1]
                            if haversine_km(legs[i]["lat"], legs[i]["lon"], ap[2], ap[3]) < 8:
                                legs[i]["ap"], legs[i]["lat"], legs[i]["lon"] = ap[0], ap[2], ap[3]
                            else:
                                legs[i] = {**legs[i], "transport": "Auto"}
                                legs.insert(i, stop)
                    else:
                        legs = [stop]
                        if r["lat"] is not None and r["lon"] is not None \
                                and haversine_km(r["lat"], r["lon"], ap[2], ap[3]) >= 8:
                            legs.append({"name": (r["destination"] or "Ziel")[:80], "country": r["country"] or "",
                                         "lat": r["lat"], "lon": r["lon"], "transport": "Auto"})
                    self._conn.execute("UPDATE trips SET legs=?, ap_to=NULL WHERE id=?",
                                       (json.dumps(legs[:20], ensure_ascii=False), r["id"]))
                self._conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('airport_stations', '1')")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            self._conn.execute("COMMIT")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                yield self._conn
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            self._conn.execute("COMMIT")

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, tuple(params))]

    def scalar(self, sql: str, params: Iterable[Any] = ()) -> Any:
        with self._lock:
            row = self._conn.execute(sql, tuple(params)).fetchone()
            return row[0] if row else None

    # ---- points -------------------------------------------------------
    def add_points(self, rows: Iterable[tuple]) -> int:
        """rows: (ts, lat, lon, person, source, accuracy, hint). Returns new rows."""
        with self.tx() as c:
            before = c.total_changes
            c.executemany(
                "INSERT OR IGNORE INTO points (ts, lat, lon, person, source, accuracy, hint)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                ((int(t), round(float(a), 6), round(float(o), 6), p or "", s, acc, h)
                 for t, a, o, p, s, acc, h in rows),
            )
            return c.total_changes - before

    def points(self, t0: int | None = None, t1: int | None = None, person: str | None = None) -> list[dict]:
        sql, args = "SELECT ts, lat, lon, person, source, hint FROM points WHERE 1=1", []
        if t0 is not None:
            sql += " AND ts >= ?"
            args.append(t0)
        if t1 is not None:
            sql += " AND ts < ?"
            args.append(t1)
        if person is not None:
            sql += " AND person = ?"
            args.append(person)
        return self.query(sql + " ORDER BY person, ts", args)

    # ---- trips --------------------------------------------------------
    def trips(self, include_ignored: bool = False) -> list[dict]:
        if include_ignored:
            return self.query("SELECT * FROM trips ORDER BY start_date, id")
        return self.query("SELECT * FROM trips WHERE status != 'ignored' ORDER BY start_date, id")

    def trip(self, trip_id: int) -> dict | None:
        r = self.query("SELECT * FROM trips WHERE id = ?", (trip_id,))
        return r[0] if r else None

    def upsert_trip(self, data: dict, trip_id: int | None = None) -> int:
        clean = {k: data[k] for k in TRIP_FIELDS if k in data}
        if trip_id is None:
            cols = ", ".join(clean)
            marks = ", ".join("?" for _ in clean)
            with self.tx() as c:
                cur = c.execute(f"INSERT INTO trips ({cols}) VALUES ({marks})", tuple(clean.values()))  # nosec B608 - column names are whitelisted
                trip_id = int(cur.lastrowid)
                self._sync_stations(c, trip_id, set(clean))
            return trip_id
        if not clean:
            return trip_id
        sets = ", ".join(f"{k} = ?" for k in clean)
        with self.tx() as c:
            c.execute(
                f"UPDATE trips SET {sets}, updated_at = strftime('%s','now') WHERE id = ?",  # nosec B608 - whitelisted
                (*clean.values(), trip_id),
            )
            self._sync_stations(c, trip_id, set(clean))
        return trip_id

    @staticmethod
    def _sync_stations(c, trip_id: int, changed: set) -> None:
        """Where a trip went is its stations; country, transport and position of the trip follow from them.

        * no stations yet (import, Excel, GPS, old data): one station from destination/country/position/transport,
          marked ``auto`` – it may be replaced by better data later, a station edited by hand never is
        * one station and the trip's position, country or transport was written (an answer, a GPS refresh):
          the station follows
        * then country, transport and position of the trip are taken from the stations
        """
        if not changed & STATION_KEYS:
            return
        r = c.execute("SELECT destination, country, lat, lon, transport, legs FROM trips WHERE id = ?",
                      (trip_id,)).fetchone()
        if not r:
            return
        try:
            legs = json.loads(r["legs"]) if r["legs"] else []
        except ValueError:
            legs = []
        if not isinstance(legs, list):
            legs = []
        if not legs:
            if r["lat"] is None and not (r["destination"] or r["country"]):
                return
            from . import stations  # "Flug via Dubai · Wasserflugzeug" → ✈ DXB → ✈ MLE → 🛩 resort

            legs = stations.from_fields(r["destination"] or "", r["country"] or "", r["lat"], r["lon"], r["transport"])
        elif len(legs) == 1 and "legs" not in changed:
            st = legs[0]
            if changed & {"lat", "lon"} and r["lat"] is not None:
                st["lat"], st["lon"] = r["lat"], r["lon"]
            if "country" in changed and r["country"]:
                st["country"] = r["country"]
            if "transport" in changed:
                from . import stations

                st["transport"] = " · ".join(stations.words(r["transport"]))
        countries: list = []
        for x in legs:
            for cc in str(x.get("country") or "").split(" · "):
                if cc and cc not in countries:
                    countries.append(cc)
        transport: list = []
        for x in legs:
            for part in str(x.get("transport") or "").split("·"):
                part = part.strip()
                if part and part not in transport:
                    transport.append(part)
        placed = [x for x in legs if x.get("lat") is not None and x.get("lon") is not None]
        spots = [x for x in placed if not x.get("ap")]
        main = (max(spots, key=lambda x: x.get("n") or 0) if spots and any(x.get("n") for x in spots)  # most nights
                else spots[0] if spots else placed[0] if placed else None)
        lat, lon = (main["lat"], main["lon"]) if main else (None, None)
        if "legs" in changed and changed & {"lat", "lon"} and r["lat"] is not None:
            lat, lon = r["lat"], r["lon"]  # written together with the stops: the caller knows the main place
        if not main and len(legs) == 1 and "legs" not in changed:
            lat, lon = r["lat"], r["lon"]
        country = " · ".join(countries) or (r["country"] or "")
        if "legs" in changed and "country" in changed and r["country"]:
            country = r["country"]  # written together with the stops: the trip's own country wins
        c.execute("UPDATE trips SET legs = ?, country = ?, transport = ?, lat = ?, lon = ? WHERE id = ?",
                  (json.dumps(legs[:20], ensure_ascii=False), country,
                   r["transport"] if "legs" in changed and "transport" in changed and r["transport"]
                   else " · ".join(transport) or (r["transport"] or ""), lat, lon, trip_id))

    def migrate_stations_v3(self) -> int:
        """0.12.2: stations made from old fields again, with clean transport words and stopovers ("via Dubai")."""
        with self._lock:
            if self._conn.execute("SELECT 1 FROM meta WHERE key='stations_v3'").fetchone():
                return 0
            n = 0
            with self.tx() as c:
                for r in c.execute("SELECT id, legs FROM trips").fetchall():
                    try:
                        legs = json.loads(r["legs"]) if r["legs"] else []
                    except ValueError:
                        continue
                    if len(legs) == 1 and legs[0].get("auto") and not legs[0].get("gps"):
                        c.execute("UPDATE trips SET legs = '' WHERE id = ?", (r["id"],))
                        self._sync_stations(c, r["id"], {"legs"})  # transport words from the new stations
                        n += 1
                c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('stations_v3', '1')")
            return n

    def migrate_stations(self) -> int:
        """0.12.0: every trip gets stations (its old destination becomes its name and its first station). Once."""
        with self._lock:
            if self._conn.execute("SELECT 1 FROM meta WHERE key='stations_v2'").fetchone():
                return 0
            ids = [r[0] for r in self._conn.execute("SELECT id FROM trips")]
            with self.tx() as c:
                for i in ids:
                    self._sync_stations(c, i, set(STATION_KEYS))
                c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('stations_v2', '1')")
            return len(ids)

    def delete_trip(self, trip_id: int) -> bool:
        with self.tx() as c:
            return c.execute("DELETE FROM trips WHERE id = ?", (trip_id,)).rowcount > 0

    # ---- questions ----------------------------------------------------
    def open_questions(self) -> list[dict]:
        rows = self.query(
            "SELECT q.*, t.start_date, t.end_date, t.destination, t.max_km FROM questions q"
            " JOIN trips t ON t.id = q.trip_id WHERE q.answer IS NULL"
            " ORDER BY (q.trip_ids IS NOT NULL) DESC, t.max_km DESC, t.start_date DESC"
        )
        for r in rows:
            r["options"] = json.loads(r["options"])
            r["trip_ids"] = json.loads(r["trip_ids"]) if r.get("trip_ids") else [r["trip_id"]]
        return rows

    def add_question(self, trip_id: int, kind: str, text: str, options: list[str], suggestion: str | None,
                     trip_ids: list[int] | None = None, notified: int = 0) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO questions (trip_id, kind, text, options, suggestion, trip_ids, notified)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (trip_id, kind) DO UPDATE SET text = excluded.text, options = excluded.options,"
                " suggestion = excluded.suggestion, trip_ids = excluded.trip_ids WHERE questions.answer IS NULL",
                (trip_id, kind, text, json.dumps(options, ensure_ascii=False), suggestion,
                 json.dumps(trip_ids) if trip_ids else None, notified),
            )

    def clear_open_questions(self) -> set:
        """Remove unanswered questions (they are rebuilt); returns keys that were already notified."""
        rows = self.query("SELECT kind, trip_ids, trip_id FROM questions WHERE answer IS NULL AND notified = 1")
        with self.tx() as c:
            c.execute("DELETE FROM questions WHERE answer IS NULL")
        return {(r["kind"], r["trip_ids"] or str(r["trip_id"])) for r in rows}

    # ---- rules ---------------------------------------------------------
    def rules(self) -> list[dict]:
        return self.query("SELECT * FROM rules ORDER BY created_at DESC")

    def add_rule(self, lat, lon, radius_km, days, action, value, label) -> int:
        with self.tx() as c:
            cur = c.execute("INSERT INTO rules (lat, lon, radius_km, days, action, value, label) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (lat, lon, radius_km, days, action, value, label))
            return int(cur.lastrowid)

    def delete_rule(self, rid: int) -> bool:
        with self.tx() as c:
            return c.execute("DELETE FROM rules WHERE id = ?", (rid,)).rowcount > 0

    def answer_question(self, qid: int, answer: str) -> dict | None:
        rows = self.query("SELECT * FROM questions WHERE id = ?", (qid,))
        if not rows:
            return None
        q = rows[0]
        options = json.loads(q["options"])
        if answer not in options:
            raise ValueError("answer is not one of the options")
        with self.tx() as c:
            c.execute("UPDATE questions SET answer = ?, answered_at = strftime('%s','now') WHERE id = ?", (answer, qid))
            if q["kind"] == "who":
                c.execute(
                    "UPDATE trips SET who = ?, confidence = 'bestätigt', locked = 1,"
                    " updated_at = strftime('%s','now') WHERE id = ?",
                    (answer, q["trip_id"]),
                )
        return q

    # ---- segments / meta ---------------------------------------------
    def add_segment(self, person: str, t0: int, t1: int, mode: str, geometry: list) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT OR REPLACE INTO segments (person, t0, t1, mode, geometry) VALUES (?, ?, ?, ?, ?)",
                (person, t0, t1, mode, json.dumps(geometry)),
            )

    def segments(self) -> list[dict]:
        rows = self.query("SELECT person, t0, t1, mode, geometry FROM segments ORDER BY person, t0")
        for r in rows:
            r["geometry"] = json.loads(r["geometry"])
        return rows

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        v = self.scalar("SELECT value FROM meta WHERE key = ?", (key,))
        return default if v is None else v

    def set_meta(self, key: str, value: str) -> None:
        with self.tx() as c:
            c.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
