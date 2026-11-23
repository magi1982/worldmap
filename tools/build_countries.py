"""Build worldmap/app/worldmap/data/countries.json.gz from Natural Earth admin-0 countries (public domain).

Usage: python tools/build_countries.py ne_50m_admin_0_countries.geojson
Rows: [iso_a2, [names in German, English, local …], label lat, label lon, radius km] – lets you pick a whole
country as destination ("Kenia", "Thailand") when you add a trip by hand.
"""
import gzip
import json
import math
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "worldmap/app/worldmap/data/countries.json.gz"


def main(path):
    rows = []
    for f in json.load(open(path, encoding="utf-8"))["features"]:
        p = f["properties"]
        cc = p.get("ISO_A2_EH") if p.get("ISO_A2") in (None, "-99") else p.get("ISO_A2")
        names = []
        for k in ("NAME_DE", "NAME", "NAME_EN", "NAME_LONG", "ADMIN", "NAME_FR", "NAME_IT"):
            v = p.get(k)
            if v and v not in names:
                names.append(v)
        b = f.get("bbox")
        if not b:
            xs, ys = [], []
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                for x, y in poly[0]:
                    xs.append(x)
                    ys.append(y)
            b = [min(xs), min(ys), max(xs), max(ys)]
        la, lo = p.get("LABEL_Y"), p.get("LABEL_X")
        h = (b[3] - b[1]) * 111
        w = (b[2] - b[0]) * 111 * math.cos(math.radians(la or 0))
        r = max(20, min(1500, round(math.hypot(h, w) / 4)))
        rows.append([cc or "", names, round(la, 3), round(lo, 3), r])
    OUT.write_bytes(gzip.compress(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode(), 9, mtime=0))
    print(len(rows), "countries", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1])
