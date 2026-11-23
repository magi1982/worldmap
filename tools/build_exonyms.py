"""Build worldmap/app/worldmap/data/exonyms.json.gz from Natural Earth populated places (public domain).

Usage: python tools/build_exonyms.py ne_10m_populated_places.geojson
Other-language names of world cities ("Wien" → Vienna, "Mailand" → Milan): [alias, name, lat, lon, cc, population].
"""
import gzip
import json
import sys
import unicodedata
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "worldmap/app/worldmap/data/exonyms.json.gz"
LANGS = ("NAME_DE", "NAME_EN", "NAME_FR", "NAME_IT", "NAME_ES", "NAME_NL", "NAME_PT", "NAMEALT")


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def main(path):
    out, seen = [], set()
    for f in json.load(open(path, encoding="utf-8"))["features"]:
        p = f["properties"]
        name, pop = p["NAME"], int(p.get("POP_MAX") or 0)
        for k in LANGS:
            for alias in str(p.get(k) or "").split("|"):
                a = fold(alias)
                if len(a) < 3 or a == fold(name) or (a, name) in seen:
                    continue
                seen.add((a, name))
                out.append([a, name, round(p["LATITUDE"], 4), round(p["LONGITUDE"], 4), p.get("ISO_A2") or "", pop])
    out.sort(key=lambda r: -r[5])
    OUT.write_bytes(gzip.compress(json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode(), 9, mtime=0))
    print(len(out), "aliases", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1])
