from datetime import date
from pydantic import BaseModel, Field


class GeocodeResult(BaseModel):
    name: str
    state: str = ""
    country: str = ""
    latitude: float
    longitude: float


class DailyWeather(BaseModel):
    date: date
    temp_max_c: float
    temp_min_c: float
    rain_mm: float
    rain_prob_pct: int
    humidity_pct: float | None = None
    wind_kmh: float | None = None


class WeatherReport(BaseModel):
    location: str
    state: str = ""
    latitude: float
    longitude: float
    days: list[DailyWeather]
    summary: str = ""
    source: str = "Open-Meteo"


class MandiPrice(BaseModel):
    commodity: str
    mandi: str
    district: str = ""
    state: str = ""
    min_price: float | None = None
    max_price: float | None = None
    modal_price: float
    price_date: str = ""
    unit: str = "Rs/Quintal"


class MandiPriceReport(BaseModel):
    commodity: str
    prices: list[MandiPrice]
    fetched_at: str = ""
    source: str = "Agmarknet (data.gov.in)"


class SoilProfile(BaseModel):
    latitude: float
    longitude: float
    ph: float | None = None
    nitrogen_kg_ha: float | None = None
    organic_carbon_g_kg: float | None = None
    clay_pct: float | None = None
    sand_pct: float | None = None
    silt_pct: float | None = None
    source: str = "SoilGrids (ISRIC)"


class AdvisoryPassage(BaseModel):
    crop: str = ""
    topic: str = ""
    text: str = Field(..., description="Advisory text passage")
    doc: str = ""
    score: float | None = None


class ToolOutput(BaseModel):
    """Standard wrapper so the agent knows which tool produced this data."""
    tool: str
    ok: bool
    data: dict
    error: str | None = None
