from datetime import datetime

import pytest

from calendar_reader import Event
from conftest import make_forecast_response, make_geocode_response, make_mock_fetch
from weather import (
    EventWeather,
    WeatherResult,
    describe_weather_code,
    format_daily_conditions,
    get_event_weather,
    get_weather_for_events,
    is_severe_weather_code,
)


@pytest.fixture
def houston_event():
    return Event(
        title="Team Meeting",
        location="Houston, TX",
        start=datetime(2026, 6, 17, 9, 0),
    )


def test_get_event_weather_success(houston_event):
    forecast_response = make_forecast_response(
        ["2026-06-17T08:00", "2026-06-17T09:00", "2026-06-17T10:00"],
        [70.0, 72.4, 75.0],
        [10, 20, 30],
        daily_weather_code=63,
    )

    result = get_event_weather(
        houston_event,
        fetch=make_mock_fetch(make_geocode_response(), forecast_response),
    )

    assert result.success
    assert result.weather.temperature_f == 72
    assert result.weather.rain_chance_percent == 20
    assert result.weather.daily_weather_code == 63
    assert result.weather.daily_condition == "Rain: Moderate intensity"


def test_get_event_weather_failure_when_geocoding_fails(houston_event):
    result = get_event_weather(
        houston_event,
        fetch=make_mock_fetch({"results": []}, {"hourly": {}, "daily": {}}),
    )

    assert not result.success
    assert result.failed


def test_get_weather_for_events_continues_after_failure(houston_event):
    missing_location_event = Event(
        title="Untitled Event",
        location="",
        start=datetime(2026, 6, 17, 10, 0),
    )
    forecast_response = make_forecast_response(
        ["2026-06-17T09:00"],
        [72.0],
        [20],
    )
    fetch = make_mock_fetch(make_geocode_response(), forecast_response)

    results = get_weather_for_events([missing_location_event, houston_event], fetch=fetch)

    assert len(results) == 2
    assert results[0][1].insufficient_data
    assert results[1][1].success


def test_describe_weather_code():
    assert describe_weather_code(95) == "Thunderstorm: Slight or moderate"
    assert describe_weather_code(999) == "Unknown weather code (999)"


def test_is_severe_weather_code():
    assert is_severe_weather_code(95)
    assert not is_severe_weather_code(63)


def test_format_daily_conditions_deduplicates_locations():
    event_a = Event("A", "Houston, TX", datetime(2026, 6, 17, 9, 0))
    event_b = Event("B", "Houston, TX", datetime(2026, 6, 17, 12, 0))
    weather = WeatherResult(
        weather=EventWeather(temperature_f=80, rain_chance_percent=10, daily_weather_code=3)
    )

    lines = format_daily_conditions([(event_a, weather), (event_b, weather)])

    assert lines == ["Houston, TX: Overcast"]
