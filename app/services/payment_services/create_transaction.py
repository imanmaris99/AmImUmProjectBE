from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel

from app.dtos.payment_dtos import PaymentCreateDto, PaymentMidtransResponseDTO, PaymentInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.libs.midtrans_config import snap
from app.services.payment_services.support_function import generate_midtrans_payload, validate_midtrans_response
from app.utils.result import build, Result

def create_transaction(
        payment_data: PaymentCreateDto,
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

        if order.status != "pending":
            return build(
                error=HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order tidak valid untuk pembayaran."
                )
            )

        # Buat payload untuk transaksi Midtrans
        transaction_payload = generate_midtrans_payload(order, payment_data.payment_type)

        # Buat transaksi di Midtrans
        try:
            transaction_response = snap.create_transaction(transaction_payload)
        except Exception as e:
            return build(
                error=HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Kesalahan saat membuat transaksi: {str(e)}",
                )
            )

        # Validasi respons Midtrans
        if not validate_midtrans_response(transaction_response):
            return build(
                error=HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Respons dari Midtrans tidak lengkap."
                )
            )

        # Simpan transaksi ke database
        payment = PaymentModel(
            order_id=order.id,
            transaction_id=transaction_response["transaction_id"],
            payment_type=payment_data.payment_type,
            gross_amount=order.total_price,
            transaction_status="pending",
            payment_response=transaction_response,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Buat DTO response
        payment_callback = PaymentMidtransResponseDTO(
                transaction_id=transaction_response["transaction_id"],
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
                    message=f"Unexpected error: {str(e)}",
                ).dict(),
            )
        )
    
