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


def scheduler(engine: Engine, stop: threading.Event) -> None:
    s = engine.s
    try:
        if engine.ha.available and s.persons:
            log.info("history backfill: %d new points", engine.backfill_history())
        log.info("rebuild: %s", engine.rebuild())
        warm(engine)
    except Exception:  # noqa: BLE001 - keep the add-on alive
        log.exception("startup sync failed")
    last_rebuild = last_photos = time.time()
    if s.photo_folders:
        last_photos = 0
    while not stop.wait(max(60, engine.s.poll_interval_min * 60)):
        s = engine.s  # settings may change through the UI
        try:
            if engine.ha.available and s.persons:
                engine.poll_once()
            if s.photo_folders and time.time() - last_photos > s.photo_scan_hours * 3600:
                log.info("photo scan: %d new points", engine.scan_photos())
                last_photos = time.time()
            if time.time() - last_rebuild > 3600:
                engine.rebuild()
                engine.fill_routes()
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
    sup = Supervisor()
    if sup.available:
        engine.ingress_url = sup.ingress_path()
    stop = threading.Event()
    threading.Thread(target=scheduler, args=(engine, stop), daemon=True, name="scheduler").start()
    httpd = serve(engine, port=int(os.environ.get("WORLDMAP_PORT", "8099")))

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
