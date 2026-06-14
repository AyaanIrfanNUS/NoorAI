"""
Tests for zakat calculator endpoints.
"""

from unittest.mock import AsyncMock, patch


async def _register_and_get_token(client, unique_email, currency="USD"):
    response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
            "currency": currency,
        },
    )
    return response.json()["tokens"]["access_token"]


# Fixed prices used across all zakat tests for deterministic results.
# Gold: $60.00/g, Silver: $0.80/g, all rates = 1.0 (USD baseline).
MOCK_GOLD_PRICE = 60.00
MOCK_SILVER_PRICE = 0.80
MOCK_EXCHANGE_RATES = {
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

# Pre-computed nisab values using mock prices.
MOCK_NISAB_GOLD_USD = round(87.48 * MOCK_GOLD_PRICE, 2)      # 5248.80
MOCK_NISAB_SILVER_USD = round(612.36 * MOCK_SILVER_PRICE, 2)  # 489.89


def mock_pricing():
    """Return a context manager that patches all three live pricing functions."""
    gold_patch = patch(
        "app.core.exchange_rates.get_gold_price_per_gram_usd",
        new=AsyncMock(return_value=MOCK_GOLD_PRICE),
    )
    silver_patch = patch(
        "app.core.exchange_rates.get_silver_price_per_gram_usd",
        new=AsyncMock(return_value=MOCK_SILVER_PRICE),
    )
    rates_patch = patch(
        "app.core.exchange_rates.get_exchange_rates",
        new=AsyncMock(return_value=MOCK_EXCHANGE_RATES),
    )
    return gold_patch, silver_patch, rates_patch


async def test_calculate_zakat_due(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    with mock_pricing()[0], mock_pricing()[1], mock_pricing()[2]:
        response = await client.post(
            "/zakat/calculate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cash_savings": 10000,
                "gold_value": 0,
                "silver_value": 0,
                "business_assets": 0,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["total_wealth"] == 10000
    assert data["currency"] == "USD"
    assert data["is_zakat_due"] is True
    assert data["zakat_amount"] == round(10000 * 0.025, 2)
    assert data["nisab_gold"] > 0
    assert data["nisab_silver"] > 0


async def test_calculate_zakat_below_nisab(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    with mock_pricing()[0], mock_pricing()[1], mock_pricing()[2]:
        response = await client.post(
            "/zakat/calculate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cash_savings": 1,
                "gold_value": 0,
                "silver_value": 0,
                "business_assets": 0,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["total_wealth"] == 1
    assert data["is_zakat_due"] is False
    assert data["zakat_amount"] == 0.0


async def test_calculate_zakat_uses_user_currency(client, unique_email):
    token = await _register_and_get_token(client, unique_email, currency="SGD")

    with mock_pricing()[0], mock_pricing()[1], mock_pricing()[2]:
        response = await client.post(
            "/zakat/calculate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cash_savings": 10000,
                "gold_value": 0,
                "silver_value": 0,
                "business_assets": 0,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["currency"] == "SGD"


async def test_calculate_zakat_unsupported_currency_falls_back(client, unique_email):
    token = await _register_and_get_token(client, unique_email, currency="XYZ")

    with mock_pricing()[0], mock_pricing()[1], mock_pricing()[2]:
        response = await client.post(
            "/zakat/calculate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cash_savings": 10000,
                "gold_value": 0,
                "silver_value": 0,
                "business_assets": 0,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["currency"] == "XYZ"
    assert data["nisab_gold"] > 0


async def test_calculate_zakat_requires_auth(client):
    response = await client.post(
        "/zakat/calculate",
        json={
            "cash_savings": 10000,
            "gold_value": 0,
            "silver_value": 0,
            "business_assets": 0,
        },
    )
    assert response.status_code == 401


async def test_zakat_history(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    for amount in [5000, 10000, 15000]:
        with mock_pricing()[0], mock_pricing()[1], mock_pricing()[2]:
            await client.post(
                "/zakat/calculate",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "cash_savings": amount,
                    "gold_value": 0,
                    "silver_value": 0,
                    "business_assets": 0,
                },
            )

    response = await client.get(
        "/zakat/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


async def test_zakat_history_requires_auth(client):
    response = await client.get("/zakat/history")
    assert response.status_code == 401


async def test_zakat_pricing_fallback(client, unique_email):
    """Zakat calculation succeeds using fallback constants when live APIs fail."""
    from app.services.pricing import PricingError

    token = await _register_and_get_token(client, unique_email)

    with patch(
        "app.core.exchange_rates.get_gold_price_per_gram_usd",
        new=AsyncMock(side_effect=PricingError("API down")),
    ), patch(
        "app.core.exchange_rates.get_silver_price_per_gram_usd",
        new=AsyncMock(side_effect=PricingError("API down")),
    ), patch(
        "app.core.exchange_rates.get_exchange_rates",
        new=AsyncMock(side_effect=PricingError("API down")),
    ):
        response = await client.post(
            "/zakat/calculate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cash_savings": 10000,
                "gold_value": 0,
                "silver_value": 0,
                "business_assets": 0,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["is_zakat_due"] is True
    assert data["zakat_amount"] == round(10000 * 0.025, 2)


async def test_calculate_zakat_negative_value_rejected(client, unique_email):
    """Negative asset values are rejected at the schema level (422),
    before reaching the pricing/calculation logic."""
    token = await _register_and_get_token(client, unique_email)

    response = await client.post(
        "/zakat/calculate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "cash_savings": -5000,
            "gold_value": 0,
            "silver_value": 0,
            "business_assets": 0,
        },
    )

    assert response.status_code == 422