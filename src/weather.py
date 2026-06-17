"""Retrieve event-specific weather forecasts from Open-Meteo."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from calendar_reader import Event

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

JsonFetcher = Callable[[str], dict]

# WMO weather interpretation codes returned by Open-Meteo.
WEATHER_CODE_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Drizzle: Light intensity",
    53: "Drizzle: Moderate intensity",
    55: "Drizzle: Dense intensity",
    56: "Freezing drizzle: Light intensity",
    57: "Freezing drizzle: Dense intensity",
    61: "Rain: Slight intensity",
    63: "Rain: Moderate intensity",
    65: "Rain: Heavy intensity",
    66: "Freezing rain: Light intensity",
    67: "Freezing rain: Heavy intensity",
    71: "Snowfall: Slight intensity",
    73: "Snowfall: Moderate intensity",
    75: "Snowfall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight intensity",
    81: "Rain showers: Moderate intensity",
    82: "Rain showers: Violent intensity",
    85: "Snow showers: Slight intensity",
    86: "Snow showers: Heavy intensity",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

SEVERE_WEATHER_CODES = {65, 67, 82, 86, 95, 96, 99}


@dataclass(frozen=True)
class EventWeather:
    temperature_f: int
    rain_chance_percent: int
    daily_weather_code: int

    @property
    def daily_condition(self) -> str:
        return describe_weather_code(self.daily_weather_code)


@dataclass(frozen=True)
class WeatherResult:
    weather: EventWeather | None = None
    insufficient_data: bool = False
    failed: bool = False

    @property
    def success(self) -> bool:
        return self.weather is not None


def describe_weather_code(code: int) -> str:
    return WEATHER_CODE_DESCRIPTIONS.get(code, f"Unknown weather code ({code})")


def is_severe_weather_code(code: int) -> bool:
    return code in SEVERE_WEATHER_CODES


def default_fetch(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def _location_query(location: str) -> str:
    return location.split(",")[0].strip()


def geocode_location(
    location: str,
    fetch: JsonFetcher = default_fetch,
) -> tuple[float, float] | None:
    if not location.strip():
        return None

    params = urllib.parse.urlencode({"name": _location_query(location), "count": 1})
    data = fetch(f"{GEOCODING_URL}?{params}")
    results = data.get("results") or []
    if not results:
        logger.info("Geocoding returned no results for location=%s", location)
        return None

    first = results[0]
    logger.info(
        "Geocoded location=%s to lat=%s lon=%s",
        location,
        first["latitude"],
        first["longitude"],
    )
    return first["latitude"], first["longitude"]


def _match_hourly_forecast(
    event_time: datetime,
    hourly: dict,
) -> tuple[float, float] | None:
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rain = hourly.get("precipitation_probability", [])
    hour_key = event_time.strftime("%Y-%m-%dT%H:00")

    try:
        index = times.index(hour_key)
    except ValueError:
        logger.info("No hourly forecast match for event_time=%s", hour_key)
        return None

    return temps[index], rain[index]


def _match_daily_weather_code(event_time: datetime, daily: dict) -> int | None:
    times = daily.get("time", [])
    codes = daily.get("weather_code", [])
    date_key = event_time.date().isoformat()

    try:
        index = times.index(date_key)
    except ValueError:
        logger.info("No daily weather_code match for date=%s", date_key)
        return None

    return int(codes[index])


def format_daily_conditions(
    event_weather_results: list[tuple[Event, WeatherResult]],
) -> list[str]:
    """Build deduplicated daily condition lines per event location."""
    seen_locations: set[str] = set()
    lines: list[str] = []

    for event, weather_result in event_weather_results:
        if not weather_result.success or weather_result.weather is None:
            continue
        if event.location in seen_locations:
            continue

        seen_locations.add(event.location)
        lines.append(
            f"{event.location}: {weather_result.weather.daily_condition}"
        )

    return lines


def get_event_weather(
    event: Event,
    fetch: JsonFetcher = default_fetch,
) -> WeatherResult:
    if not event.location.strip():
        logger.info("Insufficient event data for weather: title=%s", event.title)
        return WeatherResult(insufficient_data=True)

    try:
        coords = geocode_location(event.location, fetch)
        if coords is None:
            return WeatherResult(failed=True)

        lat, lon = coords
        params = urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation_probability",
                "daily": "weather_code",
                "temperature_unit": "fahrenheit",
                "timezone": "auto",
                "forecast_days": 16,
            }
        )
        forecast = fetch(f"{FORECAST_URL}?{params}")
        hourly = forecast.get("hourly", {})
        daily = forecast.get("daily", {})

        matched_hourly = _match_hourly_forecast(event.start, hourly)
        daily_weather_code = _match_daily_weather_code(event.start, daily)
        if matched_hourly is None or daily_weather_code is None:
            return WeatherResult(failed=True)

        temperature_f, rain_chance_percent = matched_hourly
        weather = EventWeather(
            temperature_f=round(temperature_f),
            rain_chance_percent=round(rain_chance_percent),
            daily_weather_code=daily_weather_code,
        )
        logger.info(
            "Retrieved weather for title=%s location=%s temp=%s rain=%s condition=%s",
            event.title,
            event.location,
            weather.temperature_f,
            weather.rain_chance_percent,
            weather.daily_condition,
        )
        return WeatherResult(weather=weather)
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.exception("Weather retrieval failed for title=%s", event.title)
        return WeatherResult(failed=True)


def get_weather_for_events(
    events: list[Event],
    fetch: JsonFetcher = default_fetch,
) -> list[tuple[Event, WeatherResult]]:
    return [(event, get_event_weather(event, fetch)) for event in events]
