from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.cart_product_model import CartProductModel
from app.models.order_item_model import OrderItemModel
from app.models.order_model import OrderModel
from app.dtos import cart_dtos

import json
import logging

from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error
# from app.services.cart_services.support_function import get_total_records

from app.utils.result import build, Result
from app.libs.redis_config import redis_client, custom_json_serializer

logger = logging.getLogger(__name__)

CACHE_TTL = 300
RESPONSE_MESSAGE = "All products in cart accessed successfully"


def _invalidate_cart_cache(user_id: str):
    if not redis_client:
        return

    for pattern in [f"cart:{user_id}:*", f"carts:{user_id}"]:
        try:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)
        except Exception as cache_error:
            logger.warning("Failed to invalidate cart cache for pattern %s: %s", pattern, cache_error)


def _delete_stale_checked_out_cart_rows(db: Session, user_id: str) -> int:
    """
    Clean up legacy cart rows from older checkout behavior.

    Historically checkout marked purchased cart rows is_active=False instead of
    deleting them. Some direct-buy retries/duplicates may also leave a stale row
    active.

    Safe cleanup rules:
    - inactive rows are stale if the same user already has a matching order item;
      inactive cart rows are not purchase intent and should not remain visible
      after checkout/payment.
    - active rows are only removed when an order was created after the cart row;
      this preserves products the customer intentionally re-adds after buying.
    """
    stale_rows = db.execute(
        select(CartProductModel)
        .join(
            OrderItemModel,
            (OrderItemModel.product_id == CartProductModel.product_id)
            & (OrderItemModel.variant_id == CartProductModel.variant_id),
        )
        .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
        .where(
            CartProductModel.customer_id == user_id,
            OrderModel.customer_id == user_id,
            (
                (CartProductModel.is_active == False)
                | (OrderModel.created_at >= CartProductModel.created_at)
            ),
        )
    ).scalars().all()

    unique_rows = {row.id: row for row in stale_rows}.values()
    for row in unique_rows:
        db.delete(row)

    deleted_count = len(list(unique_rows))
    if deleted_count:
        db.commit()
        _invalidate_cart_cache(user_id)

    return deleted_count

def my_cart(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Result[cart_dtos.AllCartResponseCreateDto, Exception]:
    try:
        _delete_stale_checked_out_cart_rows(db, user_id)

        # Redis key for caching
        redis_key = f"cart:{user_id}:{skip}:{limit}"

        # Check if wishlist data exists in Redis
        cached_cart = None
        if redis_client:
            try:
                cached_cart = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read cart cache for key %s: %s", redis_key, cache_error)

        if cached_cart:
            # Data is found in cache, return it
            cart_data = json.loads(cached_cart)
            return build(data=cart_dtos.AllCartResponseCreateDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                total_prices=cart_data['total_prices'],
                data=cart_data['data']
            ))

        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        cart_items = db.execute(
            select(CartProductModel)
            .where(CartProductModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not cart_items:
            return build(data=cart_dtos.AllCartResponseCreateDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=[],
                total_prices=cart_dtos.CartProductTotalDto()
            ))

        # Hitung total_records
        # total_records = get_total_records(db, user_id)

        # Konversi cart_items menjadi DTO
        cart_dto = [
            cart_dtos.CartInfoDetailDto(
                id=cart_item.id,
                product_name=cart_item.product_name,
                product_price=float(cart_item.product_price or 0),
                variant_info=cart_item.variant_info,
                quantity=cart_item.quantity,
                is_active=cart_item.is_active,
                created_at=cart_item.created_at
            )
            for cart_item in cart_items
        ]

        cart_total_items_response = get_cart_total(cart_items)

        # Save the result to Redis cache
        cache_data = {
            'total_prices': cart_total_items_response,
            'data': [wish.model_dump() for wish in cart_dto]
        }
        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(cache_data, default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write cart cache for key %s: %s", redis_key, cache_error)

        # Return DTO dengan respons yang telah dibangun
        return build(data=cart_dtos.AllCartResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            # total_records=total_records,
            data=cart_dto,
            total_prices=cart_total_items_response
        ))

    except (IntegrityError, DataError) as db_error:
        db.rollback()
        error_type = "Conflict" if isinstance(db_error, IntegrityError) else "Unprocessable Entity"
        status_code = status.HTTP_409_CONFLICT if isinstance(db_error, IntegrityError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        return build(error=HTTPException(
            status_code=status_code,
            detail=ErrorResponseDto(
                status_code=status_code,
                error=error_type,
                message="Data belum bisa diproses. Silakan coba beberapa saat lagi."
            ).dict()
        ))

    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))

    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi HTTPException
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Permintaan belum bisa diproses. Silakan coba beberapa saat lagi."
            ).dict()
        ))