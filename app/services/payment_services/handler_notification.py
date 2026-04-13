from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import requests
import base64
import hashlib
from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.models.enums import TransactionStatusEnum, FraudStatusEnum
from app.dtos.payment_dtos import (
    PaymentNotificationResponseDto,
    PaymentNotificationSchemaDto,
    MidtransNotificationDto,
)
from app.utils.result import build, Result
from app.libs.midtrans_config import MIDTRANS_SERVER_KEY, MIDTRANS_IS_PRODUCTION
import logging

logger = logging.getLogger(__name__)


def handler_notification(notification_data: dict, db: Session) -> Result[dict, Exception]:
    """
    Menangani notifikasi pembayaran dari Midtrans.
    """
    try:
        if not MIDTRANS_SERVER_KEY:
            return build(error=HTTPException(status_code=503, detail="Konfigurasi Midtrans belum tersedia."))

        # Debug payload awal
        logger.debug(f"Payload diterima: {notification_data}")

        # Validasi payload dengan DTO
        try:
            notification = MidtransNotificationDto(**notification_data)
        except ValidationError as ve:
            logger.error(f"Payload tidak valid: {ve.json()}")
            missing_fields = [
                field for field in ["transaction_status", "payment_type", "gross_amount", "signature_key"]
                if not notification_data.get(field)
            ]
            return build(error=HTTPException(
                status_code=400,
                detail={
                    "error": "Payload tidak valid.",
                    "missing_fields": missing_fields,
                }
            ))

        normalized_notification = notification.dict()
        order_id = notification.order_id
        logger.info(f"Memproses notifikasi untuk order_id: {order_id}")

        # Ambil status transaksi dari Midtrans untuk sinkronisasi final, namun tetap fail-soft
        midtrans_result = fetch_midtrans_transaction_status(order_id)
        fetched_data = midtrans_result.data if not midtrans_result.error else {}

        candidate_status_codes = [
            notification.status_code,
            fetched_data.get("status_code") if fetched_data else None,
            "200",
        ]
        signature_valid = False
        for candidate_status_code in candidate_status_codes:
            if not candidate_status_code:
                continue
            if validate_signature_key(
                order_id=order_id,
                status_code=str(candidate_status_code),
                gross_amount=notification.gross_amount,
                server_key=MIDTRANS_SERVER_KEY,
                signature_key=notification.signature_key,
            ):
                signature_valid = True
                break

        if not signature_valid:
            logger.warning(
                "Signature key tidak valid untuk order_id: %s. candidate_status_codes=%s gross_amount=%s",
                order_id,
                candidate_status_codes,
                notification.gross_amount,
            )
            return build(error=HTTPException(
                status_code=400,
                detail="Signature key tidak valid."
            ))

        if midtrans_result.error:
            logger.warning("Fetch status Midtrans gagal untuk order_id %s, fallback ke payload callback: %s", order_id, midtrans_result.error)
            midtrans_data = normalized_notification
        else:
            fetched_data = fetched_data or {}
            midtrans_data = {
                **normalized_notification,
                **{key: value for key, value in fetched_data.items() if value is not None}
            }
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
        update_payment_data(payment, midtrans_data or normalized_notification, db)

        # Validasi dan update status pesanan
        order = get_order_by_id(payment.order_id, db)
        if not order:
            logger.warning(f"Pesanan terkait dengan order_id {order_id} tidak ditemukan.")
            return build(error=HTTPException(
                status_code=404,
                detail="Pesanan tidak ditemukan."
            ))

        # Map status pembayaran ke status pesanan
        transaction_status = resolve_transaction_status(midtrans_data.get("transaction_status"))
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

    except ValidationError as ve:
        logger.error(f"Error validasi: {ve.json()}")
        return build(error=HTTPException(
            status_code=400,
            detail={
                "error": "Kesalahan validasi.",
                "validation_errors": ve.errors()
            }
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


def validate_signature_key(order_id: str, status_code: str, gross_amount: str, server_key: str, signature_key: str) -> bool:
    key = f"{order_id}{status_code}{gross_amount}{server_key}"
    generated_key = hashlib.sha512(key.encode()).hexdigest()
    return generated_key == signature_key


def resolve_transaction_status(status_value: str) -> TransactionStatusEnum:
    try:
        return TransactionStatusEnum(status_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Status transaksi Midtrans tidak dikenali: {status_value}") from exc


def resolve_fraud_status(fraud_value: str | None) -> FraudStatusEnum:
    candidate = fraud_value or FraudStatusEnum.accept.value
    try:
        return FraudStatusEnum(candidate)
    except ValueError:
        logger.warning("Fraud status Midtrans tidak dikenali: %s. Fallback ke accept.", candidate)
        return FraudStatusEnum.accept


def fetch_midtrans_transaction_status(order_id: str) -> Result[dict, Exception]:
    """
    Mengambil status transaksi dari API Midtrans.
    """
    try:
        base_url = "https://api.midtrans.com" if MIDTRANS_IS_PRODUCTION else "https://api.sandbox.midtrans.com"
        url = f"{base_url}/v2/{order_id}/status"
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
    payment.transaction_id = midtrans_data.get("transaction_id") or payment.transaction_id
    payment.payment_type = midtrans_data.get("payment_type") or payment.payment_type
    payment.transaction_status = resolve_transaction_status(midtrans_data.get("transaction_status"))
    payment.fraud_status = resolve_fraud_status(midtrans_data.get("fraud_status"))
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
        TransactionStatusEnum.capture:"capture",
        TransactionStatusEnum.refund:"refund"
    }
    mapped_status = status_mapping.get(transaction_status, "unknown")
    if mapped_status == "unknown":
        logger.warning(f"Unmapped transaction status: {transaction_status}")
    return mapped_status
