"""Telegram-Collector OHNE Account: nutzt die oeffentliche Web-Vorschau
https://t.me/s/<channel>, die fuer oeffentliche Channels (nicht: private Gruppen)
ohne Login als normales HTML ausgeliefert wird. Kein API-Key noetig.

Einschraenkung: funktioniert nur fuer Channels mit oeffentlichem Usernamen
(t.me/<name>). Private/geschlossene Gruppen ohne oeffentlichen Link sind
darueber nicht erreichbar.
"""
import logging
import re

import requests
from bs4 import BeautifulSoup

from .base import Event

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CityEventsBot/1.0)"}
DATE_HINT = re.compile(r"\b(\d{1,2}[./]\d{1,2}([./]\d{2,4})?|heute|morgen|Mo|Di|Mi|Do|Fr|Sa|So)\b", re.IGNORECASE)


def collect(source: dict) -> list[Event]:
    channel = source["channel"]
    url = f"https://t.me/s/{channel}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Telegram collector failed for %s: %s", source["id"], e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    messages = soup.select(".tgme_widget_message")
    events = []
    for msg in messages:
        text_el = msg.select_one(".tgme_widget_message_text")
        if not text_el:
            continue
        text = text_el.get_text("\n", strip=True)
        if not text or not DATE_HINT.search(text):
            continue

        time_el = msg.select_one(".tgme_widget_message_date time")
        date_iso = time_el.get("datetime") if time_el else None

        link_el = msg.select_one(".tgme_widget_message_date")
        link = link_el.get("href") if link_el and link_el.get("href") else url

        title = text.split("\n")[0][:120]
        event = Event(
            title=title,
            source_id=source["id"],
            source_name=source["name"],
            category=source.get("category", "community"),
            link=link,
            date=date_iso,
            needs_review=True,
        )
        events.append(event)
    return events
