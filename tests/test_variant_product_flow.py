from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


NOW = datetime(2026, 4, 21, 11, 30, 0)


class DummyDB:
    def __init__(self, product=None, variant=None):
        self.product = product
        self.variant = variant
        self.added = []
        self.committed = False
        self.refreshed = []
        self.rolled_back = False

    def query(self, model):
        db = self

        class Query:
            def filter(self, *_args, **_kwargs):
                return self

            def first(self):
                if model.__name__ == "ProductModel":
                    return db.product
                return db.variant

        return Query()

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "created_at", None) is None:
            obj.created_at = NOW
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = NOW
        if getattr(obj, "id", None) is None:
            obj.id = 99

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)
        if getattr(obj, "created_at", None) is None:
            obj.created_at = NOW
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = NOW

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def create_type_module():
    import importlib

    return importlib.import_module("app.services.pack_type_services.create_type")


@pytest.fixture
def update_stock_module():
    import importlib

    return importlib.import_module("app.services.pack_type_services.update_stock")


@pytest.fixture
def cart_post_item_module():
    import importlib

    return importlib.import_module("app.services.cart_services.post_item")


def test_create_type_rejects_missing_product(create_type_module):
    db = DummyDB(product=None)
    payload = SimpleNamespace(
        product_id="missing-product",
        model_dump=lambda: {
            "product_id": "missing-product",
            "name": "Sachet",
            "min_amount": 1,
            "variant": "Jeruk",
            "expiration": None,
            "stock": 10,
            "price": 15000.0,
            "discount": 5.0,
        }
    )

    result = create_type_module.create_type(db, payload, "admin-1")

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 404


def test_create_type_returns_variant_price(create_type_module):
    product = SimpleNamespace(id="prod-1", name="Teh Herbal")
    db = DummyDB(product=product)
    payload = SimpleNamespace(
        product_id="prod-1",
        model_dump=lambda: {
            "product_id": "prod-1",
            "name": "Sachet",
            "min_amount": 1,
            "variant": "Jeruk",
            "expiration": None,
            "stock": 10,
            "price": 15000.0,
            "discount": 10.0,
        }
    )

    result = create_type_module.create_type(db, payload, "admin-1")

    assert result.error is None
    assert result.data.data.price == 15000.0
    assert result.data.data.discounted_price == 13500.0


def test_update_stock_only_updates_provided_fields(update_stock_module):
    variant = SimpleNamespace(
        id=2,
        product_id="prod-1",
        product="Teh Herbal",
        name="Sachet",
        img=None,
        variant="Jeruk",
        expiration=None,
        stock=10,
        price=15000.0,
        discount=10.0,
        base_price=15000.0,
        discounted_price=13500.0,
        updated_at=NOW,
    )
    db = DummyDB(variant=variant)
    payload = SimpleNamespace(model_dump=lambda exclude_none=False: {
        "stock": 5,
        "price": 12000.0,
    })
    type_id_update = SimpleNamespace(type_id=2)

    result = update_stock_module.update_stock(db, type_id_update, payload)

    assert result.error is None
    assert variant.stock == 5
    assert variant.price == 12000.0
    assert variant.discount == 10.0


def test_post_item_rejects_variant_product_mismatch(cart_post_item_module, monkeypatch):
    product = SimpleNamespace(id="prod-1", name="Produk A")
    variant = SimpleNamespace(id=3, product_id="prod-2", variant="Jeruk")

    class ScalarResult:
        def __init__(self, value):
            self.value = value

        def scalars(self):
            return self

        def first(self):
            return self.value

    class ExecDB:
        def execute(self, stmt):
            text = str(stmt)
            if 'FROM products' in text:
                return ScalarResult(product)
            return ScalarResult(variant)

        def rollback(self):
            pass

    monkeypatch.setattr(cart_post_item_module, 'redis_client', None)

    result = cart_post_item_module.post_item(
        ExecDB(),
        SimpleNamespace(product_id='prod-1', variant_id=3),
        'user-1'
    )

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 400
