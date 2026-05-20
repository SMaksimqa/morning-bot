import logging
import os
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

OWM_API_KEY = os.getenv("OWM_API_KEY")
OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

CITIES = {
    "moscow": {"name": "Москва", "lat": 55.7558, "lon": 37.6173},
    "pattaya": {"name": "Паттайя", "lat": 12.9236, "lon": 100.8825},
}


@dataclass
class ForecastPoint:
    temp: float
    description: str
    rain: bool
    snow: bool


@dataclass
class Weather:
    city: str
    temp: float
    feels_like: float
    description: str
    icon: str
    forecast: list[ForecastPoint] = field(default_factory=list)


def _icon_to_emoji(icon_code: str) -> str:
    mapping = {
        "01": "☀️",
        "02": "🌤",
        "03": "⛅",
        "04": "☁️",
        "09": "🌧",
        "10": "🌦",
        "11": "⛈",
        "13": "❄️",
        "50": "🌫",
    }
    return mapping.get(icon_code[:2], "🌡")


async def fetch_weather(city_key: str, with_forecast: bool = False) -> Weather | None:
    if city_key not in CITIES:
        logger.error("Неизвестный город: %s", city_key)
        return None

    city = CITIES[city_key]
    params = {
        "lat": city["lat"],
        "lon": city["lon"],
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "ru",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            current_resp = await client.get(OWM_CURRENT_URL, params=params)
            current_resp.raise_for_status()
            current_data = current_resp.json()

            forecast_points = []
            if with_forecast:
                forecast_resp = await client.get(OWM_FORECAST_URL, params=params)
                forecast_resp.raise_for_status()
                forecast_data = forecast_resp.json()

                for item in forecast_data.get("list", [])[:4]:
                    weather_main = item["weather"][0]["main"].lower()
                    forecast_points.append(ForecastPoint(
                        temp=round(item["main"]["temp"], 1),
                        description=item["weather"][0]["description"],
                        rain="rain" in weather_main,
                        snow="snow" in weather_main,
                    ))

    except httpx.HTTPError as e:
        logger.error("Ошибка запроса погоды для %s: %s", city_key, e)
        return None

    return Weather(
        city=city["name"],
        temp=round(current_data["main"]["temp"], 1),
        feels_like=round(current_data["main"]["feels_like"], 1),
        description=current_data["weather"][0]["description"],
        icon=_icon_to_emoji(current_data["weather"][0]["icon"]),
        forecast=forecast_points,
    )


def describe_forecast(weather: Weather) -> str | None:
    if not weather.forecast:
        return None

    temps = [p.temp for p in weather.forecast]
    min_t = min(temps)
    max_t = max(temps)
    last_t = temps[-1]

    has_rain = any(p.rain for p in weather.forecast)
    has_snow = any(p.snow for p in weather.forecast)

    parts = []

    diff = last_t - weather.temp
    if diff <= -4:
        parts.append(f"к вечеру похолодает до {last_t:+.0f}°")
    elif diff >= 4:
        parts.append(f"к вечеру потеплеет до {last_t:+.0f}°")
    else:
        parts.append(f"днём около {max_t:+.0f}°")

    if has_snow:
        parts.append("ожидается снег")
    elif has_rain:
        parts.append("возможен дождь")
    else:
        parts.append("без осадков")

    return ", ".join(parts).capitalize() + "."
