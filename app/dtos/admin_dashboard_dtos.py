from pydantic import BaseModel, Field


class AdminDashboardSummaryDto(BaseModel):
    total_users: int = 0
    total_active_users: int = 0
    total_orders: int = 0
    total_pending_orders: int = 0
    total_paid_orders: int = 0
    total_pending_payments: int = 0
    total_settlement_payments: int = 0
    gross_revenue_paid_orders: float = 0.0


class AdminDashboardSummaryResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Admin dashboard summary accessed successfully")
    data: AdminDashboardSummaryDto
