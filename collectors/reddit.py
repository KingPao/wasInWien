"""Reddit-Collector OHNE Account: nutzt Reddits öffentlichen JSON-Endpoint
(https://www.reddit.com/r/<sub>/new.json), der für öffentliche Subreddits ohne
Login/OAuth funktioniert. Kein Client-ID/Secret nötig.
"""
import logging
import requests

from .base import Event

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CityEventsBot/1.0)"}


def collect(source: dict) -> list[Event]:
    subreddit = source["subreddit"]
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=100"
    keywords = [k.lower() for k in source.get("keywords", [])]

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Reddit collector failed für %s: %s", source["id"], e)
        return []

    events = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        title = post.get("title", "")
        title_lower = title.lower()
        if keywords and not any(k in title_lower for k in keywords):
            continue
        events.append(Event(
            title=title,
            source_id=source["id"],
            source_name=source["name"],
            category=source.get("category", "community"),
            link=f"https://reddit.com{post.get('permalink', '')}",
            date=None,
            needs_review=True,
        ))
    return events
