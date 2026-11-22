# Changelog

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
