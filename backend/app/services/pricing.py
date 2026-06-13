"""
Live pricing service.

Wraps gold-api.com (gold/silver spot prices) and open.er-api.com
(currency exchange rates), both with Redis caching. Falls back to
hardcoded constants in app.core.exchange_rates if a live call fails
and nothing is cached.
"""

import json

import httpx

from app.core.redis import redis_client

GOLD_API_BASE_URL = "https://api.gold-api.com/price"
EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"

# Metal and exchange rate prices don't meaningfully change within a day
# for zakat calculation purposes.
CACHE_TTL_SECONDS = 24 * 60 * 60

GRAMS_PER_TROY_OUNCE = 31.1034768


class PricingError(Exception):
    """Raised when a live price cannot be fetched and no cache exists."""


async def _fetch_metal_price_usd_per_gram(symbol: str) -> float:
    """Fetch a spot price (USD per troy ounce) and convert to USD per gram."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(f"{GOLD_API_BASE_URL}/{symbol}")
        response.raise_for_status()
        data = response.json()

    price_per_ounce = data["price"]
    return price_per_ounce / GRAMS_PER_TROY_OUNCE


async def get_gold_price_per_gram_usd() -> float:
    """Get the current gold price in USD per gram, cached for 24h."""
    key = "pricing:gold_per_gram_usd"

    cached = await redis_client.get(key)
    if cached:
        return float(cached)

    try:
        price = await _fetch_metal_price_usd_per_gram("XAU")
    except (httpx.HTTPError, KeyError) as exc:
        raise PricingError(f"Could not fetch gold price: {exc}") from exc

    await redis_client.set(key, str(price), ex=CACHE_TTL_SECONDS)
    return price


async def get_silver_price_per_gram_usd() -> float:
    """Get the current silver price in USD per gram, cached for 24h."""
    key = "pricing:silver_per_gram_usd"

    cached = await redis_client.get(key)
    if cached:
        return float(cached)

    try:
        price = await _fetch_metal_price_usd_per_gram("XAG")
    except (httpx.HTTPError, KeyError) as exc:
        raise PricingError(f"Could not fetch silver price: {exc}") from exc

    await redis_client.set(key, str(price), ex=CACHE_TTL_SECONDS)
    return price


async def get_exchange_rates() -> dict[str, float]:
    """Get all USD exchange rates, cached for 24h."""
    key = "pricing:exchange_rates"

    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(EXCHANGE_RATE_API_URL)
            response.raise_for_status()
            data = response.json()

        if data.get("result") != "success":
            raise PricingError(f"Exchange rate API returned an error: {data}")

        rates = data["rates"]
    except (httpx.HTTPError, KeyError) as exc:
        raise PricingError(f"Could not fetch exchange rates: {exc}") from exc

    await redis_client.set(key, json.dumps(rates), ex=CACHE_TTL_SECONDS)
    return rates