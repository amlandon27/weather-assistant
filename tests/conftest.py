"""Shared test helpers."""


def make_mock_fetch(geocode_response: dict, forecast_response: dict):
    def fetch(url: str) -> dict:
        if "geocoding-api.open-meteo.com" in url:
            return geocode_response
        if "api.open-meteo.com" in url:
            return forecast_response
        raise AssertionError(f"Unexpected URL: {url}")

    return fetch


def make_forecast_response(
    hourly_times: list[str],
    temperatures: list[float],
    rain_chances: list[int],
    daily_weather_code: int = 0,
    daily_date: str = "2026-06-17",
):
    return {
        "hourly": {
            "time": hourly_times,
            "temperature_2m": temperatures,
            "precipitation_probability": rain_chances,
        },
        "daily": {
            "time": [daily_date],
            "weather_code": [daily_weather_code],
        },
    }


def make_geocode_response():
    return {"results": [{"latitude": 29.76, "longitude": -95.36, "name": "Houston"}]}
