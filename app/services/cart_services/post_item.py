from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.models.pack_type_model import PackTypeModel
from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result

def post_item(
        db: Session, 
        cart: cart_dtos.CartCreateOfIdProductDto,
        user_id:str
) -> Result[CartProductModel, Exception]:
    try:
        # Mencari model Product berdasarkan ID
        product = db.execute(
            select(ProductModel)
            .where(
                ProductModel.id == cart.product_id
            )  
        ).scalars().first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Information about product with ID {cart.product_id} not found."
                ).dict()
            )
        
        # Mencari model PackType (variant produk) berdasarkan ID
        variant = db.execute(
            select(PackTypeModel)
            .where(
                PackTypeModel.id == cart.variant_id
            )  
        ).scalars().first()
        
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Information about variant with ID {cart.variant_id} not found."
                ).dict()
            )

        # Buat instance baru dari CartProductModel
        cart_instance = CartProductModel(
            product_id=cart.product_id,
            variant_id=cart.variant_id,
            quantity=1,
            customer_id=user_id
        )

        # Tambahkan dan commit instance ke database
        db.add(cart_instance)
        db.commit()
        db.refresh(cart_instance)

        # Buat DTO response
        post_cart_response = cart_dtos.CartInfoCreateDto(
            id=cart_instance.id,
            product_name=product.name,
            variant_product=variant.variant,
            quantity=cart_instance.quantity,
            is_active=cart_instance.is_active,
            customer_name=cart_instance.customer_name,
            created_at=cart_instance.created_at
        )

        return build(data=cart_dtos.CartResponseCreateDto(
            status_code=201,
            message="Your product choice has been saved in cart",
            data=post_cart_response
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

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
