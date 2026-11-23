"""Build worldmap/app/worldmap/data/airports.json from OurAirports (public domain).

Usage: python tools/build_airports.py airports.csv
Keeps airports with scheduled flights and an IATA code: [IATA, name, city, lat, lon, size] with size 2 = large, 1 = medium.
"""
import csv
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "worldmap/app/worldmap/data/airports.json"


def main(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["scheduled_service"] != "yes" or not r["iata_code"] or r["type"] not in ("large_airport", "medium_airport"):
                continue
            out.append([r["iata_code"], r["name"], r["municipality"], round(float(r["latitude_deg"]), 4),
                        round(float(r["longitude_deg"]), 4), 2 if r["type"] == "large_airport" else 1])
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(len(out), "airports", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1])
