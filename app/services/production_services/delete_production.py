from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos

from app.utils.result import build, Result


def delete_production(
        db: Session, 
        deleted_data: production_dtos.ProductionIdToUpdateDto
        ) -> Result[None, Exception]:
    try:
        company = db.query(ProductionModel).filter(ProductionModel.id == deleted_data.production_id).first()
        if not company:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="Company not found"
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        company_delete_info = production_dtos.InfoDeleteProductionDto(
            id= company.id,
            name= company.name
        )

        db.delete(company)
        db.commit()

        return build(data=production_dtos.DeleteProdutionResponseDto(
            status_code=200,
            message="Info about company some product has been deleted",
            data=company_delete_info
        ))
    
    except SQLAlchemyError as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except Exception as e:
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))
