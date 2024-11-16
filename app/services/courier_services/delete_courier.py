from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.courier_model import CourierModel
from app.dtos import courier_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result


def delete_courier(
        db: Session, 
        request_delete: courier_dtos.DeleteCourierDto,
        user_id: str
        ) -> Result[None, Exception]:
    try:
        courier_model = db.execute(
            select(CourierModel)
            .where(
                CourierModel.id == request_delete.courier_id,
                CourierModel.customer_id == user_id
            )  
        ).scalars().first()

        if not courier_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Courier data with ID : {request_delete.courier_id} not found"
                ).dict()
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        courier_delete_info = courier_dtos.DeleteInfoCourierDto(
            courier_id=courier_model.id,
            courier_name=courier_model.courier_name,
            service_type=courier_model.service_type,
            cost=courier_model.cost
        )

        db.delete(courier_model)
        db.commit()

        return build(data=courier_dtos.DeleteCourierResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Your data of Courier with ID {request_delete.courier_id} has been deleted",
            data=courier_delete_info
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
