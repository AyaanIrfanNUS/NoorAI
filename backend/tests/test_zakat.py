"""
Tests for zakat calculator endpoints.
"""


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


async def test_calculate_zakat_due(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

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