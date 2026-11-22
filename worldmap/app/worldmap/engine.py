"""Orchestration: rebuild trips, ask questions, poll HA, notify, publish sensors."""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from . import photos, places, questions, routing, trips
from .db import Database
from .geo import haversine_km, simplify
from .ha import HomeAssistant, position_from_state
from .settings import Settings
from .timeparse import local_date

log = logging.getLogger(__name__)


class Engine:
    def __init__(self, db: Database, settings: Settings, ha: HomeAssistant | None = None):
        self.db = db
        self.s = settings
        self.ha = ha or HomeAssistant()
        self._lock = threading.Lock()
        self._track_cache: dict = {}
        self.version = 0
        self.home: tuple[float, float] | None = None
        self.ingress_url = "/hassio/ingress/worldmap"
        if settings.home_lat is not None and settings.home_lon is not None:
            self.home = (float(settings.home_lat), float(settings.home_lon))

    # ---------------------------------------------------------------- home
    def resolve_home(self) -> tuple[float, float] | None:
        if self.home:
            return self.home
        if self.ha.available:
            st = self.ha.state(self.s.home_zone)
            if st and st.get("attributes", {}).get("latitude") is not None:
                a = st["attributes"]
                self.home = (float(a["latitude"]), float(a["longitude"]))
        return self.home

    # --------------------------------------------------------------- import
    def import_points(self, rows) -> int:
        n = self.db.add_points(rows)
        if n:
            self.touch()
        return n

    def touch(self) -> None:
        self.version += 1
        self._track_cache.clear()

    # ---------------------------------------------------------------- trips
    def rebuild(self) -> dict:
        """Detect trips from points and (re)create open questions. Locked trips stay untouched."""
        home = self.resolve_home()
        if not home:
            return {"error": "home position unknown – set home_lat/home_lon or a zone"}
        with self._lock:
            pts = self.db.points()
            tz = self.s.timezone
            days = trips.days_away(pts, home, self.s.min_trip_km, tz)
            cands = trips.group_trips(days)
            presence = self._presence(pts, home, tz)
            holidays = questions.parse_ranges(self.s.school_holidays)
            existing = self.db.trips()
            created = updated = asked = 0
            labels = set(self.s.labels)
            for c in cands:
                present = {p for p in c.persons if p in labels}
                match = next((t for t in existing if not (c.end < t["start_date"] or c.start > t["end_date"])), None)
                if match and match["locked"]:
                    continue
                name, country = places.describe(c.lat, c.lon)
                at_home = {p for p in labels - present
                           if all(presence.get((p, d)) == "home" for d in self._days(c.start, c.end))}
                overlap = trips.overlap_share(c, *sorted(present)[:2]) if len(present) >= 2 else 0.0
                hol = questions.in_holidays(c.start, c.end, holidays)
                sug = questions.suggest(present, labels, at_home, overlap, hol,
                                        questions.is_weekend_trip(c.start, c.end), c.hints,
                                        self.s.who_options, self.s.hint_keywords)
                data = {
                    "start_date": c.start, "end_date": c.end, "destination": name, "country": country,
                    "who": sug.who, "confidence": sug.confidence, "nights": c.nights,
                    "max_km": round(c.max_km, 1), "lat": c.lat, "lon": c.lon,
                    "reason": sug.reason, "source": "auto",
                }
                if match:
                    tid = self.db.upsert_trip(data, match["id"])
                    updated += 1
                else:
                    tid = self.db.upsert_trip(data)
                    created += 1
                if questions.needs_question(sug, self.s.ask_below):
                    trip = self.db.trip(tid)
                    opts = questions.options(self.s.labels, self.s.who_options)
                    if sug.who and sug.who not in opts:
                        opts.append(sug.who)
                    self.db.add_question(tid, "who", questions.question_text(trip, sug, hol, present), opts, sug.who or None)
                    asked += 1
            self.touch()
        self.publish_sensors()
        return {"trips_created": created, "trips_updated": updated, "questions": asked, "candidates": len(cands)}

    @staticmethod
    def _days(start: str, end: str):
        d = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end)
        while d <= e:
            yield d.date().isoformat()
            d += timedelta(days=1)

    def _presence(self, pts, home, tz) -> dict:
        """(person, day) -> 'home' | 'away' from the points of that day."""
        out: dict = {}
        for p in pts:
            key = (p["person"], local_date(p["ts"], tz))
            far = haversine_km(home[0], home[1], p["lat"], p["lon"]) >= self.s.min_trip_km
            if far:
                out[key] = "away"
            else:
                out.setdefault(key, "home")
        return out

    # ---------------------------------------------------------------- stats
    def stats(self) -> dict:
        per_year: dict = defaultdict(float)
        prev = None
        for p in self.db.query("SELECT ts, lat, lon, person FROM points ORDER BY person, ts"):
            if prev and prev["person"] == p["person"] and p["ts"] - prev["ts"] < 12 * 3600:
                d = haversine_km(prev["lat"], prev["lon"], p["lat"], p["lon"])
                if d < 1500:
                    per_year[local_date(p["ts"], self.s.timezone)[:4]] += d
            prev = p
        trips_ = self.db.trips()
        countries = sorted({t["country"] for t in trips_ if t["country"]})
        return {
            "points": self.db.scalar("SELECT COUNT(*) FROM points"),
            "trips": len(trips_),
            "open_questions": len(self.db.open_questions()),
            "countries": countries,
            "km_per_year": {k: round(v) for k, v in sorted(per_year.items())},
            "km_total": round(sum(per_year.values())),
            "home_known": self.home is not None,
        }

    def publish_sensors(self) -> None:
        if not self.ha.available:
            return
        st = self.stats()
        year = str(datetime.now().year)
        self.ha.set_sensor("sensor.worldmap_km_this_year", st["km_per_year"].get(year, 0),
                           {"unit_of_measurement": "km", "friendly_name": "Worldmap km this year", "icon": "mdi:map-marker-distance"})
        self.ha.set_sensor("sensor.worldmap_trips", st["trips"], {"friendly_name": "Worldmap trips", "icon": "mdi:airplane"})
        self.ha.set_sensor("sensor.worldmap_open_questions", st["open_questions"],
                           {"friendly_name": "Worldmap open questions", "icon": "mdi:help-circle"})
        last = self.db.query("SELECT destination, country, start_date, end_date, who FROM trips"
                             " ORDER BY end_date DESC LIMIT 1")
        if last:
            t = last[0]
            self.ha.set_sensor("sensor.worldmap_last_trip", t["destination"][:250] or "–",
                               {"friendly_name": "Worldmap last trip", "icon": "mdi:map-marker-radius", **t})
        self.ha.set_sensor("sensor.worldmap_countries", len(st["countries"]),
                           {"friendly_name": "Worldmap countries", "icon": "mdi:earth", "countries": st["countries"]})

    # --------------------------------------------------------------- tracks
    def tracks(self, tolerance: float) -> dict:
        key = (round(tolerance, 6), self.version)
        if key in self._track_cache:
            return self._track_cache[key]
        lines: dict = defaultdict(list)
        segs = {(s["person"], s["t0"], s["t1"]): s for s in self.db.segments()}
        tz = self.s.timezone
        cur, prev, key = [], None, None
        years: dict = {}
        for p in self.db.query("SELECT ts, lat, lon, person FROM points ORDER BY person, ts"):
            hb = p["ts"] // 3600
            if hb not in years:
                years[hb] = local_date(p["ts"], tz)[:4]
            k = f"{p['person'] or '?'}|{years[hb]}"
            if prev and k == key:
                seg = segs.get((p["person"], prev["ts"], p["ts"]))
                if seg:
                    cur.extend(seg["geometry"][1:])
                elif (routing.classify_gap(prev, p) is None
                      and haversine_km(prev["lat"], prev["lon"], p["lat"], p["lon"]) > routing.MIN_GAP_KM):
                    self._flush(lines, key, cur, tolerance)
                    cur = []
                cur.append([p["lat"], p["lon"]])
            else:
                if prev:
                    self._flush(lines, key, cur, tolerance)
                cur, key = [[p["lat"], p["lon"]]], k
            prev = p
        if prev:
            self._flush(lines, key, cur, tolerance)
        flights = [{"person": s["person"], "year": local_date(s["t0"], tz)[:4], "line": s["geometry"]}
                   for s in segs.values() if s["mode"] == "flight"]
        out = {"version": self.version, "lines": dict(lines), "flights": flights}
        if len(self._track_cache) > 8:
            self._track_cache.clear()
        self._track_cache[key] = out
        return out

    @staticmethod
    def _flush(lines, key, cur, tol) -> None:
        if len(cur) >= 2:
            lines[key].append([[round(a, 5), round(b, 5)] for a, b in simplify(cur, tol)])

    # ------------------------------------------------------------- HA live
    def poll_once(self) -> int:
        rows = []
        for p in self.s.persons:
            st = self.ha.state(p["entity"])
            pos = position_from_state(st)
            if pos:
                lat, lon, acc, ts = pos
                rows.append((ts, lat, lon, p["label"], "ha", acc, None))
        return self.import_points(rows)

    def backfill_history(self) -> int:
        since = datetime.now(UTC) - timedelta(days=self.s.history_days_on_start)
        rows = []
        for p in self.s.persons:
            for st in self.ha.history(p["entity"], since):
                pos = position_from_state(st)
                if pos:
                    lat, lon, acc, ts = pos
                    rows.append((ts, lat, lon, p["label"], "ha", acc, None))
        return self.import_points(rows)

    def scan_photos(self) -> int:
        since = float(self.db.get_meta("photo_scan_mtime", "0") or 0)
        started = time.time()
        n = self.import_points(photos.scan(self.s.photo_folders, since, self.s.persons, self.s.timezone))
        self.db.set_meta("photo_scan_mtime", str(started))
        return n

    def notify_open(self, ingress_url: str | None = None) -> int:
        ingress_url = ingress_url or self.ingress_url
        if self.s.notify_mode == "off" or not self.ha.available:
            return 0
        qs = [q for q in self.db.open_questions() if not q["notified"]]
        if not qs:
            return 0
        if self.s.notify_mode != "instant":
            last = float(self.db.get_meta("last_notify", "0") or 0)
            period = 86400 if self.s.notify_mode == "daily" else 7 * 86400
            if time.time() - last < period:
                return 0
        first = qs[0]
        title = "Worldmap: Wer war dabei?" if len(qs) == 1 else f"Worldmap: {len(qs)} Reisen prüfen"
        msg = first["text"] if len(qs) == 1 else f"{first['text']} (+{len(qs) - 1} weitere)"
        if self.s.notify_service:
            self.ha.notify(self.s.notify_service, title, msg, url=ingress_url)
        else:
            self.ha.persistent(title, f"{msg}\n\n[Öffnen]({ingress_url})")
        with self.db.tx() as c:
            c.executemany("UPDATE questions SET notified = 1 WHERE id = ?", [(q["id"],) for q in qs])
        self.db.set_meta("last_notify", str(time.time()))
        return len(qs)

    def fill_routes(self) -> int:
        router = routing.OsrmRouter(self.s.osrm_url) if self.s.routing == "osrm" else None
        n = routing.fill_gaps(self.db, router)
        if n:
            self.touch()
        return n
