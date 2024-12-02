import uuid

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client  # Redis client


def post_wishlist(
    db: Session, 
    # product_id: uuid.UUID,
    wish:wishlist_dtos.WishlistCreateOfIdProductDto,
    user_id: str
) -> Result[WishlistModel, Exception]:
    try:
        # Cek apakah product_id ada di tabel products
        product = db.query(ProductModel).filter(ProductModel.id == str(wish.product_id)).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Information about product with ID {str(wish.product_id)} not found."
                ).dict()
            )

        # Buat instance baru dari WishlistModel
        wishlist_instance = WishlistModel(
            product_id=str(wish.product_id),
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
            product_variant=wishlist_instance.product_variant,
            created_at=wishlist_instance.created_at
        )

        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"wishlist:{user_id}:*",
            f"wishlists:{user_id}"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)
        
        return build(data=wishlist_dtos.WishlistResponseCreateDto(
            status_code=201,
            message="Your wishlist for the product has been saved",
            data=post_wishlist_response
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occured : {str(e)}"
            ).dict()
        ))

    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
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
