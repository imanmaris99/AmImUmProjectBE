from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.dtos.product_dtos import ProductIdToUpdateDTO, ProductUpdateDTO, ProductInfoDTO, ProductResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args
from app.libs.redis_config import redis_client

def update_product(
        db: Session, 
        product_id_update: ProductIdToUpdateDTO,
        product_update: ProductUpdateDTO
        ) -> Result[ProductModel, Exception]:
    try:
        # Mencari model Product berdasarkan ID
        product_model = db.execute(
            select(ProductModel)
            .where(
                ProductModel.id == product_id_update.product_id
            )  
        ).scalars().first()
        
        if not product_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about product with ID {product_id_update.product_id} not found"
                ).dict()
            ))
        
        # Update atribut product jika ada
        for attr, value in product_update.model_dump().items():
            setattr(product_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(product_model)

        # --- Buat DTO Response ---
        update_response = ProductInfoDTO(
                id=product_model.id,
                name=product_model.name,
                info=product_model.info,
                weight=product_model.weight,
                description=product_model.description,
                instruction=product_model.instruction,
                price=product_model.price, 
                is_active=product_model.is_active,
                created_at=product_model.created_at,
                updated_at=product_model.updated_at
            )

        # Invalidasi cache dengan pendekatan yang lebih efisien
        redis_keys = [
            f"products:*", 
            f"product:*",
            f"discounts:*",
            f"promotions:*"
        ]
        for pattern in redis_keys:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        # Menggunakan model ter-update untuk membuat respons
        return build(data=ProductResponseDto(
            status_code=200,
            message="Your information of product has been updated",
            data=update_response
        ))
    
    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args("products", str(e.args))}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
    except Exception as e:
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))
    
