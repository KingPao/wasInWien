# WasInWien

Leichtgewichtiges Event-Aggregator-Tool: kein Server, keine Datenbank. Ein Python-Skript sammelt Events aus konfigurierten Quellen und schreibt sie in eine JSON-Datei; eine einzelne HTML-Seite zeigt sie als Kacheln oder Kalender.

## Struktur

```
config/cities/vienna.json   ← alle Quellen für Wien, editierbar ohne Code
config/schema.md            ← wie man eine neue Stadt hinzufügt
collectors/                 ← ein Modul pro Quellen-Typ (html, rss, reddit, telegram, instagram)
main.py                     ← liest Config, ruft Collectors auf, schreibt data/<stadt>_events.json
data/                       ← generierte JSON-Dateien (30-Tage-Fenster), plus cities.json als Städte-Liste
web/index.html              ← die eigentliche Website (Kacheln + Kalender + Städte-Dropdown)
```

## Setup

```bash
pip install -r requirements.txt
```

## Events sammeln

```bash
python main.py --city vienna
```

Schreibt `data/vienna_events.json` neu (überschreibt die alte Version) und aktualisiert `data/cities.json`.

## Website öffnen

`web/index.html` lädt `/data/...` als absoluten Pfad (passend zum Vercel-Setup). Für lokale Tests am besten über einen kleinen lokalen Server starten, im Projekt-Root:

```bash
python -m http.server
```

Dann im Browser `http://localhost:8000/web/` öffnen. Es liegen Beispieldaten in `data/vienna_events.json`, damit die Seite auch ohne vorherigen Sammel-Lauf etwas zeigt.

## Tägliches Auto-Update

Lokaler Cron (täglich um 6 Uhr):

```
0 6 * * * cd /pfad/zu/was-in-wien && python3 main.py --city vienna
```

Für automatisches Update ohne eigenen Rechner: siehe GitHub Actions unten.

## Neue Stadt hinzufügen

1. `config/cities/vienna.json` kopieren → `config/cities/graz.json`, Inhalte anpassen.
2. `python main.py --city graz` ausführen.
3. Fertig — die Website zeigt „Graz“ automatisch im Dropdown, weil sie `data/cities.json` liest.

## Deployment auf Vercel

Die Website ist statisch (kein Server), die Auto-Aktualisierung läuft über GitHub Actions statt über Vercel selbst — Vercel-Deployments können keine Dateien dauerhaft überschreiben.

1. Repo auf GitHub pushen. Keine Secrets nötig — alle aktiven Collectors laufen ohne Login.
2. Der Workflow `.github/workflows/update-events.yml` läuft täglich um 5 Uhr UTC, führt `main.py` aus und committed die neue `data/vienna_events.json` zurück ins Repo.
3. Repo bei vercel.com importieren, Framework Preset auf "Other" lassen (kein Build-Schritt nötig) — `vercel.json` sorgt dafür, dass `/` auf `web/index.html` zeigt und `/data/*.json` normal ausgeliefert wird.
4. Jeder Commit (auch der automatische vo