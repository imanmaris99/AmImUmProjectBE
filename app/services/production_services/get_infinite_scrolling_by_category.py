from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from typing import Dict, Any
import json

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client


CACHE_TTL = 300  # Waktu cache dalam detik


def get_infinite_scrolling_by_category(
    db: Session, 
    categories_id: int, 
    skip: int = 0, 
    limit: int = 8
) -> Result[Dict[str, Any], Exception]:
    cache_key = f"all_brand_by_categories:{categories_id}:{skip}:{limit}"

    try:
        # Periksa Redis Cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return build(data=json.loads(cached_data))
        
        # Ambil data produk dengan query
        product_bies = (
            db.execute(
                select(ProductionModel)
                .options(selectinload(ProductionModel.herbal_category))
                .where(ProductionModel.herbal_category_id == categories_id)
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()

        if not product_bies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No information about productions found."
                ).dict()
            )
        
        # Hitung total records tanpa memuat data relasi
        total_records = db.execute(
            select(func.count())
            .select_from(ProductionModel)
            .where(ProductionModel.herbal_category_id == categories_id)
        ).scalar()
        
        # Hitung sisa data
        displayed_records = skip + len(product_bies)
        remaining_records = max(total_records - displayed_records, 0)
        has_more = displayed_records < total_records

        # Konversi produk menjadi DTO
        productions_dto = [
            production_dtos.AllProductionsDto(
                id=production.id,
                name=production.name,
                photo_url=production.photo_url,
                description_list=production.description_list,
                category=production.category,
                created_at=production.created_at
            )
            for production in product_bies
        ]

        # Bangun respons dengan DTO lengkap
        response_data = production_dtos.ArticleListScrollResponseDto(
            data=productions_dto,
            remaining_records=remaining_records,
            has_more=has_more
        )

        # Simpan data ke Redis Cache
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_data.dict(), default=custom_json_serializer))

        return build(data=response_data)

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()
        raise http_ex  # HTTPException dilempar langsung agar diproses oleh FastAPI
    
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
