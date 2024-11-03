import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos

from app.utils.result import build, Result

def post_wishlist(
        db: Session, 
        product_id: uuid.UUID,
        user_id: str
) -> Result[WishlistModel, Exception]:
    try:
        # Cek apakah product_id ada di tabel products
        product = db.query(ProductModel).filter(ProductModel.id == str(product_id)).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"Product with id {product_id} not found"
            )

        # Buat instance baru dari WishlistModel
        wishlist_instance = WishlistModel(
            product_id=product_id,
            customer_id=user_id
        )

        # Tambahkan dan commit instance ke database
        db.add(wishlist_instance)
        db.commit()
        db.refresh(wishlist_instance)

        # Buat DTO response
        post_wishlist_response = wishlist_dtos.WishlistInfoCreateDto(
            id=wishlist_instance.id,
            product_name=product.name,
            created_at=wishlist_instance.created_at
        )

        return build(data=wishlist_dtos.WishlistResponseCreateDto(
            status_code=201,
            message="Your wishlist for the product has been saved",
            data=post_wishlist_response
        ))

    except SQLAlchemyError as e:
        db.rollback()  # Rollback untuk semua error SQLAlchemy umum lainnya
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred : {str(e)}"
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        return build(error=http_ex)

    except Exception as e:
        db.rollback()  # Rollback untuk error tak terduga
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Unexpected error: {str(e)}"
        ))
