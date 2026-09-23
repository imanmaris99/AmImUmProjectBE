from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class DummyScalarResult:
    def __init__(self, value):
        self.value = value

    def first(self):
        return self.value


class DummyExecuteResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return DummyScalarResult(self.value)


class DummyDB:
    def __init__(self, order):
        self.order = order
        self.rolled_back = 0

    def execute(self, stmt):
        return DummyExecuteResult(self.order)

    def rollback(self):
        self.rolled_back += 1


@pytest.fixture
def qris_module():
    import importlib

    return importlib.import_module("app.services.order_services.qris_payment_confirmation")


def make_order(**overrides):
    base = dict(
        id="order-1",
        customer_id="user-1",
        status="pending",
        total_price=12000,
        notes="[PAYMENT: qris_manual]",
        customer_name="Aris",
        customer_email="aris@example.com",
        customer_phone="08123456789",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_qris_confirmation_notifies_admin_without_marking_paid(monkeypatch, qris_module):
    order = make_order()
    sent = []
    monkeypatch.setattr(qris_module, "send_email", lambda to_email, subject, body, html=False: sent.append((to_email, subject, body, html)))
    monkeypatch.setenv("QRIS_NOTIFICATION_EMAIL", "admin@example.com")

    result = qris_module.submit_qris_payment_confirmation(DummyDB(order), "user-1", "order-1")

    assert result.error is None
    assert result.data.status_code == 200
    assert result.data.data.order_id == "order-1"
    assert result.data.data.status == "pending"
    assert result.data.data.admin_notified is True
    assert order.status == "pending"
    assert sent and sent[0][0] == "admin@example.com"
    assert "Konfirmasi QRIS" in sent[0][1]
    assert "token" not in sent[0][2].lower()


def test_qris_confirmation_rejects_non_qris_order(qris_module):
    order = make_order(notes="[PAYMENT: cod]")

    result = qris_module.submit_qris_payment_confirmation(DummyDB(order), "user-1", "order-1")

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 400
    assert "QRIS" in result.error.detail["message"]


def test_qris_confirmation_rejects_non_pending_order(qris_module):
    order = make_order(status="processing")

    result = qris_module.submit_qris_payment_confirmation(DummyDB(order), "user-1", "order-1")

    assert isinstance(result.error, HTTPException)
    assert result.error.status_code == 409


def test_qris_confirmation_is_non_blocking_if_admin_email_fails(monkeypatch, qris_module):
    order = make_order()

    def fail_send(*args, **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(qris_module, "send_email", fail_send)

    result = qris_module.submit_qris_payment_confirmation(DummyDB(order), "user-1", "order-1")

    assert result.error is None
    assert result.data.data.admin_notified is False
    assert order.status == "pending"
