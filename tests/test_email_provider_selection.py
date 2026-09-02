import pytest

from app.utils import firebase_utils


def test_send_email_prefers_brevo_api_when_api_key_is_configured(monkeypatch):
    calls = []

    monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
    monkeypatch.setenv("BREVO_API_KEY", "dummy-key")
    monkeypatch.setenv("FROM_EMAIL", "sender@example.com")

    def fake_brevo(to_email: str, subject: str, body: str, html: bool = False):
        calls.append(("brevo", to_email, subject, body, html))

    def fake_smtp(to_email: str, subject: str, body: str, html: bool = False):
        calls.append(("smtp", to_email, subject, body, html))

    monkeypatch.setattr(firebase_utils, "_send_email_via_brevo_api", fake_brevo)
    monkeypatch.setattr(firebase_utils, "_send_email_via_smtp", fake_smtp)

    firebase_utils.send_email("user@example.com", "Subject", "Body", html=True)

    assert calls == [("brevo", "user@example.com", "Subject", "Body", True)]


def test_send_email_uses_explicit_smtp_when_requested(monkeypatch):
    calls = []

    monkeypatch.setenv("EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("BREVO_API_KEY", "dummy-key")

    def fake_brevo(to_email: str, subject: str, body: str, html: bool = False):
        calls.append(("brevo", to_email, subject, body, html))

    def fake_smtp(to_email: str, subject: str, body: str, html: bool = False):
        calls.append(("smtp", to_email, subject, body, html))

    monkeypatch.setattr(firebase_utils, "_send_email_via_brevo_api", fake_brevo)
    monkeypatch.setattr(firebase_utils, "_send_email_via_smtp", fake_smtp)

    firebase_utils.send_email("user@example.com", "Subject", "Body")

    assert calls == [("smtp", "user@example.com", "Subject", "Body", False)]
