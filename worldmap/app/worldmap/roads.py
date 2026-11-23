"""Estimated car routes on the real road network, for trips without GPS ("we drove to the Costa Dorada").

Long distances use zoom-7 OpenFreeMap tiles (motorways, trunk and primary roads only – a few tiles cover a whole
country), short stretches (to and from the motorway, day trips) use the zoom-12 map matcher. Only tile numbers are
requested, no coordinates of the user leave the house; tiles are cached on disk like the map-matching tiles.

``route`` returns a path [[lat, lon], ...], "none" when there is no plausible road path (an island without a bridge,
data missing), or None when tiles could not be loaded right now (try again later).
"""
from __future__ import annotations

import math

from .geo import haversine_km
from .netmatch import KX, KY, Graph, tiles_for_bbox

LONG_Z = 7
# motorway, trunk, primary – the long-distance network
LONG_WEIGHTS = {"0": 0.75, "1": 0.85, "2": 1.0}
LONG_SNAP_M = 45_000     # how far a destination may be from the main network
LONG_STITCH_M = 400      # tile seams at zoom 7 are coarse
MAX_LONG_TILES = 120
SHORT_KM = 30            # below this the detailed zoom-12 network is used


class RoadRouter:
    def __init__(self, long_source, short_matcher=None, max_tiles: int = MAX_LONG_TILES):
        self.long = long_source
        self.short = short_matcher
        self.max_tiles = max_tiles
        self.stats = {"long": 0, "short": 0, "none": 0, "no_data": 0}

    # ------------------------------------------------------------ public
    def route(self, a, b):
        d = haversine_km(a[0], a[1], b[0], b[1])
        if d < 1:
            return [list(a), list(b)]
        if d < SHORT_KM and self.short is not None:
            got = self.short.match("road", tuple(a), tuple(b))
            if isinstance(got, list):
                self.stats["short"] += 1
                return got
            if got is None:
                self.stats["no_data"] += 1
                return None
        return self._long(a, b, d)

    # ------------------------------------------------------------ zoom 7
    def _long(self, a, b, d_km):
        span = max(abs(a[0] - b[0]), abs(a[1] - b[1]))
        m = max(0.5, 0.15 * span)
        bbox = (min(a[0], b[0]) - m, min(a[1], b[1]) - m * 1.4, max(a[0], b[0]) + m, max(a[1], b[1]) + m * 1.4)
        tiles = tiles_for_bbox(*bbox, z=LONG_Z)
        if len(tiles) > self.max_tiles:
            self.stats["none"] += 1
            return "none"
        lines = []
        for x, y in tiles:
            got = self.long.lines(x, y)
            if got is None:
                self.stats["no_data"] += 1
                return None
            lines.extend((c, p) for c, p in got if c in LONG_WEIGHTS)
        if not lines:
            self.stats["none"] += 1
            return "none"
        g = Graph(lines, LONG_WEIGHTS, (a[0] + b[0]) / 2, cell=0.05, stitch_m=LONG_STITCH_M)
        sa, sb = g.snap(a[0], a[1], LONG_SNAP_M), g.snap(b[0], b[1], LONG_SNAP_M)
        if not sa or not sb:
            self.stats["none"] += 1
            return "none"
        dd = math.hypot((a[0] - b[0]) * KY, (a[1] - b[1]) * KX * math.cos(math.radians((a[0] + b[0]) / 2)))
        limit = dd * 1.8 + 80_000
        res = g.route(sa[0], sb[0], limit * 1.6) if sa[0] != sb[0] else ([sa[0]], 0.0)
        if not res or res[1] > limit:
            self.stats["none"] += 1
            return "none"
        core = [[g.coord[i][0], g.coord[i][1]] for i in res[0]]
        head = self._stub(a, core[0])
        tail = self._stub(core[-1], b)
        self.stats["long"] += 1
        return head[:-1] + core + tail[1:]

    def _stub(self, p, q):
        """From the destination to the motorway (and back): the detailed network if possible, else straight."""
        if haversine_km(p[0], p[1], q[0], q[1]) >= 2 and self.short is not None:
            got = self.short.match("road", tuple(p), tuple(q))
            if isinstance(got, list) and len(got) >= 2:
                return [list(p)] + got[1:-1] + [list(q)]
        return [list(p), list(q)]
