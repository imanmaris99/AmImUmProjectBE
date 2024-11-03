from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
from typing import List, Type

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos

from app.utils.result import build, Result

def my_wishlist(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[wishlist_dtos.AllWishlistResponseCreateDto, Exception]:
    try:
        # Query untuk mengambil wishlist berdasarkan user_id dengan pagination
        wishlist_model = db.execute(
            select(WishlistModel)
            .where(WishlistModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not wishlist_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"All products wishlist from user ID: {user_id} not found"
            )

        # Hitung total_records
        total_records = db.execute(
            select(func.count())
            .select_from(WishlistModel)
            .where(
                WishlistModel.customer_id == user_id
            )
        ).scalar()

        # Konversi wishlist menjadi DTO
        wishlist_dto = [
            wishlist_dtos.WishlistInfoCreateDto(
                id=wish.id,
                product_name=wish.product_name,
                product_variant=wish.product_variant,
                created_at=wish.created_at
            )
            for wish in wishlist_model
        ]

        # Return DTO dengan respons yang telah dibangun
        return build(data=wishlist_dtos.AllWishlistResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message=f"All products wishlist for user ID {user_id} accessed successfully",
            total_records=total_records,
            data=wishlist_dto
        ))
    
    # Error SQLAlchemy untuk data yang tidak valid, seperti id tidak ditemukan
    except IntegrityError as ie:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database integrity error: {str(ie)}"
        ))

    # Error SQLAlchemy untuk data input yang tidak sesuai tipe
    except DataError as de:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="Unprocessable Entity",
            message=f"Data error: {str(de)}"
        ))

    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except HTTPException as http_ex:
        return build(error=http_ex)
    
    # Error tipe data tidak valid (misal, `skip` atau `limit` bukan integer)
    except (ValueError, TypeError) as te:
        return build(error=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="Unprocessable Entity",
            message=f"Invalid input: {str(te)}"
        ))
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))
