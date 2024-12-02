from fastapi import HTTPException, status

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from typing import Dict, Any
import json

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client


CACHE_TTL = 300  

def get_infinite_scrolling(
        db: Session, skip: int = 0, limit: int = 6
    ) -> Result[Dict[str, Any], Exception]:
    cache_key = f"productions:{skip}:{limit}"

    try:
        # Cek data di Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON dari Redis dan kirim sebagai response
            cached_response = json.loads(cached_data)
            return build(data=cached_response)
        
        # Ambil data produk dengan lazy loading, ambil kolom yang relevan saja
        product_bies = (
            db.execute(
                select(ProductionModel)
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

        # Hitung total_records
        total_records = db.execute(select(func.count()).select_from(ProductionModel)).scalar()

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

        # Bangun respons dengan data produk dan has_more
        response_data = production_dtos.ArticleListScrollResponseDto(
            data=productions_dto,
            remaining_records=remaining_records,
            has_more=has_more
        )

        # Simpan data ke Redis (dengan TTL 300 detik)
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_data.dict(), default=custom_json_serializer))

        return build(data=response_data)

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

