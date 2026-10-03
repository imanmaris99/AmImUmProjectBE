from types import SimpleNamespace


class _FakeScalarsWithRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeExecuteRowsResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _FakeScalarsWithRows(self._rows)


class _FakeCleanupDB:
    def __init__(self, rows):
        self.rows = rows
        self.deleted = []
        self.committed = False

    def execute(self, stmt):
        return _FakeExecuteRowsResult(self.rows)

    def delete(self, row):
        self.deleted.append(row)

    def commit(self):
        self.committed = True


def test_my_cart_cleanup_deletes_stale_inactive_checked_out_rows(monkeypatch):
    import importlib

    my_cart_module = importlib.import_module("app.services.cart_services.my_cart")
    stale_inactive_row = SimpleNamespace(id=396, is_active=False)
    db = _FakeCleanupDB([stale_inactive_row])

    monkeypatch.setattr(my_cart_module, "redis_client", None)

    deleted_count = my_cart_module._delete_stale_checked_out_cart_rows(db, "user-1")

    assert deleted_count == 1
    assert db.deleted == [stale_inactive_row]
    assert db.committed is True



def test_my_cart_lists_all_cart_rows_because_is_active_is_checkout_selection(monkeypatch):
    import importlib

    my_cart_module = importlib.import_module("app.services.cart_services.my_cart")

    where_args = []

    class ColumnProbe:
        def __init__(self, name):
            self.name = name

        def __eq__(self, other):
            return (self.name, other)

    class FakeSelect:
        def where(self, *args):
            where_args.extend(args)
            return self

        def offset(self, value):
            return self

        def limit(self, value):
            return self

    class FakeScalars:
        def all(self):
            return []

    class FakeExecuteResult:
        def scalars(self):
            return FakeScalars()

    class FakeDB:
        def execute(self, stmt):
            return FakeExecuteResult()

    monkeypatch.setattr(my_cart_module, "redis_client", None)
    monkeypatch.setattr(my_cart_module, "_delete_stale_checked_out_cart_rows", lambda db, user_id: 0)
    monkeypatch.setattr(
        my_cart_module,
        "CartProductModel",
        SimpleNamespace(
            customer_id=ColumnProbe("customer_id"),
            is_active=ColumnProbe("is_active"),
        ),
    )
    monkeypatch.setattr(my_cart_module, "select", lambda model: FakeSelect())

    result = my_cart_module.my_cart(FakeDB(), "user-1")

    assert result.error is None
    assert ("customer_id", "user-1") in where_args
    assert ("is_active", True) not in where_args
    assert result.data.data == []
