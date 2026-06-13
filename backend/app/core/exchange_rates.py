"""
Currency conversion and metals pricing.

Live prices are fetched from gold-api.com (metals) and open.er-api.com
(exchange rates) via app.services.pricing, cached in Redis for 24h.
Hardcoded constants below serve as fallback values if live API calls fail.
"""

from app.services.pricing import PricingError, get_exchange_rates, get_gold_price_per_gram_usd, get_silver_price_per_gram_usd

# Fallback constants - used only if live API calls fail.
GOLD_PRICE_PER_GRAM_USD_FALLBACK = 63.50
SILVER_PRICE_PER_GRAM_USD_FALLBACK = 0.85

FALLBACK_EXCHANGE_RATES = {
    "USD": 1.0,
    "SGD": 1.34,
    "GBP": 0.79,
    "EUR": 0.92,
    "PKR": 278.50,
    "MYR": 4.47,
    "INR": 86.50,
    "AED": 3.67,
    "SAR": 3.75,
}


async def get_gold_price_usd() -> float:
    """Return live gold price per gram in USD, falling back to constant on failure."""
    try:
        return await get_gold_price_per_gram_usd()
    except PricingError:
        return GOLD_PRICE_PER_GRAM_USD_FALLBACK


async def get_silver_price_usd() -> float:
    """Return live silver price per gram in USD, falling back to constant on failure."""
    try:
        return await get_silver_price_per_gram_usd()
    except PricingError:
        return SILVER_PRICE_PER_GRAM_USD_FALLBACK


async def convert_from_usd(amount_usd: float, currency: str) -> float:
    """Convert a USD amount to the target currency using live exchange rates."""
    try:
        rates = await get_exchange_rates()
        rate = rates.get(currency.upper(), 1.0)
    except PricingError:
        rate = FALLBACK_EXCHANGE_RATES.get(currency.upper(), 1.0)
    return round(amount_usd * rate, 2)