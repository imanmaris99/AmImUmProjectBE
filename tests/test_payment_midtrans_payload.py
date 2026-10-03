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
        customer_phone="+628****7890",
        user=SimpleNamespace(
            firstname="Test",
            lastname="Payment",
            fullname="Test Payment",
            address="Jl. Herbal No. 1",
        ),
        shipments=None,
        order_items=[],
    )

    payload = generate_midtrans_payload(order)

    assert payload["transaction_details"] == {
        "order_id": "865740b2-8274-4b4c-b18e-bfed0aeaa176",
        "gross_amount": 18500,
    }
    assert payload["customer_details"]["first_name"] == "Test"
    assert payload["customer_details"]["last_name"] == "Payment"
    assert payload["customer_details"]["billing_address"] == {
        "first_name": "Test",
        "last_name": "Payment",
        "phone": "+628****7890",
        "address": "Jl. Herbal No. 1",
    }
    assert payload["callbacks"] == {
        "finish": "https://amimumherbalproject.vercel.app/transaction/865740b2-8274-4b4c-b18e-bfed0aeaa176",
    }


def test_generate_midtrans_payload_includes_shipping_address_and_product_details():
    order = SimpleNamespace(
        id="683e47dc-02be-4857-9301-540723b8d579",
        total_price=27000,
        customer_name="Maris",
        customer_email="maris@example.com",
        customer_phone="+628789216035",
        user=SimpleNamespace(
            firstname="Maris",
            lastname="Iman",
            fullname="Maris Iman",
            address="Alamat akun utama",
        ),
        shipments=SimpleNamespace(
            shipment_address=SimpleNamespace(
                name="Maris Iman",
                phone="+628789216035",
                address="Jl. Tujuan No. 2",
                city="Bandung",
                zip_code="40111",
            )
        ),
        order_items=[
            SimpleNamespace(
                id=1,
                product_id="prod-phytofresh",
                product_name="Phytofresh",
                variant_product="Eceran",
                quantity=2,
                total_price=24000,
                price_per_item=12000,
            )
        ],
    )

    payload = generate_midtrans_payload(order)

    assert payload["customer_details"]["shipping_address"] == {
        "first_name": "Maris Iman",
        "phone": "+628789216035",
        "address": "Jl. Tujuan No. 2",
        "city": "Bandung",
        "postal_code": "40111",
        "country_code": "IDN",
    }
    assert payload["item_details"] == [
        {
            "id": "prod-phytofresh",
            "price": 12000,
            "quantity": 2,
            "name": "Phytofresh - Eceran",
        },
        {
            "id": "shipping_fee",
            "price": 3000,
            "quantity": 1,
            "name": "Ongkir / biaya pengiriman",
        },
    ]
    assert sum(item["price"] * item["quantity"] for item in payload["item_details"]) == payload["transaction_details"]["gross_amount"]
    assert payload["custom_field1"] == "Phytofresh - Eceran x2"
    assert payload["custom_field2"] == "Order 683e47dc-02be-4857-9301-540723b8d579"
    assert payload["custom_field3"] == "Toko Herbal Amimum"


def test_generate_midtrans_payload_uses_explicit_order_items_when_relation_is_empty():
    order = SimpleNamespace(
        id="f31eb8e6-0faf-4f1d-abcd-test",
        total_price=12000,
        customer_name="Maris",
        customer_email="maris@example.com",
        customer_phone="+628****6035",
        user=SimpleNamespace(
            firstname="Maris",
            lastname="",
            fullname="Maris",
            address="Alamat akun utama",
        ),
        shipments=None,
        order_items=[],
    )
    explicit_items = [
        SimpleNamespace(
            id=11,
            product_id="prod-explicit",
            product_name="Produk dari Query",
            variant_product="Botol",
            quantity=1,
            total_price=12000,
            price_per_item=12000,
        )
    ]

    payload = generate_midtrans_payload(order, order_items=explicit_items)

    assert payload["item_details"] == [
        {
            "id": "prod-explicit",
            "price": 12000,
            "quantity": 1,
            "name": "Produk dari Query - Botol",
        }
    ]
    assert payload["custom_field1"] == "Produk dari Query - Botol x1"


def test_generate_midtrans_payload_can_use_retry_midtrans_order_id():
    order = SimpleNamespace(
        id="5ef46775-a393-49e0-8a82-64dabd05a9de",
        total_price=1500,
        customer_name="Maris",
        customer_email="maris@example.com",
        customer_phone="+628****6035",
        user=None,
        shipments=None,
        order_items=[],
    )

    payload = generate_midtrans_payload(
        order,
        midtrans_order_id="5ef46775-a393-49e0-8a82-64dabd05a9de-rabc123",
    )

    assert payload["transaction_details"] == {
        "order_id": "5ef46775-a393-49e0-8a82-64dabd05a9de-rabc123",
        "gross_amount": 1500,
    }
    assert payload["callbacks"]["finish"].endswith(
        "/transaction/5ef46775-a393-49e0-8a82-64dabd05a9de"
    )
