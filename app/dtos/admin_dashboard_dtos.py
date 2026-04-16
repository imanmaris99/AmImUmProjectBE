from pydantic import BaseModel, Field


class AdminDashboardSummaryDto(BaseModel):
    total_users: int = 0
    total_active_users: int = 0
    total_orders: int = 0
    total_pending_orders: int = 0
    total_paid_orders: int = 0
    total_processing_orders: int = 0
    total_shipped_orders: int = 0
    total_completed_orders: int = 0
    total_cancelled_orders: int = 0
    total_failed_orders: int = 0
    total_pending_payments: int = 0
    total_settlement_payments: int = 0
    total_expire_payments: int = 0
    total_cancel_payments: int = 0
    total_deny_payments: int = 0
    total_refund_payments: int = 0
    total_capture_payments: int = 0
    gross_revenue_paid_orders: float = 0.0


class AdminDashboardSummaryResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Admin dashboard summary accessed successfully")
    data: AdminDashboardSummaryDto
