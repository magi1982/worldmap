# Changelog

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
