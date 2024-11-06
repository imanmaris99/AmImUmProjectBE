from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result


def delete_wishlist(
        db: Session, 
        wishlist_data: wishlist_dtos.DeleteByIdWishlistDto,
        user_id: str
        ) -> Result[None, Exception]:
    try:
        wishlist_model = db.execute(
            select(WishlistModel)
            .where(
                WishlistModel.id == wishlist_data.wishlist_id,
                WishlistModel.customer_id == user_id
            )  
        ).scalars().first()

        if not wishlist_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Products wishlist from ID : {wishlist_data.wishlist_id} not found"
                ).dict()
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        wishlist_delete_info = wishlist_dtos.InfoDeleteWishlistDto(
            wishlist_id= wishlist_model.id,
            product_name= wishlist_model.product_name
        )

        # Hapus artikel
        db.delete(wishlist_model)
        db.commit()

        return build(data=wishlist_dtos.DeleteWishlistResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Your product wishlist with ID {wishlist_data.wishlist_id} has been deleted",
            data=wishlist_delete_info
        ))
    
    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args("productions", str(e.args))}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))
