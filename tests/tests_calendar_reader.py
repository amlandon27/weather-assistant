import json
from datetime import date, datetime

import pytest

from calendar_reader import format_event_time, get_events_for_date, load_calendar
from conftest import make_forecast_response, make_geocode_response, make_mock_fetch
from main import display_todays_plan


@pytest.fixture
def sample_calendar(tmp_path):
    calendar = {
        "events": [
            {
                "title": "Lunch with Sarah",
                "location": "Sugar Land, TX",
                "start": "2026-06-17T12:00:00",
            },
            {
                "title": "Team Meeting",
                "location": "Houston, TX",
                "start": "2026-06-17T09:00:00",
            },
            {
                "title": "Doctor Appointment",
                "location": "Houston, TX",
                "start": "2026-06-18T16:00:00",
            },
        ]
    }
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps(calendar), encoding="utf-8")
    return path


def test_load_calendar_returns_events(sample_calendar):
    events = load_calendar(sample_calendar)
    assert len(events) == 3


def test_get_events_for_date_filters_and_sorts(sample_calendar):
    events = get_events_for_date(sample_calendar, date(2026, 6, 17))
    assert len(events) == 2
    assert events[0].title == "Team Meeting"
    assert events[1].title == "Lunch with Sarah"


def test_get_events_for_date_empty_when_no_matches(sample_calendar):
    events = get_events_for_date(sample_calendar, date(2026, 6, 19))
    assert events == []


def test_get_events_for_date_skips_malformed_records(tmp_path):
    calendar = {
        "events": [
            {"title": "Valid Event", "location": "Houston, TX", "start": "2026-06-17T09:00:00"},
            {"title": "Missing Location", "start": "2026-06-17T10:00:00"},
            {"location": "Houston, TX", "start": "2026-06-17T11:00:00"},
            {"title": "Bad Start", "location": "Houston, TX", "start": "not-a-datetime"},
        ]
    }
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps(calendar), encoding="utf-8")

    events = get_events_for_date(path, date(2026, 6, 17))

    assert len(events) == 1
    assert events[0].title == "Valid Event"


def test_format_event_time():
    assert format_event_time(datetime(2026, 6, 17, 9, 0)) == "9:00 AM"
    assert format_event_time(datetime(2026, 6, 17, 16, 0)) == "4:00 PM"


def test_display_todays_plan_with_events(sample_calendar):
    fetch = make_mock_fetch(
        make_geocode_response(),
        make_forecast_response(
            ["2026-06-17T09:00", "2026-06-17T12:00"],
            [72.0, 80.0],
            [20, 15],
            daily_weather_code=3,
        ),
    )

    output = display_todays_plan(sample_calendar, date(2026, 6, 17), fetch=fetch)

    assert "Today's Plan" in output
    assert "9:00 AM Team Meeting (Houston, TX) | 72°F | Rain Chance: 20%" in output
    assert "12:00 PM Lunch with Sarah (Sugar Land, TX) | 80°F | Rain Chance: 15%" in output
    assert "Weather Conditions" in output


def test_display_todays_plan_empty(sample_calendar):
    output = display_todays_plan(sample_calendar, date(2026, 6, 19))
    assert "No events scheduled for today." in output
