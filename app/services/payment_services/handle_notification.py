from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dtos.payment_dtos import InfoTransactionIdDto, PaymentNotificationResponseDto, PaymentNotificationSchemaDto
from app.libs.redis_config import redis_client
from app.services.payment_services.handler_notification import (
    apply_order_status_transition,
    fetch_midtrans_transaction_status,
    get_order_by_id,
    get_payment_by_order_id,
    map_payment_status_to_order_status,
    resolve_transaction_status,
    update_payment_data,
)
from app.utils.result import build, Result


def handle_notification(
    notification_data: InfoTransactionIdDto,
    db: Session,
    user_id: str,
) -> Result[dict, Exception]:
    if not user_id:
        return build(error=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        ))

    payment = get_payment_by_order_id(notification_data.order_id, db)
    if not payment:
        return build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pembayaran tidak ditemukan."
        ))

    order = get_order_by_id(payment.order_id, db)
    if not order:
        return build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pesanan tidak ditemukan."
        ))

    if str(getattr(order, "customer_id", "")) != str(user_id):
        return build(error=HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        ))

    midtrans_result = fetch_midtrans_transaction_status(notification_data.order_id)
    if midtrans_result.error:
        return build(error=midtrans_result.error)

    midtrans_data = midtrans_result.data or {}
    transaction_status = resolve_transaction_status(midtrans_data.get("transaction_status"))
    update_payment_data(payment, midtrans_data, db)

    next_order_status = map_payment_status_to_order_status(transaction_status)
    order.status = apply_order_status_transition(order.status, next_order_status)
    db.commit()

    if redis_client:
        for pattern in (f"order:{user_id}:*", f"orders:{user_id}:*"):
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

    return build(data=PaymentNotificationResponseDto(
        status_code=200,
        message=f"Berhasil menyinkronkan status pembayaran untuk transaksi {notification_data.order_id}",
        data=PaymentNotificationSchemaDto(
            order_id=notification_data.order_id,
            transaction_status=transaction_status.value,
            fraud_status=midtrans_data.get("fraud_status"),
        )
    ))
