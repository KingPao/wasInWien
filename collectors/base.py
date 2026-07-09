"""Gemeinsames Event-Format, das jeder Collector zurückgibt."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Event:
    title: str
    source_id: str
    source_name: str
    category: str
    link: str
    date: Optional[str] = None       # ISO 8601, z.B. "2026-07-15T20:00" – None wenn nicht extrahierbar
    location: Optional[str] = None
    image: Optional[str] = None
    needs_review: bool = False       # True wenn Datum/Ort nur geraten/unklar (z.B. Instagram-Caption)

    def to_dict(self):
        return asdict(self)
