<p align="center"><img src="worldmap/logo.png" alt="Worldmap" width="360"></p>

<p align="center"><b>Alle Reisen auf einer Karte – direkt in Home Assistant.</b><br>
<a href="README.md">🇬🇧 English</a></p>

Worldmap ist ein Home-Assistant-Add-on, das sammelt, wo du überall warst – live aus der
Home-Assistant-App, aus den GPS-Daten deiner Fotos und aus Exporten von Google und Apple.
Es erkennt Reisen, stellt kurze Fragen („Wer war dabei?“) und zeigt alles auf einer schnellen,
schönen Karte.

![Karte](docs/images/map.jpg)

> Alle Screenshots zeigen erfundene Beispieldaten („Alex“ und „Sam“).

## Funktionen

| | |
|---|---|
| 🗺️ **Karte** | Spuren, Flugbögen und geschätzte Flächen für Reisen ohne GPS. Filter nach Person/Gruppe und Jahr. Verschieben und Zoomen bleibt flüssig, auch mit Millionen Punkten (Bild-Cache, vereinfachte Spuren je Zoomstufe, gzip). |
| 📋 **Reiseliste** | Durchsuchbare Liste mit Ziel, Land, Wer, Sicherheit, Nächten und Entfernung. Jede Reise lässt sich bearbeiten; deine Änderungen überschreibt die automatische Erkennung nie. Export als CSV für Excel. |
| ❓ **Kluge Fragen** | Für jede neue Reise schlägt Worldmap vor, wer dabei war – anhand davon, wer gleichzeitig weg war, Wochenenden, Schulferien und Wörtern in Fotoordnern – und fragt nur, wenn es unsicher ist. |
| ✍️ **Reise von Hand** | Ein kurzer Assistent für alte Reisen ohne Daten (*Wohin? Wann? Wie lange? Wer? Womit? Wie gross war die Gegend?*). Regionen wie „Korsika“ oder „Toskana“ bringen gleich eine passende Fläche mit. |
| 📥 **Alles importieren** | Dateien hineinziehen – das Format wird am Inhalt erkannt: Google-Zeitachse (Takeout und der neue Export vom Handy, Android und iPhone), iCloud-/exiftool-CSV, jede CSV- oder Excel-Datei mit Breiten-/Längengrad (deutsche oder englische Spaltennamen, Dezimal oder Grad-Minuten-Sekunden), GPX und KML. Eine Vorschau zeigt, was gefunden wurde, bevor gespeichert wird. |
| 🔌 **Verbindungen** | Live-Positionen aus `person.*`- / `device_tracker.*`-Entitäten, Fotoordner auf dem NAS, Benachrichtigungen – direkt in der App einstellbar. |
| 🛣️ **Echte Routen** | Lücken zwischen GPS-Punkten folgen echten Strassen (OSRM, optional); lange, schnelle Sprünge werden zu Flugbögen. |
| 🔔 **Benachrichtigungen** | Offene Fragen kommen aufs Handy (sofort, täglich oder wöchentlich) oder als Hinweis in Home Assistant. |
| 📊 **Sensoren** | `sensor.worldmap_km_this_year`, `sensor.worldmap_trips`, `sensor.worldmap_countries`, `sensor.worldmap_open_questions`, `sensor.worldmap_last_trip` für Dashboards und Automationen. |

| Fragen | Verbindungen | Reise von Hand |
|---|---|---|
| ![Fragen](docs/images/questions.jpg) | ![Verbindungen](docs/images/connectors.jpg) | ![Assistent](docs/images/wiz.jpg) |

## Installation

1. In Home Assistant **Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories** öffnen und
   `https://github.com/magi1982/worldmap` hinzufügen.
2. **Worldmap** installieren, starten und **In Seitenleiste anzeigen** einschalten.
3. Worldmap öffnen → **Verbindungen** und die Personen hinzufügen.

## So kommst du an Standortdaten

| Quelle | Automatisch? | Wie |
|---|---|---|
| **Home-Assistant-App** (iPhone & Android) | ✅ live | App auf jedem Handy installieren, Standort *Immer* erlauben. Die `person.*`-Entität liefert dann laufend GPS. **Empfohlene Hauptquelle.** |
| **iCloud „Wo ist?“** | ✅ | Die HACS-Integration *iCloud3* legt Geräte-Tracker für Apple-Geräte an. |
| **Fotos auf dem NAS** | ✅ | Freigabe unter *Einstellungen → System → Speicher → Netzwerkspeicher* einbinden (Verwendung *Medien* oder *Share*) und den Ordner in Worldmap eintragen. Ordnernamen helfen bei „Wer war dabei?“. |
| **Google-Maps-Zeitachse** | ⚠️ von Hand | Google speichert die Zeitachse nur noch auf dem Handy und bietet keine Schnittstelle. Ab und zu exportieren (*Android: Einstellungen → Standort → Zeitachse → Exportieren*; *iPhone: Google Maps → Profil → Zeitachse → ⋯ → Exportieren*) und unter **Import** ablegen. |
| **Apple „Wichtige Orte“** | ❌ | Kein Export, keine Schnittstelle. Stattdessen die Home-Assistant-App nutzen. |
| **GPX / KML** (Garmin, Strava, Komoot …) | ⚠️ von Hand | Datei unter **Import** ablegen. |

## Einstellungen

Alles lässt sich in der App (**Verbindungen**) oder in der Add-on-Konfiguration einstellen. Jede Option hat dort eine Beschreibung.

| Option | Standard | Bedeutung |
|---|---|---|
| `persons` | – | `entity` (`person.x` oder `device_tracker.x`), `label` (Name in der App), `camera_models` (Fotos dieser Kameras gehören zur Person) |
| `who_options` | `Paar`, `Familie` | weitere Antworten für „Wer war dabei?“ |
| `hint_keywords` | – | `Wort=Antwort` – wird vorgeschlagen, wenn ein Fotoordner das Wort enthält |
| `home_zone` / `home_lat` / `home_lon` | `zone.home` | wo zu Hause ist |
| `min_trip_km` | 30 | ab dieser Entfernung zählt ein Tag als Reise |
| `routing` / `osrm_url` | `osrm`, öffentlicher Demo-Server | Lücken auf Strassen legen; `off` = alles bleibt lokal |
| `photo_folders` | – | Ordner unter `/media` oder `/share` (nur lesend) |
| `notify_service` / `notify_mode` | – / `weekly` | z. B. `notify.mobile_app_handy`; `off`, `instant`, `daily`, `weekly` |
| `ask_below` | `hoch` | fragen, wenn die Sicherheit tiefer ist |
| `school_holidays` | – | Zeiträume wie `2026-07-04..2026-08-09` |

## Datenschutz & Sicherheit

- Dein Standortverlauf bleibt im Ordner `/data` des Add-ons (Teil deiner Home-Assistant-Backups). Nichts wird hochgeladen –
  ausser Start- und Endpunkt einer Lücke, wenn das Routing über einen öffentlichen OSRM-Server eingeschaltet ist (ausschalten oder eigenen Server nutzen).
- Die Oberfläche ist nur über Home Assistant Ingress erreichbar; alle anderen Verbindungen werden abgewiesen.
- Strenge Eingabeprüfung, parametrisiertes SQL, XXE-sicheres XML, CSV-Export ohne Formel-Einschleusung, Content-Security-Policy.
- CI: Tests, Ruff, Bandit, pip-audit, CodeQL, Dependabot und ein Datenschutz-Check. Siehe [SECURITY.md](SECURITY.md).

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

Kartendaten: [Natural Earth](https://www.naturalearthdata.com/) (gemeinfrei), Schweizer Grenzen: swisstopo / BFS.
Ortsnamen: [GeoNames](https://www.geonames.org/) (CC BY 4.0). Routing: [OSRM](https://project-osrm.org/) / OpenStreetMap-Mitwirkende.

Lizenz: MIT
