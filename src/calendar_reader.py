"""Load and filter calendar events from calendar.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class Event:
    title: str
    location: str
    start: datetime


def load_calendar(path: str | Path) -> list[dict]:
    calendar_path = Path(path)
    with calendar_path.open(encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("events", [])
    if not isinstance(events, list):
        raise ValueError("calendar.json 'events' must be a list")
    return events


def parse_event(raw: dict) -> Event | None:
    """Parse a calendar record, returning None for malformed entries."""
    try:
        return Event(
            title=raw["title"],
            location=raw["location"],
            start=datetime.fromisoformat(raw["start"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def get_events_for_date(
    path: str | Path,
    target_date: date | None = None,
) -> list[Event]:
    if target_date is None:
        target_date = date.today()

    events = []
    for raw in load_calendar(path):
        event = parse_event(raw)
        if event is None or event.start.date() != target_date:
            continue
        events.append(event)

    return sorted(events, key=lambda e: e.start)


def format_event_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")
