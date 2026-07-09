"""RSS-Collector für Quellen, die einen Feed anbieten (oft stabiler als HTML-Scraping)."""
import logging
import feedparser
from dateutil import parser as dtparser

from .base import Event

logger = logging.getLogger(__name__)


def collect(source: dict) -> list[Event]:
    try:
        feed = feedparser.parse(source["url"])
    except Exception as e:
        logger.warning("RSS collector failed for %s: %s", source["id"], e)
        return []

    events = []
    for entry in feed.entries:
        date_iso = None
        for key in ("published", "updated"):
            if hasattr(entry, key):
                try:
                    date_iso = dtparser.parse(getattr(entry, key)).isoformat()
                    break
                except Exception:
                    pass

        events.append(Event(
            title=entry.get("title", "").strip(),
            source_id=source["id"],
            source_name=source["name"],
            category=source.get("category", "misc"),
            link=entry.get("link", source["url"]),
            date=date_iso,
            image=None,
            needs_review=date_iso is None,
        ))
    return events
