from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class DummyScalarResult:
    def __init__(self, value):
        self.value = value

    def all(self):
        return self.value

    def first(self):
        return self.value


class DummyExecuteResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return DummyScalarResult(self.value)


class DummyQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class DummyDB:
    def __init__(self, execute_results=None, query_result=None):
        self.execute_results = list(execute_results or [])
        self.query_result = query_result
        self.added = []
        self.committed = 0
        self.rolled_back = 0
        self.refreshed = []

    def execute(self, stmt):
        if not self.execute_results:
            raise AssertionError("Unexpected execute call")
        return DummyExecuteResult(self.execute_results.pop(0))

    def query(self, model):
        return DummyQuery(self.query_result)

    def add(self, obj):
        if getattr(obj, "id", None) is None and obj.__class__.__name__ == "OrderModel":
            obj.id = "generated-order-id"
        self.added.append(obj)

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def refresh(self, obj):
        self.refreshed.append(obj)

    def flush(self):
        return None


@pytest.fixture
def checkout_module():
    import importlib

    return importlib.import_module("app.services.order_services.checkout")


@pytest.fixture
def my_order_module():
    import importlib

    return importlib.import_module("app.services.order_services.my_order")


@pytest.fixture
def detail_order_module():
    import importlib

    return importlib.import_module("app.services.order_services.detail_order")


@pytest.fixture
def edit_order_module():
    import importlib

    return importlib.import_module("app.services.order_services.edit_order")


@pytest.fixture
def fake_cart_item():
    return SimpleNamespace(
        product_id="product-1",
        variant_id=10,
        quantity=2,
        is_active=True,
        product_price=5000,
        total_price=9000,
    )


def test_checkout_creates_order_and_items(monkeypatch, checkout_module, fake_cart_item):
    shipment = SimpleNamespace(id="ship-1", shipping_cost=2000)
    db = DummyDB(execute_results=[[fake_cart_item]], query_result=shipment)

    monkeypatch.setattr(
        checkout_module,
        "get_cart_total",
        lambda items: SimpleNamespace(total_all_active_prices=9000),
    )
    monkeypatch.setattr(checkout_module, "redis_client", None)

    result = checkout_module.checkout(db, "user-1")

    assert result.error is None
    assert result.data["status_code"] == 201
    assert result.data["data"]["total_price"] == 11000.0
    assert db.committed == 1
    assert len(db.added) == 2


def test_checkout_returns_404_style_payload_when_cart_empty(monkeypatch, checkout_module):
    db = DummyDB(execute_results=[[]], query_result=None)
    monkeypatch.setattr(checkout_module, "redis_client", None)

    result = checkout_module.checkout(db, "user-1")

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 400
    assert result.error.detail["status_code"] == 404


def test_my_order_returns_empty_list(monkeypatch, my_order_module):
    db = DummyDB(execute_results=[[]])
    monkeypatch.setattr(my_order_module, "redis_client", None)

    result = my_order_module.my_order(db, "user-1")

    assert result.error is None
    assert result.data.status_code == 200
    assert result.data.data == []


def test_my_order_handles_missing_shipping_relations(monkeypatch, my_order_module):
    order = SimpleNamespace(
        id="order-1",
        status="pending",
        total_price=12000,
        shipment_id="ship-1",
        delivery_type="delivery",
        notes=None,
        customer_name="Aris",
        created_at="2026-04-21T00:00:00",
        shipping_cost=0,
        order_item_lists=[],
    )
    db = DummyDB(execute_results=[[order]])
    monkeypatch.setattr(my_order_module, "redis_client", None)

    result = my_order_module.my_order(db, "user-1")

    assert result.error is None
    assert result.data.status_code == 200
    assert len(result.data.data) == 1
    assert result.data.data[0].shipping_cost == 0


def test_detail_order_returns_404_when_missing(monkeypatch, detail_order_module):
    db = DummyDB(execute_results=[None])
    monkeypatch.setattr(detail_order_module, "redis_client", None)

    result = detail_order_module.detail_order(db, "user-1", "order-x")

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 404


def test_detail_order_handles_missing_shipping_relations(monkeypatch, detail_order_module):
    order = SimpleNamespace(
        id="order-1",
        status="pending",
        total_price=12000,
        delivery_type="delivery",
        notes=None,
        customer_name="Aris",
        created_at="2026-04-21T00:00:00",
        shipping_cost=0,
        my_shipping={
            "id": "ship-1",
            "my_address": None,
            "my_courier": None,
            "created_at": "2026-04-21T00:00:00",
        },
        order_item_lists=[],
    )
    db = DummyDB(execute_results=[order])
    monkeypatch.setattr(detail_order_module, "redis_client", None)

    result = detail_order_module.detail_order(db, "user-1", "order-1")

    assert result.error is None
    assert result.data.status_code == 200
    assert result.data.data.my_shipping["my_address"] is None
    assert result.data.data.my_shipping["my_courier"] is None


def test_edit_order_switches_to_pickup(monkeypatch, edit_order_module):
    order = SimpleNamespace(
        id="order-1",
        customer_id="user-1",
        shipment_id="ship-1",
        delivery_type="delivery",
        notes="old",
        total_price=12000,
        status="pending",
        created_at="2026-04-21T00:00:00",
    )
    db = DummyDB(execute_results=[order])
    monkeypatch.setattr(edit_order_module, "redis_client", None)

    payload = SimpleNamespace(order_id="order-1")
    order_dto = SimpleNamespace(delivery_type=edit_order_module.DeliveryTypeEnum.pickup, notes="ambil sendiri")

    result = edit_order_module.edit_order(db, payload, order_dto, "user-1")

    assert result.error is None
    assert result.data["status_code"] == 200
    assert order.shipment_id is None
    assert order.notes == "ambil sendiri"
    assert db.committed == 1


def test_edit_order_rejects_invalid_shipment(monkeypatch, edit_order_module):
    order = SimpleNamespace(
        id="order-1",
        customer_id="user-1",
        shipment_id=None,
        delivery_type="pickup",
        notes=None,
        total_price=12000,
        status="pending",
        created_at="2026-04-21T00:00:00",
    )
    db = DummyDB(execute_results=[order], query_result=None)
    monkeypatch.setattr(edit_order_module, "redis_client", None)

    payload = SimpleNamespace(order_id="order-1")
    order_dto = SimpleNamespace(
        delivery_type=edit_order_module.DeliveryTypeEnum.delivery,
        shipment_id="ship-missing",
        notes="kirim",
    )

    result = edit_order_module.edit_order(db, payload, order_dto, "user-1")

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 400
