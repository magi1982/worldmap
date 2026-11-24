# Security policy

## Reporting a vulnerability

Please report security issues privately via GitHub: **Security → Report a vulnerability** in this repository.
Do not open a public issue. You will get an answer within 7 days.

## Design

- The web UI is only reachable through Home Assistant Ingress; the server accepts connections from the Ingress proxy only (`172.30.32.2`).
- No secrets in the repository. The add-on uses the `SUPERVISOR_TOKEN` provided at runtime.
- All database access is parameterised; all user input is validated and size-limited.
- XML imports (GPX/KML) are parsed with defusedxml and reject DTDs, entities and external references (XXE, billion laughs); CSV exports neutralise spreadsheet formulas.
- Google Maps short links are resolved by asking one fixed address (`https://maps.app.goo.gl/<id>` or `https://goo.gl/maps/<id>`, rebuilt from constants, the id checked); the place is read from where it points, nothing else is fetched.
- Text parsing uses regular expressions with bounded or unambiguous repetition (no ReDoS); the map-style editor ignores `__proto__`/`constructor`/`prototype` keys.
- Strict Content-Security-Policy, no inline scripts, all API text is escaped in the UI.
- The optional OwnTracks endpoint (port 8098, disabled unless mapped) accepts only `POST` with HTTP Basic auth, compares credentials in constant time, slows down failed attempts and locks an address out for 15 minutes after 10 wrong passwords in 10 minutes. Use it in your local network only (or behind a VPN) – Basic auth is not encrypted on plain HTTP.
- Both servers close connections that stall (no hanging threads); extra headers: Permissions-Policy, Cross-Origin-Opener/Resource-Policy.
- Online place search (optional) talks only https to OpenStreetMap Nominatim or Google Places and sends only the search word; Google Maps links are followed only over https and only to Google hosts. The Google key stays in the add-on options and is never sent to the browser or logged.
- Estimated routes (optional, `route_service`) talk only https to `routing.openstreetmap.de` (FOSSGIS OSRM) or `routes.googleapis.com`. Only two coordinates per leg are sent, rounded to about 2 km (never the exact home, never names, dates or people), at most one request a second, each leg once (cached). The Google key goes in a request header, never in a URL or a log line. `offline` sends nothing.
- Map matching runs locally; only map tiles are downloaded by tile number.
- CI runs tests, Ruff, Bandit, pip-audit (add-on and dev tools), a JavaScript syntax check of all scripts, a privacy guard and CodeQL; GitHub Actions run on Node 24 with read-only permissions and without stored git credentials. Dependabot keeps dependencies and actions current.

## Privacy

Location history is personal. It is stored only in the add-on's `/data` folder (included in Home Assistant backups).
The repository contains invented sample data only.
- Own AppArmor profile (`worldmap/apparmor.txt`): read-only system and code, writes only to `/data` and temporary files, no mount, no ptrace, no admin capabilities. Together with Ingress this gives the highest security rating Home Assistant hands out (8).
