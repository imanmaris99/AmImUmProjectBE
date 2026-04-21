from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.pack_type_model import PackTypeModel
from app.models.product_model import ProductModel
from app.dtos.pack_type_dtos import PackTypeCreateDto, PackTypeInfoDto, PackTypeResponseCreateDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.pack_type_services.support_function import handle_db_error

from app.utils.result import build, Result


def create_type(
        db: Session, 
        pack_types: PackTypeCreateDto,
        admin_id: str
) -> Result[PackTypeModel, Exception]:
    try:
        product = db.query(ProductModel).filter(ProductModel.id == pack_types.product_id).first()
        if not product:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Product with ID {pack_types.product_id} not found"
                ).model_dump()
            ))

        pack_type_instance = PackTypeModel(
            **pack_types.model_dump(),
            fk_admin_id=admin_id
        )
        db.add(pack_type_instance)
        db.commit()
        db.refresh(pack_type_instance)

        pack_type_response = PackTypeInfoDto(
            id=pack_type_instance.id,
            img=pack_type_instance.img,
            product_id=pack_type_instance.product_id,
            product=pack_type_instance.product,
            name=pack_type_instance.name,
            min_amount=pack_type_instance.min_amount,
            variant=pack_type_instance.variant,
            expiration=pack_type_instance.expiration,
            stock=pack_type_instance.stock,
            price=float(pack_type_instance.base_price),
            discount=pack_type_instance.discount,
            discounted_price=float(pack_type_instance.discounted_price),
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
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).model_dump()
        ))
