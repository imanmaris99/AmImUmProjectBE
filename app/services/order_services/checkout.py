from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models import OrderModel, OrderItemModel, CartProductModel, ShipmentModel
from app.models.order_model import DeliveryTypeEnum

from app.dtos import order_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import redis_client

def checkout(
        db: Session, 
        user_id: str
    ) -> Result[order_dtos.OrderInfoResponseDto, Exception]:
    """
    Membuat order baru dari item aktif di keranjang.
    """
    try:
        # --- Validasi Item Keranjang ---
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
                    message=f"Active cart items for user {user_id} not found."
                ).dict()
            )

        # --- Validasi Pengiriman ---
        shipment = db.query(ShipmentModel).filter(
            ShipmentModel.customer_id == user_id,
            ShipmentModel.is_active == True
        ).first()

        shipping_cost = float(shipment.shipping_cost or 0.0) if shipment else 0.0

        # --- Hitung Total Biaya Order ---
        cart_total_items_response = get_cart_total(cart_items).total_all_active_prices
        total_cost = cart_total_items_response + shipping_cost

        # --- Buat Order Baru ---
        order = OrderModel(
            customer_id=user_id,
            total_price=total_cost,
            status="pending",
            shipment_id=shipment.id if shipment else None,
            delivery_type=DeliveryTypeEnum.delivery if shipment else DeliveryTypeEnum.pickup,
            notes=None,
        )
        db.add(order)
        db.commit()

        # --- Buat DTO Response ---
        order_response = order_dtos.OrderCreateInfoDTO(
            id=order.id,
            status=order.status,
            total_price=order.total_price,
            shipment_id=order.shipment_id,
            delivery_type=order.delivery_type,
            notes=order.notes,
            created_at=order.created_at
        )

        # Invalidasi cache dengan pendekatan yang lebih efisien
        redis_keys = [
            f"orders:{user_id}:*", 
            f"order:{user_id}:*"
        ]
        for pattern in redis_keys:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        return build(data=order_dtos.OrderInfoResponseDto(
            status_code=201,
            message="Your order has been created successfully.",
            data=order_response
        ))

    except (IntegrityError, DataError) as db_error:
        db.rollback()
        raise handle_db_error(db, db_error)

    except SQLAlchemyError as e:
        db.rollback()
        raise handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()
        raise http_ex

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        )
