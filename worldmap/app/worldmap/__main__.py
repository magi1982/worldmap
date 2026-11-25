"""Entry point: ``python -m worldmap``."""
from __future__ import annotations

import logging
import os
import signal
import threading
import time

from .atlas import Atlas
from .db import Database
from .engine import Engine
from .ha import Supervisor
from .owntracks import serve as serve_owntracks
from .server import serve
from .settings import load

log = logging.getLogger("worldmap")


def warm(engine: Engine) -> None:
    """Pre-build the map data so the map opens instantly."""
    atlas = getattr(engine, "atlas", None)
    if atlas is not None:
        t0 = time.time()
        atlas.get("core")
        log.debug("map data ready in %.1f s", time.time() - t0)


def route_worker(engine: Engine, stop: threading.Event) -> None:
    """Lay all open gaps onto the rail/road network in small batches; the map is refreshed after each batch."""
    while not stop.is_set():
        engine.routes_wanted.wait(3600)
        engine.routes_wanted.clear()
        try:
            while not stop.is_set():
                n = engine.fill_routes(budget_s=180)
                if n:
                    warm(engine)
                if not engine.route_progress.get("todo"):
                    break
                if not n:  # the tile server asked us to wait: continue after the pause
                    src = getattr(engine.matcher, "source", None)
                    wait = (getattr(src, "pause_until", 0) - time.monotonic()) if src else 0
                    if wait <= 0 or stop.wait(min(wait + 5, 900)):
                        break
        except Exception:  # noqa: BLE001 - keep the add-on alive
            log.exception("routing failed")
        try:  # estimated car routes of trips without GPS on real roads (0.7.2)
            atlas = getattr(engine, "atlas", None)
            if atlas is not None and atlas.fill_roads(budget_s=600):
                warm(engine)
        except Exception:  # noqa: BLE001 - keep the add-on alive
            log.exception("road routes failed")


def scheduler(engine: Engine, stop: threading.Event) -> None:
    s = engine.s
    for attempt in range(6):  # Home Assistant may not be ready yet right after a restart (502): try again
        try:
            if engine.ha.available and s.persons:
                log.info("history backfill: %d new points", engine.backfill_history())
            res = engine.rebuild()
            if res.get("error") and engine.ha.available and attempt < 5:
                log.info("Home Assistant not ready yet (%s) – trying again in 30 s", res["error"])
                if stop.wait(30):
                    return
                continue
            log.info("rebuild: %s", res)
            warm(engine)
            engine.routes_wanted.set()  # lay new gaps onto the rail/road network in the background
        except Exception:  # noqa: BLE001 - keep the add-on alive
            log.exception("startup sync failed")
        break
    last_rebuild = time.time()
    while not stop.wait(max(60, engine.s.poll_interval_min * 60)):
        s = engine.s  # settings may change through the UI
        try:
            if engine.ha.available and s.persons:
                engine.poll_once()
            if time.time() - last_rebuild > 3600:
                engine.rebuild()
                engine.routes_wanted.set()
                last_rebuild = time.time()
            warm(engine)
            engine.notify_open()
        except Exception:  # noqa: BLE001
            log.exception("scheduled job failed")


def main() -> None:
    data_dir = os.environ.get("WORLDMAP_DATA", "/data")
    settings = load(os.path.join(data_dir, "options.json"))
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db = Database(os.path.join(data_dir, "worldmap.db"))
    engine = Engine(db, settings)
    engine.atlas = Atlas(engine, data_dir)
    engine.tile_dir = os.path.join(data_dir, "tiles")
    sup = Supervisor()
    if sup.available:
        engine.ingress_url = sup.ingress_path()
    stop = threading.Event()
    threading.Thread(target=scheduler, args=(engine, stop), daemon=True, name="scheduler").start()
    threading.Thread(target=route_worker, args=(engine, stop), daemon=True, name="routes").start()
    httpd = serve(engine, port=int(os.environ.get("WORLDMAP_PORT", "8099")))
    try:  # local live source for phones; reachable only if port 8098 is enabled in the add-on network settings
        ot = serve_owntracks(engine, port=int(os.environ.get("WORLDMAP_OWNTRACKS_PORT", "8098")))
        threading.Thread(target=ot.serve_forever, daemon=True, name="owntracks").start()
    except OSError as exc:
        log.warning("OwnTracks endpoint not started: %s", exc)

    def shutdown(*_):
        stop.set()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown)
    log.info("Worldmap listening on port %s", httpd.server_address[1])
    try:
        httpd.serve_forever()
    finally:
        db.close()


if __name__ == "__main__":
    main()
