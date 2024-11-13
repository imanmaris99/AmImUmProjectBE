from fastapi import HTTPException, status

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Type

from app.models.product_model import ProductModel
from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error

from app.utils.result import build, Result


def get_all_promo(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[production_dtos.AllProductionPromoResponseDto, Exception]:
    try:
        # Mengambil semua produk dengan promo yang valid
        product_bies = (
            db.query(ProductionModel)
            .options(joinedload(ProductionModel.products))  # Eager loading produk terkait
            .join(ProductModel)
            .filter(ProductModel.is_active.is_(True), ProductionModel.products != None)  # Hanya ambil produk aktif yang memiliki promo
            .offset(skip)
            .limit(limit)
            .all()
        )

        if not product_bies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No information about productions found."
                ).dict()
            )
        
        # Menyiapkan DTO promo untuk response
        info_promo = [
            production_dtos.AllProductionPromoDto(
                id=prod.id,
                name=prod.name,
                photo_url=prod.photo_url,
                promo_special=prod.promo_special  # Menggunakan promo_special dari model
            )
            for prod in product_bies if prod.promo_special > 0  # Hanya ambil produk dengan promo
        ]

        # return build(data=info_promo)
    
        return build(data=production_dtos.AllProductionPromoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List product promo from this brand accessed successfully",
            data=info_promo
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
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
