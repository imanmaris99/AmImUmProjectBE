from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.dtos.product_dtos import ProductCreateDTO, ProductInfoDTO, ProductResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result

def create_product(
        db: Session, 
        create_product: ProductCreateDTO,
) -> Result[ProductModel, Exception]:
    try:
        # Buat model PackType baru dengan data dari DTO
        product_instance = ProductModel(
            **create_product.model_dump()
        )

        db.add(product_instance)
        db.commit()
        db.refresh(product_instance)

        # Buat model PackTypeInfoDto dengan data dari instance yang baru saja dibuat
        create_product_response = ProductInfoDTO(
            id=product_instance.id,
            name=product_instance.name,
            info=product_instance.info,
            weight=product_instance.weight,
            description=product_instance.description,
            instruction=product_instance.instruction,
            price=product_instance.price,
            product_by_id=product_instance.product_by_id,
            created_at=product_instance.created_at,
            updated_at=product_instance.updated_at
        )

        return build(data=ProductResponseDto(
            status_code=201,
            message="Your product has been created",
            data=create_product_response
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
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
