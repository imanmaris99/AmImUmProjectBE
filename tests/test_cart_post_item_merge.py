from types import SimpleNamespace


class DummyScalarResult:
    def __init__(self, value):
        self.value = value

    def first(self):
        return self.value

    def all(self):
        return self.value


class DummyExecuteResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return DummyScalarResult(self.value)


class DummyDB:
    def __init__(self, execute_results):
        self.execute_results = list(execute_results)
        self.added = []
        self.deleted = []
        self.committed = 0
        self.refreshed = []
        self.rolled_back = 0

    def execute(self, stmt):
        if not self.execute_results:
            raise AssertionError("Unexpected execute call")
        return DummyExecuteResult(self.execute_results.pop(0))

    def add(self, obj):
        self.added.append(obj)

    def delete(self, obj):
        self.deleted.append(obj)

    def commit(self):
        self.committed += 1

    def refresh(self, obj):
        self.refreshed.append(obj)

    def rollback(self):
        self.rolled_back += 1


class DummyRedis:
    def __init__(self):
        self.deleted = []

    def scan_iter(self, pattern):
        return [f"matched:{pattern}"]

    def delete(self, key):
        self.deleted.append(key)


class DummySelect:
    def where(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self


class ColumnProbe:
    def __eq__(self, other):
        return True

    def asc(self):
        return self


def test_post_item_reuses_existing_product_variant_and_deletes_duplicates(monkeypatch):
    import importlib

    post_item_module = importlib.import_module("app.services.cart_services.post_item")

    product = SimpleNamespace(id="prod-1", name="Jamu Jago")
    variant = SimpleNamespace(id=10, product_id="prod-1", variant="MT")
    existing_row = SimpleNamespace(
        id=101,
        quantity=3,
        is_active=False,
        customer_name="Customer",
        created_at="2026-01-01T00:00:00",
    )
    duplicate_row = SimpleNamespace(id=102, quantity=1, is_active=False)
    db = DummyDB(execute_results=[product, variant, [existing_row, duplicate_row]])
    redis = DummyRedis()

    monkeypatch.setattr(post_item_module, "select", lambda model: DummySelect())
    monkeypatch.setattr(
        post_item_module,
        "CartProductModel",
        SimpleNamespace(
            customer_id=ColumnProbe(),
            product_id=ColumnProbe(),
            variant_id=ColumnProbe(),
            created_at=ColumnProbe(),
            id=ColumnProbe(),
        ),
    )
    monkeypatch.setattr(post_item_module, "redis_client", redis)

    result = post_item_module.post_item(
        db,
        SimpleNamespace(product_id="prod-1", variant_id=10),
        "user-1",
    )

    assert result.error is None
    assert existing_row.quantity == 1
    assert existing_row.is_active is True
    assert db.added == []
    assert db.deleted == [duplicate_row]
    assert db.committed == 1
    assert db.refreshed == [existing_row]
    assert "matched:cart:user-1:*" in redis.deleted
    assert "matched:carts:user-1" in redis.deleted
