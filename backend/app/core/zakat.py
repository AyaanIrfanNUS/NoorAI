"""
Zakat calculation logic.

Nisab thresholds are computed using live gold and silver spot prices
fetched via app.core.exchange_rates. Falls back to hardcoded constants
if live pricing is unavailable.
"""

from app.core.exchange_rates import convert_from_usd, get_gold_price_usd, get_silver_price_usd

ZAKAT_RATE = 0.025

GOLD_NISAB_GRAMS = 87.48
SILVER_NISAB_GRAMS = 612.36


async def calculate_nisab_gold(currency: str) -> float:
    gold_price = await get_gold_price_usd()
    value_usd = GOLD_NISAB_GRAMS * gold_price
    return await convert_from_usd(value_usd, currency)


async def calculate_nisab_silver(currency: str) -> float:
    silver_price = await get_silver_price_usd()
    value_usd = SILVER_NISAB_GRAMS * silver_price
    return await convert_from_usd(value_usd, currency)


async def calculate_zakat(
    cash_savings: float,
    gold_value: float,
    silver_value: float,
    business_assets: float,
    currency: str,
) -> dict:
    total_wealth = cash_savings + gold_value + silver_value + business_assets

    nisab_gold = await calculate_nisab_gold(currency)
    nisab_silver = await calculate_nisab_silver(currency)

    nisab_threshold = min(nisab_gold, nisab_silver)

    is_zakat_due = total_wealth >= nisab_threshold
    zakat_amount = round(total_wealth * ZAKAT_RATE, 2) if is_zakat_due else 0.0

    return {
        "total_wealth": round(total_wealth, 2),
        "nisab_threshold": nisab_threshold,
        "nisab_gold": nisab_gold,
        "nisab_silver": nisab_silver,
        "is_zakat_due": is_zakat_due,
        "zakat_amount": zakat_amount,
        "currency": currency.upper(),
    }