import logging
import os
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

from app.models.order_model import OrderModel

logger = logging.getLogger("midtrans")

CUSTOMER_APP_URL = os.getenv(
    "CUSTOMER_APP_URL",
    "https://amimumherbalproject.vercel.app",
).rstrip("/")


def build_customer_transaction_url(order_id: str) -> str:
    return f"{CUSTOMER_APP_URL}/transaction/{quote(str(order_id), safe='')}"


def _clean_text(value, max_length: int | None = None) -> str:
    cleaned = " ".join(str(value or "").split())
    if max_length and len(cleaned) > max_length:
        return cleaned[:max_length].rstrip()
    return cleaned


def _to_midtrans_amount(value) -> int:
    amount = Decimal(str(value or 0)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(amount)


def _split_customer_name(order: OrderModel) -> tuple[str, str]:
    user = getattr(order, "user", None)
    full_name = _clean_text(
        getattr(user, "fullname", None)
        or " ".join(
            part for part in [
                getattr(user, "firstname", None),
                getattr(user, "lastname", None),
            ]
            if part
        )
        or getattr(order, "customer_name", None)
        or "Customer",
        255,
    )
    parts = full_name.split(" ", 1)
    first_name = parts[0] if parts else "Customer"
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name[:255], last_name[:255]


def _build_customer_address(order: OrderModel) -> dict | None:
    user = getattr(order, "user", None)
    address = _clean_text(getattr(user, "address", None), 255)
    if not address:
        return None

    first_name, last_name = _split_customer_name(order)
    return {
        "first_name": first_name,
        "last_name": last_name,
        "phone": _clean_text(getattr(order, "customer_phone", None), 50),
        "address": address,
    }


def _build_shipping_address(order: OrderModel) -> dict | None:
    shipment = getattr(order, "shipments", None)
    address_model = getattr(shipment, "shipment_address", None) if shipment else None
    if not address_model:
        return None

    return {
        "first_name": _clean_text(getattr(address_model, "name", None) or getattr(order, "customer_name", None), 255),
        "phone": _clean_text(getattr(address_model, "phone", None) or getattr(order, "customer_phone", None), 50),
        "address": _clean_text(getattr(address_model, "address", None), 255),
        "city": _clean_text(getattr(address_model, "city", None), 50),
        "postal_code": _clean_text(getattr(address_model, "zip_code", None), 10),
        "country_code": "IDN",
    }


def _build_item_details(order: OrderModel, gross_amount: int, order_items=None) -> list[dict]:
    item_details: list[dict] = []

    for item in order_items or getattr(order, "order_items", None) or []:
        quantity = int(getattr(item, "quantity", 0) or 0)
        if quantity <= 0:
            continue

        total_price = _to_midtrans_amount(getattr(item, "total_price", 0))
        unit_price = int(round(total_price / quantity)) if total_price else _to_midtrans_amount(getattr(item, "price_per_item", 0))
        if unit_price <= 0:
            continue

        name_parts = [
            _clean_text(getattr(item, "product_name", None), 40),
            _clean_text(getattr(item, "variant_product", None), 20),
        ]
        item_details.append({
            "id": _clean_text(getattr(item, "product_id", None) or getattr(item, "id", None), 50) or "product",
            "price": unit_price,
            "quantity": quantity,
            "name": " - ".join(part for part in name_parts if part)[:50] or "Produk Herbal",
        })

    current_total = sum(item["price"] * item["quantity"] for item in item_details)
    adjustment = gross_amount - current_total
    if adjustment > 0:
        item_details.append({
            "id": "shipping_fee",
            "price": adjustment,
            "quantity": 1,
            "name": "Ongkir / biaya pengiriman",
        })
    elif adjustment < 0 and item_details:
        # Keep Midtrans item_details total equal to gross_amount even when rounding/discounts exist.
        item_details.append({
            "id": "order_discount",
            "price": adjustment,
            "quantity": 1,
            "name": "Penyesuaian total pesanan",
        })

    return item_details


def _build_product_summary(item_details: list[dict]) -> str:
    product_lines = [
        f"{item.get('name', 'Produk')} x{item.get('quantity', 1)}"
        for item in item_details
        if item.get("id") not in {"shipping_fee", "order_discount"}
    ]
    return _clean_text("; ".join(product_lines), 255)


def generate_midtrans_payload(order: OrderModel, order_items=None, midtrans_order_id: str | None = None) -> dict:
    """
    Membuat payload untuk transaksi Midtrans.
    """
    gross_amount = _to_midtrans_amount(getattr(order, "total_price", 0))
    first_name, last_name = _split_customer_name(order)

    customer_details = {
        "first_name": first_name,
        "last_name": last_name,
        "email": _clean_text(getattr(order, "customer_email", None), 255),
        "phone": _clean_text(getattr(order, "customer_phone", None), 50),
    }

    billing_address = _build_customer_address(order)
    if billing_address:
        customer_details["billing_address"] = billing_address

    shipping_address = _build_shipping_address(order)
    if shipping_address:
        customer_details["shipping_address"] = shipping_address

    payload = {
        "transaction_details": {
            "order_id": str(midtrans_order_id or order.id),
            "gross_amount": gross_amount,
        },
        "credit_card": {
            "secure": True,
        },
        "customer_details": customer_details,
        "callbacks": {
            "finish": build_customer_transaction_url(str(order.id)),
        },
    }

    item_details = _build_item_details(order, gross_amount, order_items=order_items)
    if item_details:
        payload["item_details"] = item_details
        product_summary = _build_product_summary(item_details)
        if product_summary:
            payload["custom_field1"] = product_summary
            payload["custom_field2"] = f"Order {str(order.id)[:36]}"
            payload["custom_field3"] = "Toko Herbal Amimum"

    return payload


def validate_midtrans_response(response: dict) -> bool:
    """
    Validasi apakah respons Midtrans memiliki field yang diperlukan.
    """
    required_fields = ["redirect_url", "token"]
    return all(response.get(field) for field in required_fields)
