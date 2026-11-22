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
"""

TRIP_FIELDS = (
    "start_date", "end_date", "destination", "country", "who", "confidence", "nights",
    "max_km", "lat", "lon", "transport", "reason", "note", "source", "locked", "radius_km", "approx",
)
CONFIDENCE = ("tief", "mittel", "hoch", "bestätigt")


class Database:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)

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
    def trips(self) -> list[dict]:
        return self.query("SELECT * FROM trips ORDER BY start_date, id")

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
                return int(cur.lastrowid)
        if not clean:
            return trip_id
        sets = ", ".join(f"{k} = ?" for k in clean)
        with self.tx() as c:
            c.execute(
                f"UPDATE trips SET {sets}, updated_at = strftime('%s','now') WHERE id = ?",  # nosec B608 - whitelisted
                (*clean.values(), trip_id),
            )
        return trip_id

    def delete_trip(self, trip_id: int) -> bool:
        with self.tx() as c:
            return c.execute("DELETE FROM trips WHERE id = ?", (trip_id,)).rowcount > 0

    # ---- questions ----------------------------------------------------
    def open_questions(self) -> list[dict]:
        rows = self.query(
            "SELECT q.*, t.start_date, t.end_date, t.destination FROM questions q"
            " JOIN trips t ON t.id = q.trip_id WHERE q.answer IS NULL ORDER BY t.start_date DESC"
        )
        for r in rows:
            r["options"] = json.loads(r["options"])
        return rows

    def add_question(self, trip_id: int, kind: str, text: str, options: list[str], suggestion: str | None) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO questions (trip_id, kind, text, options, suggestion) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (trip_id, kind) DO UPDATE SET text = excluded.text, options = excluded.options,"
                " suggestion = excluded.suggestion WHERE questions.answer IS NULL",
                (trip_id, kind, text, json.dumps(options, ensure_ascii=False), suggestion),
            )

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
