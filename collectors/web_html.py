"""Generischer HTML-Collector: liest eine Eventliste anhand von CSS-Selektoren
aus der Config. Muss pro Website einmal per Hand geprüft/angepasst werden,
da jede Seite ihre eigene HTML-Struktur hat.
"""
import logging
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from .base import Event

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CityEventsBot/1.0)"}


def collect(source: dict) -> list[Event]:
    url = source["url"]
    sel = source.get("selectors", {})
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("HTML collector failed for %s: %s", source["id"], e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select(sel.get("item", ".event"))
    events = []
    for item in items:
        title_el = item.select_one(sel.get("title", ""))
        date_el = item.select_one(sel.get("date", ""))
        link_el = item.select_one(sel.get("link", "a"))
        img_el = item.select_one(sel.get("image", "img"))

        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            continue

        link = link_el.get("href") if link_el else url
        if link and link.startswith("/"):
            base = "/".join(url.split("/")[:3])
            link = base + link

        date_iso = None
        if date_el:
            raw_date = date_el.get_text(strip=True)
            try:
                date_iso = dtparser.parse(raw_date, fuzzy=True, dayfirst=True).isoformat()
            except Exception:
                date_iso = None

        image = None
        if img_el:
            image = img_el.get("src") or img_el.get("data-src")

        events.append(Event(
            title=title,
            source_id=source["id"],
            source_name=source["name"],
            category=source.get("category", "misc"),
            link=link,
            date=date_iso,
            image=image,
            needs_review=date_iso is None,
        ))
    return events
