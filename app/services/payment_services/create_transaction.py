import logging
import re
import random
import string
import time
from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.models.order_item_model import OrderItemModel
from app.models.shipment_model import ShipmentModel

from app.dtos.payment_dtos import PaymentOrderByIdDto, PaymentCreateDto, PaymentMidtransResponseDTO, PaymentInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.libs.midtrans_config import snap
from app.services.payment_services.support_function import generate_midtrans_payload, validate_midtrans_response
from app.utils.result import build, Result

# Logger untuk Midtrans
logger = logging.getLogger("midtrans")

NON_RETRYABLE_PAYMENT_ORDER_STATUSES = {
    "paid",
    "settlement",
    "capture",
    "processing",
    "shipped",
    "delivered",
    "completed",
    "refund",
    "refunded",
}


def _status_value(value) -> str:
    return str(value or "").split(".")[-1].lower()


def _base36(value: int) -> str:
    alphabet = string.digits + string.ascii_lowercase
    if value <= 0:
        return "0"
    digits = []
    while value:
        value, remainder = divmod(value, 36)
        digits.append(alphabet[remainder])
    return "".join(reversed(digits))


def _build_midtrans_order_id(order_id: str, existing_payment: PaymentModel | None) -> str:
    if not existing_payment:
        return str(order_id)

    suffix = f"r{_base36(int(time.time()))}{random.randint(100, 999)}"
    # Keep below Midtrans' practical 50-char order_id limit: UUID36 + '-' + 9-10 chars.
    return f"{order_id}-{suffix}"[:50]


def _payment_status_value(payment: PaymentModel) -> str:
    return _status_value(getattr(payment, "transaction_status", ""))


def _existing_pending_payment_response(payment: PaymentModel) -> PaymentInfoResponseDto | None:
    """
    Reuse an unfinished Midtrans Snap transaction.

    Midtrans rejects creating a new transaction with the same order_id while the
    old one is still pending. Customers who close GoPay/Snap and press
    "Lanjutkan Pembayaran" must be sent back to the stored redirect URL instead
    of creating another Midtrans transaction.
    """
    if _payment_status_value(payment) != "pending":
        return None

    response_payload = payment.payment_response or {}
    redirect_url = response_payload.get("redirect_url")
    token = response_payload.get("token") or payment.transaction_id
    if not redirect_url or not token:
        return None

    return PaymentInfoResponseDto(
        status_code=200,
        message="Existing pending payment reused",
        data=PaymentMidtransResponseDTO(
            transaction_id=payment.transaction_id,
            redirect_url=redirect_url,
            token=token,
            transaction_status="pending",
        ),
    )


def _extract_shipping_fee_payment(notes: str | None) -> str:
    match = re.search(r'\[SHIPPING_FEE_PAYMENT:\s*([^\]]+)\]', notes or '', re.IGNORECASE)
    mode = (match.group(1).strip().lower() if match else 'prepaid')
    return mode if mode in {'prepaid', 'cod_shipping'} else 'prepaid'


def _extract_shipping_due_on_delivery(notes: str | None, shipping_cost: float) -> float:
    if _extract_shipping_fee_payment(notes) != 'cod_shipping':
        return 0.0

    match = re.search(r'\[SHIPPING_DUE_ON_DELIVERY:\s*(\d+(?:\.\d+)?)\]', notes or '', re.IGNORECASE)
    requested_due = float(match.group(1)) if match else shipping_cost
    return max(0.0, min(float(shipping_cost or 0.0), requested_due))


def _calculate_midtrans_payable_amount(order: OrderModel, order_items: list[OrderItemModel]) -> float:
    order_items_total = sum(float(order_item.total_price or 0.0) for order_item in order_items)
    shipping_cost = float(order.shipping_cost or 0.0)
    shipping_due_on_delivery = _extract_shipping_due_on_delivery(order.notes, shipping_cost)
    payable_shipping_cost = max(shipping_cost - shipping_due_on_delivery, 0.0)
    return order_items_total + payable_shipping_cost

def create_transaction(
        payment_data: PaymentOrderByIdDto,
        db: Session,
        user_id: str
    ) -> Result[PaymentInfoResponseDto, Exception]:
    """
    Membuat transaksi di Midtrans dan menyimpan detail pembayaran ke database.

    Args:
        payment_data (PaymentCreateDto): Data pembayaran dari klien.
        db (Session): Koneksi database SQLAlchemy.

    Returns:
        Result[PaymentMidtransResponseDTO, Exception]: Hasil transaksi atau error.
    """
    try:
        # Ambil detail order dari database
        order = db.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.user),
                selectinload(OrderModel.shipments).selectinload(ShipmentModel.shipment_address),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.products),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.pack_type),
            )
            .filter(
                OrderModel.id == payment_data.order_id,
                OrderModel.customer_id == user_id,
            )
        ).scalars().first()

        if not order:
            return build(
                error=HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order tidak ditemukan."
                )
            )

        order_status = _status_value(order.status)
        if order_status in NON_RETRYABLE_PAYMENT_ORDER_STATUSES:
            return build(
                error=HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order tidak valid untuk pembayaran."
                )
            )

        if snap is None:
            return build(
                error=HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        error="Service Unavailable",
                        message="Layanan pembayaran online sementara belum tersedia. Silakan pilih metode COD/bayar di toko atau coba beberapa saat lagi."
                    ).dict()
                )
            )

        existing_payment = db.execute(
            select(PaymentModel).where(PaymentModel.order_id == order.id)
        ).scalars().first()

        if existing_payment:
            reusable_payment = _existing_pending_payment_response(existing_payment)
            if reusable_payment:
                return build(data=reusable_payment)

        existing_order_items = db.execute(
            select(OrderItemModel)
            .options(
                selectinload(OrderItemModel.products),
                selectinload(OrderItemModel.pack_type),
            )
            .where(OrderItemModel.order_id == order.id)
        ).scalars().all()

        if not existing_order_items:
            return build(
                error=HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order belum memiliki item yang valid untuk pembayaran."
                )
            )

        payable_amount = _calculate_midtrans_payable_amount(order, existing_order_items)
        if payable_amount <= 0:
            return build(
                error=HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nominal pembayaran tidak valid."
                )
            )

        order.total_price = payable_amount

        midtrans_order_id = _build_midtrans_order_id(str(order.id), existing_payment)

        # Buat payload untuk transaksi Midtrans setelah nominal payable final dihitung.
        transaction_payload = generate_midtrans_payload(
            order,
            order_items=existing_order_items,
            midtrans_order_id=midtrans_order_id,
        )

        # Buat transaksi di Midtrans
        try:
            transaction_response = snap.create_transaction(transaction_payload)

        except Exception as e:
            logger.warning("Midtrans create transaction failed for order %s: %s", order.id, e)
            return build(
                error=HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        error="Bad Gateway",
                        message="Layanan pembayaran online sementara belum tersedia. Silakan pilih metode COD/bayar di toko atau coba beberapa saat lagi."
                    ).dict(),
                )
            )

        # Validasi respons Midtrans
        if not validate_midtrans_response(transaction_response):
            logger.warning("Midtrans response missing required fields for order %s: %s", order.id, transaction_response)
            return build(
                error=HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        error="Bad Gateway",
                        message="Layanan pembayaran online sementara belum tersedia. Silakan pilih metode COD/bayar di toko atau coba beberapa saat lagi."
                    ).dict()
                )
            )

        payment_reference = transaction_response.get("token")
        stored_payment_response = {
            **transaction_response,
            "_amimum_request_payload": transaction_payload,
            "_amimum_order_id": str(order.id),
            "_amimum_midtrans_order_id": midtrans_order_id,
        }
        if existing_payment:
            existing_payment.transaction_id = payment_reference
            existing_payment.gross_amount = payable_amount
            existing_payment.transaction_status = "pending"
            existing_payment.payment_response = stored_payment_response
            payment = existing_payment
        else:
            payment = PaymentModel(
                order_id=order.id,
                transaction_id=payment_reference,
                gross_amount=payable_amount,
                transaction_status="pending",
                payment_response=stored_payment_response,
            )
            db.add(payment)

        order.status = "pending"

        db.commit()
        db.refresh(payment)

        # Buat DTO response
        payment_callback = PaymentMidtransResponseDTO(
                transaction_id=payment.transaction_id,
                redirect_url=transaction_response["redirect_url"],
                token=transaction_response["token"],
                transaction_status="pending"
            )

        # return order
        return build(data=PaymentInfoResponseDto(
            status_code=201,
            message="Your payment has been created",
            data=payment_callback
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error=handle_db_error(db, e))

    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi HTTPException
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(
            error=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server Error",
                    message="Permintaan belum bisa diproses. Silakan coba beberapa saat lagi.",
                ).dict(),
            )
        )