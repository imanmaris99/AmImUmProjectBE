import uuid
from sqlalchemy import select, cast, String
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

def detail_production(
        db: Session, 
        production_id: int,
    ) -> Result[ProductionModel, Exception]:
    try:
        production_model = db.execute(
            select(ProductionModel)
            .filter(ProductionModel.id == production_id)
        ).scalars().first()

        # Check if product was found
        if not production_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Production with ID {production_id} not found"
                ).dict()
            ))

        # Convert the product to ProductDetailDTO
        production_detail_dto = production_dtos.DetailProductionDto(
            id=production_model.id,
            name=production_model.name,
            photo_url=production_model.photo_url,
            description_list=production_model.description_list or [],
            category=production_model.category,
            total_product=production_model.total_product,
            created_at=production_model.created_at
        )

        # Build success response
        return build(data=production_dtos.ProductionDetailResponseDto(
            status_code=200,
            message="Production detail info successfully retrieved",
            data=production_detail_dto
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

