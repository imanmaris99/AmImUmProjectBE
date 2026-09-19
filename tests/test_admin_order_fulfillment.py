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


def test_admin_update_status_can_store_tracking_code_clear_cache_and_notify_customer(monkeypatch):
    order = SimpleNamespace(
        id="order-1",
        status="paid",
        total_price=18500,
        shipment_id="shipment-1",
        delivery_type="delivery",
        notes=None,
        created_at="2026-09-11T00:00:00",
        customer_id="customer-1",
        customer_email="customer@example.com",
        customer_name="Customer Test",
        my_shipping=SimpleNamespace(code_tracking=""),
    )
    shipment = SimpleNamespace(id="shipment-1", code_tracking="")
    db = _DummyDB(order, shipment)
    redis = _DummyRedis()
    sent = []
    monkeypatch.setattr(admin_order, "redis_client", redis)
    monkeypatch.setattr(admin_order, "send_order_status_email", lambda **kwargs: sent.append(kwargs) or True)

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
    assert sent == [{
        "to_email": "customer@example.com",
        "order_id": "order-1",
        "customer_name": "Customer Test",
        "status_value": "shipped",
        "code_tracking": "JNE123456789",
    }]
    assert redis.deleted == [
        "cache::orders:customer-1:*",
        "cache::order:customer-1:order-1",
    ]


def test_admin_update_status_does_not_fail_when_customer_email_fails(monkeypatch):
    order = SimpleNamespace(
        id="order-2",
        status="processing",
        total_price=18500,
        shipment_id=None,
        delivery_type="pickup",
        notes=None,
        created_at="2026-09-11T00:00:00",
        customer_id="customer-2",
        customer_email="customer@example.com",
        customer_name="Customer Test",
        my_shipping=None,
    )
    db = _DummyDB(order)
    monkeypatch.setattr(admin_order, "redis_client", None)

    def fail_email(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(admin_order, "send_order_status_email", fail_email)

    result = admin_order.update_order_status_admin(
        db=db,
        order_id="order-2",
        new_status="completed",
    )

    assert result.error is None
    assert order.status == "completed"
    assert db.committed == 1
    assert db.rolled_back == 0
