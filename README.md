<p align="center"><img src="worldmap/logo.png" alt="Worldmap" width="360"></p>

<p align="center"><b>All your trips on one map – inside Home Assistant, fully local.</b><br>
<a href="README.de.md">🇩🇪 Deutsch</a></p>

Worldmap is a Home Assistant add-on that collects where you have been – live from your phones, from Google Timeline
exports and from trip lists – detects trips, asks a few smart questions ("who was there?") and shows everything on a
fast, good-looking map with five views. Everything runs inside the add-on; no cloud service is needed.

![Map](docs/images/map.jpg)

> All screenshots use invented sample data ("Alex" and "Sam").

## Features

| | |
|---|---|
| 🗺️ **Five map views** | **Trips** (who went where and how, destinations, flight arcs, estimated areas for trips without GPS), **Tracks** (every route, coloured by transport, year or person), **Places & days** (where you spent time, a calendar of every day), **Regions** (states, provinces and cantons worldwide) and **Time-lapse** (your history as a film, hour by hour, with animated flights and a timeline). |
| 🛤️ **Real rail and road lines** | Gaps between GPS points are map-matched onto the real rail and road network from OpenStreetMap. The network is built from map tiles that are downloaded once by tile number and kept in the add-on – no positions are ever sent, afterwards it works offline. Gaps without a plausible path stay open instead of becoming straight lines. |
| ❓ **Smart questions – no AI needed** | Similar trips (same area, same kind of day, same suggestion) are asked **once** – one answer for all. Answers can be remembered as **rules**, so the same question never comes again. Answers: every person and group, "no trip (everyday life)", "merge with the trip before", "ask one by one". |
| 👥 **People & groups** | Single persons and groups (couple, family …) with colours. A bar on top of every map shows everyone, one person or one group. Home and work with radius; the workplace is hidden on the map unless you switch it on. |
| 📋 **Excel-style trip list** | In the settings: filter per column, sort, edit cells in place, delete rows, paste rows straight from Excel or Google Sheets (Ctrl+V). Duplicates are detected. |
| 📥 **Import anything** | Trip lists (CSV/Excel with From, To, Destination …) – destinations are placed on the map automatically – Google Timeline (Takeout and the on-device export for Android and iPhone), iCloud/exiftool photo CSV, any CSV/Excel with coordinates, GPX, KML. A preview shows what was found before anything is saved; data that is already there is not stored twice. |
| 📡 **Live without cloud** | Positions from `person.*` / `device_tracker.*` entities and a built-in **OwnTracks** endpoint: the phone buffers positions while you are away and sends them when it is back in your home network – no Nabu Casa, no port opened to the internet. |
| ✍️ **Trips by hand** | The "+" button asks a few questions (where, when, how long, who, how, how big was the area) – for old trips without any data. |
| 🔔 **Notifications** | Choose one of your phones (found automatically) or a Home Assistant notification, how often (instant, daily, weekly) and send a test. |
| 🎨 **Map style with versions** | Colour, line type and width per transport, areas and base map – with a live preview. Every save is a version you can go back to. |
| 🌙 **Light & dark mode** | Follows the system or the ☾/☀ button on the map; lakes, borders and coasts stay visible in the dark. |
| 📊 **Sensors** | `sensor.worldmap_km_this_year`, `sensor.worldmap_trips`, `sensor.worldmap_countries`, `sensor.worldmap_open_questions`, `sensor.worldmap_last_trip`. |

| Tracks | Places & days | Regions | Time-lapse |
|---|---|---|---|
| ![Tracks](docs/images/spuren.jpg) | ![Places](docs/images/orte.jpg) | ![Regions](docs/images/regionen.jpg) | ![Time-lapse](docs/images/zeit.jpg) |

| People & groups | Questions | Trip list |
|---|---|---|
| ![People](docs/images/people.jpg) | ![Questions](docs/images/questions.jpg) | ![Trip list](docs/images/trips.jpg) |

![Map style](docs/images/style.jpg)

## Installation

1. In Home Assistant open **Settings → Add-ons → Add-on store → ⋮ → Repositories** and add
   `https://github.com/magi1982/worldmap`.
2. Install **Worldmap**, start it and enable **Show in sidebar**.
3. Open Worldmap → ⚙️ **Settings → People & groups**: add the people (with their phone) and groups such as couple or family.

## Getting location data

| Source | Automatic? | How |
|---|---|---|
| **OwnTracks app** (iPhone & Android) | ✅ live, no cloud | Settings → Connections → OwnTracks: create a user. In the add-on's *Network* settings enter port `8098`. In the app: mode *HTTP*, URL `http://<home-assistant-ip>:8098/pub`, user and password. Positions are buffered on the phone and sent when it is back home. |
| **Home Assistant Companion App** | ✅ live | `person.*` entity with GPS. Only delivers while the phone can reach Home Assistant – from outside the home network you need Nabu Casa, a VPN (WireGuard/Tailscale add-on) or your own domain. |
| **iCloud "Find My"** | ✅ | HACS integration *iCloud3* (needs your Apple ID). |
| **Google Maps Timeline** | ⚠️ export | Google keeps the timeline only on the phone. Export it now and then (*Android: Settings → Location → Timeline → Export*; *iPhone: Google Maps → profile → Timeline → ⋯ → Export*) and drop the file into **Import**. |
| **Trip lists** | ⚠️ import / paste | CSV or Excel with columns like From, To, Destination, Country, Who – or paste rows into the trip list. |
| **Photos** | ⚠️ import | Export capture place and time as CSV (e.g. with exiftool) and import; photos are assigned to people by camera model. |
| **Apple Significant Locations** | ❌ | Apple offers no export or API. |

## Configuration

Everything can be set in the app (⚙️ **Settings**) or in the add-on configuration; each option has a description.

| Option | Default | Meaning |
|---|---|---|
| `persons` | – | `label` (name), optional `entity` (`person.x` / `device_tracker.x`), `camera_models` for photo imports |
| `owntracks` | – | `user`, `password` (≥ 8 characters), `label` (person) for the OwnTracks endpoint on port 8098 |
| `groups` | – | `name`, `members` (comma-separated persons), `extra` (people without a phone), `color` |
| `home_radius_m` | 0 | home radius in metres; 0 = radius of the home zone |
| `work_lat` / `work_lon` / `work_radius_m` | – / – / 300 | workplace; empty = detected automatically |
| `show_work` | false | show the workplace on the map |
| `min_trip_km` | 30 | a day counts as a trip from this distance |
| `routine_days` | 20 | places visited on this many days (work, school) never start a trip; 0 = off |
| `ask_below` | `hoch` | ask when the confidence is below this level |
| `school_holidays` | – | ranges like `2026-07-04..2026-08-09` – suggests "family" |
| `hint_keywords` | – | `word=answer` – suggested when a file or folder name contains the word |
| `routing` | `tiles` | `tiles` = rail/road network from OpenStreetMap tiles (local after the first download); `off` |
| `notify_service` / `notify_mode` | – / `weekly` | e.g. `notify.mobile_app_phone`; `off`, `instant`, `daily`, `weekly` |

## Privacy & security

- Location history stays in the add-on's `/data` folder (part of your Home Assistant backups). Nothing is uploaded.
  The only downloads are OpenStreetMap tiles by tile number (once; then cached).
- The UI is only reachable through Home Assistant Ingress. The optional OwnTracks port accepts only authenticated `POST`s.
- Input validation, parameterised SQL, XXE-safe XML, CSV-injection-safe export, Content-Security-Policy, escaped output.
- CI: tests, Ruff, Bandit, pip-audit, CodeQL, Dependabot, Home Assistant add-on linter and a privacy guard. See [SECURITY.md](SECURITY.md).

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest
python tools/demo.py /tmp/demo        # invented sample data
WORLDMAP_DATA=/tmp/demo WORLDMAP_ALLOWED_IPS=127.0.0.1 PYTHONPATH=worldmap/app python -m worldmap
# open http://127.0.0.1:8099
```

Ideas and the roadmap live in [NEXT.md](NEXT.md).

## Credits

Map and place data: [Natural Earth](https://www.naturalearthdata.com/) (public domain, including the regions),
place names: [GeoNames](https://www.geonames.org/) (CC BY 4.0). Rail and road network: © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors via [OpenFreeMap](https://openfreemap.org/).

License: MIT
