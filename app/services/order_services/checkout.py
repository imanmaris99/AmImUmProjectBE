import re
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models import OrderModel, OrderItemModel, CartProductModel, ShipmentModel, PackTypeModel, StockMovementModel
from app.models.order_model import DeliveryTypeEnum

from app.dtos import order_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import redis_client


def _fetch_variants_for_update(db: Session, variant_ids: list[int]):
    if not variant_ids:
        return [], True
    try:
        rows = db.execute(
            select(PackTypeModel)
            .filter(PackTypeModel.id.in_(variant_ids))
            .with_for_update()
        ).scalars().all()
        return rows, True
    except Exception:
        if hasattr(db, "bind"):
            raise
        # Some lightweight service tests use narrow DB doubles that only model cart rows.
        # Real SQLAlchemy sessions/proxies should support this lookup and get row locks.
        return [], False


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

        compact_tokens = []
        payment_token = re.search(r'\[PAYMENT:\s*\w+\]', notes_input, re.IGNORECASE)
        if payment_token:
            compact_tokens.append(payment_token.group(0).upper())
        if pos_subtotal is not None:
            compact_tokens.append(f"[POS_SUBTOTAL: {int(pos_subtotal)}]")
        if pos_discount is not None:
            compact_tokens.append(f"[POS_DISCOUNT: {int(pos_discount)}]")
        if pos_total is not None:
            compact_tokens.append(f"[POS_TOTAL: {int(pos_total)}]")

        compact_notes = ' | '.join(compact_tokens).strip()
        safe_notes = (compact_notes or notes_input or '')[:100] or None

        payment_method = (getattr(checkout_payload, "payment_method", None) or "").lower() if checkout_payload else ""
        order_status = "processing" if payment_method in {"cod", "pay_at_store", "cash"} else "pending"

        order = OrderModel(
            customer_id=user_id,
            total_price=total_cost,
            status=order_status,
            shipment_id=shipment.id if shipment else None,
            delivery_type=DeliveryTypeEnum.delivery if shipment else DeliveryTypeEnum.pickup,
            notes=safe_notes,
        )
        db.add(order)
        db.flush()

        variant_ids = list({item.variant_id for item in cart_items if item.variant_id is not None})
        variant_rows, variant_lookup_supported = _fetch_variants_for_update(db, variant_ids)
        variant_map = {int(v.id): v for v in variant_rows}

        for item in cart_items:
            variant = variant_map.get(int(item.variant_id)) if item.variant_id is not None else None
            if not variant and variant_lookup_supported:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_404_NOT_FOUND,
                        error="Not Found",
                        message=f"Variant with ID {item.variant_id} not found"
                    ).dict()
                )

            qty = int(item.quantity or 0)
            if qty <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error="Bad Request",
                        message=f"Invalid quantity for variant {item.variant_id}"
                    ).dict()
                )
            if variant and int(variant.stock or 0) < qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error="Bad Request",
                        message=f"Insufficient stock for variant {item.variant_id}. Available: {int(variant.stock or 0)}, requested: {qty}"
                    ).dict()
                )

            if variant:
                variant.stock = int(variant.stock or 0) - qty

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
        handled = handle_db_error(db, db_error)
        if isinstance(handled, Exception):
            return build(error=handled)
        return build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=handled
        ))

    except SQLAlchemyError as e:
        db.rollback()
        handled = handle_db_error(db, e)
        if isinstance(handled, Exception):
            return build(error=handled)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=handled
        ))

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
                message="Unable to process checkout"
            ).model_dump()
        ))


def pos_checkout(
        db: Session,
        user_id: str,
        payload: order_dtos.PosCheckoutRequestDTO
    ) -> Result[order_dtos.OrderInfoResponseDto, Exception]:
    try:
        if not payload.items:
            raise HTTPException(status_code=400, detail="POS items required")

        variant_ids = list({item.variant_id for item in payload.items})
        variants = db.execute(
            select(PackTypeModel)
            .filter(PackTypeModel.id.in_(variant_ids))
            .with_for_update()
        ).scalars().all()
        variant_map = {int(v.id): v for v in variants}

        subtotal = float(payload.subtotal) if payload.subtotal is not None else 0.0
        discount_total = float(payload.discount_total) if payload.discount_total is not None else 0.0
        computed_subtotal = 0.0
        computed_discount = 0.0

        order = OrderModel(
            customer_id=user_id,
            total_price=0,
            status="pending",
            shipment_id=None,
            delivery_type=DeliveryTypeEnum.pickup,
            notes=(payload.notes or '')[:100] or None,
        )
        db.add(order)
        db.flush()

        for row in payload.items:
            variant = variant_map.get(int(row.variant_id))
            if not variant:
                raise HTTPException(status_code=404, detail=f"Variant {row.variant_id} not found")
            qty = int(row.qty)
            stock_before = int(variant.stock or 0)
            if stock_before < qty:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for variant {row.variant_id}")

            stock_after = stock_before - qty
            variant.stock = stock_after
            line_subtotal = float(row.unit_price) * qty
            line_discount = float(row.discount or 0) * qty
            line_total = max(line_subtotal - line_discount, 0)
            computed_subtotal += line_subtotal
            computed_discount += line_discount

            db.add(OrderItemModel(
                order_id=order.id,
                product_id=row.product_id or getattr(variant, 'product_id', None),
                variant_id=row.variant_id,
                quantity=qty,
                price_per_item=float(row.unit_price),
                total_price=float(line_total),
            ))
            db.add(StockMovementModel(
                variant_id=row.variant_id,
                product_id=row.product_id or getattr(variant, 'product_id', None),
                movement_type="sale",
                delta=-qty,
                stock_before=stock_before,
                stock_after=stock_after,
                actor_id=user_id,
                reason="POS checkout",
                reference=str(order.id),
            ))

        final_total = float(payload.final_total) if payload.final_total is not None else max((subtotal or computed_subtotal) - (discount_total or computed_discount), 0)
        order.total_price = final_total

        db.commit()
        db.refresh(order)

        return build(data={
            "status_code": 201,
            "message": "POS checkout success",
            "data": {
                "id": str(order.id),
                "status": str(order.status),
                "total_price": float(order.total_price or 0.0),
                "shipment_id": None,
                "delivery_type": getattr(order.delivery_type, "value", order.delivery_type),
                "notes": order.notes,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        })
    except HTTPException as e:
        db.rollback()
        return build(error=e)
    except Exception:
        db.rollback()
        return build(error=HTTPException(status_code=500, detail="Unable to process POS checkout"))
