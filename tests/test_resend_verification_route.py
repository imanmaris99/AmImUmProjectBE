import importlib
from datetime import datetime
from types import SimpleNamespace

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.dtos import user_dtos
from app.services import user_services
from app.utils import optional


client = TestClient(app)
GENERIC_MESSAGE = "If the email is registered and not verified, a verification email will be sent."


class DummyDB:
    def __init__(self, user):
        self.user = user
        self.committed = False
        self.rolled_back = False
        self.refreshed = []

    def query(self, _model):
        db = self

        class Query:
            def filter(self, *_args, **_kwargs):
                return self

            def first(self):
                return db.user

        return Query()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
        if self.user:
            self.user.verification_code = "OLD-CODE"
            self.user.verification_expiry = OLD_EXPIRY

    def refresh(self, obj):
        self.refreshed.append(obj)


OLD_EXPIRY = datetime(2026, 9, 2, 12, 0, 0)


def test_resend_verification_endpoint_returns_frontend_contract(monkeypatch):
    payload = user_dtos.ResendVerificationResponseDto(
        status_code=200,
        message=GENERIC_MESSAGE,
        data=user_dtos.ResendVerificationRequestDto(email="user@example.com"),
    )
    monkeypatch.setattr(
        user_services,
        "resend_verification_email",
        lambda db, request: optional.build(data=payload),
        raising=False,
    )

    response = client.post("/user/resend-verification", json={"email": "user@example.com"})

    assert response.status_code == 200
    assert response.json() == {
        "status_code": 200,
        "message": GENERIC_MESSAGE,
        "data": {"email": "user@example.com"},
    }


def test_resend_verification_provider_failure_still_returns_generic_success(monkeypatch):
    user = SimpleNamespace(
        email="user@example.com",
        firstname="User",
        firebase_uid="firebase-1",
        is_active=False,
        verification_code="OLD-CODE",
        verification_expiry=OLD_EXPIRY,
    )
    db = DummyDB(user)
    resend_service = importlib.import_module("app.services.user_services.resend_verification_email")
    monkeypatch.setattr(resend_service, "generate_verification_code", lambda: "NEW-CODE")

    def fail_send(*_args, **_kwargs):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="provider down")

    monkeypatch.setattr(resend_service, "send_verification_email", fail_send)

    result = resend_service.resend_verification_email(
        db,
        user_dtos.ResendVerificationRequestDto(email="user@example.com"),
    )

    assert result.error is None
    assert result.data.status_code == 200
    assert result.data.message == GENERIC_MESSAGE
    assert db.committed is False
    assert db.rolled_back is True
    assert user.verification_code == "OLD-CODE"
    assert user.verification_expiry == OLD_EXPIRY
