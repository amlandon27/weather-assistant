"""Generate rule-based weather recommendations."""

from __future__ import annotations

import logging

from calendar_reader import Event
from weather import EventWeather, WeatherResult, is_severe_weather_code

logger = logging.getLogger(__name__)

UMBRELLA_RECOMMENDATION = "Bring an umbrella."
HEAT_RECOMMENDATION = "Dress appropriately and bring a fan."
SEVERE_WEATHER_RECOMMENDATION = "Plan travel accordingly."

RAIN_THRESHOLD_PERCENT = 30
HEAT_THRESHOLD_F = 90
COLD_THRESHOLD_F = 65


def _jacket_recommendation(temperature_f: int) -> str:
    return f"It's {temperature_f}°F — bring a jacket."


def _recommendations_for_weather(weather: EventWeather) -> list[str]:
    """Apply RR-1 through RR-4 to a single event's forecast."""
    recommendations: list[str] = []

    if weather.rain_chance_percent >= RAIN_THRESHOLD_PERCENT:
        recommendations.append(UMBRELLA_RECOMMENDATION)

    if weather.temperature_f > HEAT_THRESHOLD_F:
        recommendations.append(HEAT_RECOMMENDATION)

    if weather.temperature_f < COLD_THRESHOLD_F:
        recommendations.append(_jacket_recommendation(weather.temperature_f))

    if is_severe_weather_code(weather.daily_weather_code):
        recommendations.append(SEVERE_WEATHER_RECOMMENDATION)

    return recommendations


def _deduplicate(recommendations: list[str]) -> list[str]:
    """Keep first occurrence of each recommendation (FR-13)."""
    seen: set[str] = set()
    unique: list[str] = []
    for recommendation in recommendations:
        if recommendation not in seen:
            seen.add(recommendation)
            unique.append(recommendation)
    return unique


def generate_recommendations(
    event_weather_results: list[tuple[Event, WeatherResult]],
) -> list[str]:
    """Evaluate PRD rules across events and return deduplicated recommendations."""
    recommendations: list[str] = []

    for event, weather_result in event_weather_results:
        if not weather_result.success or weather_result.weather is None:
            logger.info(
                "Skipping recommendations for event=%s due to missing weather",
                event.title,
            )
            continue

        recommendations.extend(_recommendations_for_weather(weather_result.weather))

    deduped = _deduplicate(recommendations)
    logger.info("Generated recommendations=%s", deduped)
    return deduped
