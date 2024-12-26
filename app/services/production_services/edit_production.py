# services/article_service.py

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args
from app.libs.redis_config import redis_client

    
def edit_production(
        db: Session, 
        company_id: production_dtos.ProductionIdToUpdateDto,
        production_update: production_dtos.ProductionInfoUpdateDTO
        ) -> Result[ProductionModel, Exception]:
    try:
        production = db.query(ProductionModel).filter(ProductionModel.id == company_id.production_id).first()
        if not production:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Production with ID {company_id.production_id} not found"
                ).dict()
            ))
        
        # Update atribut bisnis
        for attr, value in production_update.model_dump().items():
            setattr(production, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(production)

        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"productions:*",
            f"brand_promotions:*",
            f"production:{company_id.production_id}"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        return build(data=production_dtos.ProductionInfoUpdateResponseDto(
            status_code=200,
            message="Information about company product has been updated",
            data=production_dtos.ProductionInfoUpdateDTO(
                name=production.name,
                description=production.description
            )
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
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))
