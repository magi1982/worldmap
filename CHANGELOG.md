# Changelog

## 0.6.1 – 2026-11-23

### Fixed
- Rail/road network: when the map tile server answers "too many requests" or is unreachable, downloads pause
  (2–5 minutes) and continue automatically instead of failing thousands of times; slower, polite download rate.
  The reason is written to the log and shown in the Tracks map.

## 0.6.0 – 2026-11-23

### Added
- **Animated map**: small planes in the colour of the trip fly back and forth on the flight arcs (the line under the plane
  fades out), trains and cars travel along trips abroad. Switch "Animation" on top of every map; runs on its own layer at
  60 fps and pauses when the page is hidden. Off for "reduce motion".
- **Time-lapse rebuilt**: cinema look (dark map, glowing trails, only big place names), a title card for every trip
  (who, where, when, how), the current car or train is drawn instead of a dot, calm camera at home, everyday life plays
  up to 6× faster. Quick switch Cinema / Map in the panel.
- Map style: colour palettes for persons and groups (neon, classic, pastel, earth tones, contrast, tone in tone),
  base map colours (standard, paper, grey), three more line types (long dash, dash-dot, sparse dots), settings for the
  animation (planes, vehicles, hide line, speed, size) and the time-lapse.
- Rail/road network: computed continuously in the background after an import, with progress shown in the Tracks map.

### Changed
- Phone: the header with the map choice stays on top while scrolling, the map sits right below it.
- New levels of detail fade in smoothly when zooming instead of popping.
- Place names without district suffixes ("Zürich" instead of "Zürich (Kreis 11) / …").

## 0.5.3 – 2026-11-23

### Fixed
- AppArmor profile: SQLite may map its WAL index into memory (`m` on `/data`), temporary files also in `/var/tmp` –
  0.5.2 failed with "unable to open database file" and the settings showed "502".
- Persons without a Home Assistant entity (only imports or OwnTracks) no longer break the live position polling.
- Regions view: places only flown over (GPS points recorded in a plane) no longer count as visited.

## 0.5.2 – 2026-11-23

### Added
- **Worldmap package** (`*.worldmap.json.gz`): one file with all trips (who was there, transport, notes) and all GPS points
  (with the person they belong to). Import it under Import; download your own under Import › "Worldmap package" – for
  backups or moving to another Home Assistant. Gzip is unpacked with a size limit; every trip is checked before anything is stored.
- New setting `min_day_trip_km` (default 100 km): a day out without a night away counts as a trip only from this distance.

### Changed
- Trips that were imported or entered by hand are never overwritten by GPS detection any more – GPS only fills in missing
  coordinates and distances.

## 0.5.1 – 2026-11-23

### Security
- Own AppArmor profile: the add-on may only write to `/data` and temporary files, cannot mount, trace other processes or
  use admin capabilities. Raises the Home Assistant security rating from 7 to 8 (the maximum).

### Fixed
- Phone: the "show for" bar no longer sticks over the map while scrolling the side panel.
- Trip lists that also contain latitude/longitude columns are imported as trips (with these coordinates) instead of failing
  with "no usable coordinates".

## 0.5.0 – 2026-11-23

### Added
- Settings › **Map style**: colour, line type (solid, dashed, dotted) and width per transport; areas for "many short ways"
  (on/off, opacity, size, outline); base map (rivers, region borders, place names, light/dark). Live preview.
- **Style versions**: every save creates a version with an optional note; one click goes back. The last 20 are kept in `/data/style.json`.
- Trip list: transport is chosen from a list (car, train, bus, plane, ship, camper, bike, on foot – several at once);
  the filters for who, confidence and transport are drop-downs.
- Questions & rules: simpler controls (sliders, switches, plain-language choices, date pickers for school holidays,
  keyword rows).

### Changed
- Settings tabs ordered by what you need first, with icons.
- `routing: osrm` from 0.2 is accepted by the add-on configuration again (read as `tiles`), so updates no longer stop.

## 0.4.0 – 2026-11-23

### Added
- The maps are the start page. Header icons on the right: open questions (only when there are any), "+" for a trip by hand, settings.
- Settings with an Excel-style trip list: filter per column, sort, edit cells in place, delete rows, paste rows from Excel/Google Sheets.
- Trip lists (CSV/Excel with From/To/Destination …) can be imported; destinations are placed on the map from the bundled gazetteer.
- Duplicate detection for imported and pasted trips (same dates and same name or less than 30 km apart); empty cells never overwrite data.
- Smart questions without AI: similar trips are asked once, answers can be remembered as rules (place + kind of day), new answers
  "no trip (everyday life)", "merge with the trip before" and "ask one by one". Learned rules can be reviewed and deleted.
- OwnTracks endpoint (port 8098, Basic auth): live positions from phones without Nabu Casa – the app buffers while away and
  sends when back in the home network.
- Notification settings with a list of the phones found in Home Assistant and a test button.
- Time-lapse rebuilt: days play hour by hour, glowing head, animated flights, smooth camera, timeline with trips, keyboard control.
- Worldwide place names (Natural Earth) for trips outside Europe; home country button instead of a fixed "CH".
- Failed or old import entries can be removed.
- "Show for" bar on top of every map: everyone, one person or one group – all five maps, numbers, calendar and time-lapse follow.
- Settings › People & groups: single persons (colour, live location, camera) and groups such as couple or family (members,
  people without a tracked phone, colour), with templates.
- Home and work settings: home radius, workplace position and radius (or automatic), and whether the workplace is shown on the map
  (off by default).
- Regions view (states, provinces, cantons worldwide, Natural Earth) replaces the Swiss municipalities view.
- Descriptions moved behind small (i) buttons in the maps and settings; the map side panel is split into clear sections.
- Empty map explains what to do next (import, people & groups).
- Trips without GPS (by hand or from trip lists) get offline kilometre estimates per transport (detour factors, airport
  transfers, driving on the spot) and count for the regions view.
- Light and dark mode (system setting or the ☾/☀ button on the map, also for the settings).
- Older configurations keep working (`routing: osrm` is read as `tiles`, plain group names become groups).

### Changed
- Routing works fully locally on the OpenStreetMap network; the OSRM option was removed.
- Swiss borders, cantons and municipalities are no longer drawn stronger.
- Database migrations for installations of 0.1–0.3.

### Removed
- Swiss municipalities view and its data file (replaced by worldwide regions).
- Photo folder scanning (NAS) and the `media`/`share` mounts – photo positions can still be imported as CSV.

## 0.3.0 – 2026-11-22

### Added
- Map matching onto the real rail and road network: gaps between GPS points follow the actual railway lines and roads
  from OpenStreetMap (OpenFreeMap vector tiles, decoded in the add-on and cached in `/data/tiles`). Loose line ends at
  tile borders are stitched, paths with large detours are rejected and stay open instead of becoming straight lines.
- Trams, buses and city tunnels fall back to the street network.
- Google Timeline path points inherit the transport type of the activity they belong to (train, car, walking …).
- New routing mode `tiles` (default): only tile numbers are downloaded, no positions are sent.

### Fixed
- iCloud location exports with "Aufnahme UTC" / "Breite" / "Länge" columns are imported (the "Datei" column was taken for a date).
- Short GPS jumps are no longer shown as flights.

## 0.2.0 – 2026-11-22

### Added
- New map with five views – **Trips**, **Tracks**, **Places & days**, **Municipalities** and **Time-lapse** – with a side panel
  (colour by who or by transport, statistics with bars, year bars, top destinations), labelled destinations, legend,
  CH/EU buttons and a tile renderer that stays fast with millions of points.
- Flights are drawn as curved arcs; trips entered by hand appear as dotted estimated areas.
- Transport mode per segment (car, train & public transport, on foot, flight, ferry) from Google activity data and speed.
- Swiss municipalities visited (first visit, number of days, stays) and places where most time was spent.
- "Edit" link in the map opens the trip editor.
- New setting `routine_days`: places visited on many days (work, school) no longer start a trip.

### Changed
- Days on which you came home in the evening are no longer merged into one multi-day trip.
- Far trips are named after the nearest well-known city instead of a suburb.
- Map data is pre-built in the background and cached, so the map opens in under a second.

### Security
- All names shown in the map are HTML-escaped; trip editing from the map uses `postMessage` restricted to the same origin.
- Pillow 13.0.0.

## 0.1.0 – 2026-11-22

First release.

### Added
- Ingress UI with map, trip list, questions, import and connectors.
- "Trip by hand" wizard with region search for trips without GPS data (shown as estimated areas).
- Import with automatic format detection: Google Timeline (Takeout and on-device exports for Android and iOS),
  CSV/Excel with unknown columns (iCloud, exiftool, English/German headers, DMS coordinates), GPX, KML.
- Live positions from `person.*` / `device_tracker.*` entities and history backfill from the recorder.
- Photo EXIF scanning of folders below `/media` and `/share`.
- Trip detection, merging of people travelling together and who-suggestions with confidence levels.
- Notifications via a mobile app notify service or persistent notifications; `sensor.worldmap_*` entities.
- Optional gap routing via OSRM and great-circle flight arcs.
- Connector settings editable in the app (saved to the add-on options through the Supervisor API).

### Security
- Ingress-only access, input validation, parameterised SQL, XXE-safe XML, CSV-injection-safe export, strict CSP.
- CI with tests, Ruff, Bandit, pip-audit, CodeQL, Dependabot and a privacy guard.
