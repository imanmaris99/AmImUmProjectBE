from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import TypeIdToUpdateDto, PackTypeEditInfoDto, PackTypeUpdatedInfoDto, PackTypeEditInfoResponseDto 
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args


def update_stock(
        db: Session, 
        type_id_update: TypeIdToUpdateDto,
        type_update: PackTypeEditInfoDto
        ) -> Result[PackTypeModel, Exception]:
    try:
        type_model = db.query(PackTypeModel).filter(PackTypeModel.id == type_id_update.type_id).first()
        if not type_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about variant product with ID {type_id_update.type_id} not found"
                ).model_dump()
            ))

        update_payload = type_update.model_dump(exclude_none=True)
        for attr, value in update_payload.items():
            setattr(type_model, attr, value)

        db.commit()
        db.refresh(type_model)

        response_data = PackTypeUpdatedInfoDto(
            id=type_model.id,
            product_id=type_model.product_id,
            product=type_model.product,
            name=type_model.name,
            img=type_model.img,
            variant=type_model.variant,
            expiration=type_model.expiration,
            stock=type_model.stock,
            price=float(type_model.base_price),
            discount=type_model.discount,
            discounted_price=float(type_model.discounted_price),
            updated_at=type_model.updated_at
        )

        return build(data=PackTypeEditInfoResponseDto(
            status_code=200,
            message="Edit stock and discount product has been success",
            data=response_data
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args('pack_types', str(e.args))}"
            ).model_dump()
        ))
    
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
            ).model_dump()
        ))
