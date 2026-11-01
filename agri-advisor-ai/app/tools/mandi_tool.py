import datetime as _dt
import json as _json
import time as _time
import xml.etree.ElementTree as _ET

import httpx

from app.utils.config import AGMARKNET_BASE, DATA_GOV_API_KEY, UA
from app.tools.schemas import MandiPrice, MandiPriceReport

# The national feed doesn't change minute-to-minute and costs several seconds
# to pull (limit=2000) — cache it for 30 minutes across requests.
_FEED_CACHE_TTL = 1800  # seconds
_feed_cache: dict = {"ts": 0.0, "records": []}


def _parse_payload(text: str) -> list[dict]:
    """data.gov.in flaps between JSON and XML — parse either."""
    text = text.strip()
    if text.startswith("{"):
        try:
            return (_json.loads(text) or {}).get("records") or []
        except _json.JSONDecodeError:
            pass
    if "<result" in text or text.startswith("<?xml"):
        try:
            root = _ET.fromstring(text)
            records = root.find("records")
            out = []
            if records is not None:
                for item in records.findall("item"):
                    out.append({child.tag: (child.text or "") for child in item})
            else:
                for item in root.findall(".//records/item"):
                    out.append({child.tag: (child.text or "") for child in item})
            return out
        except _ET.ParseError:
            pass
    raise ValueError("unparsable mandi API payload")


async def _get_feed() -> list[dict]:
    """Live Agmarknet national feed, cached for 30 minutes."""
    if _feed_cache["records"] and (_time.time() - _feed_cache["ts"]) < _FEED_CACHE_TTL:
        return _feed_cache["records"]
    if not DATA_GOV_API_KEY:
        raise RuntimeError("DATA_GOV_API_KEY missing — get one free at data.gov.in")
    params = {"api-key": DATA_GOV_API_KEY, "limit": 2000}
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.get(
            AGMARKNET_BASE,
            params=params,
            headers={"User-Agent": UA, "Accept": "application/json"},
        )
        r.raise_for_status()
        records = _parse_payload(r.text)
    if records:
        _feed_cache["records"] = records
        _feed_cache["ts"] = _time.time()
    return records


# Commodity name variants used by Agmarknet, so a farmer saying "bhindi"
# still resolves to Okhra etc.
COMMODITY_ALIASES = {
    "bhindi": "Okhra", "okra": "Okhra", "lady finger": "Okhra",
    "brinjal": "Brinjal", "eggplant": "Brinjal",
    "tomato": "Tomato", "potato": "Potato", "onion": "Onion",
    "paddy": "Paddy(Dhan)(Common)", "dhan": "Paddy(Dhan)(Common)", "rice": "Rice",
    "wheat": "Wheat", "maize": "Maize", "cotton": "Cotton",
    "groundnut": "Groundnut", "soybean": "Soybean", "gram": "Gram",
    "tur": "Tur", "arhar": "Arhar (Tur-Whole)", "dal": "Tur",
    "chana": "Chana", "mustard": "Mustard", "sunflower": "Sunflower",
    "chilli": "Chilli(Dry)", "banana": "Banana", "mango": "Mango",
    "apple": "Apple", "cabbage": "Cabbage", "cauliflower": "Cauliflower",
    "carrot": "Carrot", "ginger": "Ginger", "garlic": "Garlic",
    "capsicum": "Capsicum", "coriander": "Coriander(Seed)",
    "bajra": "Bajra(Pearl Millet/Cumbu)", "jowar": "Jowar(Sorghum)",
    "ragi": "Ragi (Finger Millet)", "urad": "Urad(Black Matpe-Whole)",
}


def _normalize_commodity(name: str) -> str:
    return COMMODITY_ALIASES.get(name.strip().lower(), name.strip().title())


def _to_price(rec: dict, commodity: str) -> MandiPrice | None:
    def _num(key: str) -> float | None:
        try:
            return float(rec.get(key))
        except (TypeError, ValueError):
            return None
    modal = _num("modal_price")
    if modal is None:
        return None
    return MandiPrice(
        commodity=rec.get("commodity", commodity),
        mandi=rec.get("market", rec.get("market_name", "")),
        district=rec.get("district", ""),
        state=rec.get("state", ""),
        min_price=_num("min_price"),
        max_price=_num("max_price"),
        modal_price=modal,
        price_date=str(rec.get("arrival_date", "")),
        unit=rec.get("unit", "Rs/Quintal"),
    )


def _filter_feed(
    records: list[dict],
    raw_crop: str,
    district: str = "",
    state: str = "",
) -> list[MandiPrice]:
    prices: list[MandiPrice] = []
    for rec in records:
        if raw_crop and raw_crop not in str(rec.get("commodity", "")).upper():
            continue
        if district and district.lower() not in str(rec.get("district", "")).lower():
            continue
        if state and state.lower() not in str(rec.get("state", "")).lower():
            continue
        p = _to_price(rec, raw_crop)
        if p:
            prices.append(p)
    prices.sort(key=lambda p: p.modal_price, reverse=True)
    return prices


async def fetch_mandi_prices(
    commodity: str, state: str = "", district: str = "", limit: int = 10
) -> MandiPriceReport:
    commodity = _normalize_commodity(commodity)
    raw_crop = commodity.split("(")[0].strip().upper()

    records = await _get_feed()

    # The Agmarknet feed doesn't support server-side field filters —
    # filter the live feed locally (still real-time data).
    prices = _filter_feed(records, raw_crop, district, state)
    widened = False
    if not prices and (district or state):
        # district/state had no rows today → widen to nationwide matches
        prices = _filter_feed(records, raw_crop)
        widened = bool(prices)

    return MandiPriceReport(
        commodity=commodity,
        prices=prices[:limit],
        fetched_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        source=("Agmarknet (data.gov.in) — nationwide feed, district had no rows"
                if widened else "Agmarknet (data.gov.in)"),
    )
