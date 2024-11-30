from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
import json

from app.models.product_model import ProductModel
from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import redis_client

CACHE_TTL = 3600  # Waktu cache dalam detik (1 jam)

def get_all_promo(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[production_dtos.AllProductionPromoResponseDto, Exception]:
    cache_key = f"promotions:{skip}:{limit}"

    try:
        # Cek data di Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON dari Redis dan kembalikan sebagai response
            cached_response = json.loads(cached_data)
            return build(data=production_dtos.AllProductionPromoResponseDto(**cached_response))

        # Query database untuk promo
        product_bies = (
            db.query(ProductionModel)
            .options(joinedload(ProductionModel.products))  # Eager loading produk terkait
            .join(ProductModel)
            .filter(
                ProductModel.is_active.is_(True),  # Produk aktif
                ProductionModel.products != None  # Hanya yang memiliki produk terkait
            )
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
                    message="No information about promotions found."
                ).dict()
            )

        # Konversi data menjadi DTO promo
        info_promo = [
            production_dtos.AllProductionPromoDto(
                id=str(prod.id),  # Konversi UUID ke string
                name=prod.name,
                photo_url=prod.photo_url,
                promo_special=prod.promo_special
            )
            for prod in product_bies if prod.promo_special > 0  # Hanya yang memiliki promo
        ]

        # Bungkus dalam response DTO
        response_dto = production_dtos.AllProductionPromoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All promotions retrieved successfully.",
            data=info_promo
        )

        # Simpan hasil ke Redis dengan TTL
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_dto.dict()))

        # Kembalikan response
        return build(data=response_dto)

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi HTTPException
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))
