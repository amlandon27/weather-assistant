import json
from datetime import date

import pytest

from advice_engine import NO_RECOMMENDATIONS_MESSAGE
from conftest import make_forecast_response, make_geocode_response, make_mock_fetch
from main import HELP_TEXT, handle_command, run_repl


@pytest.fixture
def sample_calendar(tmp_path):
    calendar = {
        "events": [
            {
                "title": "Team Meeting",
                "location": "Houston, TX",
                "start": "2026-06-17T09:00:00",
            },
        ]
    }
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps(calendar), encoding="utf-8")
    return path


def test_handle_command_today_success(sample_calendar):
    fetch = make_mock_fetch(
        make_geocode_response(),
        make_forecast_response(
            ["2026-06-17T09:00"],
            [72.0],
            [40],
            daily_weather_code=63,
        ),
    )

    output = handle_command(
        "today",
        calendar_path=sample_calendar,
        target_date=date(2026, 6, 17),
        fetch=fetch,
    )

    assert "Today's Plan" in output
    assert "9:00 AM Team Meeting (Houston, TX) | 72°F | Rain Chance: 40%" in output
    assert "Weather Conditions" in output
    assert "Houston, TX: Rain: Moderate intensity" in output
    assert "Bring an umbrella." in output


def test_handle_command_today_weather_failure(sample_calendar):
    fetch = make_mock_fetch({"results": []}, {"hourly": {}, "daily": {}})

    output = handle_command(
        "today",
        calendar_path=sample_calendar,
        target_date=date(2026, 6, 17),
        fetch=fetch,
    )

    assert "9:00 AM Team Meeting (Houston, TX) | Weather unavailable" in output
    assert NO_RECOMMENDATIONS_MESSAGE in output


def test_handle_command_help():
    assert handle_command("help") == HELP_TEXT


def test_handle_command_exit_returns_none():
    assert handle_command("exit") is None


def test_handle_command_unknown():
    output = handle_command("foo")
    assert "Unknown command" in output
    assert "help" in output


def test_run_repl_exits_on_exit_command(sample_calendar):
    commands = iter(["help", "exit"])
    outputs: list[str] = []

    run_repl(
        input_fn=lambda: next(commands),
        output_fn=outputs.append,
        calendar_path=sample_calendar,
        target_date=date(2026, 6, 17),
        fetch=make_mock_fetch(
            make_geocode_response(),
            make_forecast_response(["2026-06-17T09:00"], [72.0], [40]),
        ),
    )

    assert outputs[0] == HELP_TEXT
