from types import SimpleNamespace

from app.dtos.order_dtos import AdminOrderStatusUpdateDto
from app.services.order_services import admin_order


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def first(self):
        return self.value


class _ExecuteResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return _ScalarResult(self.value)


class _DummyDB:
    def __init__(self, *values):
        self.values = list(values)
        self.committed = 0
        self.refreshed = []
        self.rolled_back = 0

    def execute(self, _stmt):
        return _ExecuteResult(self.values.pop(0))

    def commit(self):
        self.committed += 1

    def refresh(self, obj):
        self.refreshed.append(obj)

    def rollback(self):
        self.rolled_back += 1


class _DummyRedis:
    def __init__(self):
        self.deleted = []

    def scan_iter(self, pattern):
        return [f"cache::{pattern}"]

    def delete(self, key):
        self.deleted.append(key)


def test_admin_order_status_payload_accepts_tracking_code():
    payload = AdminOrderStatusUpdateDto(status="shipped", code_tracking="JNE123")

    assert payload.status == "shipped"
    assert payload.code_tracking == "JNE123"


def test_admin_update_status_can_store_tracking_code_and_clear_customer_cache(monkeypatch):
    order = SimpleNamespace(
        id="order-1",
        status="paid",
        total_price=18500,
        shipment_id="shipment-1",
        delivery_type="delivery",
        notes=None,
        created_at="2026-09-11T00:00:00",
        customer_id="customer-1",
    )
    shipment = SimpleNamespace(id="shipment-1", code_tracking="")
    db = _DummyDB(order, shipment)
    redis = _DummyRedis()
    monkeypatch.setattr(admin_order, "redis_client", redis)

    result = admin_order.update_order_status_admin(
        db=db,
        order_id="order-1",
        new_status="shipped",
        code_tracking=" JNE123456789 ",
    )

    assert result.error is None
    assert order.status == "shipped"
    assert shipment.code_tracking == "JNE123456789"
    assert db.committed == 1
    assert redis.deleted == [
        "cache::orders:customer-1:*",
        "cache::order:customer-1:order-1",
    ]
