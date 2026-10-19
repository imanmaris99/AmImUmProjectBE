from datetime import datetime, timezone
from importlib import import_module
from types import SimpleNamespace
import uuid

import pytest

from app.dtos.rating_dtos import RatingCreateDto, RatingCreateOfIdProductDto
from app.models.order_item_model import OrderItemModel
from app.models.order_model import OrderModel
from app.models.product_model import ProductModel
from app.models.rating_model import RatingModel

rating_service = import_module("app.services.rating_services.create_rating")


class DummyQuery:
    def __init__(self, result, model=None):
        self.result = result
        self.model = model
        self.filters = []
        self.joins = []

    def filter(self, *conditions):
        self.filters.extend(conditions)
        return self

    def join(self, *args, **kwargs):
        self.joins.append((args, kwargs))
        return self

    def first(self):
        if self.model is not OrderItemModel:
            return self.result

        for item in self.result or []:
            if all(
                getattr(item, condition.left.name, None) == condition.right.value
                for condition in self.filters
            ):
                return item
        return None


class DummyDB:
    def __init__(self, *, product, purchase_rows, existing_rating=None):
        self.product = product
        self.purchase_rows = purchase_rows
        self.existing_rating = existing_rating
        self.purchase_query = None
        self.added = []
        self.committed = 0
        self.rolled_back = 0

    def query(self, model):
        if model is ProductModel:
            return DummyQuery(self.product, model)
        if model is OrderItemModel:
            self.purchase_query = DummyQuery(self.purchase_rows, model)
            return self.purchase_query
        if model is RatingModel:
            return DummyQuery(self.existing_rating, model)
        raise AssertionError(f"Unexpected model queried: {model}")

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def refresh(self, instance):
        instance.id = 1
        instance.created_at = datetime.now(timezone.utc)


def test_rating_is_rejected_when_user_has_no_eligible_completed_purchase():
    product_id = uuid.uuid4()
    db = DummyDB(
        product=SimpleNamespace(id=str(product_id)),
        purchase_rows=[],
    )

    result = rating_service.create_rating(
        db,
        RatingCreateOfIdProductDto(product_id=product_id),
        RatingCreateDto(rate=5, review="Ulasan pembeli"),
        user_id="user-1",
    )

    assert result.error is not None
    assert result.error.status_code == 403
    assert db.added == []
    assert db.committed == 0


@pytest.mark.parametrize(
    "row_overrides",
    [
        {"customer_id": "another-user", "status": "completed"},
        {"customer_id": "user-1", "product_id": "another-product", "status": "completed"},
        {"customer_id": "user-1", "status": "processing"},
    ],
    ids=["different-owner", "different-product", "not-fulfilled"],
)
def test_rating_requires_matching_buyer_product_and_completed_status(row_overrides):
    product_id = uuid.uuid4()
    row = {
        "product_id": str(product_id),
        "customer_id": "user-1",
        "status": "completed",
    }
    row.update(row_overrides)
    db = DummyDB(
        product=SimpleNamespace(id=str(product_id)),
        purchase_rows=[SimpleNamespace(**row)],
    )

    result = rating_service.create_rating(
        db,
        RatingCreateOfIdProductDto(product_id=product_id),
        RatingCreateDto(rate=5, review="Ulasan pembeli"),
        user_id="user-1",
    )

    assert result.error is not None
    assert result.error.status_code == 403
    assert db.added == []
    assert db.committed == 0


def test_rating_is_created_for_matching_completed_purchase():
    product_id = uuid.uuid4()
    db = DummyDB(
        product=SimpleNamespace(id=str(product_id)),
        purchase_rows=[
            SimpleNamespace(
                product_id=str(product_id),
                customer_id="user-1",
                status="completed",
            )
        ],
    )
    result = rating_service.create_rating(
        db,
        RatingCreateOfIdProductDto(product_id=product_id),
        RatingCreateDto(rate=5, review="Ulasan pembeli"),
        user_id="user-1",
    )

    assert result.error is None
    assert db.committed == 1
    assert len(db.added) == 1
    assert db.purchase_query.joins[0][0][0] is OrderModel
    assert db.purchase_query.filters


def test_existing_rating_is_rejected_and_customer_can_edit_instead():
    product_id = uuid.uuid4()
    db = DummyDB(
        product=SimpleNamespace(id=str(product_id)),
        purchase_rows=[
            SimpleNamespace(
                product_id=str(product_id),
                customer_id="user-1",
                status="completed",
            )
        ],
        existing_rating=SimpleNamespace(id=22),
    )
    result = rating_service.create_rating(
        db,
        RatingCreateOfIdProductDto(product_id=product_id),
        RatingCreateDto(rate=4, review="Ulasan kedua"),
        user_id="user-1",
    )

    assert result.error is not None
    assert result.error.status_code == 409
    assert db.added == []
    assert db.committed == 0
