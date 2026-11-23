# NEXT – ideas / Ideen

Ideas are collected here first. Code is only written after an explicit "go".
Ideen werden zuerst hier gesammelt. Code entsteht erst nach einem ausdrücklichen „mach es“.

## Working agreement / Arbeitsweise

- Security check on every update (input validation, least privilege, no secrets, dependency scans).
- New logic gets tests; all tests green before a release.
- Privacy: **no real names, family data, addresses or real GPS values** in code, examples, screenshots or commits – invented sample data only. Real data lives only in Home Assistant (`/data`).
- Home Assistant, HACS and GitHub best practices.
- Ask before every release. Changelog / release notes in English, README in English and German.
- Every new feature: check whether it needs a setting with a description.

## Done in 0.1.0

- Add-on with Ingress UI: map, trip list, questions, import, connectors, "trip by hand" wizard.
- Import with format detection: Google Timeline (Takeout, on-device Android/iOS), CSV/Excel with unknown columns (iCloud, exiftool, German headers), GPX, KML.
- Live positions from `person.*` / `device_tracker.*`, history backfill from the recorder.
- Photo EXIF scan of folders under `/media` and `/share`.
- Trip detection, merging of people travelling together, who-suggestions with confidence.
- Notifications (mobile app or persistent notification), sensors `sensor.worldmap_*`.
- Gap routing via OSRM (optional) and flight arcs.

## Done in 0.2.0

- Five-view map (trips, tracks, places & days, municipalities, time-lapse) with the full design of the standalone map.
- Transport mode per segment, curved flight arcs, estimated areas, routine places, background map cache.

## Done in 0.3.0

- Map matching onto the real rail and road network (OpenFreeMap tiles), activity types for Google path points.

## Done in 0.4.0

- Maps as start page with icon header, Excel-style trip list, trip-list import, duplicate detection, rule-learning questions,
  OwnTracks endpoint, notification picker, new time-lapse, worldwide place names; OSRM and NAS scanning removed.
- "Show for" bar (person / group) in all maps, people & groups configurator, home/work settings, worldwide regions view,
  info buttons.

## Done in 0.5.0 (not released yet)

- Map style editor with live preview and versions, transport picker in the trip list, clearer question settings.

## Next update – waiting for "mach es" / Nächstes Update – wartet auf „mach es“

- [ ] Export/import of a map style as a small JSON file (share a style).
- [ ] Every fix gets a new version number (so Home Assistant always offers it as an update).

## Next

- [ ] Actionable notifications ("who was there?" answered directly on the phone).
- [ ] Offline network package: pre-load the rail/road tiles for a whole country with one click.
- [ ] Finer worldwide gazetteer (towns outside Europe).
- [ ] Dashboard card (Lovelace) with a small live map.

## Ideas for later

- [ ] Actionable notifications: answer "who was there?" directly from the phone (listen to `mobile_app_notification_action` over the WebSocket API).
- [ ] Small HACS integration: services `worldmap.add_trip`, `worldmap.import_file`, calendar entity with all trips.
- [ ] Self-hosted OSRM / Valhalla as optional companion add-on (nothing leaves the network).
- [ ] School holidays from an iCal URL instead of manual ranges.
- [ ] HEIC support for photos (pillow-heif).
- [ ] Reverse geocoding with a finer offline gazetteer (villages) and Swiss municipalities.
- [ ] AppArmor profile, signed images via the HA builder, CodeQL for JavaScript.
- [ ] Export as KML/GPX and image poster.
- [ ] OwnTracks / Traccar HTTP endpoint as an extra live source.
