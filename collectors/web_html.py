"""Generischer HTML-Collector mit zwei Modi:

1. CSS-Selektoren (Default, `selectors` in der Config): braucht exakte Klassennamen,
   die man einmal gegen das echte HTML pruefen muss. Bricht leicht bei Layout-Aenderungen.

2. Link-Pattern (`link_pattern` in der Config, ein Regex): robuster gegen Layout-
   Aenderungen, weil es keine CSS-Klassen braucht. Sucht alle <a>-Tags, deren href
   auf das Pattern passt (z.B. Detail-Links wie /veranstaltungen/<slug>), nimmt den
   Link-Text als Titel und versucht, aus der URL selbst oder dem umgebenden Text-
   Block ein Datum zu extrahieren.

Wichtig: beide Modi funktionieren nur, wenn der Inhalt bereits im initialen HTML
steht (server-seitig gerendert). Seiten, deren Eventliste per JavaScript nachgeladen
wird (z.B. ohschonhell.at, wien.info, goodnight.at), liefern hier gar nichts zurueck --
dafuer braeuchte man einen echten Browser (Playwright), was ausserhalb des
"kein Server"-Designs dieses Projekts liegt. Solche Quellen sind in der Config
bewusst enabled: false.
"""
import logging
import re

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from .base import Event

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CityEventsBot/1.0)"}


def _absolute(url, link):
    if link and link.startswith("/"):
        base = "/".join(url.split("/")[:3])
        return base + link
    return link


GERMAN_MONTHS = {
    "januar": "1", "februar": "2", "maerz": "3", "märz": "3", "april": "4",
    "mai": "5", "juni": "6", "juli": "7", "august": "8", "september": "9",
    "oktober": "10", "november": "11", "dezember": "12",
}


def _normalize_german_date(text):
    lowered = text.lower()
    for name, num in GERMAN_MONTHS.items():
        if name in lowered:
            lowered = lowered.replace(name, num)
            break
    return lowered


def _try_parse_date(text):
    for candidate in (text, _normalize_german_date(text)):
        try:
            return dtparser.parse(candidate, fuzzy=True, dayfirst=True).isoformat()
        except Exception:
            continue
    return None


def _date_from_url(href):
    # Manche Seiten (z.B. mqw.at) haben das Datum direkt im Link,
    # z.B. .../20260612-1900/ -> 2026-06-12T19:00
    m = re.search(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})", href)
    if not m:
        return None
    year, month, day, hour, minute = m.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}"


def collect(source):
    url = source["url"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("HTML collector failed for %s: %s", source["id"], e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    if source.get("link_pattern"):
        return _collect_by_link_pattern(soup, source, url)
    return _collect_by_selectors(soup, source, url)


def _collect_by_link_pattern(soup, source, url):
    pattern = re.compile(source["link_pattern"])
    seen_links = set()
    events = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not pattern.search(href):
            continue
        link = _absolute(url, href)
        if link in seen_links:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        seen_links.add(link)

        date_iso = _date_from_url(href)

        block = a.find_parent(["article", "li", "div", "tr"]) or a.parent
        block_text = block.get_text(" ", strip=True) if block else ""

        if not date_iso:
            for match in re.findall(r"\d{1,2}\.\s*(?:bis\s*\d{1,2}\.)?\d{1,2}\.\d{4}", block_text):
                date_iso = _try_parse_date(match.split("bis")[-1].strip())
                if date_iso:
                    break
            if not date_iso:
                m = re.search(r"\d{1,2}\.\s*[A-Za-zäöüÄÖÜ]+\s*\d{4}(?:\s*um\s*\d{1,2}[:.]\d{2})?", block_text)
                if m:
                    date_iso = _try_parse_date(m.group(0).replace(" um ", " "))

        image = None
        img_el = block.find("img") if block else None
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


def _collect_by_selectors(soup, source, url):
    sel = source.get("selectors", {})
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
        link = _absolute(url, link)

        date_iso = None
        if date_el:
            date_iso = _try_parse_date(date_el.get_text(strip=True))

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
