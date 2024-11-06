from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.dtos.product_dtos import DeleteByIdProductDto, InfoDeleteProductDto, DeleteProductResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result


def delete_product(
        db: Session, 
        product_data: DeleteByIdProductDto,
        ) -> Result[None, Exception]:
    try:
        product_model = db.execute(
            select(ProductModel)
            .where(
                ProductModel.id == product_data.product_id
            )  
        ).scalars().first()

        if not product_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about product with ID {product_data.product_id} not found"
                ).dict()
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        product_delete_info = InfoDeleteProductDto(
            product_id= product_model.id,
            name= product_model.name
        )

        # Hapus artikel
        db.delete(product_model)
        db.commit()

        return build(data=DeleteProductResponseDto(
            status_code=200,
            message="Your data of product has been deleted",
            data=product_delete_info
        ))
    
    except SQLAlchemyError as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
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
    
