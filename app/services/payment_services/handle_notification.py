from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
import requests
import base64
from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.models.enums import TransactionStatusEnum, FraudStatusEnum
from app.dtos.payment_dtos import (
    InfoTransactionIdDto,
    PaymentNotificationResponseDto,
    PaymentNotificationSchemaDto
)
from app.utils.result import build, Result
from app.libs.midtrans_config import MIDTRANS_SERVER_KEY
import logging

logger = logging.getLogger(__name__)


def handle_notification(
    notification_data: InfoTransactionIdDto, 
    db: Session, 
    user_id: str
) -> Result[dict, Exception]:
    """
    Menangani notifikasi dari Midtrans.
    """
    try:
        # Fetch status transaksi dari Midtrans
        logger.info(f"Mengambil status transaksi untuk order_id: {notification_data.order_id}")
        midtrans_result = fetch_midtrans_transaction_status(notification_data.order_id)
        
        if midtrans_result.error:
            logger.error(f"Kesalahan saat fetch status Midtrans: {midtrans_result.error}")
            return build(error=midtrans_result.error)

        midtrans_data = midtrans_result.data
        transaction_id = midtrans_data.get("transaction_id")
        payment_type = midtrans_data.get("payment_type")
        transaction_status = TransactionStatusEnum(midtrans_data.get("transaction_status"))
        fraud_status = FraudStatusEnum(midtrans_data.get("fraud_status"))

        logger.info(f"Data Midtrans: {midtrans_data}")

        # Validasi data pembayaran
        payment = get_payment_by_order_id(notification_data.order_id, db)
        if not payment:
            logger.warning("Pembayaran tidak ditemukan di database.")
            return build(error=HTTPException(status_code=404, detail="Pembayaran tidak ditemukan."))
        
        # Update payment data
        payment.transaction_id = transaction_id
        payment.payment_type = payment_type
        payment.transaction_status = transaction_status
        payment.payment_response = midtrans_data
        payment.fraud_status = fraud_status

        # Validasi dan update status pesanan
        order = get_order_by_id(payment.order_id, db)
        if not order:
            logger.warning("Pesanan terkait tidak ditemukan.")
            db.rollback()
            return build(error=HTTPException(status_code=404, detail="Pesanan terkait tidak ditemukan."))

        if order.customer_id != user_id:
            logger.warning(f"Akses pesanan ditolak untuk user_id: {user_id}")
            db.rollback()
            return build(error=HTTPException(status_code=403, detail="Akses tidak diizinkan untuk pesanan ini."))

        order.status = map_payment_status_to_order_status(transaction_status)
        logger.info(f"Status pesanan diupdate menjadi: {order.status}")

        # Commit perubahan ke database
        db.commit()

        # Return response sukses
        return build(data=PaymentNotificationResponseDto(
            status_code=200,
            message=f"Berhasil memproses notifikasi untuk transaksi id {notification_data.order_id}",
            data=PaymentNotificationSchemaDto(
                order_id=notification_data.order_id,
                transaction_status=transaction_status.value,
                fraud_status=fraud_status.value
            )
        ))

    except (DataError, IntegrityError) as db_error:
        db.rollback()
        logger.error(f"Kesalahan database: {db_error}")
        return build(error=HTTPException(status_code=400, detail=f"Database error: {str(db_error)}"))

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Kesalahan SQLAlchemy: {e}")
        return build(error=HTTPException(status_code=500, detail=f"SQLAlchemy error: {str(e)}"))

    except Exception as e:
        db.rollback()
        logger.critical(f"Kesalahan tidak terduga: {e}")
        return build(error=HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}"))


def fetch_midtrans_transaction_status(order_id: str) -> Result[dict, Exception]:
    """
    Mengambil status transaksi dari Midtrans.
    """
    try:
        url = f"https://api.sandbox.midtrans.com/v2/{order_id}/status"
        auth_key = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_key}",
            "accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return build(data=response.json())
        elif response.status_code == 404:
            return build(error=HTTPException(status_code=404, detail="Transaksi tidak ditemukan di Midtrans."))
        elif response.status_code == 401:
            return build(error=HTTPException(status_code=401, detail="Autentikasi ke Midtrans gagal."))
        else:
            logger.error(f"Kesalahan API Midtrans: {response.text}")
            return build(error=HTTPException(status_code=500, detail=f"Error: {response.text}"))

    except requests.RequestException as e:
        logger.error(f"Kesalahan jaringan saat mengakses Midtrans: {e}")
        return build(error=HTTPException(status_code=500, detail=f"Network error: {str(e)}"))


def get_payment_by_order_id(order_id: str, db: Session) -> PaymentModel:
    """
    Mengambil data pembayaran berdasarkan order_id.
    """
    return db.execute(select(PaymentModel).where(PaymentModel.order_id == order_id)).scalars().first()


def get_order_by_id(order_id: int, db: Session) -> OrderModel:
    """
    Mengambil data pesanan berdasarkan ID.
    """
    return db.execute(select(OrderModel).where(OrderModel.id == order_id)).scalars().first()


def map_payment_status_to_order_status(transaction_status: TransactionStatusEnum) -> str:
    """
    Memetakan status pembayaran ke status pesanan.
    """
    status_mapping = {
        TransactionStatusEnum.settlement: "paid",
        TransactionStatusEnum.expire: "failed",
        TransactionStatusEnum.cancel: "failed",
        TransactionStatusEnum.deny: "failed",
        TransactionStatusEnum.pending: "pending",
    }
    return status_mapping.get(transaction_status, "unknown")
