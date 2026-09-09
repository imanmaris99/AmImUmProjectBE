from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import FraudStatusEnum, TransactionStatusEnum
from app.utils.result import build


class DummyDB:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def user_login_module():
    import importlib

    return importlib.import_module("app.services.user_services.user_login")


@pytest.fixture
def handler_notification_module():
    import importlib

    return importlib.import_module("app.services.payment_services.handler_notification")


@pytest.fixture
def handle_notification_module():
    import importlib

    return importlib.import_module("app.services.payment_services.handle_notification")


@pytest.fixture
def active_user():
    return SimpleNamespace(
        id="user-1",
        email="user@example.com",
        role="customer",
        is_active=True,
        hash_password="hashed-password",
    )


def test_user_login_success(monkeypatch, active_user, user_login_module):
    monkeypatch.setattr(
        user_login_module,
        "get_user_by_email",
        lambda db, email: SimpleNamespace(data=active_user, error=None),
    )
    monkeypatch.setattr(
        user_login_module.password_lib,
        "verify_password",
        lambda plain_password, hashed_password: True,
    )
    monkeypatch.setattr(
        user_login_module.jwt_service,
        "create_access_token",
        lambda data: {"access_token": "token", "exp": "2099-01-01 00:00:00"},
    )

    result = user_login_module.user_login(DummyDB(), SimpleNamespace(email="user@example.com", password="Secret123!"))

    assert result.error is None
    assert result.data["user"]["id"] == "user-1"
    assert result.data["access_token"]["access_token"] == "token"


def test_user_login_wrong_password(monkeypatch, active_user, user_login_module):
    monkeypatch.setattr(
        user_login_module,
        "get_user_by_email",
        lambda db, email: SimpleNamespace(data=active_user, error=None),
    )
    monkeypatch.setattr(
        user_login_module.password_lib,
        "verify_password",
        lambda plain_password, hashed_password: False,
    )

    result = user_login_module.user_login(DummyDB(), SimpleNamespace(email="user@example.com", password="Wrong123!"))

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 401


def test_user_login_inactive_user(monkeypatch, active_user, user_login_module):
    inactive_user = SimpleNamespace(**{**active_user.__dict__, "is_active": False})

    monkeypatch.setattr(
        user_login_module,
        "get_user_by_email",
        lambda db, email: SimpleNamespace(data=inactive_user, error=None),
    )

    result = user_login_module.user_login(DummyDB(), SimpleNamespace(email="user@example.com", password="Secret123!"))

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 403


def test_handler_notification_rejects_invalid_signature(monkeypatch, handler_notification_module):
    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(error=HTTPException(status_code=500, detail="down")),
    )
    monkeypatch.setattr(
        handler_notification_module,
        "get_payment_by_order_id",
        lambda order_id, db: SimpleNamespace(order_id=order_id, payment_type=None, transaction_id=None),
    )

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "invalid",
        },
        DummyDB(),
    )

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 400


def test_handler_notification_updates_payment_and_order(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(order_id="order-1", status="pending", customer_id="user-1")
    deleted_keys = []

    class DummyRedis:
        def scan_iter(self, pattern):
            return [f"matched:{pattern}"]

        def delete(self, key):
            deleted_keys.append(key)

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(
        handler_notification_module,
        "validate_signature_key",
        lambda **kwargs: True,
    )
    monkeypatch.setattr(
        handler_notification_module,
        "get_payment_by_order_id",
        lambda order_id, db: payment,
    )
    monkeypatch.setattr(
        handler_notification_module,
        "get_order_by_id",
        lambda order_id, db: order,
    )
    monkeypatch.setattr(handler_notification_module, "redis_client", DummyRedis())

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert result.error is None
    assert payment.transaction_id == "trx-1"
    assert payment.payment_type == "bank_transfer"
    assert payment.transaction_status == TransactionStatusEnum.settlement
    assert payment.fraud_status == FraudStatusEnum.accept
    assert order.status == "paid"
    assert db.committed is True
    assert "matched:orders:user-1:*" in deleted_keys
    assert "matched:order:user-1:order-1" in deleted_keys


def test_handler_notification_returns_404_when_payment_missing(monkeypatch, handler_notification_module):
    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: None)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-missing",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        DummyDB(),
    )

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 404


def test_handler_notification_returns_404_when_order_missing(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handler_notification_module, "get_order_by_id", lambda order_id, db: None)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "settlement",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 404
    assert db.rolled_back is False


def test_handler_notification_does_not_regress_completed_order(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(order_id="order-1", status="completed")

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "pending",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handler_notification_module, "get_order_by_id", lambda order_id, db: order)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "pending",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert result.error is None
    assert order.status == "completed"
    assert db.committed is True


def test_handler_notification_does_not_regress_processing_order_to_pending(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(order_id="order-1", status="processing")

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "pending",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handler_notification_module, "get_order_by_id", lambda order_id, db: order)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "pending",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert result.error is None
    assert order.status == "processing"
    assert db.committed is True


def test_handler_notification_allows_capture_from_paid(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(order_id="order-1", status="paid")

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "capture",
            "status_code": "200",
            "payment_type": "credit_card",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handler_notification_module, "get_order_by_id", lambda order_id, db: order)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "capture",
            "status_code": "200",
            "payment_type": "credit_card",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert result.error is None
    assert order.status == "capture"


def test_handler_notification_allows_refund_from_completed(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(order_id="order-1", status="completed")

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "refund",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "accept",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handler_notification_module, "get_order_by_id", lambda order_id, db: order)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "refund",
            "status_code": "200",
            "payment_type": "bank_transfer",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert result.error is None
    assert order.status == "refund"


def test_handler_notification_allows_failed_from_paid(monkeypatch, handler_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        payment_type=None,
        transaction_id=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(order_id="order-1", status="paid")

    monkeypatch.setattr(handler_notification_module, "MIDTRANS_SERVER_KEY", "server-key")
    monkeypatch.setattr(
        handler_notification_module,
        "fetch_midtrans_transaction_status",
        lambda order_id: build(data={
            "order_id": order_id,
            "transaction_id": "trx-1",
            "transaction_status": "deny",
            "status_code": "200",
            "payment_type": "credit_card",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
            "fraud_status": "deny",
        }),
    )
    monkeypatch.setattr(handler_notification_module, "validate_signature_key", lambda **kwargs: True)
    monkeypatch.setattr(handler_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handler_notification_module, "get_order_by_id", lambda order_id, db: order)

    result = handler_notification_module.handler_notification(
        {
            "order_id": "order-1",
            "transaction_status": "deny",
            "status_code": "200",
            "payment_type": "credit_card",
            "gross_amount": "10000.00",
            "signature_key": "valid-signature",
        },
        db,
    )

    assert result.error is None
    assert order.status == "failed"


def test_handle_notification_syncs_midtrans_status_for_order_owner(monkeypatch, handle_notification_module):
    db = DummyDB()
    payment = SimpleNamespace(
        order_id="order-1",
        transaction_id="trx-old",
        payment_type=None,
        transaction_status=None,
        fraud_status=None,
        payment_response=None,
    )
    order = SimpleNamespace(id="order-1", customer_id="user-1", status="pending")

    deleted_keys = []

    class FakeRedis:
        def scan_iter(self, pattern):
            return [f"{pattern}:cached"]

        def delete(self, key):
            deleted_keys.append(key)

    monkeypatch.setattr(handle_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handle_notification_module, "get_order_by_id", lambda order_id, db: order)
    monkeypatch.setattr(handle_notification_module, "redis_client", FakeRedis())
    monkeypatch.setattr(handle_notification_module, "fetch_midtrans_transaction_status", lambda order_id: build(data={
        "order_id": order_id,
        "transaction_id": "trx-1",
        "transaction_status": "settlement",
        "payment_type": "credit_card",
        "gross_amount": "11900.00",
        "fraud_status": "accept",
    }))

    result = handle_notification_module.handle_notification(
        SimpleNamespace(order_id="order-1"),
        db,
        user_id="user-1",
    )

    assert result.error is None
    assert payment.transaction_id == "trx-1"
    assert payment.transaction_status == TransactionStatusEnum.settlement
    assert order.status == "paid"
    assert db.committed is True
    assert "order:user-1:*:cached" in deleted_keys
    assert "orders:user-1:*:cached" in deleted_keys


def test_handle_notification_rejects_sync_for_non_owner(monkeypatch, handle_notification_module):
    payment = SimpleNamespace(order_id="order-1")
    order = SimpleNamespace(id="order-1", customer_id="owner-1", status="pending")

    monkeypatch.setattr(handle_notification_module, "get_payment_by_order_id", lambda order_id, db: payment)
    monkeypatch.setattr(handle_notification_module, "get_order_by_id", lambda order_id, db: order)

    result = handle_notification_module.handle_notification(
        SimpleNamespace(order_id="order-1"),
        DummyDB(),
        user_id="other-user",
    )

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 403
