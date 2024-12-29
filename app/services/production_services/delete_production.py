from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

from app.libs.redis_config import redis_client

def delete_production(
        db: Session, 
        deleted_data: production_dtos.ProductionIdToUpdateDto
        ) -> Result[None, Exception]:
    try:
        company = db.query(ProductionModel).filter(ProductionModel.id == deleted_data.production_id).first()
        if not company:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Production with ID {deleted_data.production_id} not found"
                ).dict()
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        company_delete_info = production_dtos.InfoDeleteProductionDto(
            id= company.id,
            name= company.name
        )

        db.delete(company)
        db.commit()

        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"productions:*",
            f"all_brand_by_categories:*",
            f"brand_promotions:*"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        return build(data=production_dtos.DeleteProdutionResponseDto(
            status_code=200,
            message="Info about company some product has been deleted",
            data=company_delete_info
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

