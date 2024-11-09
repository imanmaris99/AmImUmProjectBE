from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import DeletePackTypeDto, InfoDeletePackTypeDto, DeletePackTypeResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.pack_type_services.support_function import handle_db_error

from app.utils.result import build, Result


def delete_type(
        db: Session, 
        variant_data: DeletePackTypeDto,
        ) -> Result[None, Exception]:
    """Menghapus variasi produk berdasarkan ID dan mengatur ulang display_id."""
    try:
        type = db.query(PackTypeModel).filter(PackTypeModel.id == variant_data.type_id).first()
        if not type:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about variant product with ID {variant_data.type_id} not found"
                ).dict()
            ))

        # Simpan informasi pengguna sebelum dihapus
        variant_delete_info = InfoDeletePackTypeDto(
            type_id= type.id,
            variant= type.variant
        )

        # Hapus artikel
        db.delete(type)
        db.commit()

        return build(data=DeletePackTypeResponseDto(
            status_code=200,
            message="Your pack and variant type product has been deleted",
            data=variant_delete_info
        ))
    
    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
    except Exception as e:
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))
