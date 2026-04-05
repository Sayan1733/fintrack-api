from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_any_role, require_analyst_or_admin
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.analytics import SummaryResponse, AnalyticsResponse
from app.services.analytics_service import (
    get_summary, get_category_breakdown,
    get_monthly_totals, get_full_analytics,
)

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse, summary="Get financial summary (all roles)")
def summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    return get_summary(db, current_user, date_from, date_to)


@router.get("/categories", summary="Category-wise breakdown (analyst and admin)")
def category_breakdown(
    type: TransactionType = Query(..., description="income or expense"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return get_category_breakdown(db, current_user, type, date_from, date_to)


@router.get("/monthly", summary="Monthly income vs expense totals (analyst and admin)")
def monthly_totals(
    months: int = Query(6, ge=1, le=24, description="Number of recent months"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return get_monthly_totals(db, current_user, months)


@router.get("/full", response_model=AnalyticsResponse, summary="Full analytics dashboard (analyst and admin)")
def full_analytics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return get_full_analytics(db, current_user, date_from, date_to)
