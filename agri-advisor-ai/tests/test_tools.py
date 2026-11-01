import asyncio

import pytest

from app.tools.mandi_tool import _normalize_commodity
from app.utils.language import detect_language


def test_commodity_aliases():
    assert _normalize_commodity("bhindi") == "Okhra"
    assert _normalize_commodity("TOMATO ") == "Tomato"
    assert _normalize_commodity("unknown-crop") == "Unknown-Crop"


def test_language_detect():
    assert detect_language("What is the rice price?").code == "en"
    declared = detect_language("రైస్ ధర ఎంత?", "Telugu")
    assert declared.code == "te" and declared.label == "Telugu"


@pytest.mark.asyncio
async def test_weather_tool_live():
    from app.tools.weather_tool import fetch_weather

    report = await fetch_weather(15.83, 78.04, "Kurnool", "Andhra Pradesh")
    assert report.location == "Kurnool"
    assert 5 <= len(report.days) <= 7


@pytest.mark.asyncio
async def test_soil_tool_live():
    from app.tools.soil_tool import fetch_soil

    soil = await fetch_soil(15.83, 78.04)
    assert soil.source.startswith("SoilGrids")
    assert soil.clay_pct is not None or soil.ph is not None


@pytest.mark.asyncio
async def test_geocode_fallback():
    from app.utils.geo import geocode

    r = await geocode("Kurnool")
    assert r is not None and 8 < r.latitude < 20
