from types import SimpleNamespace

from app.services.payment_services.create_transaction import (
    _build_midtrans_order_id,
    _existing_pending_payment_response,
    _status_value,
    NON_RETRYABLE_PAYMENT_ORDER_STATUSES,
)


def test_existing_pending_payment_reuses_stored_midtrans_redirect():
    payment = SimpleNamespace(
        transaction_id="snap-token-old",
        transaction_status="pending",
        payment_response={
            "redirect_url": "https://app.midtrans.com/snap/v4/redirection/snap-token-old",
            "token": "snap-token-old",
        },
    )

    response = _existing_pending_payment_response(payment)

    assert response is not None
    assert response.status_code == 200
    assert response.data.transaction_id == "snap-token-old"
    assert response.data.token == "snap-token-old"
    assert response.data.redirect_url == "https://app.midtrans.com/snap/v4/redirection/snap-token-old"
    assert response.data.transaction_status == "pending"


def test_existing_pending_payment_does_not_reuse_non_pending_status():
    payment = SimpleNamespace(
        transaction_id="snap-token-old",
        transaction_status="settlement",
        payment_response={
            "redirect_url": "https://app.midtrans.com/snap/v4/redirection/snap-token-old",
            "token": "snap-token-old",
        },
    )

    assert _existing_pending_payment_response(payment) is None


def test_existing_pending_payment_requires_redirect_url():
    payment = SimpleNamespace(
        transaction_id="snap-token-old",
        transaction_status="pending",
        payment_response={"token": "snap-token-old"},
    )

    assert _existing_pending_payment_response(payment) is None


def test_retry_midtrans_order_id_is_unique_and_keeps_order_uuid_prefix():
    order_id = "5ef46775-a393-49e0-8a82-64dabd05a9de"
    existing_payment = SimpleNamespace(id="payment-1")

    midtrans_order_id = _build_midtrans_order_id(order_id, existing_payment)

    assert midtrans_order_id.startswith(f"{order_id}-r")
    assert midtrans_order_id != order_id
    assert len(midtrans_order_id) <= 50


def test_first_midtrans_order_id_uses_plain_order_uuid():
    order_id = "5ef46775-a393-49e0-8a82-64dabd05a9de"

    assert _build_midtrans_order_id(order_id, None) == order_id


def test_payment_retry_blocks_only_successful_or_fulfillment_statuses():
    retryable_statuses = [
        "pending",
        "failed",
        "payment_failed",
        "expire",
        "expired",
        "cancel",
        "cancelled",
        "deny",
        "",
    ]

    for status in retryable_statuses:
        assert _status_value(status) not in NON_RETRYABLE_PAYMENT_ORDER_STATUSES

    for status in ["paid", "settlement", "capture", "processing", "shipped", "completed", "refund"]:
        assert _status_value(status) in NON_RETRYABLE_PAYMENT_ORDER_STATUSES
