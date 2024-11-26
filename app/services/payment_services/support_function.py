import logging
from app.models.order_model import OrderModel

logger = logging.getLogger("midtrans")

def generate_midtrans_payload(order: OrderModel) -> dict:
    """
    Membuat payload untuk transaksi Midtrans.
    """
    return {
        "transaction_details": {
            "order_id": str(order.id),
            "gross_amount": float(order.total_price),
        },
        "credit_card":{
            "secure" : True
        },
        "customer_details": {
            "first_name": order.customer_name,
            "email": order.customer_email,
            "phone": order.customer_phone,
        }
    }


def validate_midtrans_response(response: dict) -> bool:
    """
    Validasi apakah respons Midtrans memiliki field yang diperlukan.
    """
    required_fields = ["redirect_url", "token"]
    return all(response.get(field) for field in required_fields)



# def validate_midtrans_response(response: dict) -> bool:
#     """
#     Validasi apakah respons Midtrans memiliki field yang diperlukan.
#     """
#     required_fields = ["transaction_id", "redirect_url", "token"]
#     missing_fields = [field for field in required_fields if not response.get(field)]

#     if missing_fields:
#         logger.error(f"Missing fields in Midtrans response: {missing_fields}")
#         # Tambahkan fallback untuk menangani respons tanpa transaction_id
#         if "transaction_id" in missing_fields and response.get("token"):
#             logger.warning("Fallback: Using token as transaction_id.")
#             response["transaction_id"] = response["token"]  # Gunakan token sebagai ID
#             missing_fields.remove("transaction_id")

#     return len(missing_fields) == 0