#!/usr/bin/env python3
"""Orchestrator: liest config/cities/<city>.json, ruft passende Collectors auf,
merged + dedupliziert + filtert auf 30-Tage-Fenster, schreibt data/<city>_events.json.

Nutzung:
    python main.py --city vienna

Neue Stadt: config/cities/<neue-stadt>.json anlegen (siehe config/schema.md),
dann `python main.py --city <neue-stadt>` -- kein Code-Änderung nötig.
"""
import argparse
import json
import logging
import os
from datetime import datetime, timedelta

from collectors import web_html, web_rss, reddit, telegram, instagram

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("main")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config", "cities")
DATA_DIR = os.path.join(BASE_DIR, "data")

COLLECTORS = {
    "html": web_html.collect,
    "rss": web_rss.collect,
    "reddit": reddit.collect,
    "telegram": telegram.collect,
    "instagram": instagram.collect,
}


def load_city_config(city: str) -> dict:
    path = os.path.join(CONFIG_DIR, f"{city}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dedupe(events: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for e in events:
        key = (e["title"].strip().lower(), (e.get("date") or "")[:10])
        if key in seen:
            continue
        seen.add(key)
        result.append(e)
    return result


def filter_window(events: list[dict], window_days: int) -> list[dict]:
    now = datetime.now()
    cutoff = now + timedelta(days=window_days)
    kept = []
    for e in events:
        if not e.get("date"):
            kept.append(e)  # ohne Datum drin lassen, aber needs_review ist schon True
            continue
        try:
            d = datetime.fromisoformat(e["date"])
        except Exception:
            kept.append(e)
            continue
        if now - timedelta(days=1) <= d <= cutoff:
            kept.append(e)
    return kept


def update_cities_manifest(city: str, label: str):
    manifest_path = os.path.join(DATA_DIR, "cities.json")
    manifest = []
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    manifest = [m for m in manifest if m["city"] != city]
    manifest.append({"city": city, "label": label, "file": f"{city}_events.json"})
    manifest.sort(key=lambda m: m["label"])
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def run(city: str):
    config = load_city_config(city)
    os.makedirs(DATA_DIR, exist_ok=True)

    all_events = []
    for source in config["sources"]:
        if not source.get("enabled", True):
            continue
        collector = COLLECTORS.get(source["type"])
        if not collector:
            logger.warning("Unbekannter type '%s' für Quelle %s", source["type"], source["id"])
            continue
        logger.info("Sammle: %s (%s)", source["name"], source["type"])
        try:
            events = collector(source)
        except Exception as e:
            logger.error("Collector-Fehler bei %s: %s", source["id"], e)
            events = []
        logger.info("  -> %d Events", len(events))
        all_events.extend(e.to_dict() for e in events)

    all_events = dedupe(all_events)
    all_events = filter_window(all_events, config.get("window_days", 30))
    all_events.sort(key=lambda e: e.get("date") or "9999")

    out_path = os.path.join(DATA_DIR, f"{city}_events.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "city": city,
            "label": config.get("label", city),
            "generated_at": datetime.now().isoformat(),
            "events": all_events,
        }, f, ensure_ascii=False, indent=2)

    update_cities_manifest(city, config.get("label", city))
    logger.info("Fertig: %d Events -> %s", len(all_events), out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True, help="Name der Config-Datei ohne .json, z.B. vienna")
    args = parser.parse_args()
    run(args.city)
