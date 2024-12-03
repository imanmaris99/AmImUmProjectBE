from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models import OrderModel, OrderItemModel, CartProductModel, ShipmentModel
from app.models.order_model import DeliveryTypeEnum

from typing import List, Optional

from app.dtos import order_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error

from app.utils.result import build, Result


def edit_order(
    db: Session,
    order_updated: order_dtos.OrderIdCompleteDataDTO,
    order_dto: order_dtos.OrderCreateDTO,
    user_id: str
) -> Result[order_dtos.OrderInfoResponseDto, Exception]:
    """
    Memperbarui order yang ada dengan data baru (pickup/delivery).
    """
    try:
        # --- Ambil Order Berdasarkan ID ---
        order_model = db.execute(
            select(OrderModel)
            .where(
                OrderModel.id == order_updated.order_id,
                OrderModel.customer_id == user_id
            )
        ).scalars().first()

        if not order_model:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Your order with ID {order_updated.order_id} was not found."
                ).dict()
            ))

        # --- Perbarui Order Berdasarkan Delivery Type ---
        if order_dto.delivery_type == DeliveryTypeEnum.pickup:
            # Pickup tidak memerlukan shipment
            order_model.shipment_id = None
            order_model.delivery_type = DeliveryTypeEnum.pickup
            order_model.notes = order_dto.notes
        else:
            # Validasi Shipment untuk Delivery
            shipment = db.query(ShipmentModel).filter(
                ShipmentModel.id == order_dto.shipment_id,
                ShipmentModel.customer_id == user_id,
                ShipmentModel.is_active == True
            ).first()

            if not shipment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or inactive shipment. Please ensure shipment_id is valid."
                )

            # Validasi dan Konversi Shipping Cost
            shipping_cost = _validate_shipping_cost(shipment.shipping_cost)

            # Perbarui Order
            order_model.shipment_id = order_dto.shipment_id
            order_model.delivery_type = DeliveryTypeEnum.delivery
            order_model.notes = order_dto.notes
            order_model.total_price += shipping_cost  # Tambahkan biaya pengiriman

        # --- Simpan Perubahan ---
        db.commit()
        db.refresh(order_model)

        # --- Buat DTO Response ---
        order_response = order_dtos.OrderCreateInfoDTO(
            id=order_model.id,
            status=order_model.status,
            total_price=order_model.total_price,
            shipment_id=order_model.shipment_id,
            delivery_type=order_model.delivery_type,
            notes=order_model.notes,
            created_at=order_model.created_at
        )

        return build(data=order_dtos.OrderInfoResponseDto(
            status_code=200,
            message="Your order has been updated successfully.",
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


def _validate_shipping_cost(shipping_cost: Optional[float]) -> float:
    """
    Validasi dan konversi shipping cost menjadi float.
    """
    if shipping_cost is None or shipping_cost == '':
        return 0.0  # Default jika kosong
    try:
        return float(shipping_cost)  # Pastikan berupa float
    except ValueError:
        return 0.0  # Default jika gagal konversi

