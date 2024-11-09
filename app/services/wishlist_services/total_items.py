from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.wishlist_services.support_function import get_total_records, handle_db_error

from app.utils.result import build, Result


def total_items(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[wishlist_dtos.AllItemNotificationDto, Exception]:
    try:
        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        wishlist_items = db.execute(
            select(WishlistModel)
            .where(WishlistModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not wishlist_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"There are no wishlist products stored in user ID {user_id}."
                ).dict()
            )

        # Hitung total_records
        total_records = get_total_records(db, user_id)

        # Return DTO dengan respons yang telah dibangun
        return build(data=wishlist_dtos.AllItemNotificationDto(
            status_code=status.HTTP_200_OK,
            message=f"All products wishlist for user ID {user_id} have been successfully calculated",
            total_items=total_records
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