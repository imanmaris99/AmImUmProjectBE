from app.controllers import admin_router, user_router
from app.dtos import user_dtos


class _Result:
    error = None

    def unwrap(self):
        return {"status_code": 200}


def test_customer_forgot_password_uses_customer_frontend_reset_url(monkeypatch):
    calls = []

    def fake_send_reset_password_request(db, payload, reset_base_url=None):
        calls.append(reset_base_url)
        return _Result()

    monkeypatch.setattr(
        user_router.user_services,
        "send_reset_password_request",
        fake_send_reset_password_request,
    )

    payload = user_dtos.ForgotPasswordDto(email="customer@gmail.com")
    user_router.forgot_password(payload=payload, db=object())

    assert calls == ["https://amimumherbalproject.vercel.app/reset-password"]


def test_admin_forgot_password_keeps_internal_dashboard_reset_url(monkeypatch):
    calls = []

    def fake_send_reset_password_request(db, payload, reset_base_url=None):
        calls.append(reset_base_url)
        return _Result()

    monkeypatch.setattr(
        admin_router.user_services,
        "send_reset_password_request",
        fake_send_reset_password_request,
    )

    payload = user_dtos.ForgotPasswordDto(email="admin@gmail.com")
    admin_router.admin_forgot_password(payload=payload, db=object())

    assert calls == [None]
