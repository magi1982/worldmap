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
- (Photo EXIF scan of folders: planned, not built – see "Photos as a location source" below.)
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

### 10 ideas (24.11., waiting for "mach es" per idea)
- [ ] 1 "Heute vor X Jahren": dashboard tile + wall tablet + optional notification, sensor (S)
- [ ] 2 Travel diary per trip: day by day place, km, transport, historical weather (Open-Meteo, cached), note per day (M)
- [ ] 3 Bucket list with automatic tick when first visited, "still open" tile (M)
- [ ] 4 Planned trips: status "geplant", dashed route, km/time/CO2, countdown sensor, school-holiday check (M)
- [ ] 5 3D globe (canvas, no library) with day/night and flight arcs, wall-tablet spin (M)
- [ ] 6 Poster to print (A3/A2, PNG/PDF made in the browser, templates world/Europe/year/person) (L)
- [ ] 7 Year story video 9:16 / 16:9 via MediaRecorder, home never shown (L)
- [ ] 8 Album per person: country stickers, region progress, badges, printable page (S)
- [ ] 9 Home Assistant sensors: on a trip, current country, day x of y, return in z days + blueprints (S)
- [ ] 10 Share safely: one offline HTML file without home/work/everyday life, simplified tracks, preview (M)

### Security gate: open alerts turn the checks red (waiting for "mach es")
- [ ] New job "Security alerts" in codeql.yml after the analysis (also weekly): lists the open **code scanning**
      and **Dependabot** alerts of the repo with the workflow token (`security-events: read`) and fails when one is
      open – each alert as an error line (rule, severity, file:line). Like this an open finding is a red check that
      is seen after every push, without reading the Security tab.
- [ ] Same for family-planer.

### Dashboard first, clearer choices, a real postcard (done in 0.15.0)
- [x] Tab order: **Dashboard first** in the bar (1 Dashboard, 2 Reisen, …), but Worldmap still **opens on the map**
      (Reisen) – a remembered last tab is not used; number keys follow the new order.
- [x] Dashboard controls look different from the tab bar: the views (Übersicht, Jahresrückblick, Familie,
      Entdecker, Wandtablet, Eigene) become small picture cards with an icon, a colour and one line; "Anzeigen für"
      becomes round avatars in the person colours; "Kacheln" / "bearbeiten" become one clear "✏️ Anpassen" button.
- [x] **Reise-Postkarte, much better**: a real postcard look – front with the real map of the trip (coastlines,
      the route as recorded or estimated: plane arcs, car/train lines, ship lines, stations with their icons),
      big handwritten-style place name, a stamp with the country (colour, perforated edge) and a postmark with date
      and place; flip it (tap) to the back: "Grüsse aus …", dates or "Juli 2009", nights, km per transport, who was
      there, stations in order, address field with home. Swipe / arrows for the previous and next trip, "Zufall"
      for a random memory, "Als Bild speichern" (PNG, made in the browser). Wall-tablet view turns it every 15 s.
- [x] Tests (tab order, postcard data for trips with stations / only a country / vague dates), README EN/DE,
      new screenshots.

### Vague dates, "Daten & Import" tab, AI helper (done in 0.14.0)
- [x] Trips can have a day, only a month or only a year ("summer 2009, don't know exactly"). New trip field
      `date_prec` = day | month | year; the trip list shows "13.–25.07.2009", "Juli 2009" or "2009". The date cell
      accepts "13.07.2009", "07.2009", "Juli 2009" or "2009" (a range of years like "2008–2009" is NOT built – one year only); the wizard already asks
      year / month and now stores the precision too. Map, film, dashboard and sorting use a representative date
      (mid-month / mid-July), shown with "~". Migration: hand trips marked "approx" from the wizard get month/year
      precision when their dates are the wizard placeholders; everything else stays "day". Worldmap package, CSV
      export and the trip-list import carry the field.
- [x] "Import" and "Verbindungen" become one tab **"📦 Daten & Import"** (rarely used, so it explains itself):
      1. "So kommen Daten in Worldmap" – short overview cards: Worldmap-Paket (the standard format of this map,
         backup / move / import), Google Zeitachse (phone export), live from Home Assistant / OwnTracks, files
         (GPX, KML, CSV/Excel trip lists, photo CSV), Apple users (no timeline export: OwnTracks, photos), and
         "everything else: let an AI convert it" (below).
      2. Drop zone + past imports (as now). 3. Connections (as now).
- [x] Small box **"Andere Daten? Mit einer KI umwandeln"**: a ready prompt with the Worldmap JSON format (trips +
      points, field list, a short invented example) and a copy button – paste it into any AI together with your
      own file, get back a `*.worldmap.json` to drop in here. Also a download "Beispiel.worldmap.json" (sample data).
      Hint: only share what you are fine giving to that AI service.
- [x] Wording & design: buttons get short, telling names; every longer explanation moves behind an "i" info button
      that gently pulses (stops after it was opened once, respects "reduce motion") so you see there is help.
- [x] Overview "So kommen Daten in Worldmap" also lists:
      - **Von Hand**: "Reise von Hand" wizard and editing in the trip list (with vague dates).
      - **Home Assistant Companion app**: sends GPS only while Home Assistant is reachable – on the road that needs
        remote access, i.e. Home Assistant Cloud (Nabu Casa) or your own VPN / domain; it does not keep positions
        while offline.
      - **OwnTracks**: collects positions on the phone and sends them when you are home again (no Nabu Casa, no open
        port) – step by step with URL, user, password.
      - **Photo galleries with exiftool**: one ready command (`exiftool -csv -n -r -GPSLatitude -GPSLongitude
        -DateTimeOriginal <folder> > fotos.csv`, Windows/Mac/Linux) and drop the CSV here.
      - **Ask Claude**: e.g. "list GPS and date of all photos in my iCloud Photos folder on Windows (or the Photos
        library on the Mac) as CSV" – with folder access in the Claude desktop app – then drop the CSV here.
- [x] Review of ALL settings pages (people, map style, trips, data & import, connections, notifications, questions &
      rules): one consistent layout, plain German, short labels, info buttons, no duplicate or dead options.
- [x] Import quality check: run every importer against the sample files and against malformed / mixed files
      (wrong date formats, comma vs. dot, swapped lat/lon, empty rows, duplicates, time zones, HEIC exiftool
      output, huge files); clear summary after each import ("1234 Punkte, 12 Reisen, 3 Zeilen übersprungen: …").
- [x] Tests (date parsing of all forms, sorting, migration, package round trip, importer edge cases), README EN/DE,
      changelog.

### Photos as a location source – for every user (waiting for "mach es")
- [ ] Scan photo folders for where and when each photo was taken (EXIF GPS + time). Only the metadata is read; photos
      are never copied, changed or sent anywhere. Read-only access to `/media` and `/share` (add-on `map`), so
      everything works that Home Assistant can mount there: a NAS share (Settings › System › Storage › network
      storage), a folder synced by iCloud for Windows / a Mac, Synology Photos, Google Photos Takeout, camera cards.
- [ ] JPG, HEIC (iPhone), PNG, ARW/CR2/NEF (EXIF only, no decoding). Videos (MOV/MP4 location) later.
- [ ] Apple: also read `.xmp` sidecar files (Mac Photos "Export IPTC as XMP" – locations added by hand), Live Photo
      pairs (HEIC + MOV) count once; README chapter "Apple users: Windows / Mac / iPhone only" with the ways to get
      the originals into a folder Home Assistant can see.
- [ ] Apple "Takeout": the ZIP parts from privacy.apple.com (Request a copy of your data › iCloud Photos) can be
      dropped into Import or into a folder under /share – read the EXIF of each photo inside the ZIP without
      unpacking it to disk, keep nothing but place + time. Big parts (up to 25 GB): folder way preferred over upload.
      README: step-by-step like the Google Timeline export.
- [ ] To test: upload photos straight from the iPhone in the app (photo picker) – read only GPS + time in the browser
      and send just those; check whether iOS keeps the location in that case.
- [ ] Settings page "Fotos": pick folders, assign each folder to a person or group (or "who was there" stays a
      question), scan now / every night, only new or changed files (cache of path + size + time).
- [ ] Photos become points with source `photo` (an extra "was really there" hint for stations and questions),
      not a GPS track on their own; photos without GPS are skipped.
- [ ] Not planned: logging in to iCloud directly with Apple ID + password + 2FA inside the add-on (unofficial web API,
      breaks with Advanced Data Protection, the password would have to be stored).
- [ ] Tests with invented sample images (generated EXIF), privacy check: no real photos in the repo.

### Found while taking the README screenshots (waiting for "mach es")
- [ ] Trip list: the km column is empty for trips entered by hand (e.g. a round trip with stations), so they sort last
      with "km absteigend" – the dashboard already knows their km.
- [ ] Regions map: a trip entered by hand far away (Australia, 2017) is coloured like the first year of the GPS data
      (2023) instead of its own year; check which regions the stations of hand trips count.
- [ ] Stations popup: on a narrow row the × (remove) button wraps to its own line.

### Real routes for trips entered by hand (done in 0.13.0)
- [x] Car / camper / bus legs of trips without GPS asked once from a routing service, stored, dashed estimate
- [x] Option `route_service`: `osm` (FOSSGIS, default), `google` (Routes API), `offline`; fallback to the built-in network
- [x] Cache across restarts, 1 request a second, retry after an hour when the service fails
- [x] Only coordinates rounded to ~2 km are sent; documented in SECURITY.md / README
- [x] Tests with mocked services, no network in CI
- [x] One button "Routen neu berechnen" for all routes (on the Connections page, not per trip)

### Trips = name + stations (done in 0.12.0)
- [x] A trip has a **name** you choose ("Sommerferien Korsika"); *where* is only ever given as **stations**
      (places or airports, each with its own transport). The columns "Ziel", "Land" and "Verkehrsmittel" in the trip
      list become "Name" and "Stationen"; countries and transport are shown, filtered and counted from the stations.
- [x] New transport **Wasserflugzeug** (seaplane): a low, short arc straight to the place (no airport), own
      icon in the animation and the film, counted as flight km.
- [x] Field **"Sicherheit"** removed from the trip list and the wizard. Internally it stays (the questions use it):
      trips entered or edited by hand count as confirmed, imported ones keep their value.
- [x] **Migration** (once, at start): every trip without stations gets one station from its old destination,
      country, position and transport; the name becomes the old destination. Trips that only know a country get a
      station "Kenia (nur Land)" without a point – still marked as vague, still asked "where exactly?".
      Trips with stations keep them; transport moves into the stations (first station: the old trip transport).
- [x] Wizard: "Wie heisst die Reise?" + stations; the transport step disappears (it is in the stations).
- [x] Import (CSV/Excel trip lists with Ziel/Land/Verkehrsmittel) and export map to name + stations; the Worldmap
      package keeps working with old files. Dashboard, film titles and map labels use the name.
- [x] **Imports fill in the stations** when the data allows it: Google Timeline (Takeout and phone export), OwnTracks
      and Home Assistant positions, photo CSV, GPX/KML. The places where you slept or stayed (≥ 1 night or several
      hours) become stations in order, with the transport found on the way there (flight → airport station at the
      real airport, ferry → Schiff, train, car, foot). The nearest town names the station.
- [ ] Google's own place names (hotel, restaurant) as station names – the import does not keep them yet. Short stops on the way (petrol, lunch) are not stations. Stations you edited by hand are
      never overwritten by a later import.
- [x] Tests for migration, import of old lists, seaplane route, stations from a sample timeline; run on a copy of the private test data.

### Stations with airports – one picker for everything (done in 0.11.0)
- [x] One search per station finds **places and airports** by city, airport name or code: "Dubai" shows
      "Dubai (city)", "✈ Dubai International (DXB)", "✈ Al Maktoum (DWC)". Nobody has to know the codes.
- [x] A station is either a place or an airport. An airport station is exactly where the plane lands; the next
      station starts from there (✈ DXB → 🚗 Dubai Marina, or ✈ DXB → ✈ Bangkok BKK).
- [x] Choosing "Flug" for a station offers that city's airports first; if none is chosen the big airport nearby
      is taken automatically (as now).
- [x] "Abflug ab" above the list: automatic (your home airport) or search one by name (e.g. Basel, Milano Malpensa).
- [x] Same picker in the "+" wizard and in the trip list (button "Stationen"). The separate column "Flughäfen" goes
      away; airports already set there are shown as departure and as airport station (nothing is lost).
- [x] Map, travel film and dashboard postcard use the airport stations. Airport search works offline (OurAirports,
      large and medium airports worldwide). Tests for search, saving and the drawn route.

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

## Ideen Runde 2 (25.11.)
- Abgelehnt: 1 Heute vor X Jahren, 2 Reisetagebuch, 4 Geplante Reisen, 7 Jahres-Video, 8 Sammelalbum, 9 HA-Sensoren, 10 Sicher teilen
- 3 Reiseideen (Ja): eigener Bereich, nicht in der Reiseliste; Ort, wer, Jahreszeit, Notiz; automatisch abgehakt bei Reise im Umkreis (30 km, einstellbar); Dashboard-Kachel „Noch offen“
- 5 3D-Globus (Vorschau): Punkte-Globus, Tag/Nacht, Bögen nach Jahr, Flugzeug auf gewählter Route; Zoom passt sich an (regionale Daten → näher)
- 6 Poster (Vorschau): Neon/Papier/SW, A3/A2/50×50, Welt/Europa (automatisch), Beschriftung ohne Überlappung, Zahlen + Länder

### Feedback Runde 2 (25.11.)
- 3 Reiseideen: **Ja** (wie Vorschau)
- 5 3D-Globus: Verbessern – Ziehen fühlt sich seitenverkehrt an (Globus muss der Hand folgen); richtig reinzoomen; echte Karte statt Punkte, immer im gewählten Kartenstil (Hell/Dunkel/Neon/Miniwelt …); Vollbild-Knopf; Screenshot-Knopf mit Teilen
- 6 Poster: Verbessern – viel zu wenig Details; für A2 so detailreich wie die Karte selbst (Tracks, Stationen, Regionen, Länderfarben, Beschriftungen) in Druckauflösung
- Neu: Kartenstil „Miniwelt“ (Gelände aus Landumrissen: Wiesen, Wälder, Wüste, Gebirge mit Schnee, flaches/tiefes Meer; Wolken, Wellen, Flugzeuge; Nacht mit leuchtenden Orten; Minimap) – Vorschau geschickt, Antwort offen
- Miniwelt v1: Verbessern – zu weich, man sieht kaum, wo man war; Berge echter und detailreicher; Zoom muss gehen. Gewünscht: Catan-Stil, nur offline (kein Download von Reliefdaten)
- Miniwelt v2 (Vorschau): Sechseck-Spielbrett, Felder teilen sich beim Zoomen (≈150 km bis ≈1 km), Gebirge von Hand nach echter Lage (>120 Züge), besuchte Felder mit goldenem Rand, Siedlung und Zähl-Chip, Zuhause als Stadt, Minimap, Vollbild, Karte folgt dem Finger
- Miniwelt v2 (Spielbrett): Nein – „übel daneben“, kein Catan; Stil wie v1, aber cool und scharf
- Miniwelt v3 (Vorschau): v1-Stil ohne Weichzeichner; Küsten/Seen/Flüsse/Grenzen/Orte aus base.json als Vektoren; Relief aus Gebirgszügen + Gratmuster mit Schattierung und Schneegrenze nach Breite; Baumkronen, Felder mit Hecken beim Reinzoomen; eigene GPS-Spuren pink, besuchte Regionen umrandet, Reiseziele mit Nadel und Namen; Ebenen schaltbar; Zoom bis ca. 1 cm ≈ 2 km
- Miniwelt v4 (Minigame-Vektor) abgebrochen; stattdessen 10 Stilvorschläge auf Basis v1 (Game-Look, realistisch, minimal) – Antworten offen
- Kartenstil-Suche 25.11.: 4 Game-Karten, gemalte Welt (von oben), Alpen 5 Varianten (2 Runden), 5 Regionen; aktuell Anno-Stil (Relief + 3D-Bäume/Tannen/Akazien, Sicheldünen, Outback-Tafelberge, Wasser randlos) – Antwort offen. Offen: Flüsse ausserhalb Europas fehlen in base.json

## Neuer Kartenstil „Earth“ – Architektur für Leistung (Vorschlag 25.11.)
Problem Vorschau: Gelände wird bei jedem Zoom im Browser komplett neu gerechnet (Relief pro Pixel, Tausende Sprites, ganze Weltküste als Pfad) → 1–3 s CPU pro Bild, 20 % CPU, bis 1,5 GB RAM. Nicht reparierbar durch Feintuning.
Vorschlag: rechnen nur einmal, im Browser nur noch Bilder anzeigen.
- Kacheln vorberechnen (Web-Mercator, 256 px, WebP): z0–z6 Welt (~5’500 Kacheln), Detail z7–z9 nur rund um eigene Reisen bei Bedarf
- Erzeugung einmal beim Build (GitHub Action) bzw. einmalig im Add-on im Hintergrund; danach nur Dateien ausliefern (Cache, ETag)
- Gelände aus echten, freien Daten statt nachgebildet: Höhenmodell (z. B. ETOPO/GEBCO, gemeinfrei) + Landbedeckung (Natural Earth) → Alpen, Himalaya, Seen und Flüsse stimmen wirklich
- Browser: einfacher Kachel-Viewer (<img> + CSS-Transform, GPU), nur sichtbare Kacheln, max. ~60 im Speicher; Reisen (Spuren, Bögen, Farben) als eigene leichte Ebene, pro Zoom vereinfacht
- Ziele: Zoomen/Ziehen 60 fps, < 2 % CPU im Ruhezustand, < 150 MB RAM, erstes Bild < 0,5 s; funktioniert gleich auf Laptop, Handy, Wandtablet
- Gleiche Kacheln für Postkarte, Poster und Dashboard-Kacheln
- Speicher: z0–z6 ca. 60–120 MB; Option „Detailstufe“ (bis z5 ≈ 25 MB) als Einstellung
- Offen: Daten-Download beim Build ok? Kacheln im Add-on-Image mitliefern oder beim ersten Start erzeugen?
- Prototyp Kachel-Karte gebaut (25.11.): 2’676 WebP-Kacheln (Welt z0–5, Europa z6–8, Alpen z9, 25 MB), erzeugt per Headless-Chrome mit dem Earth-Stil; Viewer mit <img>-Kacheln + GPU-Transform, Reisen als eigene Ebene. Gemessen mit 4× gedrosselter CPU: längste Blockade 80 ms, 25 MB JS-Speicher, Bildaufbau < 4 ms. Gelände noch nachgebildet (keine echten Höhendaten).
- Trace 25.11. (Laptop): JavaScript nur ~3 s von 177 s; die GPU war bis zu 32 s am Stück blockiert. Ursachen: (1) Spuren als Pfad in Weltkoordinaten mit riesigem Zoom-Faktor gezeichnet, (2) gestrichelte Flugbögen, die beim Reinzoomen Millionen Pixel lang werden. Fix v2: alles in Bildschirm-Pixeln, nur sichtbarer Teil, eine einzige Canvas statt vieler Bild-Ebenen, grobe Spuren beim Rauszoomen. Gilt auch für die bestehende Karte – dort prüfen.
- Schwache HA-Hardware: Server liefert nur fertige Dateien (Kacheln, vereinfachte Spuren pro Zoom) mit Cache; nichts wird auf dem HA-Gerät gerechnet; Kacheln entstehen beim Build auf GitHub.
- Prototyp v3 (25.11.): Kacheln als Ebenen pro Zoomstufe, nur eine Transformation pro Bild; Reise-Ebene komplett in einem Worker (Seite zeichnet nichts); Spuren nur sichtbare Segmente, Unterpixel-Stücke weg (55'000 Mini-Teilpfade waren eine Raster-Falle). Gemessen (Hauptthread): Start 2,5×, Zoomen ~3,5×, Verschieben ~10× weniger Arbeit, keine Blockaden > 50 ms, 3 MB statt 64 MB Speicher. Restzeit = Browser-Zusammensetzen der Bilder.

## Map designs: base map × line style, 3 saved designs (idea, waiting for "mach es")
- Base map: Earth (tiles with trees, mountains), Light, Dark – every base works with every line style.
- Line styles: Classic (today's lines), Star journey (golden 3D stars, sparkling flight trails), Crystal quest (floating crystals, comet flights), Medals (bronze/silver/gold coin with readable visit count, ribbon from 6 visits).
- Nothing covers the map: no fog, no darkening, no area fills.
- Markers never pile up (a close smaller place merges into the bigger one); names never sit on another marker.
- "My designs": 3 slots (name + base + line style + colours + layers), quick-select bar on the map, one slot marked ★ as the default at start, slots can be overwritten and renamed any time.
- Settings: stored with the other map settings on the server (not only in the browser), so every device sees the same 3 designs.
- In the prototype Light/Dark are only filtered Earth tiles; the app keeps its real light/dark map designs.
- Flights: trail fades in towards the aircraft, aircraft casts a shadow (offset by height), max 14 at once.
