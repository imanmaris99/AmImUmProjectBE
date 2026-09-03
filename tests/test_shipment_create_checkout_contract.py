from types import SimpleNamespace
from datetime import datetime


class DummyQuery:
    def __init__(self, db):
        self.db = db

    def filter(self, *args, **kwargs):
        return self

    def update(self, values, synchronize_session=False):
        self.db.updated_values = values
        self.db.synchronize_session = synchronize_session
        return 1


class DummyDB:
    def __init__(self):
        self.updated_values = None
        self.synchronize_session = None
        self.added = []
        self.committed = 0
        self.refreshed = []
        self.rolled_back = 0

    def query(self, _model):
        return DummyQuery(self)

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = "shipment-1"
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime(2026, 9, 3, 12, 0, 0)
        self.added.append(obj)

    def commit(self):
        self.committed += 1

    def refresh(self, obj):
        self.refreshed.append(obj)

    def rollback(self):
        self.rolled_back += 1


def test_create_shipment_sets_customer_and_deactivates_previous(monkeypatch):
    import importlib
    from app.models.shipment_model import ShipmentModel

    module = importlib.import_module("app.services.shipment_services.create_shipment")
    db = DummyDB()

    monkeypatch.setattr(
        module,
        "create_shipment_address",
        lambda request_address, user_id, db: SimpleNamespace(
            error=None,
            data=SimpleNamespace(data=SimpleNamespace(id=11)),
        ),
    )
    monkeypatch.setattr(
        module,
        "process_shipping_cost",
        lambda request_courier, user_id, db: SimpleNamespace(
            error=None,
            data=SimpleNamespace(data=SimpleNamespace(id=22)),
        ),
    )

    request_data = SimpleNamespace(address=object(), courier=object())

    result = module.create_shipment(request_data, "user-1", db)

    assert result.error is None
    assert db.updated_values == {ShipmentModel.is_active: False}
    assert db.synchronize_session is False
    assert db.committed == 1
    shipment = db.added[0]
    assert shipment.customer_id == "user-1"
    assert shipment.address_id == 11
    assert shipment.courier_id == 22
    assert shipment.is_active is True
