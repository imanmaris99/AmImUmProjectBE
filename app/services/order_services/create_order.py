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


def create_order(
        db: Session, 
        order_dto: order_dtos.OrderCreateDTO, 
        user_id: str
    ) -> Result[OrderModel, Exception]:
    """
    Membuat order baru dari item aktif di keranjang.
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

        # Menghitung total harga order
        # total_price = sum(item.quantity * item.product_price for item in cart_items)
        # Mendapatkan total harga keranjang sebagai angka
        cart_total_items_response = get_cart_total(cart_items).total_all_active_prices


        # Jika delivery_type adalah pickup
        if order_dto.delivery_type == DeliveryTypeEnum.pickup:
            order = OrderModel(
                customer_id=user_id,
                total_price=cart_total_items_response,
                status="pending",
                shipment_id=None,  # Tidak ada shipment untuk pickup
                delivery_type=DeliveryTypeEnum.pickup,
                notes=order_dto.notes,  # Notes wajib diisi
            )
        else:
            # Jika delivery_type adalah delivery
            shipment = db.query(ShipmentModel).filter(
                ShipmentModel.id == order_dto.shipment_id,
                ShipmentModel.customer_id == user_id,
                ShipmentModel.is_active == True
            ).first()

            if not shipment:
                raise HTTPException(
                    status_code=400, 
                    detail="Pengiriman tidak valid atau tidak aktif."
                )

            shipping_cost = shipment.shipping_cost
            if shipping_cost is None:
                raise HTTPException(
                    status_code=400, 
                    detail="Biaya pengiriman tidak valid."
                )

            # Menghitung total_cost untuk delivery
            total_cost = cart_total_items_response + shipping_cost

            order = OrderModel(
                customer_id=user_id,
                total_price=total_cost,
                status="pending",
                shipment_id=order_dto.shipment_id,
                delivery_type=DeliveryTypeEnum.delivery,
                notes=order_dto.notes,
            )

        db.add(order)
        db.commit()

        # Menambahkan item order dari keranjang aktif
        for item in cart_items:
            order_item = OrderItemModel(
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_item=item.product_price,
                total_price=cart_total_items_response,
            )
            db.add(order_item)

        # Menghapus item aktif dari keranjang setelah order dibuat
        db.query(CartProductModel).filter(
            CartProductModel.customer_id == user_id,
            CartProductModel.is_active == True
        ).delete()

        db.commit()

        # Buat DTO response
        order_response = order_dtos.OrderCreateInfoDTO(
            id=order.id,
            status=order.status,
            total_price=order.total_price,
            shipment_id=order.shipment_id,
            delivery_type=order.delivery_type,
            notes=order.notes,
            created_at=order.created_at
        )

        # return order
        return build(data=order_dtos.OrderInfoResponseDto(
            status_code=201,
            message="Your order has been created",
            data=order_response
        ))

    except (IntegrityError, DataError) as db_error:
        raise handle_db_error(db, db_error)

    except SQLAlchemyError as e:
        raise handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi HTTPException
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))
