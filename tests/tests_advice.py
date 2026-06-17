from datetime import datetime

from advice_engine import generate_recommendations
from calendar_reader import Event
from weather import EventWeather, WeatherResult


def _make_event(title: str = "Team Meeting") -> Event:
    return Event(
        title=title,
        location="Houston, TX",
        start=datetime(2026, 6, 17, 9, 0),
    )


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


def test_generate_recommendations_success():
    event_weather_results = [
        (_make_event("Doctor Appointment"), _weather_result(94, 65)),
        (_make_event("Lunch"), _weather_result(91, 15)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations == [
        "Bring an umbrella.",
        "Dress appropriately and bring a fan.",
    ]


def test_generate_recommendations_failure_skips_events_without_weather():
    event_weather_results = [
        (_make_event("Bad Event"), WeatherResult(failed=True)),
        (_make_event("Good Event"), _weather_result(72, 10)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations == []


def test_generate_recommendations_deduplicates():
    event_weather_results = [
        (_make_event("Event A"), _weather_result(92, 40)),
        (_make_event("Event B"), _weather_result(95, 50)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations.count("Bring an umbrella.") == 1
    assert recommendations.count("Dress appropriately and bring a fan.") == 1


def test_generate_recommendations_jacket_rule():
    event_weather_results = [(_make_event("Morning Walk"), _weather_result(62, 0))]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations == ["It's 62°F — bring a jacket."]


def test_generate_recommendations_severe_weather_code():
    event_weather_results = [
        (_make_event("Commute"), _weather_result(75, 10, daily_weather_code=95)),
    ]

    recommendations = generate_recommendations(event_weather_results)

    assert recommendations == ["Plan travel accordingly."]
