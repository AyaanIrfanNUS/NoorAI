"""
Exchange rate constants for currency conversion.

Gold and silver prices are stored in USD per gram. Exchange rates convert
USD to other supported currencies. All values are placeholders and should
be replaced with a live exchange rate API and live metals price API.
"""

GOLD_PRICE_PER_GRAM_USD = 63.50
SILVER_PRICE_PER_GRAM_USD = 0.85

USD_EXCHANGE_RATES = {
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


def convert_from_usd(amount_usd: float, currency: str) -> float:
    rate = USD_EXCHANGE_RATES.get(currency.upper())
    if rate is None:
        rate = USD_EXCHANGE_RATES["USD"]
    return round(amount_usd * rate, 2)