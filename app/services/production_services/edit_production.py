# services/article_service.py

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos

from app.utils.result import build, Result

    
def edit_production(
        db: Session, 
        company_id: production_dtos.ProductionIdToUpdateDto,
        production_update: production_dtos.ProductionInfoUpdateDTO
        ) -> Result[ProductionModel, Exception]:
    try:
        production = db.query(ProductionModel).filter(ProductionModel.id == company_id.production_id).first()
        if not production:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="production id not found"
            )
        )
        
        # Update atribut bisnis
        for attr, value in production_update.model_dump().items():
            setattr(production, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(production)
        return build(data=production_dtos.ProductionInfoUpdateResponseDto(
            status_code=200,
            message="Information about company product has been updated",
            data=production_dtos.ProductionInfoUpdateDTO(
                name=production.name,
                description=production.description
            )
        ))
    
    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))
