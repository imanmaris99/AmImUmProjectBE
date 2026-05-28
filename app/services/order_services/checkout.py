import re
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models import OrderModel, OrderItemModel, CartProductModel, ShipmentModel, PackTypeModel
from app.models.order_model import DeliveryTypeEnum

from app.dtos import order_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import redis_client

def checkout(
        db: Session, 
        user_id: str,
        checkout_payload: order_dtos.CheckoutRequestDTO | None = None
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

        notes_input = (checkout_payload.notes or '').strip() if checkout_payload else ''
        subtotal_match = re.search(r'\[POS_SUBTOTAL:\s*(\d+)\]', notes_input, re.IGNORECASE)
        discount_match = re.search(r'\[POS_DISCOUNT:\s*(\d+)\]', notes_input, re.IGNORECASE)
        total_match = re.search(r'\[POS_TOTAL:\s*(\d+)\]', notes_input, re.IGNORECASE)

        payload_subtotal = float(checkout_payload.subtotal) if checkout_payload and checkout_payload.subtotal is not None else None
        payload_discount = float(checkout_payload.discount_total) if checkout_payload and checkout_payload.discount_total is not None else None
        payload_total = float(checkout_payload.final_total) if checkout_payload and checkout_payload.final_total is not None else None

        pos_subtotal = payload_subtotal if payload_subtotal is not None else (float(subtotal_match.group(1)) if subtotal_match else None)
        pos_discount = payload_discount if payload_discount is not None else (float(discount_match.group(1)) if discount_match else 0.0)
        pos_total = payload_total if payload_total is not None else (float(total_match.group(1)) if total_match else None)

        if pos_subtotal is not None and pos_total is not None and 0 <= pos_total <= pos_subtotal:
            total_cost = pos_total + shipping_cost
        else:
            total_cost = cart_total_items_response + shipping_cost

        order = OrderModel(
            customer_id=user_id,
            total_price=total_cost,
            status="pending",
            shipment_id=shipment.id if shipment else None,
            delivery_type=DeliveryTypeEnum.delivery if shipment else DeliveryTypeEnum.pickup,
            notes=notes_input or None,
        )
        db.add(order)
        db.flush()

        for item in cart_items:
            variant = db.query(PackTypeModel).filter(PackTypeModel.id == item.variant_id).first()
            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_404_NOT_FOUND,
                        error="Not Found",
                        message=f"Variant with ID {item.variant_id} not found"
                    ).dict()
                )

            qty = int(item.quantity or 0)
            current_stock = int(variant.stock or 0)
            if qty <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error="Bad Request",
                        message=f"Invalid quantity for variant {item.variant_id}"
                    ).dict()
                )
            if current_stock < qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error="Bad Request",
                        message=f"Insufficient stock for variant {item.variant_id}. Available: {current_stock}, requested: {qty}"
                    ).dict()
                )

            variant.stock = current_stock - qty

            line_total = float(item.total_price or 0.0)
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=qty,
                price_per_item=float(item.product_price or 0.0),
                total_price=line_total,
            )
            db.add(order_item)

            # Prevent the same cart rows from being re-checked out on next transaction
            item.is_active = False

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
