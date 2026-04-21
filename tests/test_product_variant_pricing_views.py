from datetime import datetime
from types import SimpleNamespace

import pytest


NOW = datetime(2026, 4, 21, 12, 0, 0)
VARIANT_LIST_ITEM = {
    "id": 1,
    "product": "Teh Herbal",
    "name": "Sachet",
    "img": None,
    "variant": "Jeruk",
    "expiration": None,
    "stock": 10,
    "price": 12000.0,
    "discount": 10.0,
    "discounted_price": 10800.0,
    "updated_at": NOW,
}
VARIANT_GRID_ITEM = {
    "id": 1,
    "product_id": "prod-1",
    "product": "Teh Herbal",
    "name": "Sachet",
    "variant": "Jeruk",
    "img": None,
    "expiration": None,
    "stock": 10,
    "price": 12000.0,
    "discount": 10.0,
    "discounted_price": 10800.0,
    "updated_at": NOW,
}


@pytest.fixture
def detail_product_module():
    import importlib

    return importlib.import_module("app.services.product_services.detail_product")


@pytest.fixture
def all_product_module():
    import importlib

    return importlib.import_module("app.services.product_services.all_product")


def test_product_detail_exposes_variant_price_range(detail_product_module, monkeypatch):
    product = SimpleNamespace(
        id="prod-1",
        name="Teh Herbal",
        info="Info",
        variants_list=[VARIANT_LIST_ITEM],
        description_list=["desc"],
        instruction_list=["use"],
        price=15000.0,
        min_variant_price=12000.0,
        max_variant_price=18000.0,
        is_active=True,
        company="Amimum",
        avg_rating=4.8,
        total_rater=10,
        created_at=NOW,
        updated_at=NOW,
    )

    class ScalarResult:
        def scalars(self):
            return self

        def first(self):
            return product

    class DummyDB:
        def execute(self, _stmt):
            return ScalarResult()

        def rollback(self):
            pass

    monkeypatch.setattr(detail_product_module, "redis_client", None)

    result = detail_product_module.get_product_by_id(DummyDB(), "prod-1")

    assert result.error is None
    assert result.data.data.min_variant_price == 12000.0
    assert result.data.data.max_variant_price == 18000.0
    assert result.data.data.price == 15000.0


def test_all_product_exposes_variant_price_range(all_product_module, monkeypatch):
    product = SimpleNamespace(
        id="prod-1",
        name="Teh Herbal",
        price=15000.0,
        min_variant_price=12000.0,
        max_variant_price=18000.0,
        brand_info={"id": 1, "name": "Amimum"},
        all_variants=[VARIANT_GRID_ITEM],
        created_at=NOW,
    )

    class ScalarResult:
        def scalars(self):
            return self

        def all(self):
            return [product]

    class DummyDB:
        def execute(self, _stmt):
            return ScalarResult()

        def rollback(self):
            pass

    monkeypatch.setattr(all_product_module, "redis_client", None)

    result = all_product_module.all_product(DummyDB())

    assert result.error is None
    first = result.data.data[0]
    assert first.min_variant_price == 12000.0
    assert first.max_variant_price == 18000.0
    assert first.all_variants[0].price == 12000.0
