from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

import json

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error
from app.utils.result import build, Result

from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600  # Cache TTL dalam detik (1 jam)

def get_all_productions(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[production_dtos.AllListProductionResponseDto, Exception]:
    cache_key = f"productions:{skip}:{limit}"

    try:
        # Cek data di Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON dari Redis dan kirim sebagai response
            cached_response = json.loads(cached_data)
            return build(data=production_dtos.AllListProductionResponseDto(**cached_response))

        # Query ke database untuk mendapatkan data produksi
        productions = db.execute(
            select(ProductionModel)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        # Jika tidak ada data
        if not productions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No information about productions found."
                ).dict()
            )

        # Konversi data produksi menjadi DTO
        productions_dto = [
            production_dtos.AllProductionsDto(
                id=str(production.id),  # Konversi UUID ke string
                name=production.name,
                photo_url=production.photo_url,
                description_list=production.description_list or [],
                category=production.category,  # Ambil kategori dari property
                created_at=production.created_at
            )
            for production in productions
        ]

        # Buat response DTO
        response_dto = production_dtos.AllListProductionResponseDto(
            status_code=status.HTTP_200_OK,
            message="All productions retrieved successfully.",
            data=productions_dto
        )

        # Simpan hasil ke Redis dengan TTL
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_dto.dict(), default=custom_json_serializer))

        # Kembalikan response
        return build(data=response_dto)

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error
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
