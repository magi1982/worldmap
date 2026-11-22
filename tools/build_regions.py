"""Build static/regions.json (states, provinces, cantons worldwide) from Natural Earth.

Usage: python tools/build_regions.py ne_10m_admin_1_states_provinces.geojson ne_50m_admin_0_countries.geojson

Natural Earth is public domain. Output format:
{"countries": {A3: name}, "regions": [[id, name, A3, lat, lon, [ring, ...]], ...]}
Each ring is delta-encoded lon/lat at 1e3 (≈100 m), simplified with Douglas–Peucker.
"""
import json
import sys
from pathlib import Path

TOL = 0.012  # degrees (≈1 km)
OUT = Path(__file__).resolve().parents[1] / "worldmap/app/worldmap/static/regions.json"


def dp(pts, tol):
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        n = (dx * dx + dy * dy) or 1e-18
        best, bi = 0.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / n))
            d = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if d > best:
                best, bi = d, i
        if best > tol * tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep, strict=True) if k]


def encode(ring):
    out, px, py = [], 0, 0
    for x, y in ring:
        qx, qy = round(x * 1e3), round(y * 1e3)
        if out and qx == px and qy == py:
            continue
        out += [qx - px, qy - py]
        px, py = qx, qy
    return out


def main(a1, a0):
    names = {f["properties"]["ADM0_A3"]: f["properties"].get("NAME_DE") or f["properties"]["NAME"]
             for f in json.load(open(a0, encoding="utf-8"))["features"]}
    regions, countries = [], {}
    for i, f in enumerate(json.load(open(a1, encoding="utf-8"))["features"], 1):
        p, g = f["properties"], f["geometry"]
        if not g:
            continue
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        rings = []
        for poly in polys:
            outer = poly[0]
            xs = [c[0] for c in outer]
            ys = [c[1] for c in outer]
            if (max(xs) - min(xs)) < TOL and (max(ys) - min(ys)) < TOL and rings:
                continue  # tiny islands
            r = dp([(c[0], c[1]) for c in outer], TOL)
            if len(r) >= 4:
                rings.append(encode(r))
        if not rings:
            continue
        a3 = p.get("adm0_a3") or "?"
        countries[a3] = names.get(a3) or p.get("admin") or a3
        name = p.get("name_de") or p.get("name") or "?"
        regions.append([i, name, a3, round(p.get("latitude") or 0, 3), round(p.get("longitude") or 0, 3), rings])
    OUT.write_text(json.dumps({"countries": countries, "regions": regions}, ensure_ascii=False,
                              separators=(",", ":")), encoding="utf-8")
    print(len(regions), "regions", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
