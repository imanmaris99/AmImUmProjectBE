from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.utils.result import build, Result

def get_infinite_scrolling(
        db: Session, skip: int = 0, limit: int = 6
    ) -> Result[Dict[str, Any], Exception]:
    try:
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
                error="Not Found",
                message="No information about productions found"
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
                created_at=production.created_at.isoformat()
            )
            for production in product_bies
        ]

        # Bangun respons dengan data produk dan has_more
        response_data = production_dtos.ArticleListScrollResponseDto(
            data=productions_dto,
            remaining_records=remaining_records,
            has_more=has_more
        )

        return build(data=response_data)

    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))
