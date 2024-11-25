from app.models.order_model import OrderModel


def generate_midtrans_payload(order: OrderModel, payment_type: str) -> dict:
    """
    Membuat payload untuk transaksi Midtrans.
    """
    return {
        "transaction_details": {
            "order_id": str(order.id),
            "gross_amount": float(order.total_price),
        },
        "customer_details": {
            "first_name": order.customer_name,
            "email": order.customer_email,
            "phone": order.customer_phone,
        },
        "enabled_payments": [payment_type],
    }


def validate_midtrans_response(response: dict) -> bool:
    """
    Validasi apakah respons Midtrans memiliki field yang diperlukan.
    """
    required_fields = ["transaction_id", "redirect_url", "token"]
    return all(response.get(field) for field in required_fields)
