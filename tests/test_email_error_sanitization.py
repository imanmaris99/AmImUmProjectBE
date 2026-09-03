from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.utils import firebase_utils


def test_brevo_http_error_returns_safe_public_message(monkeypatch):
    class FakeResponse:
        text = '{"message":"unrecognised IP address 152.55.185.62"}'

        def raise_for_status(self):
            import requests

            raise requests.HTTPError(response=self)

    def fake_post(*_args, **_kwargs):
        return FakeResponse()

    monkeypatch.setenv("BREVO_API_KEY", "test-key")
    monkeypatch.setenv("FROM_EMAIL", "admin@example.com")
    monkeypatch.setattr(firebase_utils.requests, "post", fake_post)

    with pytest.raises(HTTPException) as exc_info:
        firebase_utils._send_email_via_brevo_api(
            "user@example.com",
            "Reset Password",
            "body",
            html=True,
        )

    error = exc_info.value
    assert error.status_code == 502
    assert error.detail["message"] == "Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
    assert "unrecognised IP" not in error.detail["message"]
    assert "152.55.185.62" not in error.detail["message"]
    assert "Brevo" not in error.detail["message"]


class DummyDB:
    def __init__(self, user):
        self.user = user
        self.committed = 0
        self.rolled_back = 0

    def query(self, _model):
        db = self

        class Query:
            def filter(self, *_args, **_kwargs):
                return self

            def first(self):
                return db.user

        return Query()

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1


def test_reset_password_provider_error_rolls_back_and_preserves_safe_message(monkeypatch):
    import importlib

    module = importlib.import_module("app.services.user_services.send_reset_password_request")
    user = SimpleNamespace(email="user@gmail.com", verification_code=None)
    db = DummyDB(user)

    monkeypatch.setattr(module.auth, "get_user_by_email", lambda email: object())
    monkeypatch.setattr(module, "generate_verification_code", lambda: "123456")

    def fail_send(*_args, **_kwargs):
        raise HTTPException(
            status_code=502,
            detail={
                "status_code": 502,
                "error": "Bad Gateway",
                "message": "Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi.",
            },
        )

    monkeypatch.setattr(module, "send_email_reset_password", fail_send)

    payload = SimpleNamespace(email="user@gmail.com")

    with pytest.raises(HTTPException) as exc_info:
        module.send_reset_password_request(db, payload, "https://example.com/reset-password")

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["message"] == "Layanan email sementara belum tersedia. Silakan coba beberapa saat lagi."
    assert db.committed == 0
    assert db.rolled_back == 1
