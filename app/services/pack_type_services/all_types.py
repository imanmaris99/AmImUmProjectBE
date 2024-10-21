from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Type

from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import VariantProductDto

from app.utils import optional
from app.utils.result import build, Result


def all_types(
        db: Session, skip: int = 0, limit: int = 10
    ) -> Result[List[Type[PackTypeModel]], Exception]:
    try:
        pack_types = db.query(PackTypeModel).offset(skip).limit(limit).all()

        if not pack_types:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="No information about type or variant products found"
            )

        # Konversi produk menjadi DTO
        types_dto = [
            VariantProductDto(
                id=types.id, 
                variant=types.variant,
                expiration=types.expiration,
                stock=types.stock,
                created_at=types.created_at,
                updated_at=types.updated_at
            )
            for types in pack_types
        ]

        return build(data=types_dto)

    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
        return build(error=http_ex)
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))