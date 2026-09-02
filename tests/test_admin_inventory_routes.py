from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.dtos import inventory_dtos
from app.libs.jwt_lib import jwt_dto, jwt_service
from app.services import inventory_services
from app.utils.result import build


client = TestClient(app)


def _override_admin():
    app.dependency_overrides[jwt_service.admin_access_required] = lambda: jwt_dto.TokenPayLoad(
        id="admin-1", role="admin"
    )


def _clear_overrides():
    app.dependency_overrides.clear()


def test_admin_inventory_movements_route_returns_dashboard_contract(monkeypatch):
    _override_admin()
    payload = inventory_dtos.StockMovementListResponseDto(
        status_code=200,
        message="Success",
        data=inventory_dtos.StockMovementListDataDto(
            items=[], page=1, limit=50, total=0
        ),
    )
    monkeypatch.setattr(
        inventory_services,
        "list_stock_movements",
        lambda **kwargs: build(data=payload),
        raising=False,
    )

    try:
        response = client.get("/admin/inventory/movements?page=1&limit=50")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": "Success",
        "data": {"items": [], "page": 1, "limit": 50, "total": 0},
    }


def test_admin_inventory_adjust_route_returns_movement_contract(monkeypatch):
    _override_admin()
    movement = inventory_dtos.StockMovementItemDto(
        id="mov-1",
        variant_id=1,
        product_id="prod-1",
        movement_type="adjust",
        delta=5,
        stock_before=10,
        stock_after=15,
        actor_id="admin-1",
        reason="Restock gudang",
        reference="PO-001",
        created_at=datetime(2026, 9, 2, 12, 0, 0),
    )
    payload = inventory_dtos.StockAdjustmentResponseDto(
        status_code=200,
        message="Stock adjusted successfully",
        data=movement,
    )
    monkeypatch.setattr(
        inventory_services,
        "adjust_stock",
        lambda **kwargs: build(data=payload),
        raising=False,
    )

    try:
        response = client.post(
            "/admin/inventory/adjust",
            json={"variant_id": 1, "delta": 5, "reason": "Restock gudang", "reference": "PO-001"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": "mov-1",
        "variant_id": 1,
        "product_id": "prod-1",
        "movement_type": "adjust",
        "delta": 5,
        "stock_before": 10,
        "stock_after": 15,
        "actor_id": "admin-1",
        "reason": "Restock gudang",
        "reference": "PO-001",
        "created_at": "2026-09-02T12:00:00",
    }


def test_admin_inventory_threshold_route_returns_threshold_contract(monkeypatch):
    _override_admin()
    payload = inventory_dtos.InventoryThresholdResponseDto(
        status_code=200,
        message="Inventory threshold updated successfully",
        data=inventory_dtos.InventoryThresholdDto(
            variant_id=1,
            min_threshold=10,
            updated_by="admin-1",
            updated_at=datetime(2026, 9, 2, 12, 0, 0),
        ),
    )
    monkeypatch.setattr(
        inventory_services,
        "set_variant_threshold",
        lambda **kwargs: build(data=payload),
        raising=False,
    )

    try:
        response = client.put("/admin/inventory/threshold/1", json={"min_threshold": 10})
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["data"] == {
        "variant_id": 1,
        "min_threshold": 10,
        "updated_by": "admin-1",
        "updated_at": "2026-09-02T12:00:00",
    }
