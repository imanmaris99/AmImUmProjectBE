from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
import requests
import base64
from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.models.enums import TransactionStatusEnum, FraudStatusEnum
from app.dtos.payment_dtos import InfoTransactionIdDto, PaymentNotificationResponseDto, PaymentNotificationSchemaDto
from app.utils.result import build, Result
from app.libs.midtrans_config import MIDTRANS_SERVER_KEY


def handle_notification(notification_data: InfoTransactionIdDto, db: Session, user_id: str) -> Result[dict, Exception]:
    try:
        # Fetch Midtrans status
        midtrans_result = fetch_midtrans_transaction_status(notification_data.transaction_id)
        if midtrans_result.error:
            return build(error=midtrans_result.error)

        midtrans_data = midtrans_result.data
        transaction_status = TransactionStatusEnum(midtrans_data["transaction_status"])
        fraud_status = FraudStatusEnum(midtrans_data.get("fraud_status", "accept"))

        # Validate and update payment
        payment = get_payment_by_transaction_id(notification_data.transaction_id, db)
        if not payment:
            return build(error=HTTPException(status_code=404, detail="Pembayaran tidak ditemukan."))

        payment.transaction_status = transaction_status
        payment.payment_response = payment.payment_response or {}
        payment.payment_response["fraud_status"] = fraud_status.value

        # Validate and update order
        order = get_order_by_id(payment.order_id, db)
        if not order:
            db.rollback()
            return build(error=HTTPException(status_code=404, detail="Pesanan terkait tidak ditemukan."))

        if order.user_id != user_id:
            db.rollback()
            return build(error=HTTPException(status_code=403, detail="Akses tidak diizinkan untuk pesanan ini."))

        order.status = map_payment_status_to_order_status(transaction_status)
        db.commit()

        return build(data=PaymentNotificationResponseDto(
            status_code=200,
            message=f"Success access notification of this transaction id {notification_data.transaction_id}",
            data=PaymentNotificationSchemaDto(
                transaction_id=notification_data.transaction_id,
                transaction_status=transaction_status.value,
                fraud_status=fraud_status.value
            )
        ))

    except (DataError, IntegrityError) as db_error:
        db.rollback()
        return build(error=HTTPException(status_code=400, detail=f"Database error: {str(db_error)}"))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error=HTTPException(status_code=500, detail=f"SQLAlchemy error: {str(e)}"))

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}"))


def fetch_midtrans_transaction_status(transaction_id: str) -> Result[dict, Exception]:
    try:
        url = f"https://api.sandbox.midtrans.com/v2/{transaction_id}/status"
        auth_key = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()

        headers = {"Authorization": f"Basic {auth_key}", "accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return build(data=response.json())
        elif response.status_code == 404:
            return build(error=HTTPException(status_code=404, detail="Transaksi tidak ditemukan di Midtrans."))
        elif response.status_code == 401:
            return build(error=HTTPException(status_code=401, detail="Autentikasi ke Midtrans gagal."))
        else:
            return build(error=HTTPException(status_code=500, detail=f"Error: {response.text}"))

    except requests.RequestException as e:
        return build(error=HTTPException(status_code=500, detail=f"Network error: {str(e)}"))


def get_payment_by_transaction_id(transaction_id: str, db: Session) -> PaymentModel:
    return db.execute(select(PaymentModel).where(PaymentModel.transaction_id == transaction_id)).scalars().first()


def get_order_by_id(order_id: int, db: Session) -> OrderModel:
    return db.execute(select(OrderModel).where(OrderModel.id == order_id)).scalars().first()


def map_payment_status_to_order_status(transaction_status: TransactionStatusEnum) -> str:
    status_mapping = {
        TransactionStatusEnum.settlement: "paid",
        TransactionStatusEnum.expire: "failed",
        TransactionStatusEnum.cancel: "failed",
        TransactionStatusEnum.deny: "failed",
        TransactionStatusEnum.pending: "pending",
    }
    return status_mapping.get(transaction_status, "unknown")
