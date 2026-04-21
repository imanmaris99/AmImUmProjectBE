from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import FraudStatusEnum, TransactionStatusEnum
from app.utils.result import build


class DummyDB:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

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


def test_handle_notification_delegates_to_public_callback(monkeypatch, handle_notification_module):
    captured = {}

    def fake_handler(notification_data, db):
        captured["notification_data"] = notification_data
        return build(data={
            "status_code": 200,
            "message": "ok",
            "data": {
                "order_id": "order-1",
                "transaction_status": TransactionStatusEnum.settlement,
                "fraud_status": FraudStatusEnum.accept,
            },
        })

    monkeypatch.setattr(handle_notification_module, "handler_notification", fake_handler)

    result = handle_notification_module.handle_notification(
        SimpleNamespace(order_id="order-1"),
        DummyDB(),
        user_id="user-1",
    )

    assert result.error is None
    assert captured["notification_data"] == {"order_id": "order-1"}
