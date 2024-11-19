
from typing import Type

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.courier_model import CourierModel
from app.dtos import courier_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result

def update_courier_data(
        db: Session, 
        courier_update: courier_dtos.CourierIdToUpdateDto,
        weight_data: courier_dtos.CourierCreateDto,
        user_id: str
        ) -> Result[Type[CourierModel], Exception]:
    try:
        courier_model = db.execute(
            select(CourierModel)
            .where(
                CourierModel.id == courier_update.courier_id,
                CourierModel.customer_id == user_id
            )  
        ).scalars().first()
        
        if not courier_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Data of Courier ID {courier_update.courier_id} in User ID {user_id} Not Found"
                ).dict()
            ))
        
        for attr, value in weight_data.model_dump().items():
            setattr(courier_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(courier_model)

        return build(data=courier_dtos.CourierResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Updated data Courier with ID {courier_update.courier_id} has been success",
            data=courier_dtos.CourierInfoDto(
                id=courier_model.id,
                courier_name=courier_model.courier_name,
                phone_number=courier_model.phone_number,
                service_type=courier_model.service_type,
                weight=courier_model.weight,
                length=courier_model.length,
                width=courier_model.width,
                height=courier_model.height,
                cost=courier_model.cost,
                estimated_delivery=courier_model.estimated_delivery,
                is_active=courier_model.is_active,
                created_at=courier_model.created_at
            )
        ))
    
    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args("productions", str(e.args))}"
            ).dict()
        ))
    
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
            ).dict()
        ))