"""PRD acceptance criteria and requirement validation tests."""

import json
from datetime import date, datetime

import pytest

from advice_engine import generate_recommendations
from calendar_reader import Event
from conftest import make_forecast_response, make_geocode_response, make_mock_fetch
from main import display_todays_plan, format_event_line, handle_command
from weather import EventWeather, WeatherResult, get_event_weather, get_weather_for_events


def _weather_result(
    temperature_f: int,
    rain_chance_percent: int,
    daily_weather_code: int = 0,
) -> WeatherResult:
    return WeatherResult(
        weather=EventWeather(
            temperature_f=temperature_f,
            rain_chance_percent=rain_chance_percent,
            daily_weather_code=daily_weather_code,
        )
    )


@pytest.fixture
def prd_calendar(tmp_path):
    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "title": "Team Meeting",
                        "location": "Houston, TX",
                        "start": "2026-06-17T09:00:00",
                    },
                    {
                        "title": "Offsite",
                        "location": "",
                        "start": "2026-06-17T11:00:00",
                    },
                    {
                        "title": "Doctor Appointment",
                        "location": "Houston, TX",
                        "start": "2026-06-17T16:00:00",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_ac1_today_shows_event(prd_calendar):
    fetch = make_mock_fetch(
        make_geocode_response(),
        make_forecast_response(["2026-06-17T09:00"], [72.0], [10]),
    )

    output = handle_command(
        "today",
        calendar_path=prd_calendar,
        target_date=date(2026, 6, 17),
        fetch=fetch,
    )

    assert "9:00 AM Team Meeting (Houston, TX)" in output


def test_ac2_four_pm_event_uses_four_pm_forecast():
    event = Event(
        title="Doctor Appointment",
        location="Houston, TX",
        start=datetime(2026, 6, 17, 16, 0),
    )
    forecast = make_forecast_response(
        ["2026-06-17T09:00", "2026-06-17T16:00"],
        [72.0, 94.0],
        [10, 65],
    )

    result = get_event_weather(
        event,
        fetch=make_mock_fetch(make_geocode_response(), forecast),
    )

    assert result.success
    assert result.weather.temperature_f == 94
    assert result.weather.rain_chance_percent == 65


def test_ac3_umbrella_at_thirty_percent_rain():
    event_weather_results = [
        (Event("Walk", "Houston, TX", datetime(2026, 6, 17, 9, 0)), _weather_result(75, 30)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert "Bring an umbrella." in recommendations


def test_ac4_heat_above_ninety_degrees():
    event_weather_results = [
        (Event("Lunch", "Houston, TX", datetime(2026, 6, 17, 12, 0)), _weather_result(91, 10)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert "Dress appropriately and bring a fan." in recommendations


def test_ac5_jacket_below_sixty_five_degrees():
    event_weather_results = [
        (Event("Walk", "Houston, TX", datetime(2026, 6, 17, 8, 0)), _weather_result(64, 0)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations == ["It's 64°F — bring a jacket."]


def test_ac6_duplicate_recommendations_appear_once():
    event_weather_results = [
        (Event("A", "Houston, TX", datetime(2026, 6, 17, 9, 0)), _weather_result(92, 40)),
        (Event("B", "Sugar Land, TX", datetime(2026, 6, 17, 12, 0)), _weather_result(95, 50)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations.count("Bring an umbrella.") == 1
    assert recommendations.count("Dress appropriately and bring a fan.") == 1


def test_fr8_blank_location_shows_insufficient_data():
    event = Event(title="Offsite", location="", start=datetime(2026, 6, 17, 11, 0))
    result = get_event_weather(event, fetch=make_mock_fetch(make_geocode_response(), {}))

    line = format_event_line(event, result)

    assert line == "11:00 AM Offsite () | Insufficient data to pull weather"


def test_fr9_weather_failure_continues_other_events(prd_calendar):
    fetch = make_mock_fetch(
        {"results": []},
        make_forecast_response(["2026-06-17T09:00"], [72.0], [10]),
    )

    output = display_todays_plan(prd_calendar, date(2026, 6, 17), fetch=fetch)

    assert "9:00 AM Team Meeting (Houston, TX) | Weather unavailable" in output
    assert "4:00 PM Doctor Appointment (Houston, TX) | Weather unavailable" in output
    assert "11:00 AM Offsite () | Insufficient data to pull weather" in output


def test_fr10_empty_calendar_message(tmp_path):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"events": []}), encoding="utf-8")

    output = display_todays_plan(path, date(2026, 6, 17))

    assert output == "Today's Plan\n\nNo events scheduled for today."


def test_boundary_ninety_degrees_does_not_trigger_heat():
    recommendations = generate_recommendations(
        [(Event("E", "Houston, TX", datetime(2026, 6, 17, 12, 0)), _weather_result(90, 10))]
    )

    assert "Dress appropriately and bring a fan." not in recommendations


def test_boundary_sixty_five_degrees_does_not_trigger_jacket():
    recommendations = generate_recommendations(
        [(Event("E", "Houston, TX", datetime(2026, 6, 17, 8, 0)), _weather_result(65, 0))]
    )

    assert recommendations == []


def test_weather_retrieval_success(prd_calendar):
    fetch = make_mock_fetch(
        make_geocode_response(),
        make_forecast_response(
            ["2026-06-17T09:00", "2026-06-17T16:00"],
            [77.0, 83.0],
            [47, 27],
            daily_weather_code=95,
        ),
    )

    events = [
        Event("Team Meeting", "Houston, TX", datetime(2026, 6, 17, 9, 0)),
        Event("Doctor Appointment", "Houston, TX", datetime(2026, 6, 17, 16, 0)),
    ]
    results = get_weather_for_events(events, fetch=fetch)

    assert all(result.success for _, result in results)
    assert results[0][1].weather.temperature_f == 77
    assert results[1][1].weather.temperature_f == 83


def test_weather_retrieval_failure(prd_calendar):
    fetch = make_mock_fetch({"results": []}, {"hourly": {}, "daily": {}})

    events = [Event("Team Meeting", "Houston, TX", datetime(2026, 6, 17, 9, 0))]
    results = get_weather_for_events(events, fetch=fetch)

    assert not results[0][1].success
    assert results[0][1].failed
