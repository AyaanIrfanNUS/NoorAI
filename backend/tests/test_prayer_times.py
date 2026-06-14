"""
Tests for prayer times endpoints.
"""

from unittest.mock import AsyncMock, patch

MOCK_PRAYER_TIMES = {
    "date": "2026-06-13",
    "timezone": "Asia/Singapore",
    "timings": {
        "Fajr": "05:44",
        "Sunrise": "06:59",
        "Dhuhr": "13:05",
        "Asr": "16:31",
        "Maghrib": "19:11",
        "Isha": "20:21",
    },
}


async def _register_with_location(client, unique_email):
    response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
            "location_lat": 1.3521,
            "location_lng": 103.8198,
        },
    )
    return response.json()["tokens"]["access_token"]


async def _register_without_location(client, unique_email):
    response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    return response.json()["tokens"]["access_token"]


async def test_prayer_times_today(client, unique_email):
    token = await _register_with_location(client, unique_email)

    with patch(
        "app.api.prayer_times.get_prayer_times",
        new=AsyncMock(return_value=MOCK_PRAYER_TIMES),
    ):
        response = await client.get(
            "/prayer-times/today",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-06-13"
    assert data["timezone"] == "Asia/Singapore"
    assert "Fajr" in data["timings"]
    assert "Sunrise" in data["timings"]
    assert "Isha" in data["timings"]


async def test_prayer_times_today_requires_auth(client):
    response = await client.get("/prayer-times/today")
    assert response.status_code == 401


async def test_prayer_times_today_requires_location(client, unique_email):
    token = await _register_without_location(client, unique_email)

    response = await client.get(
        "/prayer-times/today",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Location not set" in response.json()["detail"]


async def test_prayer_times_next(client, unique_email):
    token = await _register_with_location(client, unique_email)

    with patch(
        "app.api.prayer_times.get_prayer_times",
        new=AsyncMock(return_value=MOCK_PRAYER_TIMES),
    ):
        response = await client.get(
            "/prayer-times/next",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["prayer_name"] in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    assert ":" in data["time"]
    assert data["timezone"] == "Asia/Singapore"
    assert data["seconds_until"] >= 0


async def test_prayer_times_next_requires_auth(client):
    response = await client.get("/prayer-times/next")
    assert response.status_code == 401


async def test_prayer_times_aladhan_unavailable(client, unique_email):
    """Returns 503 when Aladhan API is unreachable and nothing is cached."""
    from app.services.prayer_times import PrayerTimesError

    token = await _register_with_location(client, unique_email)

    with patch(
        "app.api.prayer_times.get_prayer_times",
        new=AsyncMock(side_effect=PrayerTimesError("Aladhan unreachable")),
    ):
        response = await client.get(
            "/prayer-times/today",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 503


async def test_school_affects_asr_time():
    """Hanafi school (1) produces a later Asr time than the default
    school (0) for the same location and date - verified against the
    real Aladhan API."""
    from datetime import date
    from app.services.prayer_times import _fetch_from_aladhan

    target_date = date(2026, 6, 14)

    shafi_result = await _fetch_from_aladhan(
        lat=1.3521, lng=103.8198, calculation_method=3, school=0, target_date=target_date
    )
    hanafi_result = await _fetch_from_aladhan(
        lat=1.3521, lng=103.8198, calculation_method=3, school=1, target_date=target_date
    )

    assert shafi_result["timings"]["Asr"] != hanafi_result["timings"]["Asr"]