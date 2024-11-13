from decimal import Decimal
from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos

from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.services.cart_services.support_function import get_total_records

from app.utils.result import build, Result


def total_items(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[cart_dtos.AllItemNotificationDto, Exception]:
    try:
        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        cart_items = db.execute(
            select(CartProductModel)
            .where(CartProductModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"No products found in cart for user ID {user_id}."
                ).dict()
            )

        # Hitung total_records
        total_records = get_total_records(db, user_id)

        total_notifications=cart_dtos.TotalItemNotificationDto(
            total_items=total_records
        )

        # Return DTO dengan respons yang telah dibangun
        return build(data=cart_dtos.AllItemNotificationDto(
            status_code=status.HTTP_200_OK,
            message=f"All products in cart for user ID {user_id} have been successfully calculated",
            data=total_notifications
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
                message=f"Database error: {str(db_error)}"
            ).dict()
        ))
    
    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
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
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))