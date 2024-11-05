import uuid

from sqlalchemy import select, cast, String
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from fastapi import HTTPException, status

from app.models.product_model import ProductModel
from app.dtos.product_dtos import ProductDetailDTO, ProductDetailResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result

def get_product_by_id(
        db: Session, 
        product_id: uuid.UUID
    ) -> Result[ProductDetailResponseDto, Exception]:
    try:
        # Query to get product by ID with eager loading for related entities
        product_model = db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.pack_type))  # Eager load for pack_type
            .filter(cast(ProductModel.id, String) == str(product_id))
        ).scalars().first()

        # Check if product was found
        if not product_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about product with ID {product_id} not found"
                ).dict()
            ))
            # return build(error=HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     error="Not Found",
            #     message=f"Product with id {product_id} not found"
            # ))

        # Convert the product to ProductDetailDTO
        product_detail_dto = ProductDetailDTO(
            id=product_model.id,
            name=product_model.name,
            info=product_model.info,
            variants_list=product_model.variants_list or [],
            description_list=product_model.description_list or [],
            instructions_list=product_model.instruction_list or [],
            price=product_model.price,
            is_active=product_model.is_active,
            company=product_model.company,
            avg_rating=product_model.avg_rating,
            total_rater=product_model.total_rater,
            created_at=product_model.created_at,
            updated_at=product_model.updated_at
        )

        # Build success response
        return build(data=ProductDetailResponseDto(
            status_code=200,
            message="Product details successfully retrieved",
            data=product_detail_dto
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
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))

    # except SQLAlchemyError as e:
    #     db.rollback()
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         error="Conflict",
    #         message=f"Database conflict: {str(e)}"
    #     ))
    # except Exception as e:
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         error="Internal Server Error",
    #         message=f"Internal Server Error: {str(e)}"
    #     ))
