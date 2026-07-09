"""Instagram-Collector — EHRLICHER HINWEIS:

Es gibt aktuell keine zuverlässige Methode, öffentliche Instagram-Posts OHNE
Login zu lesen. Meta hat die anonymen Endpoints (die früher z.B. über
`?__a=1` funktionierten) weitgehend abgeschafft; alles Verbleibende ist
JS-gerendert und braucht einen eingeloggten Session-State, auch nur zum
Lesen. Es gibt keinen Weg, das robust anonym zu scrapen.

Diese Quelle bleibt deshalb standardmäßig deaktiviert (`enabled: false` in
der Config). Optionen, falls Instagram trotzdem gebraucht wird:

1. Manuell kuratieren: Posts von Hand in eine kleine JSON/CSV-Liste eintragen,
   die main.py einliest wie jede andere Quelle (kein Code-Update nötig, nur
   ein neuer Collector-Typ "manual").
2. Mit Account arbeiten (instagrapi + Dummy-Account) — technisch möglich,
   aber Sperr-Risiko und Wartungsaufwand, wie vorher besprochen.

Diese Funktion gibt daher bewusst nichts zurück, wenn sie aufgerufen wird.
"""
import logging

from .base import Event

logger = logging.getLogger(__name__)


def collect(source: dict) -> list[Event]:
    logger.info(
        "Instagram-Quelle '%s' übersprungen: keine anonyme Scraping-Methode verfügbar. "
        "Siehe Kommentar in collectors/instagram.py für Alternativen.",
        source["id"],
    )
    return []
