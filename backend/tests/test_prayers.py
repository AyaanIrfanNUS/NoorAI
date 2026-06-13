"""
Tests for prayer tracker endpoints.
"""

from datetime import datetime, timedelta, timezone


async def _register_and_get_token(client, unique_email):
    response = await client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    return response.json()["tokens"]["access_token"]


async def test_log_prayer_success(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    response = await client.post(
        "/prayers/log",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prayer_name": "fajr",
            "prayed_at": "2026-06-11T05:47:00Z",
            "was_on_time": True,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["prayer_name"] == "fajr"
    assert data["was_on_time"] is True


async def test_log_prayer_invalid_name(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    response = await client.post(
        "/prayers/log",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prayer_name": "lunch",
            "prayed_at": "2026-06-11T12:00:00Z",
            "was_on_time": True,
        },
    )

    assert response.status_code == 400


async def test_log_prayer_duplicate(client, unique_email):
    token = await _register_and_get_token(client, unique_email)
    payload = {
        "prayer_name": "fajr",
        "prayed_at": "2026-06-11T05:47:00Z",
        "was_on_time": True,
    }

    first = await client.post(
        "/prayers/log", headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    assert first.status_code == 201

    second = await client.post(
        "/prayers/log", headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    assert second.status_code == 400
    assert "already been logged" in second.json()["detail"]


async def test_log_prayer_requires_auth(client):
    response = await client.post(
        "/prayers/log",
        json={
            "prayer_name": "fajr",
            "prayed_at": "2026-06-11T05:47:00Z",
            "was_on_time": True,
        },
    )

    assert response.status_code == 401


async def test_today_prayers_empty(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    response = await client.get(
        "/prayers/today",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert all(prayer["completed"] is False for prayer in data)


async def test_today_prayers_with_logged_prayer(client, unique_email):
    token = await _register_and_get_token(client, unique_email)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT05:47:00Z")

    await client.post(
        "/prayers/log",
        headers={"Authorization": f"Bearer {token}"},
        json={"prayer_name": "fajr", "prayed_at": today, "was_on_time": True},
    )

    response = await client.get(
        "/prayers/today",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    fajr = next(p for p in data if p["prayer_name"] == "fajr")
    assert fajr["completed"] is True

    isha = next(p for p in data if p["prayer_name"] == "isha")
    assert isha["completed"] is False


async def test_streak_zero_for_new_user(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    response = await client.get(
        "/prayers/streak",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0


async def test_streak_after_complete_yesterday(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

    for name in prayer_names:
        log_response = await client.post(
            "/prayers/log",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prayer_name": name,
                "prayed_at": yesterday.replace(hour=12).isoformat(),
                "was_on_time": True,
            },
        )
        print(f"LOG {name}: status={log_response.status_code}, body={log_response.json()}")

    history_response = await client.get(
        "/prayers/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"HISTORY: {history_response.json()}")

    response = await client.get(
        "/prayers/streak",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    print(f"STREAK: {data}")
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1


async def test_history_pagination(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    for i in range(5):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        await client.post(
            "/prayers/log",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prayer_name": "fajr",
                "prayed_at": day.replace(hour=5, minute=47).isoformat(),
                "was_on_time": True,
            },
        )

    response = await client.get(
        "/prayers/history?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


async def test_stats_for_new_user(client, unique_email):
    token = await _register_and_get_token(client, unique_email)

    response = await client.get(
        "/prayers/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_prayers_logged"] == 0
    assert data["completion_rate"] == 0.0
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0