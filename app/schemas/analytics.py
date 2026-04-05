from typing import List, Dict, Optional
from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int
    percentage: float


class MonthlyTotal(BaseModel):
    year: int
    month: int
    month_name: str
    income: float
    expenses: float
    net: float


class SummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    transaction_count: int
    income_count: int
    expense_count: int
    avg_income: float
    avg_expense: float


class AnalyticsResponse(BaseModel):
    summary: SummaryResponse
    income_by_category: List[CategoryBreakdown]
    expenses_by_category: List[CategoryBreakdown]
    monthly_totals: List[MonthlyTotal]
    recent_transactions: List[dict]
