from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_model import UserModel
from app.models.order_model import OrderModel
from app.models.payment_model import PaymentModel
from app.dtos import admin_dashboard_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.utils.result import build, Result


SUMMARY_MESSAGE = "Admin dashboard summary accessed successfully"


def get_admin_dashboard_summary(
    db: Session,
) -> Result[admin_dashboard_dtos.AdminDashboardSummaryResponseDto, Exception]:
    try:
        total_users = db.execute(select(func.count()).select_from(UserModel)).scalar() or 0
        total_active_users = db.execute(
            select(func.count()).select_from(UserModel).where(UserModel.is_active == True)
        ).scalar() or 0

        total_orders = db.execute(select(func.count()).select_from(OrderModel)).scalar() or 0
        total_pending_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "pending")
        ).scalar() or 0
        total_paid_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "paid")
        ).scalar() or 0
        total_processing_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "processing")
        ).scalar() or 0
        total_shipped_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "shipped")
        ).scalar() or 0
        total_completed_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "completed")
        ).scalar() or 0
        total_cancelled_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "cancelled")
        ).scalar() or 0
        total_failed_orders = db.execute(
            select(func.count()).select_from(OrderModel).where(OrderModel.status == "failed")
        ).scalar() or 0

        total_pending_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "pending")
        ).scalar() or 0
        total_settlement_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "settlement")
        ).scalar() or 0
        total_expire_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "expire")
        ).scalar() or 0
        total_cancel_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "cancel")
        ).scalar() or 0
        total_deny_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "deny")
        ).scalar() or 0
        total_refund_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "refund")
        ).scalar() or 0
        total_capture_payments = db.execute(
            select(func.count()).select_from(PaymentModel).where(PaymentModel.transaction_status == "capture")
        ).scalar() or 0

        gross_revenue_paid_orders = db.execute(
            select(func.coalesce(func.sum(OrderModel.total_price), 0)).where(OrderModel.status == "paid")
        ).scalar() or 0

        return build(data=admin_dashboard_dtos.AdminDashboardSummaryResponseDto(
            status_code=status.HTTP_200_OK,
            message=SUMMARY_MESSAGE,
            data=admin_dashboard_dtos.AdminDashboardSummaryDto(
                total_users=int(total_users),
                total_active_users=int(total_active_users),
                total_orders=int(total_orders),
                total_pending_orders=int(total_pending_orders),
                total_paid_orders=int(total_paid_orders),
                total_processing_orders=int(total_processing_orders),
                total_shipped_orders=int(total_shipped_orders),
                total_completed_orders=int(total_completed_orders),
                total_cancelled_orders=int(total_cancelled_orders),
                total_failed_orders=int(total_failed_orders),
                total_pending_payments=int(total_pending_payments),
                total_settlement_payments=int(total_settlement_payments),
                total_expire_payments=int(total_expire_payments),
                total_cancel_payments=int(total_cancel_payments),
                total_deny_payments=int(total_deny_payments),
                total_refund_payments=int(total_refund_payments),
                total_capture_payments=int(total_capture_payments),
                gross_revenue_paid_orders=float(gross_revenue_paid_orders or 0.0),
            )
        ))

    except SQLAlchemyError as e:
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database error occurred while fetching dashboard summary. {str(e)}"
            ).dict()
        ))
