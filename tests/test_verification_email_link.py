from types import SimpleNamespace

from app.utils import firebase_utils


def test_send_verification_email_uses_customer_frontend_link(monkeypatch):
    sent = {}

    def fake_send_email_verification(email, code, link, firstname):
        sent["email"] = email
        sent["code"] = code
        sent["link"] = link
        sent["firstname"] = firstname

    monkeypatch.setenv(
        "CUSTOMER_VERIFY_ACCOUNT_URL",
        "https://amimumherbalproject.vercel.app/verify-account",
    )
    monkeypatch.setattr(
        firebase_utils,
        "send_email_verification",
        fake_send_email_verification,
    )

    firebase_user = SimpleNamespace(email="user+test@example.com", uid="firebase-1")

    firebase_utils.send_verification_email(firebase_user, "User", "ABC 123")

    assert sent == {
        "email": "user+test@example.com",
        "code": "ABC 123",
        "firstname": "User",
        "link": "https://amimumherbalproject.vercel.app/verify-account?code=ABC+123&email=user%2Btest%40example.com",
    }
    assert "amimumprojectbe-production.up.railway.app/user/verify-email" not in sent["link"]
