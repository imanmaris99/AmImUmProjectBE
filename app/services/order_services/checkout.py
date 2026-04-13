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
        cart_items = db.execute(
            select(CartProductModel)
            .filter(
                CartProductModel.customer_id == user_id,
                CartProductModel.is_active == True
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

        shipment = db.query(ShipmentModel).filter(
            ShipmentModel.customer_id == user_id,
            ShipmentModel.is_active == True
        ).first()

        shipping_cost = float(shipment.shipping_cost or 0.0) if shipment else 0.0
        cart_totals = get_cart_total(cart_items)
        cart_total_items_response = float(cart_totals.total_all_active_prices or 0.0)
        total_cost = cart_total_items_response + shipping_cost

        order = OrderModel(
            customer_id=user_id,
            total_price=total_cost,
            status="pending",
            shipment_id=shipment.id if shipment else None,
            delivery_type=DeliveryTypeEnum.delivery if shipment else DeliveryTypeEnum.pickup,
            notes=None,
        )
        db.add(order)
        db.flush()

        for item in cart_items:
            line_total = float(item.total_price or 0.0)
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_item=float(item.product_price or 0.0),
                total_price=line_total,
            )
            db.add(order_item)

        db.commit()
        db.refresh(order)

        if redis_client:
            redis_keys = [
                f"orders:{user_id}:*",
                f"order:{user_id}:*"
            ]
            for pattern in redis_keys:
                for key in redis_client.scan_iter(pattern):
                    redis_client.delete(key)

        return build(data={
            "status_code": 201,
            "message": "Your order has been created successfully.",
            "data": {
                "id": str(order.id),
                "status": str(order.status),
                "total_price": float(order.total_price or 0.0),
                "shipment_id": str(order.shipment_id) if order.shipment_id else None,
                "delivery_type": getattr(order.delivery_type, "value", order.delivery_type),
                "notes": order.notes,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        })

    except (IntegrityError, DataError) as db_error:
        db.rollback()
        return build(error=handle_db_error(db, db_error))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error=handle_db_error(db, e))

    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))
