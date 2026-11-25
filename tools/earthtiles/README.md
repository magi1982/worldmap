# Earth tiles (build tool)

The "🌍 Earth" base map is a set of ready-made picture tiles (WebP, 256 px, Web Mercator),
drawn once on a build machine and shipped with the add-on in
`worldmap/app/worldmap/static/tiles/earth/<z>/<x>/<y>.webp`. Home Assistant only serves the files –
nothing is drawn on weak hardware.

1. `python tools/earthtiles/prepare.py` – turns the app's own `base.json` into `full.json` / `welt.json`
2. `CHROME_PATH=/usr/bin/google-chrome PUPPETEER_PATH=… node tools/earthtiles/gen.js 5` – renders zoom 0–5 for the whole world
3. copy `out/0` … `out/5` into `static/tiles/earth/`

Only public geography goes in (coastlines, lakes, rivers, hand-placed mountain ranges and climate zones);
no trips, places or other personal data. `out/`, `render.html`, `full.json` and `welt.json` are not committed.

---

**Deutsch:** Die Earth-Grundkarte besteht aus fertigen Bild-Kacheln. Sie werden einmal auf einem Build-Rechner
gezeichnet und mit dem Add-on ausgeliefert; Home Assistant liefert sie nur aus. Es fliessen nur öffentliche
Geodaten ein – keine Reisen, Orte oder persönlichen Daten.
