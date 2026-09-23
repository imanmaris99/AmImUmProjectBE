import logging
import os
from html import escape

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.dtos import order_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.models.order_model import OrderModel
from app.utils.firebase_utils import send_email
from app.utils.result import Result, build
from app.services.cart_services.support_function import handle_db_error

logger = logging.getLogger(__name__)

QRIS_CONFIRMATION_MESSAGE = "QRIS payment confirmation submitted successfully"
ADMIN_QRIS_EMAIL_ENV_KEYS = (
    "QRIS_NOTIFICATION_EMAIL",
    "ADMIN_NOTIFICATION_EMAIL",
    "ADMIN_EMAIL",
)
DEFAULT_ADMIN_QRIS_EMAIL = "imannmariss@gmail.com"


def _extract_payment_method(notes: str | None) -> str | None:
    if not notes:
        return None

    marker = "[PAYMENT:"
    upper_notes = notes.upper()
    marker_index = upper_notes.find(marker)
    if marker_index < 0:
        return None

    end_index = notes.find("]", marker_index)
    if end_index < 0:
        return None

    return notes[marker_index + len(marker):end_index].strip().lower()


def _admin_qris_notification_email() -> str:
    for key in ADMIN_QRIS_EMAIL_ENV_KEYS:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return DEFAULT_ADMIN_QRIS_EMAIL


def _build_admin_qris_confirmation_body(order: OrderModel) -> str:
    order_id = escape(str(getattr(order, "id", "-")))
    customer_name = escape(str(getattr(order, "customer_name", "Customer") or "Customer"))
    customer_email = escape(str(getattr(order, "customer_email", "-") or "-"))
    customer_phone = escape(str(getattr(order, "customer_phone", "-") or "-"))
    total_price = escape(str(getattr(order, "total_price", "-") or "-"))
    status_value = escape(str(getattr(order, "status", "-") or "-"))

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #1f2937; background: #f7faf8; padding: 24px;">
      <div style="max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; border: 1px solid #e5e7eb;">
        <div style="background: #006A47; color: #ffffff; padding: 18px 22px;">
          <h2 style="margin: 0; font-size: 20px;">Konfirmasi QRIS Customer</h2>
        </div>
        <div style="padding: 22px; line-height: 1.6;">
          <p>Customer menekan tombol <strong>Saya Sudah Bayar QRIS</strong>.</p>
          <p><strong>ID Pesanan:</strong> {order_id}</p>
          <p><strong>Customer:</strong> {customer_name}</p>
          <p><strong>Email:</strong> {customer_email}</p>
          <p><strong>Telepon:</strong> {customer_phone}</p>
          <p><strong>Total Pesanan:</strong> {total_price}</p>
          <p><strong>Status Saat Ini:</strong> {status_value}</p>
          <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:12px;margin-top:14px;">
            <p style="margin:0;"><strong>Tindakan admin:</strong> cek mutasi/notifikasi QRIS merchant. Jika dana sudah masuk sesuai nominal, ubah status order menjadi <strong>paid</strong> atau <strong>processing</strong> dari dashboard.</p>
          </div>
        </div>
        <div style="padding: 16px 22px; background: #f3f4f6; font-size: 12px; color: #4b5563;">
          <p style="margin: 0;">Email ini hanya berisi ringkasan konfirmasi customer dan tidak memuat data rahasia merchant.</p>
        </div>
      </div>
    </body>
    </html>
    """


def submit_qris_payment_confirmation(
    db: Session,
    user_id: str,
    order_id: str,
) -> Result[order_dtos.QrisPaymentConfirmationResponseDto, Exception]:
    try:
        order = db.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.user))
            .where(OrderModel.id == order_id, OrderModel.customer_id == user_id)
        ).scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="Pesanan tidak ditemukan untuk akun ini.",
                ).dict(),
            )

        payment_method = _extract_payment_method(getattr(order, "notes", None))
        if payment_method != "qris_manual":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Konfirmasi QRIS hanya tersedia untuk pesanan QRIS resmi toko.",
                ).dict(),
            )

        if str(getattr(order, "status", "") or "").strip().lower() != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_409_CONFLICT,
                    error="Conflict",
                    message="Status pesanan sudah berubah. Cek detail transaksi terbaru.",
                ).dict(),
            )

        notified = False
        try:
            send_email(
                _admin_qris_notification_email(),
                f"Konfirmasi QRIS Amimum - Order {order.id}",
                _build_admin_qris_confirmation_body(order),
                html=True,
            )
            notified = True
        except Exception as email_error:
            logger.warning(
                "QRIS admin notification email failed for order %s: %s",
                getattr(order, "id", order_id),
                email_error,
            )

        return build(data=order_dtos.QrisPaymentConfirmationResponseDto(
            status_code=status.HTTP_200_OK,
            message=QRIS_CONFIRMATION_MESSAGE,
            data=order_dtos.QrisPaymentConfirmationDataDto(
                order_id=str(order.id),
                status=str(order.status),
                admin_notified=notified,
            ),
        ))

    except (IntegrityError, DataError) as db_error:
        return build(error=handle_db_error(db, db_error))
    except SQLAlchemyError as db_error:
        return build(error=handle_db_error(db, db_error))
    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)
    except Exception:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Konfirmasi pembayaran belum bisa diproses. Silakan coba beberapa saat lagi.",
            ).dict(),
        ))
