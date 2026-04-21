from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.cart_product_model import CartProductModel
from app.models.order_item_model import OrderItemModel
from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import DeletePackTypeDto, InfoDeletePackTypeDto, DeletePackTypeResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.pack_type_services.support_function import handle_db_error

from app.utils.result import build, Result


def delete_type(
        db: Session, 
        variant_data: DeletePackTypeDto,
        ) -> Result[None, Exception]:
    try:
        variant = db.query(PackTypeModel).filter(PackTypeModel.id == variant_data.type_id).first()
        if not variant:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about variant product with ID {variant_data.type_id} not found"
                ).model_dump()
            ))

        active_cart_count = db.execute(
            select(CartProductModel.id)
            .where(CartProductModel.variant_id == variant.id)
        ).scalars().first()
        if active_cart_count is not None:
            return build(error=HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_409_CONFLICT,
                    error="Conflict",
                    message="Variant cannot be deleted because it is still referenced by cart items."
                ).model_dump()
            ))

        order_item_ref = db.execute(
            select(OrderItemModel.id)
            .where(OrderItemModel.variant_id == variant.id)
        ).scalars().first()
        if order_item_ref is not None:
            return build(error=HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_409_CONFLICT,
                    error="Conflict",
                    message="Variant cannot be deleted because it is already referenced by order history."
                ).model_dump()
            ))

        variant_delete_info = InfoDeletePackTypeDto(
            type_id=variant.id,
            variant=variant.variant or variant.name
        )

        db.delete(variant)
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
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).model_dump()
        ))
