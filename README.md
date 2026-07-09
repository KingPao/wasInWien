# WasInWien

Leichtgewichtiges Event-Aggregator-Tool: kein Server, keine Datenbank. Ein Python-Skript sammelt Events aus konfigurierten Quellen und schreibt sie in eine JSON-Datei; eine einzelne HTML-Seite zeigt sie als Kacheln oder Kalender.

## Struktur

```
pyproject.toml / uv.lock    <- Abhaengigkeiten (uv), keine venv-Verwaltung von Hand noetig
config/cities/vienna.json   <- alle Quellen fuer Wien, editierbar ohne Code
config/schema.md            <- wie man eine neue Stadt hinzufuegt
collectors/                 <- ein Modul pro Quellen-Typ (html, rss, reddit, telegram, instagram)
main.py                     <- liest Config, ruft Collectors auf, schreibt data/<stadt>_events.json
data/                       <- generierte JSON-Dateien (30-Tage-Fenster), plus cities.json als Staedte-Liste
web/index.html              <- die eigentliche Website (Kacheln + Kalender + Staedte-Dropdown)
```

## Setup

Das Projekt nutzt [uv](https://docs.astral.sh/uv/) als Paketmanager (`pyproject.toml` + `uv.lock`, kein `requirements.txt` mehr, keine manuelle venv-Verwaltung noetig).

```bash
uv sync
```

## Events sammeln

```bash
uv run main.py --city vienna
```

Schreibt `data/vienna_events.json` neu (ueberschreibt die alte Version) und aktualisiert `data/cities.json`.

## Website oeffnen

`web/index.html` laedt `/data/...` als absoluten Pfad (passend zum Vercel-Setup). Fuer lokale Tests am besten ueber einen kleinen lokalen Server starten, im Projekt-Root:

```bash
uv run -m http.server
```

Dann im Browser `http://localhost:8000/web/` oeffnen. Es liegen Beispieldaten in `data/vienna_events.json`, damit die Seite auch ohne vorherigen Sammel-Lauf etwas zeigt.

## Taegliches Auto-Update

Lokaler Cron (taeglich um 6 Uhr):

```
0 6 * * * cd /pfad/zu/was-in-wien && uv run main.py --city vienna
```

Fuer automatisches Update ohne eigenen Rechner: siehe GitHub Actions unten.

## Neue Stadt hinzufuegen

1. `config/cities/vienna.json` kopieren -> `config/cities/graz.json`, Inhalte anpassen.
2. `uv run main.py --city graz` ausfuehren.
3. Fertig -- die Website zeigt "Graz" automatisch im Dropdown, weil sie `data/cities.json` liest.

## Deployment auf Vercel

Die Website ist statisch (kein Server), die Auto-Aktualisierung laeuft ueber GitHub Actions statt ueber Vercel selbst -- Vercel-Deployments koennen keine Dateien dauerhaft ueberschreiben.

1. Repo auf GitHub pushen. Keine Secrets noetig -- alle aktiven Collectors laufen ohne Login.
2. Der Workflow `.github/workflows/update-events.yml` laeuft taeglich um 5 Uhr UTC, fuehrt `main.py` aus und committed die neue `data/vienna_events.json` zurueck ins Repo.
3. Repo bei vercel.com importieren, Framework Preset auf "Other" lassen (kein Build-Schritt noetig) -- `vercel.json` sorgt dafuer, dass `/` auf `web/index.html` zeigt und `/data/*.json` normal ausgeliefert wird.
4. Jeder Commit (auch der automatische vom Workflow) triggert ein neues Vercel-Deployment -> die Website zeigt danach automatisch die aktuellen Events.

Manuell ausloesen: im GitHub-Repo unter Actions -> "Update Events Data" -> "Run workflow".

## Ohne Accounts/Logins

Bewusste Design-Entscheidung: kein Collector braucht Zugangsdaten oder eine `.env`.

- **Reddit**: oeffentlicher JSON-Endpoint (`reddit.com/r/<sub>/new.json`), funktioniert ohne Login fuer oeffentliche Subreddits.
- **Telegram**: oeffentliche Web-Vorschau (`t.me/s/<channel>`), funktioniert ohne Login -- aber nur fuer Channels mit oeffentlichem Usernamen, nicht fuer private/geschlossene Gruppen.
- **Instagram**: es gibt aktuell keine zuverlaessige Methode, oeffentliche Posts ohne Login zu lesen (Meta hat die anonymen Endpoints abgeschafft). Der Collector ist deshalb ein bewusster No-Op und bleibt `enabled: false`. Alternativen stehen als Kommentar in `collectors/instagram.py`.

## Bekannte Grenzen

- **Aktiv & verifiziert** (Link-Pattern statt CSS-Selektoren, robuster gegen Layout-Aenderungen): wien.gv.at, mqw.at (Datum steht direkt in der URL), meinbezirk.at.
- **Deaktiviert, weil die Eventliste per JavaScript nachgeladen wird** (plain `requests`/BeautifulSoup sieht nur das initiale, leere HTML -- braeuchte Playwright): wien.info, goodnight.at, ohschonhell.at.
- **Deaktiviert, weil keine strukturierte Terminliste vorhanden ist**: khm.at/ausstellungen (nur Museumsuebersicht).
- Reddit/Telegram liefern kein strukturiertes Event-Datum -- deshalb `needs_review: true`.
- Events ohne erkennbares Datum werden trotzdem angezeigt (Badge "pruefen"), damit nichts verloren geht.
- Fuer die deaktivierten JS-Seiten waere der naechste Schritt ein optionaler Playwright-Collector -- aktuell ausserhalb des "kein Server"-Scopes.
