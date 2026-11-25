# Changelog

## 0.16.2 – 2026-11-25

### Fixed
- **🎨 drawer on the map**: buttons, switches and sliders did nothing since 0.15.1. The safer style setter (no
  prototype pollution) could not see the drawer's live-style proxy; the proxy now answers that check. A test
  guards it.
- Saving into a preset no longer resets unsaved changes on the map – only "Laden" changes what you see.
- Phones: the 🎨 drawer is a bottom sheet over the whole page (78 % of the screen) instead of a small box inside the
  map that cut off its own buttons; the preset list scrolls on its own.

## 0.16.1 – 2026-11-25

### Changed
- The 🎨 button on the map shows only the essentials: your three presets, then base map, light/dark and the look
  of places & flights; this map's own settings are folded away, everything else is under "Alle Einstellungen".
- "Kartenstil" settings page starts with **Meine Designs**: three boxes with name, a short summary
  (base map · look · light/dark), "Übernehmen", "💾 Aktuelles hier speichern" and "☆ Als Start", plus a
  three-step explanation. The box that matches what is set right now is highlighted.
- The quick bar on the map hides while the 🎨 drawer is open (the drawer has the presets itself).

## 0.16.0 – 2026-11-25

### Added
- **🌍 Earth base map**: a drawn landscape (forests, mountains with snow, deserts, steppe, ice) as ready-made WebP
  picture tiles for the whole world down to zoom 5, shipped with the add-on. Home Assistant only serves files
  (`/tiles/earth/<z>/<x>/<y>.webp`, numbers only, cached for a year); deeper zoom uses the closest level.
  Build tool in `tools/earthtiles/`.
- **Looks for places and flights** (`map.look`): ⭐ stars, 💎 crystals (flights as comets) and 🏅 medals with the
  number of visits; flights get an aircraft with a shadow and a trail that fades in. "Classic" stays the default
  and draws the map exactly as before.
- **Preset 1–3**: save the current look into one of three presets, rename them, load them with one tap from the
  quick bar on the map, and mark one with ★ as the design the map opens with. Stored on the server, so every
  device sees the same presets (`POST /api/style/presets/<1-3>` with `save`, `rename`, `default`, `load`).

### Security
- Preset names are cleaned (no control characters or angle brackets, max. 24 characters) and escaped when shown;
  preset styles go through the same schema validation as every other style.
- The tile route only accepts numbers and checks them against the zoom level before touching the file system.

## 0.15.1 – 2026-11-24

### Security (CodeQL findings)
- Google Maps short links: only a fixed short-link address is ever requested, rebuilt from constants with a checked
  id; the place is read from the redirect without following it (server-side request forgery).
- GPX/KML are parsed with defusedxml (new dependency) in addition to the DTD/entity check (XML entity expansion).
- Regular expressions in trip-list stations, place names and Google coordinates rewritten without ambiguous
  repetition, inputs capped (polynomial ReDoS).
- Trip wizard: values from date and number fields are checked and escaped before they are shown (DOM text as HTML).
- Map-style editor: setting a style key can no longer touch `__proto__`, `constructor` or `prototype`
  (prototype pollution).

## 0.15.0 – 2026-11-24

### Added
- **New trip postcard**: the real map of the trip (coastlines, borders, rivers, a graticule) with the route as it
  was – flight and seaplane arcs, roads, ferries, GPS tracks –, "Grüsse aus" lettering, a perforated stamp with the
  country code and a postmark with the date. Tap (or Enter) turns it over: greetings, dates (also "Juli 2009"),
  nights, km per transport, who was there, the stations and an address field. Swipe, ‹ › or the arrow keys browse,
  🎲 shows a random trip, ⬇ saves the front as a PNG (made in the browser). The wall-tablet view turns it every 15 s.

### Changed
- The **Dashboard is the first tab**; Worldmap still opens on the map (Reisen).
- Dashboard views are picture cards with an icon, a colour and one line (no longer look like the tab bar); people
  and groups are round avatars in their colours; "Kacheln" is now "✏️ Anpassen". The postcard comes right after the
  key figures and is twice as wide.

## 0.14.0 – 2026-11-24

### Added
- **Vague dates**: a trip can have exact days, only a month or only a year. The trip list has one *When* column that
  understands "13.–25.07.2009", "13.07.–25.07.2009", "Juli 2009", "Juli–August 2009", "07.2009" or "2009" (also
  "ca. 2009"). Maps, film, statistics and sorting use a stand-in stay in the middle of the month or year, shown with
  "~". The trip wizard stores what you knew; trip lists (a *When* column or vague Von/Bis), Worldmap packages
  (`"when"`) and the CSV export carry it. Old wizard trips that knew only the year or month are marked on update.
- **Data & import** tab: Import and Connections are one page that starts with "So kommen Daten in Worldmap" – by
  hand, Worldmap package (the standard format of this map), Google Timeline, Home Assistant app (on the road only
  with Home Assistant Cloud / Nabu Casa or your own remote access), OwnTracks, iPhone, photo galleries with exiftool
  (ready command), asking Claude to list photo GPS data (ready question), other files.
- **Convert with AI**: a ready prompt describing the Worldmap format with a copy button and a sample file
  (`beispiel.worldmap.json`).
- Info buttons pulse gently until they were opened once (off with "reduce motion").

### Improved
- Worldmap packages also read trips with `"when"` and stations (`"legs"`), points as objects
  (`{"time", "lat", "lon", "person"}`), times in milliseconds or ISO text, and add unknown persons.
- Import messages and previews are in German and say what was skipped and why (rows without date or destination,
  positions without valid time or coordinates, trips with only a month or year).
- Clearer wording on the questions and notifications pages; old `#connectors` links open the new tab.

## 0.13.0 – 2026-11-24

### Added
- **Real roads for trips entered by hand**: every car / camper / bus leg of a trip without GPS is asked once from a
  routing service and the real way is drawn as a dashed estimate. New option `route_service` (also in the app under
  Connections › Estimated routes): `osm` (default – the free OpenStreetMap routing server of FOSSGIS), `google`
  (Google Routes API with your key; 10,000 free requests a month) or `offline`. Flights stay arcs between airports,
  ships stay ferry lines, trains keep the built-in estimate.
- Button **"Routen neu berechnen"** to ask all estimated routes again.

### Privacy & security
- Only start and end of a leg are sent, rounded to about 2 km; never names, dates or people. https only to the two
  routing hosts, at most one request a second, each leg once (stored, also across restarts). The Google key is sent
  in a header and never logged.
- When the service fails or answers a far detour, the offline estimate is shown and the leg is asked again an hour later.

## 0.12.6 – 2026-11-24

### Fixed
- **Lone stray points** (a photo with a wrong GPS tag, a single Google point at home in the middle of a holiday) no
  longer draw flights that never happened: a point far away that comes straight back, with nothing on the way, is
  ignored for the map and for trip detection – unless it is impossible anyway, only when no "flying" hint and no
  trip there speak for it.
- **Huge detours on estimated roads**: the offline road network has small holes at junctions; loose road ends are now
  joined to the nearest point *on* another road (not only its corners), so motorways connect (Zürich → Bern on the
  A1, not over the Klausen pass; no loop far north on the way to the Atlantic coast). A way longer than 2× the
  straight line (+20 km) – where the coarse data simply lacks the road – is not drawn; mountain routes (Gotthard,
  Brenner) stay.
- **Flight ends recorded only after landing** (first point at home, nearer to another airport) use the airport the
  same trip really flew from (out from ZRH, back to ZRH – not to FDH).
- Airports guessed from GPS stations no longer override recorded flights (Paris stays CDG), and a GPS station only
  gets an airport when the landing point is really at the airport.

## 0.12.5 – 2026-11-23

### Added
- Stations can be moved up and down (▲ ▼) in the "+" wizard and in the trip list.

### Changed
- Airport search understands "Male Flughafen", "Malé Airport", "Flughafen Zürich": words that only say "airport"
  are ignored and airports come first in the results. Towns and names match whole words only, so "Male" no longer
  finds Tamale or Trincomalee.

## 0.12.4 – 2026-11-23

### Security
- OwnTracks endpoint: an address that sends 10 wrong passwords within 10 minutes is locked out for 15 minutes
  (answers 429); connections that stall are closed after 30 s.
- Web UI: stalled connections are closed after 60 s; new headers Permissions-Policy (no location, camera,
  microphone, payment, USB), Cross-Origin-Opener-Policy and Cross-Origin-Resource-Policy.
- GPX/KML import: DTD/entity declarations are refused anywhere in the file, not only in the first 64 KB.
- Google Maps short links are only followed over https.
- CI: GitHub Actions on Node 24 (checkout v6, setup-python v6, CodeQL v4) without stored git credentials;
  pip-audit also checks the dev tools; all JavaScript files are syntax-checked.

## 0.12.3 – 2026-11-23

### Security
- The online place search refuses any address that is not https to its two services (OpenStreetMap Nominatim,
  Google Places) before it connects – the automatic security scan (Bandit) had flagged the open call since 0.9.0.
- The airport search logs a failed town lookup instead of silently ignoring it. The CI checks are green again.

## 0.12.2 – 2026-11-23

### Fixed
- A trip with "Flug via Dubai · Wasserflugzeug" to an island resort was drawn as a flight to Malé and a **ferry**
  to the resort, without Dubai. Old transport texts now become stations: ✈ DXB → ✈ MLE → seaplane straight to
  the resort (a seaplane needs no airport at the end). "Fähre" counts as ship, "U-Bahn"/"Tram" as train; words
  without a transport ("Ski", "unknown") are left out, so such stations can be edited and saved again.
- Migration (once, at start): stations made from old trip fields are made again with the clean words and stopovers.

### Changed
- Airport search also takes a country ("Malediven" → MLE, "Griechenland" → ATH, HER, …) and the airports all over
  an island or region.
- Clearer seaplane icon.

## 0.12.1 – 2026-11-23

### Fixed
- Flights recorded as "in train" or "in car" by Google (e.g. 600 km in 1.5 h) were drawn as railway or road lines.
  Nothing on the ground is faster than ~320 km/h (train) or ~200 km/h (car): faster is a flight now.
- Trips set to "Flug" by hand no longer show long ways on the ground: stray positions (e.g. photos jumping between
  home and the destination) are ignored there, and when no flight was recorded the flight is drawn from your
  airport to the destination's airport.

### Added
- Trip list: columns "Countries" and "Transport" are back (from the stations, read-only) with a pick-list filter
  each, and a "Sort" picker above the list: newest/oldest, km up/down, longest/shortest, name, country, who.
  Empty values always go to the end.

## 0.12.0 – 2026-11-23

### Changed
- **A trip = a name + stations.** Where a trip went is only given as stations (places or airports, in order), each
  with its own transport. The trip list shows "Name" and "Stations" (as chips with the transport); the columns
  "Destination", "Country", "Transport" and "Confidence" are gone – countries and transport follow from the
  stations and can still be filtered by typing in the stations filter. The wizard asks for a name and the stations;
  the separate transport step is gone. A country alone ("Kenia") is a stop without a point and keeps its
  "where exactly?" question; the answer goes into that stop.
- **Migration** (once, at start): every trip gets a station from its old destination, country, position and
  transport; the old destination becomes its name. Checked on a real-sized database: all trips stay where they
  were on the map.

### Added
- **Seaplane** as transport: a low, short arc straight to the place, no airport, with its own icon (plane with
  floats); counted as flight km.
- **Stations from recordings**: trips found in Google Timeline, OwnTracks, Home Assistant positions, photo GPS or
  GPX get their stations from the places where you slept (several nights at one place = one station; a night just
  before home on the way back is none), with the transport found on the way; a flight lands at the real airport,
  which becomes a station of its own when the place is further away. Stations you edited are never replaced;
  stations found in the recording never change your trip's name, point, country or transport, and do not change
  the estimated route of trips without a full recording.
- Trip lists: a "Stations" column is exported ("✈ DXB [Flug] → Abu Dhabi [Auto]") and read back on import;
  "Name" works as column name for the trip name.

## 0.11.0 – 2026-11-23

### Added
- **Airports as stops**: one search per stop finds places *and* airports – by town, airport name or code
  ("Dubai" shows the town, ✈ DXB and ✈ DWC; "Mailand" finds MXP, LIN, BGY). Nobody has to know the codes.
  An airport stop is exactly where the plane lands; the next stop starts from there (✈ DXB → 🚗 Abu Dhabi).
  Every stop, also the first one, has its own transport. "Departure from" above the stops picks another airport
  than your home airport (searchable by name too). Same in the "+" wizard and in the trip list (button "Stations").
- Airport stops are labelled ✈ code on the map and on the dashboard postcard.

### Changed
- The separate "Airports" column in the trip list is gone – it is part of the stops now.
- **Migration** (runs once when the add-on starts): an airport set at the destination becomes an airport stop
  (trip without stops: [✈ airport, 🚗 destination]; trip with stops: the airport before its last flight's stop).
  The departure airport stays. Unknown codes are left as they are. GPS flights use the airport stop like before.

### Fixed
- 0.10.2 is included: a trip with a ferry comes home the same way.

## 0.10.2 – 2026-11-23

### Fixed
- A trip by car to a port and on by ship to an island (car to Piombino, ferry to Corsica) showed two ships: the way
  home took the shortest ferry from somewhere else. A trip with a ferry now comes home the same way it went
  (Corsica → Piombino → home); the way back is not drawn a second time on the map.

## 0.10.1 – 2026-11-23

### Changed
- Brings together 0.7.2 (made in parallel) and 0.8.0–0.10.0. Estimated car routes now use both: the offline world
  road network always, refined with the detailed OpenFreeMap roads when they can be loaded (otherwise the offline
  route stays). Legs of trips with several stops get the same refinement. Airports set by hand still win; an island
  without a big airport flies to the big one nearby and goes on by ferry or road.

## 0.10.0 – 2026-11-23

### Added
- **Dashboard** (new tab 6): the trips as numbers and small pictures instead of a map – key figures, around the world
  and to the moon, records, a country passport with stamps, a postcard per trip with its route and stops, a calendar of
  travel days, a timeline with one lane per person (shared trips join the lanes), a travel wheel by month and transport,
  favourite places, km and a rough CO₂ estimate per year, and "white spots" (known regions per country).
  Five ready-made dashboards: Overview, Year in review (all tiles for one year), Family, Explorer and Wall tablet
  (big type, the postcard changes every 15 seconds, off with reduced motion). "Tiles" lets you pick your own set; the
  choice is kept in the browser. Every tile has an ⓘ explanation, follows the person/group bar, and works in light,
  dark and on phones. Tapping a trip in the records, calendar or timeline opens its postcard.

### Changed
- A browser that leaves a page while it is still loading no longer writes a stack trace into the add-on log.

## 0.9.0 – 2026-11-23

### Added
- **Trips with several stops**: add stops in order and how you got to each one, e.g. plane to Tenerife, ship to
  La Gomera – or plane to Sydney, camper to Canberra, train to Melbourne. Each leg is drawn its own way: planes as
  arcs between the big airports, cars along motorways and main roads, trains along railways, ships over the water,
  from the airport to the place by road, and a round trip by car gets its way back home. Stops show on the map and the
  travel film follows them in order. Works in the "add a trip" wizard and in the trip list (new column "Stops").
- **Online place search** when adding a trip (new options `place_search` and `google_maps_api_key`):
  OpenStreetMap (free, no key) or Google Maps (your own Places API key). Only the search word is sent; the built-in
  offline list always answers first.
- **Google Maps links**: paste a link from Google Maps into the search – the place and its coordinates are taken
  from the link (short links are followed, only to Google hosts).
- **Vague trips** (no place, only a country, no coordinates) are marked in colour in the trip list and can be
  filtered with "only vague".
- Style panel: denser (two switches per row, slider, value and label on one line) with ⓘ explanations.

### Changed
- Airports near any place on earth are found (the search radius grows with the distance asked for).

## 0.8.0 – 2026-11-23

### Added
- **Airports per trip**: in the trip list a new column "Airports" sets the departure and arrival airport of a trip's
  flights (outbound and return). The airports of your own flights are offered, any international IATA code works.
- **Trips without GPS follow real roads and railways**: an offline network of the world's main roads, ferries and
  railways (Natural Earth, public domain, ~2 MB) ships with the add-on. By car the way follows the motorways, by train
  the railways, ferries and the Channel Tunnel where needed. Straight lines are left for planes only.
- Long GPS gaps (no signal for a while) are drawn along the main roads / railways too instead of a dotted straight line.
- Adding a trip by hand: whole countries ("Kenia", "Thailand") and big cities all over the world ("Nairobi") can be
  picked as destination.

### Fixed
- A trip corrected by hand to "car" or "train" no longer shows a flight from fast GPS points (e.g. to Pula), and a
  trip entered by hand wins over a detected one on the same days.
- Country-sized estimated areas (e.g. "France & Spain") are no longer drawn as a huge circle.
## 0.7.2 – 2026-11-23

### Added
- **"Where exactly?" question** for trips where only the country is known ("Greece", "France & Spain"): type a
  town, island or region (or "don't remember" / "round trip"), and the trip moves to the right place on the map.
  More holiday regions are known (Costa Dorada, Costa Blanca, Costa del Sol, Santorini, Naxos, Paros, Corfu, Zakynthos,
  Chalkidiki, Peloponnese).

### Changed
- **Estimated car routes follow real roads**: trips without GPS by car now go over motorways and main roads
  (OpenFreeMap tiles at zoom 7 for the long way, the detailed zoom-12 network to and from the motorway) instead of a
  slightly bent line over a land grid. Routes are computed once and cached (`est-roads.json.gz`); while tiles are not
  loaded yet the rough estimate is shown and the map is built again later. With routing "off" nothing is downloaded.
- **Lines never move**: with the animation on, flight lines stay on the map like all other lines; only planes, trains,
  cars and ferries move. "Hide the line under the vehicle" now puts a small halo under planes too instead of cutting a
  moving gap into the line.

### Fixed
- A trip with **only a country** as destination no longer gets a point in the middle of the country (the middle of
  Greece is the Cyclades, the middle of "France & Spain" somewhere in Spain). The import no longer stores such a point,
  and points stored by older versions are recognised and dropped.
- **Islands without a big airport** (La Gomera): the plane now lands at the big airport nearby (Tenerife South) and the
  way goes on by ferry and road, instead of a flight straight onto the island.

## 0.7.1 – 2026-11-23

### Fixed
- The 🎨 style panel on the map could not be closed (and its sliders moved the map): taps inside the panel no longer
  reach the map.
- Estimated routes for trips without GPS now follow the land on a coarse offline land grid (around the Gulf of Lion to
  Spain, through Italy to the ferry to Corsica, to the Channel to England) and are drawn as a solid soft line, so they no
  longer look like flights; ferries are only drawn where there is no way by land.
- Flights without GPS only get an airport tag when the destination has a big airport within 60 km (London → LHR,
  Vienna → VIE); no more guessed island airports.
- Map data is recomputed after every add-on update (the cache key now includes the code version) and is no longer
  recomputed after every restart.

## 0.7.0 – 2026-11-23

### Added
- **Settings for every map**, live on the map: a 🎨 button opens a drawer with the settings of the map you are looking at,
  every change shows at once, "Save" makes a version. The settings page lists all of them and shows your own map as live
  preview (Trips, Tracks, Places & days, Regions, Travel film).
  - Trips: arc height, line width, destination dot size, which names and how big, IATA tags.
  - Tracks: line width, opacity, opacity of everyday life, glowing lines, IATA tags, gaps.
  - Places & days: circle size by days/visits (min/max), style (filled/ring/glow), colour by person/year/days,
    which names, from how many days, label size, hide overlapping names.
  - Regions: colour by first year/days/stay, fill opacity, region borders (visited countries/all/none) with colour,
    width and opacity, country border width, region names.
- **Estimated routes** for trips without GPS (old holidays by car or train): a soft line from home to the destination;
  where it crosses the sea it becomes a dotted ferry (Corsica, England, islands). Settings: on/off, line type,
  opacity, curve, ferries.
- **Animation choices**: planes, trains, cars and ferries each on/off, from which distance each appears, how many at the
  same time, separate tempo. Planes now fly at the **same speed** on short and long routes. Ferries sail on sea legs.
- **Areas that melt together**: the semi-transparent areas are one organic shape per person instead of circles on
  circles (shape, size, how strongly they connect, soft edge, opacity, outline width and colour).
- **Travel film** replaces the time-lapse: the camera flies from trip to trip (zooming out on long jumps), the route
  draws itself with its vehicle, title card per trip, year chapters with km/trips/countries, counters, cinema look;
  tempo, stay time and minimum distance are settings; jump to a year; **save as video** (WebM, in the browser).

## 0.6.3 – 2026-11-23

### Fixed
- After an update the browser loads the new version at once (no Ctrl+F5 needed): pages are never cached, scripts and
  data files carry a version fingerprint.

## 0.6.2 – 2026-11-23

### Fixed
- **Airports**: flights now start and end at the real airport (OurAirports data, public domain, offline) with a small
  IATA tag on the map. A flight recorded in pieces (points every few minutes in the air) is one flight again instead of
  several hops over random airports; 0-minute "jumps" and taxiing are no longer flights.
- Flights without GPS start at your **home airport**: the airport most of your recorded flights start from, or the new
  option `home_airport` (IATA code, also in Settings → Home). Destinations use the big airport (London → LHR).
- **Trips without coordinates** (older trip lists, packages) were drawn at home. Their place is now found offline by name:
  German and other names of world cities (Wien, Mailand, Genf), countries (Kenia), holiday towns with an airport,
  and the trip distance picks the right one (Brühl near Cologne, not near Mannheim). Unknown places are no longer shown
  at home.
- **Interrupted lines**: gaps without a known road or rail route are drawn as a fine dotted link in the same colour
  instead of leaving the line open. New map style option "Gaps without a known route": dotted / straight line / open.

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
