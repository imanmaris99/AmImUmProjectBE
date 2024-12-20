import logging
from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.models.order_item_model import OrderItemModel
from app.models.cart_product_model import CartProductModel

from app.dtos.payment_dtos import PaymentOrderByIdDto, PaymentCreateDto, PaymentMidtransResponseDTO, PaymentInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.libs.midtrans_config import snap
from app.services.payment_services.support_function import generate_midtrans_payload, validate_midtrans_response
from app.utils.result import build, Result

from app.libs.redis_config import redis_client

# Logger untuk Midtrans
logger = logging.getLogger("midtrans")

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
        # Mendapatkan item keranjang aktif
        cart_items = db.execute(
            select(CartProductModel)
            .filter(
                CartProductModel.customer_id == user_id,
                CartProductModel.is_active == True  # Filter hanya item aktif
            )
        ).scalars().all()
        
        if not cart_items:
            raise HTTPException(
                status_code=400, 
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Information about cart active from Customer with ID {user_id} not found."
                ).dict()
            )
        
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
        transaction_payload = generate_midtrans_payload(order)

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
        try:
            payment = PaymentModel(
                order_id=order.id,
                transaction_id="unknown",  # Atau gunakan ID yang lebih spesifik
                gross_amount=order.total_price,
                transaction_status="pending",
                payment_response=transaction_response,
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
        except IntegrityError as e:
            db.rollback()  # Rollback jika terjadi duplikasi atau masalah integritas lainnya

            # Tangani duplikasi transaction_id
            if "payments_transaction_id_key" in str(e.orig):  # Memeriksa constraint unik untuk transaction_id
                return build(
                    error=HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Transaksi dengan ID yang sama sudah ada. Harap coba lagi.",
                    )
                )
            # Jika error bukan duplikasi, lemparkan kembali exception yang lain
            return build(
                error=HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Terjadi kesalahan dalam menyimpan pembayaran.",
                )
            )

        # Menambahkan item order dari keranjang aktif
        for item in cart_items:
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_item=item.product_price,
                total_price=order.total_price,
            )
            db.add(order_item)

        # Menghapus item aktif dari keranjang setelah order dibuat
        db.query(CartProductModel).filter(
            CartProductModel.customer_id == user_id,
            CartProductModel.is_active == True
        ).delete()

        db.commit()

        # Invalidasi cache dengan pendekatan yang lebih efisien
        redis_keys = [f"cart:{user_id}:*", f"carts:{user_id}"]
        for pattern in redis_keys:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        # Buat DTO response
        payment_callback = PaymentMidtransResponseDTO(
                transaction_id="unknown",
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