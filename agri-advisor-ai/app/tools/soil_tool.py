import httpx

from app.utils.config import SOILGRIDS_BASE, UA
from app.tools.schemas import SoilProfile

# SoilGrids property metadata (units)
_PROPERTY_DEPTHS = {
    "phh2o": "ph",
    "nitrogen": "nitrogen_kg_ha",
    "soc": "organic_carbon_g_kg",
    "clay": "clay_pct",
    "sand": "sand_pct",
    "silt": "silt_pct",
}


async def fetch_soil(latitude: float, longitude: float) -> SoilProfile:
    params = {
        "lon": longitude,
        "lat": latitude,
        "property": "phh2o,nitrogen,soc,clay,sand,silt",
        "depth": "0-5cm",
        "pdepth": "mean",
        "value": "mean",
    }
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.get(SOILGRIDS_BASE, params=params, headers={"User-Agent": UA})
        r.raise_for_status()
        payload = r.json()

    profile_kwargs: dict = {"latitude": latitude, "longitude": longitude}
    layers = payload.get("properties", {}).get("layers", [])
    for layer in layers:
        name = layer.get("name")
        if name not in _PROPERTY_DEPTHS:
            continue
        values = layer.get("depths", {}).get("0-5cm", {}).get("values", {})
        mean = values.get("mean")
        if mean is None:
            continue
        # SoilGrids v2 returns scaled integers — denormalize to reporting units
        unit_scale = layer.get("metadata", {}).get("scale") or 1
        if unit_scale and unit_scale != 1:
            mean = mean / unit_scale
        field = _PROPERTY_DEPTHS[name]
        try:
            profile_kwargs[field] = float(mean)
        except (TypeError, ValueError):
            continue

    return SoilProfile(**profile_kwargs)
