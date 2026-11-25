"""Prepare the map data for the Earth tiles from the app's own base map (static/base.json).

    python tools/earthtiles/prepare.py

Writes two files next to this script (not part of the add-on):
  full.json – every coastline, lake and river as plain lon/lat pairs (used from zoom 5 on)
  welt.json – a lighter copy for the world view (fewer points, only big lakes and rivers)
Only public geography is used – no trips, places or other personal data.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "worldmap" / "app" / "worldmap" / "static" / "base.json"
Q = 1e4


def decode(ring):
    out, x, y = [], 0, 0
    for i in range(0, len(ring) - 1, 2):
        x += ring[i]
        y += ring[i + 1]
        out += [round(x / Q, 4), round(y / Q, 4)]
    return out


def simplify(pts, eps):
    """Douglas-Peucker on a flat [x, y, x, y, ...] list."""
    p = [(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)]
    if len(p) < 3:
        return pts
    keep = [False] * len(p)
    keep[0] = keep[-1] = True
    stack = [(0, len(p) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = p[a], p[b]
        dx, dy = bx - ax, by - ay
        n = (dx * dx + dy * dy) ** 0.5  # 0 for a closed ring: then the distance to the start point counts
        best, idx = 0.0, -1
        for i in range(a + 1, b):
            d = abs(dy * (p[i][0] - ax) - dx * (p[i][1] - ay)) / n if n > 1e-9 else ((p[i][0] - ax) ** 2 + (p[i][1] - ay) ** 2) ** 0.5
            if d > best:
                best, idx = d, i
        if best > eps:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [c for i, q in enumerate(p) if keep[i] for c in q]


def bbox(r):
    xs, ys = r[0::2], r[1::2]
    return max(xs) - min(xs), max(ys) - min(ys)


def main():
    b = json.loads(BASE.read_text(encoding="utf-8"))
    land = [decode(r) for r in b["land"]]
    lakes = [decode(r) for r in b["lakes"]]
    rivers = [[r[0], *decode(s)] for r in b["rivers"] for s in r[1:]]
    labels = b["labels"]
    (HERE / "full.json").write_text(json.dumps({"land": land, "lakes": lakes, "rivers": rivers, "labels": labels}, separators=(",", ":")))
    wl = [s for s in (simplify(r, 0.035) for r in land) if len(s) >= 8]
    wk = [simplify(r, 0.035) for r in lakes if max(bbox(r)) > 1.2]
    wr = [[r[0], *simplify(r[1:], 0.035)] for r in rivers if r[0] <= 5]
    wlab = [x[:4] for x in labels if x[1] <= 6]
    (HERE / "welt.json").write_text(json.dumps({"box": [-170, -60, 180, 84], "land": wl, "lakes": wk, "rivers": wr, "labels": wlab}, separators=(",", ":")))
    print(f"full.json: {len(land)} coast rings, {len(lakes)} lakes, {len(rivers)} rivers · welt.json: {len(wl)} / {len(wk)} / {len(wr)}")


if __name__ == "__main__":
    main()
