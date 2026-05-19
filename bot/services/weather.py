import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

OWM_API_KEY = os.getenv("OWM_API_KEY")
OWM_API_KEY = os.getenv("OWM_API_KEY")
print(f"DEBUG WEATHER: ключ = {OWM_API_KEY!r}")
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"







CITIES = {
    "moscow": {"name": "Москва", "lat": 55.7558, "lon": 37.6173},
    "pattaya": {"name": "Паттайя", "lat": 12.94, "lon": 100.89},
}


@dataclass
class Weather:
    city: str
    temp: float
    feels_like: float
    description: str
    icon: str


async def fetch_weather(city_key: str) -> Weather | None:
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
            response = await client.get(OWM_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        logger.error("Ошибка запроса погоды для %s: %s", city_key, e)
        return None

    return Weather(
        city=city["name"],
        temp=round(data["main"]["temp"], 1),
        feels_like=round(data["main"]["feels_like"], 1),
        description=data["weather"][0]["description"],
        icon=_icon_to_emoji(data["weather"][0]["icon"]),
    )


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
