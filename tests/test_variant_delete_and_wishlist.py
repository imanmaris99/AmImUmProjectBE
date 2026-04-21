from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


NOW = datetime(2026, 4, 21, 12, 40, 0)


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return self

    def first(self):
        return self.value


class DeleteDB:
    def __init__(self, variant, cart_ref=None, order_ref=None):
        self.variant = variant
        self.cart_ref = cart_ref
        self.order_ref = order_ref
        self.deleted = []
        self.committed = False

    def query(self, _model):
        db = self

        class Query:
            def filter(self, *_args, **_kwargs):
                return self

            def first(self):
                return db.variant

        return Query()

    def execute(self, stmt):
        text = str(stmt)
        if 'FROM cart_products' in text:
            return ScalarResult(self.cart_ref)
        if 'FROM order_items' in text:
            return ScalarResult(self.order_ref)
        return ScalarResult(None)

    def delete(self, obj):
        self.deleted.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


@pytest.fixture
def delete_type_module():
    import importlib

    return importlib.import_module("app.services.pack_type_services.delete_type")


@pytest.fixture
def wishlist_module():
    import importlib

    return importlib.import_module("app.services.wishlist_services.my_wishlist")


def test_delete_type_rejects_variant_in_cart(delete_type_module):
    db = DeleteDB(variant=SimpleNamespace(id=5, variant="Jeruk", name="Sachet"), cart_ref=99)
    result = delete_type_module.delete_type(db, SimpleNamespace(type_id=5))

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 409


def test_delete_type_rejects_variant_in_order_history(delete_type_module):
    db = DeleteDB(variant=SimpleNamespace(id=5, variant="Jeruk", name="Sachet"), order_ref=77)
    result = delete_type_module.delete_type(db, SimpleNamespace(type_id=5))

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 409


def test_delete_type_deletes_safe_variant(delete_type_module):
    variant = SimpleNamespace(id=5, variant="Jeruk", name="Sachet")
    db = DeleteDB(variant=variant)
    result = delete_type_module.delete_type(db, SimpleNamespace(type_id=5))

    assert result.error is None
    assert db.deleted == [variant]
    assert db.committed is True


def test_my_wishlist_returns_variant_pricing(wishlist_module, monkeypatch):
    wishlist_item = SimpleNamespace(
        id=1,
        product_name="Teh Herbal",
        product_variant=[
            {
                "id": 1,
                "product_id": "prod-1",
                "product": "Teh Herbal",
                "name": "Sachet",
                "variant": "Jeruk",
                "img": None,
                "expiration": None,
                "stock": 5,
                "price": 12000.0,
                "discount": 10.0,
                "discounted_price": 10800.0,
                "updated_at": NOW,
            }
        ],
        created_at=NOW,
    )

    class WishlistDB:
        def execute(self, stmt):
            text = str(stmt)
            if 'count' in text.lower():
                return SimpleNamespace(scalar=lambda: 1)
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [wishlist_item]))

        def rollback(self):
            pass

    monkeypatch.setattr(wishlist_module, 'redis_client', None)

    result = wishlist_module.my_wishlist(WishlistDB(), 'user-1')

    assert result.error is None
    variant = result.data.data[0].product_variant[0]
    assert variant.price == 12000.0
    assert variant.discounted_price == 10800.0
