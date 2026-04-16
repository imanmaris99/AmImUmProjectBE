from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.order_model import OrderModel
from app.dtos import order_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.services.cart_services.support_function import handle_db_error
from app.utils.result import build, Result


ADMIN_ORDER_LIST_MESSAGE = "Admin order list accessed successfully"
ADMIN_ORDER_DETAIL_MESSAGE = "Admin order detail accessed successfully"
ADMIN_ORDER_UPDATE_MESSAGE = "Admin order status updated successfully"
ALLOWED_ADMIN_ORDER_STATUSES = {
    "pending",
    "paid",
    "processing",
    "shipped",
    "completed",
    "cancelled",
    "failed",
    "capture",
    "refund",
}


def _to_order_info_dto(order: OrderModel) -> order_dtos.GetOrderInfoDto:
    return order_dtos.GetOrderInfoDto(
        id=order.id,
        status=order.status,
        total_price=float(order.total_price or 0.0),
        shipment_id=order.shipment_id,
        delivery_type=order.delivery_type,
        notes=order.notes,
        customer_name=order.customer_name,
        created_at=order.created_at,
        shipping_cost=float(order.shipping_cost or 0.0),
        order_item_lists=order.order_item_lists,
    )


def list_all_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = None,
) -> Result[order_dtos.GetOrderInfoResponseDto, Exception]:
    try:
        stmt = select(OrderModel)

        if status_filter:
            stmt = stmt.where(OrderModel.status == status_filter)

        order_models = db.execute(
            stmt.order_by(OrderModel.created_at.desc()).offset(skip).limit(limit)
        ).scalars().all()

        order_dtos_list = [_to_order_info_dto(order) for order in order_models]

        return build(data=order_dtos.GetOrderInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_ORDER_LIST_MESSAGE,
            data=order_dtos_list,
        ))

    except (IntegrityError, DataError) as db_error:
        return build(error=handle_db_error(db, db_error))
    except SQLAlchemyError as e:
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


def get_order_detail_admin(
    db: Session,
    order_id: str,
) -> Result[order_dtos.GetOrderDetailResponseDto, Exception]:
    try:
        order = db.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        ).scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Order with ID {order_id} not found."
                ).dict()
            )

        order_detail_dto = order_dtos.GetOrderDetailDto(
            id=order.id,
            status=order.status,
            total_price=float(order.total_price or 0.0),
            delivery_type=getattr(order.delivery_type, "value", order.delivery_type),
            notes=order.notes,
            customer_name=order.customer_name,
            created_at=order.created_at,
            shipping_cost=float(order.shipping_cost or 0.0),
            my_shipping=order.my_shipping,
            order_item_lists=order.order_item_lists,
        )

        return build(data=order_dtos.GetOrderDetailResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_ORDER_DETAIL_MESSAGE,
            data=order_detail_dto,
        ))

    except (IntegrityError, DataError) as db_error:
        return build(error=handle_db_error(db, db_error))
    except SQLAlchemyError as e:
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


def update_order_status_admin(
    db: Session,
    order_id: str,
    new_status: str,
) -> Result[order_dtos.OrderInfoResponseDto, Exception]:
    try:
        normalized_status = (new_status or "").strip().lower()
        if normalized_status not in ALLOWED_ADMIN_ORDER_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message=f"Order status '{new_status}' is not allowed."
                ).dict()
            )

        order = db.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        ).scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Order with ID {order_id} not found."
                ).dict()
            )

        order.status = normalized_status
        db.commit()
        db.refresh(order)

        return build(data=order_dtos.OrderInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_ORDER_UPDATE_MESSAGE,
            data=order_dtos.OrderInfoResponseDataDto(
                id=order.id,
                status=order.status,
                total_price=float(order.total_price or 0.0),
                shipment_id=order.shipment_id,
                delivery_type=order.delivery_type,
                notes=order.notes,
                created_at=order.created_at,
            )
        ))

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
