from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import PackTypeCreateDto, PackTypeInfoDto, PackTypeResponseCreateDto
from app.utils import optional
from app.utils.result import build, Result

def create_type(
        db: Session, 
        pack_types: PackTypeCreateDto,
        admin_id: str
) -> Result[PackTypeModel, Exception]:
    try:
        # Buat model PackType baru dengan data dari DTO
        pack_type_instance = PackTypeModel(
            **pack_types.model_dump(),
            fk_admin_id=admin_id
        )
        db.add(pack_type_instance)
        db.commit()
        db.refresh(pack_type_instance)

        # Buat model PackTypeInfoDto dengan data dari instance yang baru saja dibuat
        pack_type_response = PackTypeInfoDto(
            id=pack_type_instance.id,
            img=pack_type_instance.img,
            name=pack_type_instance.name,
            min_amount=pack_type_instance.min_amount,
            variant=pack_type_instance.variant,
            expiration=pack_type_instance.expiration,
            stock=pack_type_instance.stock,
            discount=pack_type_instance.discount,
            fk_admin_id=pack_type_instance.fk_admin_id,
            created_at=pack_type_instance.created_at,
            updated_at=pack_type_instance.updated_at
        )

        return build(data=PackTypeResponseCreateDto(
            status_code=201,
            message="Your pack and variant type product has been created",
            data=pack_type_response
        ))
    
    except SQLAlchemyError as e:
        db.rollback()  # Rollback untuk semua error SQLAlchemy umum lainnya
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred : {str(e)}"
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
        return build(error=http_ex)

    except Exception as e:
        db.rollback()  # Rollback untuk error tak terduga
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Unexpected error: {str(e)}"
        ))
