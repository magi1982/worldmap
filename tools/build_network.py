"""Build worldmap/app/worldmap/data/network.json.gz from Natural Earth roads and railroads (public domain).

Usage: python tools/build_network.py ne_10m_roads.geojson ne_10m_railroads.geojson
The main roads, ferries and railways of the world, simplified (~1 km), used offline to draw the likely way of
trips without GPS. Format: {"road": [[code, lat, lon, lat, lon, ...], ...], "rail": [...]}
road codes: "0" motorway/major highway, "1" secondary highway, "2" road, "f" ferry, "t" tunnel link; rail: "a".
"""
import gzip
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "worldmap/app/worldmap/data/network.json.gz"
ROAD = {"Major Highway": "0", "Beltway": "0", "Secondary Highway": "1", "Road": "2", "Bypass": "2",
        "Ferry Route": "f", "Ferry, seasonal": "f"}


def simplify(pts, tol):
    """Ramer–Douglas–Peucker on (lon, lat)."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        n = (dx * dx + dy * dy) ** .5 or 1e-12
        best, bi = 0.0, -1
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / n
            if d > best:
                best, bi = d, i
        if best > tol and bi > 0:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep, strict=True) if k]


def lines(geom):
    if geom["type"] == "LineString":
        yield geom["coordinates"]
    elif geom["type"] == "MultiLineString":
        yield from geom["coordinates"]


def flat(pts):
    out = []
    for lon, lat in pts:
        out += [round(lat, 3), round(lon, 3)]
    return out


def main(roads, rails):
    net = {"road": [], "rail": []}
    for f in json.load(open(roads, encoding="utf-8"))["features"]:
        p = f["properties"]
        code = "0" if p.get("expressway") == 1 else ROAD.get(p.get("type"))
        if not code or not f.get("geometry"):
            continue
        for ln in lines(f["geometry"]):
            s = simplify(ln, 0.004 if code != "f" else 0.01)
            if len(s) >= 2:
                net["road"].append([code] + flat(s))
    for f in json.load(open(rails, encoding="utf-8"))["features"]:
        if not f.get("geometry"):
            continue
        for ln in lines(f["geometry"]):
            s = simplify(ln, 0.004)
            if len(s) >= 2:
                net["rail"].append(["a"] + flat(s))
    # links Natural Earth leaves out: the Channel Tunnel car shuttle and the Calais – Dover ferry
    net["road"] += [["t", 50.922, 1.807, 51.012, 1.5, 51.093, 1.132], ["f", 50.966, 1.861, 51.05, 1.6, 51.124, 1.329]]
    net["rail"] += [["t", 50.922, 1.807, 51.012, 1.5, 51.093, 1.132]]
    OUT.write_bytes(gzip.compress(json.dumps(net, separators=(",", ":")).encode(), 9, mtime=0))
    print(len(net["road"]), "roads,", len(net["rail"]), "railways,", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
