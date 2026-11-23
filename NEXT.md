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

## Done in 0.6.0 (not released yet)

- Animated map (planes, trains, cars), cinema time-lapse with trip cards, colour palettes, base map colours, more line types,
  sticky header on phones, smooth level-of-detail fades, continuous rail/road matching with progress.

## Done in 0.6.1–0.6.3

- Polite tile downloads with back-off, real airports with IATA tags, flights recorded in pieces merged,
  trips without coordinates located offline, dotted gaps, updates without Ctrl+F5.

## Done in 0.7.0 (released)

- Settings for every map with a live 🎨 drawer and live preview on the settings page, estimated routes with ferries,
  animation choices (vehicles, distance, count, constant plane speed), areas that melt together, travel film with video export.

## Done in 0.7.2

- "Where exactly?" question for country-only trips, no point in the middle of a country, plane + ferry to islands
  without a big airport, estimated car routes on real roads, lines never move (only vehicles).

## Next update – waiting for "mach es" / Nächstes Update – wartet auf „mach es“

### Base map (idea, to decide)
- [ ] Optional **detailed base map with MapLibre GL + OpenFreeMap vector tiles**, styled with a style JSON
      (editable in Maputnik): real roads, towns, terrain, 3D buildings when zoomed in. Trade-offs: needs internet
      for the map tiles (the tile servers see which areas you look at), ~800 KB library, the current offline
      Natural Earth map stays as fallback. Our trips, areas and animation would be drawn on top.

### A. Settings you can feel / Einstellungen, die man sieht
- [x] **Style drawer on the map**: a 🎨 button opens a panel right on the real map; every slider changes the map live
      (no guessing), "Save as version" at the end. The settings page keeps the full list.
- [x] **Preview with your own data**: a mini map of your home region plus one real trip instead of a made-up picture;
      every change flashes "✓ applied"; before/after slider.
- [ ] **Theme gallery**: whole looks in one tap – "Neon Night", "Atlas paper", "Minimal", "Retro railway", "Pastel summer",
      "Random" – each sets palette, base map, line types, areas and animation together.
- [x] Areas: **outline width**, outline colour (like fill / darker / white), softness, shape (circles / hexagons / cloud).
- [ ] Lines: glow/neon, drop shadow, colour gradient along a route (old → new), width by frequency (often driven = thicker).

### B. Animation
- [ ] Contrails behind planes, comet tails behind cars and trains, landing "ripples" at destinations.
- [ ] Flight arcs with a soft shadow on the ground and height by distance (2.5D look).
- [ ] Countries/regions light up the first time you were there (in the regions map and the film).
- [ ] **Play a trip**: tap a trip → the camera flies the route day by day, the vehicle drives along, title card per day.

### C. Time-lapse as a real film / Zeitraffer als echter Film
- [x] **Storyboard instead of a sliding day counter**: world view → zoom into a trip → route animates → zoom out;
      everyday life is skipped (or shown as a short "weeks at home" interlude).
- [x] Chapters per year with a title screen and an animated year summary (km, countries, longest trip).
- [ ] Glowing comet trails, vehicles, animated counters, small country flags when a new country appears.
- [ ] Modes: "Trips only", "Everything", "One person / group".
- [x] **Export as video** (WebM, in the browser) to share.

### D. New ways to look at your data / Neue Ansichten
- [ ] **Year in review ("Wrapped")**: swipeable story slides – km, countries, new regions, top trip, most visited place.
- [ ] **Globe** for long-haul trips (rotating, orthographic).
- [ ] **Time range slider** (from–to with two handles + play) shared by all maps.
- [ ] Together vs. apart: where did two persons travel together, shown side by side.
- [ ] Tracks: favourite routes highlighted, colour by time of day (morning/evening).
- [ ] Places & days: animated calendar heat map, "play this day".
- [ ] Regions: "sticker album" with progress rings per country, new regions sparkle.

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

## Dashboard (0.10.0 gebaut)
- Gebaut: die 10 Design-Ideen als Dashboard-Kacheln, 5 fertige Dashboards (Übersicht, Jahresrückblick, Familie,
  Entdecker, Wandtablet) und eine eigene Auswahl.
- Offen / Ideen: Postkarte als Bild speichern oder teilen · Wandtablet als eigene Seite ohne Kopfzeile für das
  Küchen-Tablet · eigene CO₂-Faktoren als Einstellung · Kacheln per Ziehen umsortieren · Dashboard-Wahl pro Gerät im
  Add-on statt nur im Browser speichern.
- Animations-Ideen (A1–A10) warten noch auf Feedback.
