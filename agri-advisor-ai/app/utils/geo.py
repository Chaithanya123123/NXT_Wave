import httpx

from app.tools.schemas import GeocodeResult
from app.utils.config import GEOCODING_BASE, NOMINATIM_BASE, UA


async def geocode_openmeteo(query: str) -> GeocodeResult | None:
    params = {"name": query, "count": 1, "language": "en", "format": "json"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(GEOCODING_BASE, params=params, headers={"User-Agent": UA})
        r.raise_for_status()
        results = r.json().get("results") or []
    if not results:
        return None
    top = results[0]
    admin = top.get("admin1") or ""
    return GeocodeResult(
        name=top["name"],
        state=admin,
        country=top.get("country", ""),
        latitude=top["latitude"],
        longitude=top["longitude"],
    )


async def geocode_nominatim(query: str) -> GeocodeResult | None:
    params = {"q": f"{query}, India", "format": "json", "limit": 1, "countrycodes": "in"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(NOMINATIM_BASE, params=params, headers={"User-Agent": UA})
        r.raise_for_status()
        results = r.json()
    if not results:
        return None
    hit = results[0]
    display = hit.get("display_name", "")
    state = ""
    for part in display.split(","):
        if "pradesh" in part.lower() or "state" in part.lower() or "territory" in part.lower():
            state = part.strip()
            break
    return GeocodeResult(
        name=display.split(",")[0].strip(),
        state=state,
        country="India",
        latitude=float(hit["lat"]),
        longitude=float(hit["lon"]),
    )


async def geocode(query: str) -> GeocodeResult | None:
    """Resolve a district/location name to lat/long with a fallback chain."""
    try:
        result = await geocode_openmeteo(query)
        if result:
            return result
    except (httpx.HTTPError, httpx.StreamError):
        pass
    try:
        return await geocode_nominatim(query)
    except (httpx.HTTPError, httpx.StreamError):
        return None
