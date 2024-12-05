from fastapi import HTTPException

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import requests
import base64
from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.models.enums import TransactionStatusEnum, FraudStatusEnum
from app.dtos.payment_dtos import (
    PaymentNotificationResponseDto,
    PaymentNotificationSchemaDto,
)
from app.utils.result import build, Result
from app.libs.midtrans_config import MIDTRANS_SERVER_KEY
from app.dtos.payment_dtos import MidtransNotificationDto  # Tambahkan DTO untuk validasi notifikasi
import logging

logger = logging.getLogger(__name__)


def handler_notification(notification_data: dict, db: Session) -> Result[dict, Exception]:
    """
    Menangani notifikasi pembayaran dari Midtrans.
    """
    try:
        # Cek field wajib di payload
        required_fields = ["order_id", "transaction_status", "payment_type", "gross_amount", "signature_key"]
        missing_fields = [field for field in required_fields if field not in notification_data]

        if missing_fields:
            logger.error(f"Field yang hilang: {missing_fields}")
            return build(error=HTTPException(
                status_code=422,
                detail={
                    "error": "Payload tidak valid.",
                    "missing_fields": missing_fields
                }
            ))

        # Validasi payload dengan DTO
        try:
            notification = MidtransNotificationDto(**notification_data)
        except ValidationError as ve:
            logger.error(f"Payload tidak valid: {ve.json()}")
            return build(error=HTTPException(
                status_code=400,
                detail={
                    "error": "Payload notifikasi tidak valid.",
                    "validation_errors": ve.errors()
                }
            ))

        order_id = notification.order_id
        logger.info(f"Memproses notifikasi untuk order_id: {order_id}")

        # Ambil status transaksi dari Midtrans
        midtrans_result = fetch_midtrans_transaction_status(order_id)
        if midtrans_result.error:
            logger.error(f"Error saat mengambil status Midtrans: {midtrans_result.error}")
            return build(error=midtrans_result.error)

        midtrans_data = midtrans_result.data
        logger.debug(f"Data transaksi Midtrans: {midtrans_data}")

        # Validasi dan ambil data pembayaran dari database
        payment = get_payment_by_order_id(order_id, db)
        if not payment:
            logger.warning(f"Pembayaran dengan order_id {order_id} tidak ditemukan.")
            return build(error=HTTPException(
                status_code=404,
                detail="Pembayaran tidak ditemukan."
            ))

        # Update data pembayaran di database
        update_payment_data(payment, midtrans_data, db)

        # Validasi dan update status pesanan
        order = get_order_by_id(payment.order_id, db)
        if not order:
            logger.warning(f"Pesanan terkait dengan order_id {order_id} tidak ditemukan.")
            return build(error=HTTPException(
                status_code=404,
                detail="Pesanan tidak ditemukan."
            ))

        # Map status pembayaran ke status pesanan
        transaction_status = TransactionStatusEnum(midtrans_data.get("transaction_status"))
        order.status = map_payment_status_to_order_status(transaction_status)
        logger.info(f"Status pesanan diperbarui menjadi: {order.status}")

        # Commit perubahan ke database
        db.commit()

        # Return response sukses
        return build(data=PaymentNotificationResponseDto(
            status_code=200,
            message=f"Berhasil memproses notifikasi untuk transaksi {order_id}",
            data=PaymentNotificationSchemaDto(
                order_id=order_id,
                transaction_status=transaction_status.value,
                fraud_status=midtrans_data.get("fraud_status"),
            )
        ))

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error: {e}")
        return build(error=HTTPException(
            status_code=400,
            detail="Kesalahan database, periksa data yang dimasukkan."
        ))

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        return build(error=HTTPException(
            status_code=500,
            detail=f"Kesalahan sistem database: {str(e)}"
        ))

    except Exception as e:
        db.rollback()
        logger.critical(f"Unhandled error: {e}")
        return build(error=HTTPException(
            status_code=500,
            detail=f"Kesalahan tak terduga: {str(e)}"
        ))


def fetch_midtrans_transaction_status(order_id: str) -> Result[dict, Exception]:
    """
    Mengambil status transaksi dari API Midtrans.
    """
    try:
        url = f"https://api.sandbox.midtrans.com/v2/{order_id}/status"
        auth_key = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_key}",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return build(data=response.json())
        elif response.status_code == 404:
            return build(error=HTTPException(status_code=404, detail="Transaksi tidak ditemukan di Midtrans."))
        elif response.status_code == 401:
            return build(error=HTTPException(status_code=401, detail="Autentikasi ke Midtrans gagal."))
        else:
            logger.error(f"Midtrans API error: {response.text}")
            return build(error=HTTPException(status_code=500, detail=f"Midtrans API error: {response.text}"))

    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return build(error=HTTPException(
            status_code=500, 
            detail=f"Kesalahan jaringan ke Midtrans.{str(e)}"
            )
        )


def get_payment_by_order_id(order_id: str, db: Session) -> PaymentModel:
    """
    Mengambil data pembayaran berdasarkan order_id.
    """
    return db.execute(select(PaymentModel).where(PaymentModel.order_id == order_id)).scalars().first()


def get_order_by_id(order_id: int, db: Session) -> OrderModel:
    """
    Mengambil data pesanan berdasarkan order_id.
    """
    return db.execute(select(OrderModel).where(OrderModel.id == order_id)).scalars().first()


def update_payment_data(payment, midtrans_data, db):
    """
    Memperbarui data pembayaran di database.
    """
    payment.transaction_id = midtrans_data.get("transaction_id")
    payment.payment_type = midtrans_data.get("payment_type")
    payment.transaction_status = TransactionStatusEnum(midtrans_data.get("transaction_status"))
    payment.fraud_status = FraudStatusEnum(midtrans_data.get("fraud_status"))
    payment.payment_response = midtrans_data
    db.add(payment)
    logger.info(f"Pembayaran untuk order_id {payment.order_id} diperbarui.")


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
    mapped_status = status_mapping.get(transaction_status, "unknown")
    if mapped_status == "unknown":
        logger.warning(f"Unmapped transaction status: {transaction_status}")
    return mapped_status
