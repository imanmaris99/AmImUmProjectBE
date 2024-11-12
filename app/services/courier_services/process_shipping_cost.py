from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.courier_model import CourierModel
from app.dtos import courier_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.utils.result import build, Result

# Fungsi untuk memproses ongkos kirim dan menyimpannya ke database
def process_shipping_cost(
        request_data: courier_dtos.CourierCreateDto, 
        user_id:str,
        db: Session
        ) -> Result[courier_dtos.CourierResponseDto, Exception]:
    try:

        # courier = CourierModel(**request_data.model_dump().where(CourierModel.customer_id==user_id))
        courier = CourierModel(
            courier_name=request_data.courier_name,
            weight=request_data.weight,
            length=request_data.length,
            width=request_data.width,
            height=request_data.height,
            customer_id=user_id,
            is_active=True
        )

        db.add(courier)
        db.commit()
        db.refresh(courier)

        # Buat DTO response
        courier_response = courier_dtos.CourierInfoDto(
            id=courier.id,
            courier_name=courier.courier_name,
            phone_number=courier.phone_number,
            service_type=courier.service_type,
            weight=courier.weight,
            length=courier.length,
            width=courier.width,
            height=courier.height,
            cost=courier.cost,
            estimated_delivery=courier.estimated_delivery,
            is_active=courier.is_active,
            created_at=courier.created_at
        )

        return build(data=courier_dtos.CourierResponseDto(
            status_code=201,
            message="Your courier choice has been saved in db",
            data=courier_response
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"            
            ).dict()
        ))
