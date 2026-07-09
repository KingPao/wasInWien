# City Config Schema

Jede Stadt ist eine eigene JSON-Datei unter `config/cities/<stadt>.json`. Um eine neue Stadt hinzuzufügen: Datei kopieren, `city` anpassen, Quellen austauschen. Kein Code muss geändert werden.

## Feldübersicht

- `type`: `html` | `rss` | `reddit` | `telegram` | `instagram` — bestimmt, welcher Collector aus `collectors/` verwendet wird.
- `enabled`: Quelle ohne Löschen deaktivieren.
- `selectors` (nur `type: html`): CSS-Selektoren für Listenelement, Titel, Datum, Link, Bild. Muss pro Website einmal per Hand gegen die echte HTML-Struktur geprüft werden.
- `category`: freier String, wird in der Web-Oberfläche als Filter verwendet.
- `window_days`: wie viele Tage in die Zukunft Events behalten werden (Default 30).

Alle Collectors laufen ohne Login/Account: Reddit über den öffentlichen JSON-Endpoint, Telegram über die öffentliche Web-Vorschau (nur öffentliche Channels). Instagram ist aktuell technisch nicht anonym scrapbar und bleibt deaktiviert (siehe `collectors/instagram.py`).

## Neue Stadt hinzufügen

1. `config/cities/vienna.json` kopieren nach `config/cities/<neue-stadt>.json`.
2. `city`, `label`, `sources` anpassen (URLs/Handles der neuen Stadt).
3. `python main.py --city <neue-stadt>` ausführen → erzeugt `data/<neue-stadt>_events.json`.
4. Web-Oberfläche zeigt die neue Stadt automatisch im Dropdown (liest `data/cities.json`, wird bei jedem Lauf aktualisiert).
