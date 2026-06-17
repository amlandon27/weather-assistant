"""CLI entry point for the weather-aware daily planning advisor."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Callable

from advice_engine import generate_recommendations
from calendar_reader import Event, format_event_time, get_events_for_date
from weather import JsonFetcher, WeatherResult, default_fetch
from weather import format_daily_conditions, get_weather_for_events

logger = logging.getLogger(__name__)

DEFAULT_CALENDAR_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar.json"

HELP_TEXT = """Available commands:
  today  Show today's plan with weather and recommendations
  help   Show this message
  exit   Quit the application"""


def format_event_line(event: Event, weather: WeatherResult) -> str:
    time_str = format_event_time(event.start)
    base = f"{time_str} {event.title} ({event.location})"

    if weather.insufficient_data:
        return f"{base} | Insufficient data to pull weather"
    if weather.failed:
        return f"{base} | Weather unavailable"
    if weather.weather is None:
        return f"{base} | Weather unavailable"

    event_weather = weather.weather
    return (
        f"{base} | {event_weather.temperature_f}°F"
        f" | Rain Chance: {event_weather.rain_chance_percent}%"
    )


def display_todays_plan(
    calendar_path: Path = DEFAULT_CALENDAR_PATH,
    target_date: date | None = None,
    fetch: JsonFetcher | None = None,
) -> str:
    events = get_events_for_date(calendar_path, target_date)
    weather_fetch = fetch or default_fetch

    lines = ["Today's Plan", ""]

    if not events:
        lines.append("No events scheduled for today.")
    else:
        event_weather_results = get_weather_for_events(events, fetch=weather_fetch)
        for event, weather in event_weather_results:
            lines.append(format_event_line(event, weather))

        daily_conditions = format_daily_conditions(event_weather_results)
        if daily_conditions:
            lines.extend(["", "Weather Conditions", ""])
            lines.extend(daily_conditions)

        recommendations = generate_recommendations(event_weather_results)
        if recommendations:
            lines.extend(["", "Recommendations", ""])
            for recommendation in recommendations:
                lines.append(f"• {recommendation}")

    return "\n".join(lines)


def handle_command(
    command: str,
    calendar_path: Path = DEFAULT_CALENDAR_PATH,
    target_date: date | None = None,
    fetch: JsonFetcher | None = None,
) -> str | None:
    """Process a REPL command. Returns output text, or None to exit."""
    normalized = command.strip().lower()
    logger.info("Handling command=%s", normalized)

    if normalized == "exit":
        return None
    if normalized == "help":
        return HELP_TEXT
    if normalized == "today":
        return display_todays_plan(calendar_path, target_date, fetch=fetch)

    return f"Unknown command: {command}. Type 'help' for available commands."


def run_repl(
    input_fn: Callable[[], str] | None = None,
    output_fn: Callable[[str], None] | None = None,
    calendar_path: Path = DEFAULT_CALENDAR_PATH,
    target_date: date | None = None,
    fetch: JsonFetcher | None = None,
) -> None:
    """Run the interactive REPL until the user exits."""
    read_input = input_fn or (lambda: input("> "))
    write_output = output_fn or print

    logger.info("Starting REPL")
    while True:
        try:
            command = read_input()
        except EOFError:
            logger.info("REPL ended via EOF")
            break

        result = handle_command(command, calendar_path, target_date, fetch=fetch)
        if result is None:
            logger.info("REPL ended via exit command")
            break

        write_output(result)


def main() -> None:
    run_repl()


if __name__ == "__main__":
    main()
