from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.payment_model import PaymentModel
from app.models.order_model import OrderModel
from app.dtos import payment_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.services.cart_services.support_function import handle_db_error
from app.utils.result import build, Result


ADMIN_PAYMENT_LIST_MESSAGE = "Admin payment list accessed successfully"
ADMIN_PAYMENT_DETAIL_MESSAGE = "Admin payment detail accessed successfully"


def _build_payment_item(payment: PaymentModel) -> payment_dtos.AdminPaymentInfoDto:
    order: OrderModel | None = payment.order
    return payment_dtos.AdminPaymentInfoDto(
        id=payment.id,
        order_id=payment.order_id,
        transaction_id=payment.transaction_id,
        payment_type=payment.payment_type,
        gross_amount=float(payment.gross_amount or 0.0),
        transaction_status=getattr(payment.transaction_status, "value", payment.transaction_status),
        fraud_status=getattr(payment.fraud_status, "value", payment.fraud_status) if payment.fraud_status else None,
        customer_name=order.customer_name if order else "",
        customer_email=order.customer_email if order else "",
        order_status=order.status if order else None,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def list_all_payments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    transaction_status_filter: str | None = None,
) -> Result[payment_dtos.AdminPaymentListResponseDto, Exception]:
    try:
        stmt = select(PaymentModel)

        if transaction_status_filter:
            stmt = stmt.where(PaymentModel.transaction_status == transaction_status_filter)

        payment_models = db.execute(
            stmt.order_by(PaymentModel.created_at.desc()).offset(skip).limit(limit)
        ).scalars().all()

        payment_items = [_build_payment_item(payment) for payment in payment_models]

        return build(data=payment_dtos.AdminPaymentListResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_PAYMENT_LIST_MESSAGE,
            data=payment_items,
            meta=payment_dtos.AdminListMetaDto(
                skip=skip,
                limit=limit,
                count=len(payment_items),
            ),
        ))

    except (IntegrityError, DataError) as db_error:
        return build(error=handle_db_error(db, db_error))
    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))
    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)
    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))


def get_payment_detail_by_order_id(
    db: Session,
    order_id: str,
) -> Result[payment_dtos.AdminPaymentDetailResponseDto, Exception]:
    try:
        payment = db.execute(
            select(PaymentModel).where(PaymentModel.order_id == order_id)
        ).scalars().first()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Payment for order ID {order_id} not found."
                ).dict()
            )

        payment_detail = payment_dtos.AdminPaymentDetailDto(
            **_build_payment_item(payment).dict(),
            payment_response=payment.payment_response,
        )

        return build(data=payment_dtos.AdminPaymentDetailResponseDto(
            status_code=status.HTTP_200_OK,
            message=ADMIN_PAYMENT_DETAIL_MESSAGE,
            data=payment_detail,
        ))

    except (IntegrityError, DataError) as db_error:
        return build(error=handle_db_error(db, db_error))
    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))
    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)
    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))
