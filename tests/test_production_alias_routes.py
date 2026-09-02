from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.utils.result import build
from app.services import production_services


client = TestClient(app)


def test_legacy_production_all_alias_matches_brand_all(monkeypatch):
    payload = {
        "status_code": 200,
        "message": "All list products from Production or brand successfully retrieved",
        "data": [
            {
                "id": 1,
                "name": "Amimum Herbal",
                "photo_url": None,
                "description_list": ["Herbal pilihan"],
                "category": "Herbal",
                "created_at": datetime(2026, 1, 1, 0, 0, 0),
            }
        ],
    }
    monkeypatch.setattr(production_services, "get_all_productions", lambda db: build(data=payload))

    response = client.get("/production/all")

    assert response.status_code == 200
    assert response.json()["message"] == payload["message"]
    assert response.json()["data"][0]["name"] == "Amimum Herbal"


def test_legacy_production_promo_alias_matches_brand_promo(monkeypatch):
    payload = {
        "status_code": 200,
        "message": "Info about promo from Production or brand successfully retrieved",
        "data": [
            {
                "id": 1,
                "name": "Amimum Herbal",
                "photo_url": None,
                "promo_special": 10.0,
            }
        ],
    }
    monkeypatch.setattr(production_services, "get_all_promo", lambda db: build(data=payload))

    response = client.get("/production/promo")

    assert response.status_code == 200
    assert response.json() == payload
