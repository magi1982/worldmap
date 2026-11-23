<p align="center"><img src="worldmap/logo.png" alt="Worldmap" width="360"></p>

<p align="center"><b>Alle Reisen auf einer Karte – direkt in Home Assistant, komplett lokal.</b><br>
<a href="README.md">🇬🇧 English</a></p>

Worldmap ist ein Home-Assistant-Add-on, das sammelt, wo du überall warst – live von den Handys, aus Exporten der
Google-Zeitachse und aus Reiselisten. Es erkennt Reisen, stellt ein paar kluge Fragen („Wer war dabei?“) und zeigt alles
auf einer schnellen, schönen Karte mit fünf Ansichten. Alles läuft im Add-on, kein Cloud-Dienst nötig.

![Karte](docs/images/map.jpg)

> Alle Screenshots zeigen erfundene Beispieldaten („Alex“ und „Sam“).

## Funktionen

| | |
|---|---|
| 🗺️ **Fünf Kartenansichten** | **Reisen** (wer war wo und womit, Ziele, Flugbögen, geschätzte Flächen für Reisen ohne GPS), **Spuren** (jeder Weg, gefärbt nach Verkehrsmittel, Jahr oder Person), **Orte & Tage** (wo ihr Zeit verbracht habt, Kalender mit jedem Tag), **Regionen** (Kantone, Bundesländer und Provinzen weltweit) und **Zeitraffer** (eure Geschichte als Film, Stunde für Stunde, mit fliegenden Flugzeugen und Zeitleiste). |
| 🛤️ **Echte Bahn- und Strassenlinien** | Lücken zwischen GPS-Punkten werden auf das echte Bahn- und Strassennetz aus OpenStreetMap gelegt. Das Netz entsteht aus Kartenkacheln, die einmal per Kachelnummer geladen und im Add-on gespeichert werden – es werden nie Positionen gesendet, danach läuft alles offline. Lücken ohne plausiblen Weg bleiben offen statt gerade Striche. |
| ❓ **Kluge Fragen – ohne KI** | Ähnliche Reisen (gleiche Gegend, gleiche Art Tag, gleicher Vorschlag) kommen als **eine** Frage – eine Antwort für alle. Antworten lassen sich als **Regel** merken, dieselbe Frage kommt nie wieder. Antworten: jede Person und Gruppe, „Keine Reise (Alltag)“, „Mit Reise davor zusammenlegen“, „Einzeln fragen“. |
| 👥 **Personen & Gruppen** | Einzelpersonen und Gruppen (Paar, Familie …) mit Farben. Oben in jeder Karte: alle, eine Person oder eine Gruppe antippen. Zuhause und Arbeit mit Umkreis; die Arbeit erscheint nur auf der Karte, wenn du es einschaltest. |
| 📋 **Reiseliste wie in Excel** | In den Einstellungen: Filter pro Spalte, sortieren, Zellen direkt bearbeiten, Zeilen löschen, Zeilen direkt aus Excel oder Google Sheets einfügen (Strg+V). Doppelte werden erkannt. |
| 📥 **Alles importieren** | Reiselisten (CSV/Excel mit Von, Bis, Ziel …) – die Ziele landen automatisch auf der Karte –, Google-Zeitachse (Takeout und Export vom Handy, Android und iPhone), iCloud-/exiftool-Foto-CSV, jede CSV/Excel mit Koordinaten, GPX, KML. Eine Vorschau zeigt, was gefunden wurde; Vorhandenes wird nicht doppelt gespeichert. |
| 📡 **Live ohne Cloud** | Positionen aus `person.*`- / `device_tracker.*`-Entitäten und ein eingebauter **OwnTracks**-Empfang: das Handy sammelt unterwegs und schickt alles, sobald es wieder im Heimnetz ist – ohne Nabu Casa, ohne offenen Port ins Internet. |
| ✍️ **Reisen von Hand** | Der „+“-Knopf fragt kurz nach (wohin, wann, wie lange, wer, womit, wie gross war die Gegend) – für alte Reisen ohne Daten. |
| 🔔 **Benachrichtigungen** | Eines deiner Handys wählen (wird automatisch gefunden) oder Hinweis in Home Assistant, wie oft (sofort, täglich, wöchentlich), Test senden. |
| 🌙 **Hell & dunkel** | Folgt dem System oder dem ☾/☀-Knopf auf der Karte; Seen, Grenzen und Küsten bleiben auch im Dunkeln sichtbar. |
| 📊 **Sensoren** | `sensor.worldmap_km_this_year`, `sensor.worldmap_trips`, `sensor.worldmap_countries`, `sensor.worldmap_open_questions`, `sensor.worldmap_last_trip`. |

| Spuren | Orte & Tage | Regionen | Zeitraffer |
|---|---|---|---|
| ![Spuren](docs/images/spuren.jpg) | ![Orte](docs/images/orte.jpg) | ![Regionen](docs/images/regionen.jpg) | ![Zeitraffer](docs/images/zeit.jpg) |

| Personen & Gruppen | Fragen | Reiseliste |
|---|---|---|
| ![Personen](docs/images/people.jpg) | ![Fragen](docs/images/questions.jpg) | ![Reiseliste](docs/images/trips.jpg) |

## Installation

1. In Home Assistant **Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories** öffnen und
   `https://github.com/magi1982/worldmap` hinzufügen.
2. **Worldmap** installieren, starten und **In Seitenleiste anzeigen** einschalten.
3. Worldmap öffnen → ⚙️ **Einstellungen → Personen & Gruppen**: Personen (mit Handy) und Gruppen wie Paar oder Familie anlegen.

## So kommst du an Standortdaten

| Quelle | Automatisch? | Wie |
|---|---|---|
| **OwnTracks-App** (iPhone & Android) | ✅ live, ohne Cloud | Einstellungen → Verbindungen → OwnTracks: Benutzer anlegen. In den *Netzwerk*-Einstellungen des Add-ons Port `8098` eintragen. In der App: Modus *HTTP*, URL `http://<IP-von-Home-Assistant>:8098/pub`, Benutzer und Passwort. Das Handy sammelt unterwegs und schickt zu Hause. |
| **Home-Assistant-App** | ✅ live | `person.*`-Entität mit GPS. Liefert nur, solange das Handy Home Assistant erreicht – von unterwegs braucht es Nabu Casa, ein VPN (WireGuard-/Tailscale-Add-on) oder eine eigene Domain. |
| **iCloud „Wo ist?“** | ✅ | HACS-Integration *iCloud3* (braucht die Apple-ID). |
| **Google-Maps-Zeitachse** | ⚠️ Export | Google speichert die Zeitachse nur auf dem Handy. Ab und zu exportieren (*Android: Einstellungen → Standort → Zeitachse → Exportieren*; *iPhone: Google Maps → Profil → Zeitachse → ⋯ → Exportieren*) und unter **Import** ablegen. |
| **Reiselisten** | ⚠️ Import / Einfügen | CSV oder Excel mit Spalten wie Von, Bis, Ziel, Land, Wer – oder Zeilen in die Reiseliste einfügen. |
| **Fotos** | ⚠️ Import | Aufnahmeort und -zeit als CSV exportieren (z. B. mit exiftool) und importieren; die Kamera ordnet die Fotos den Personen zu. |
| **Apple „Wichtige Orte“** | ❌ | Apple bietet keinen Export und keine Schnittstelle. |

## Einstellungen

Alles lässt sich in der App (⚙️ **Einstellungen**) oder in der Add-on-Konfiguration einstellen; jede Option hat eine Beschreibung.

| Option | Standard | Bedeutung |
|---|---|---|
| `persons` | – | `label` (Name), optional `entity` (`person.x` / `device_tracker.x`), `camera_models` für Foto-Importe |
| `owntracks` | – | `user`, `password` (≥ 8 Zeichen), `label` (Person) für den OwnTracks-Empfang auf Port 8098 |
| `groups` | – | `name`, `members` (Personen mit Komma), `extra` (Personen ohne Handy), `color` |
| `home_radius_m` | 0 | Umkreis Zuhause in Metern; 0 = Radius der Zone |
| `work_lat` / `work_lon` / `work_radius_m` | – / – / 300 | Arbeit; leer = automatisch erkannt |
| `show_work` | false | Arbeit auf der Karte zeigen |
| `min_trip_km` | 30 | ab dieser Entfernung zählt ein Tag als Reise |
| `routine_days` | 20 | Orte, an denen man an so vielen Tagen war (Arbeit, Schule), starten keine Reise; 0 = aus |
| `ask_below` | `hoch` | fragen, wenn die Sicherheit tiefer ist |
| `school_holidays` | – | Zeiträume wie `2026-07-04..2026-08-09` – schlägt „Familie“ vor |
| `hint_keywords` | – | `Wort=Antwort` – wird vorgeschlagen, wenn ein Datei- oder Ordnername das Wort enthält |
| `routing` | `tiles` | `tiles` = Bahn-/Strassennetz aus OpenStreetMap-Kacheln (nach dem ersten Laden lokal); `off` |
| `notify_service` / `notify_mode` | – / `weekly` | z. B. `notify.mobile_app_handy`; `off`, `instant`, `daily`, `weekly` |

## Datenschutz & Sicherheit

- Der Standortverlauf bleibt im Ordner `/data` des Add-ons (Teil deiner Home-Assistant-Backups). Nichts wird hochgeladen.
  Geladen werden nur OpenStreetMap-Kacheln per Kachelnummer (einmal, danach gespeichert).
- Die Oberfläche ist nur über Home Assistant Ingress erreichbar. Der optionale OwnTracks-Port nimmt nur angemeldete `POST`s an.
- Eingabeprüfung, parametrisiertes SQL, XXE-sicheres XML, CSV-Export ohne Formel-Einschleusung, Content-Security-Policy, escapte Ausgaben.
- CI: Tests, Ruff, Bandit, pip-audit, CodeQL, Dependabot, Home-Assistant-Add-on-Linter und ein Datenschutz-Check. Siehe [SECURITY.md](SECURITY.md).

## Entwicklung

```bash
pip install -r requirements-dev.txt
python -m pytest
python tools/demo.py /tmp/demo        # erfundene Beispieldaten
WORLDMAP_DATA=/tmp/demo WORLDMAP_ALLOWED_IPS=127.0.0.1 PYTHONPATH=worldmap/app python -m worldmap
# http://127.0.0.1:8099 öffnen
```

Ideen und Planung stehen in [NEXT.md](NEXT.md).

## Quellen

Karten- und Ortsdaten: [Natural Earth](https://www.naturalearthdata.com/) (gemeinfrei, auch die Regionen),
Ortsnamen: [GeoNames](https://www.geonames.org/) (CC BY 4.0). Bahn- und Strassennetz: © [OpenStreetMap](https://www.openstreetmap.org/copyright)-Mitwirkende
via [OpenFreeMap](https://openfreemap.org/).

Lizenz: MIT
