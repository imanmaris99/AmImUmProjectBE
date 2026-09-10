from types import SimpleNamespace

from app.services.payment_services.support_function import (
    build_customer_transaction_url,
    generate_midtrans_payload,
)


def test_build_customer_transaction_url_uses_customer_transaction_detail(monkeypatch):
    monkeypatch.setattr(
        "app.services.payment_services.support_function.CUSTOMER_APP_URL",
        "https://shop.example.com",
    )

    assert (
        build_customer_transaction_url("order-123")
        == "https://shop.example.com/transaction/order-123"
    )


def test_generate_midtrans_payload_sets_finish_callback_to_customer_transaction(monkeypatch):
    monkeypatch.setattr(
        "app.services.payment_services.support_function.CUSTOMER_APP_URL",
        "https://amimumherbalproject.vercel.app",
    )
    order = SimpleNamespace(
        id="865740b2-8274-4b4c-b18e-bfed0aeaa176",
        total_price=18500,
        customer_name="Test Payment",
        customer_email="customer@example.com",
        customer_phone="+6281234567890",
    )

    payload = generate_midtrans_payload(order)

    assert payload["transaction_details"] == {
        "order_id": "865740b2-8274-4b4c-b18e-bfed0aeaa176",
        "gross_amount": 18500.0,
    }
    assert payload["callbacks"] == {
        "finish": "https://amimumherbalproject.vercel.app/transaction/865740b2-8274-4b4c-b18e-bfed0aeaa176",
    }
