import httpx

from app.utils.config import OPEN_METEO_BASE, UA
from app.tools.schemas import DailyWeather, WeatherReport

BASE_PARAMS = {
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,relative_humidity_2m_mean,wind_speed_10m_max",
    "timezone": "auto",
    "forecast_days": 7,
}


async def fetch_weather(latitude: float, longitude: float, location: str = "", state: str = "") -> WeatherReport:
    params = dict(BASE_PARAMS, latitude=latitude, longitude=longitude)
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(OPEN_METEO_BASE, params=params, headers={"User-Agent": UA})
        r.raise_for_status()
        payload = r.json()

    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    days = [
        DailyWeather(
            date=d,
            temp_max_c=daily.get("temperature_2m_max", [None] * len(dates))[i] or 0.0,
            temp_min_c=daily.get("temperature_2m_min", [None] * len(dates))[i] or 0.0,
            rain_mm=daily.get("precipitation_sum", [0.0] * len(dates))[i] or 0.0,
            rain_prob_pct=int(daily.get("precipitation_probability_max", [0] * len(dates))[i] or 0),
            humidity_pct=daily.get("relative_humidity_2m_mean", [None] * len(dates))[i],
            wind_kmh=daily.get("wind_speed_10m_max", [None] * len(dates))[i],
        )
        for i, d in enumerate(dates)
    ]

    week_rain = sum(day.rain_mm for day in days)
    parts = []
    if days:
        hot = max(days, key=lambda x: x.temp_max_c)
        wet = max(days, key=lambda x: x.rain_mm)
        parts.append(f"7-day rainfall total ≈ {week_rain:.0f} mm")
        parts.append(f"peak temperature {hot.temp_max_c:.0f}°C")
        if wet.rain_mm >= 5:
            parts.append(f"heaviest rain {wet.rain_mm:.0f} mm on {wet.date}")
    return WeatherReport(
        location=location, state=state, latitude=latitude, longitude=longitude,
        days=days, summary="; ".join(parts), source="Open-Meteo",
    )
