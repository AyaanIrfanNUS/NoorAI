"""
Tests for direct lookup endpoints (duas and Quran surahs).
"""

from unittest.mock import patch


async def test_find_duas_returns_results(client):
    mock_chunks = [
        {
            "source_file": "Hisn al-Muslim",
            "content": "Test dua content",
            "metadata": {"source_type": "dua", "title": "Test Dua"},
            "similarity": 0.75,
        }
    ]
    with patch("app.api.finder.search_duas", return_value=mock_chunks):
        response = await client.post("/duas/find", json={"situation": "anxiety"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "Test dua content"
    assert data["results"][0]["similarity"] == 0.75


async def test_find_surah_returns_results(client):
    mock_chunks = [
        {
            "source_file": "Quran",
            "content": "Test ayah content",
            "metadata": {
                "source_type": "quran",
                "surah_number": 94,
                "surah_name": "Ash-Sharh",
                "ayah_start": 1,
                "ayah_end": 4,
                "reference": "94:1-4",
            },
        }
    ]
    with patch("app.api.finder.search_quran_by_surah", return_value=mock_chunks):
        response = await client.post("/surah/find", json={"name": "Ash-Sharh"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["metadata"]["surah_name"] == "Ash-Sharh"


async def test_find_surah_not_found(client):
    with patch("app.api.finder.search_quran_by_surah", return_value=[]):
        response = await client.post("/surah/find", json={"name": "not a real surah"})

    assert response.status_code == 404


async def test_list_surahs_returns_all_114(client):
    response = await client.get("/surah/list")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 114
    assert data[0]["number"] == 1
    assert data[0]["name"] == "Al-Faatiha"
    assert data[-1]["number"] == 114
    assert data[-1]["name"] == "An-Naas"


async def test_find_duas_is_public(client):
    # No auth header provided at all; should still succeed.
    with patch("app.api.finder.search_duas", return_value=[]):
        response = await client.post("/duas/find", json={"situation": "anything"})

    assert response.status_code == 200