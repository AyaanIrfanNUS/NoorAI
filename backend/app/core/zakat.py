"""
Zakat calculation logic.

Nisab is the minimum threshold of wealth a person must have before
zakat becomes due, traditionally defined as the value of 87.48 grams
of gold or 612.36 grams of silver.

Gold and silver prices are defined in app.core.exchange_rates as
placeholders in USD per gram, then converted into the user's currency.
Replace with live metals price and exchange rate APIs when available.
"""

from app.core.exchange_rates import (
    GOLD_PRICE_PER_GRAM_USD,
    SILVER_PRICE_PER_GRAM_USD,
    convert_from_usd,
)

ZAKAT_RATE = 0.025

GOLD_NISAB_GRAMS = 87.48
SILVER_NISAB_GRAMS = 612.36


def calculate_nisab_gold(currency: str) -> float:
    value_usd = GOLD_NISAB_GRAMS * GOLD_PRICE_PER_GRAM_USD
    return convert_from_usd(value_usd, currency)


def calculate_nisab_silver(currency: str) -> float:
    value_usd = SILVER_NISAB_GRAMS * SILVER_PRICE_PER_GRAM_USD
    return convert_from_usd(value_usd, currency)


def calculate_zakat(
    cash_savings: float,
    gold_value: float,
    silver_value: float,
    business_assets: float,
    currency: str,
) -> dict:
    total_wealth = cash_savings + gold_value + silver_value + business_assets

    nisab_gold = calculate_nisab_gold(currency)
    nisab_silver = calculate_nisab_silver(currency)

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