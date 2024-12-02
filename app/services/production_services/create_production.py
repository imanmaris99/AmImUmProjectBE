
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import redis_client
    
def create_production(
        db: Session, 
        product_by: production_dtos.ProductionCreateDto,
        admin_id:str
        ) -> Result[ProductionModel, Exception]:
    try:
        
        # Buat model artikel baru dengan data dari DTO
        production = ProductionModel(
            **product_by.model_dump(), 
            fk_admin_id=admin_id) 

        db.add(production)
        db.commit()
        db.refresh(production)

        # Buat instance ProductionCreateDto dari model yang baru dibuat
        production_data = production_dtos.ProductionCreateDto(
            name=production.name,
            herbal_category_id=production.herbal_category_id,
            description=production.description
        )
        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"productions:*",
            f"promotions:*"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        return build(data=production_dtos.ProductionCreateResponseDto(
            status_code=201,
            message="Create information about manufactured company has been success",
            data=production_data
        ))
    
    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
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

