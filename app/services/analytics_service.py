from collections import defaultdict
from datetime import date
from typing import Optional
import calendar

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas.analytics import (
    SummaryResponse, CategoryBreakdown, MonthlyTotal, AnalyticsResponse
)


def _base_query(db: Session, user: User, date_from: Optional[date] = None, date_to: Optional[date] = None):
    query = db.query(Transaction)
    if user.role != UserRole.ADMIN:
        query = query.filter(Transaction.user_id == user.id)
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)
    return query


def get_summary(db: Session, user: User, date_from: Optional[date] = None, date_to: Optional[date] = None) -> SummaryResponse:
    query = _base_query(db, user, date_from, date_to)
    all_txns = query.all()

    incomes = [t.amount for t in all_txns if t.type == TransactionType.INCOME]
    expenses = [t.amount for t in all_txns if t.type == TransactionType.EXPENSE]

    total_income = round(sum(incomes), 2)
    total_expenses = round(sum(expenses), 2)

    return SummaryResponse(
        total_income=total_income,
        total_expenses=total_expenses,
        balance=round(total_income - total_expenses, 2),
        transaction_count=len(all_txns),
        income_count=len(incomes),
        expense_count=len(expenses),
        avg_income=round(total_income / len(incomes), 2) if incomes else 0.0,
        avg_expense=round(total_expenses / len(expenses), 2) if expenses else 0.0,
    )


def get_category_breakdown(db: Session, user: User, txn_type: TransactionType, date_from: Optional[date] = None, date_to: Optional[date] = None):
    query = _base_query(db, user, date_from, date_to).filter(Transaction.type == txn_type)
    txns = query.all()

    category_totals = defaultdict(lambda: {"total": 0.0, "count": 0})
    grand_total = 0.0

    for t in txns:
        category_totals[t.category]["total"] += t.amount
        category_totals[t.category]["count"] += 1
        grand_total += t.amount

    result = []
    for cat, data in sorted(category_totals.items(), key=lambda x: x[1]["total"], reverse=True):
        pct = round((data["total"] / grand_total * 100), 1) if grand_total else 0.0
        result.append(CategoryBreakdown(
            category=cat,
            total=round(data["total"], 2),
            count=data["count"],
            percentage=pct,
        ))
    return result


def get_monthly_totals(db: Session, user: User, months: int = 6) -> list:
    query = _base_query(db, user)
    txns = query.all()

    monthly = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for t in txns:
        key = (t.date.year, t.date.month)
        if t.type == TransactionType.INCOME:
            monthly[key]["income"] += t.amount
        else:
            monthly[key]["expenses"] += t.amount

    result = []
    for (year, month), data in sorted(monthly.items(), reverse=True)[:months]:
        result.append(MonthlyTotal(
            year=year,
            month=month,
            month_name=calendar.month_abbr[month],
            income=round(data["income"], 2),
            expenses=round(data["expenses"], 2),
            net=round(data["income"] - data["expenses"], 2),
        ))
    return sorted(result, key=lambda x: (x.year, x.month))


def get_full_analytics(db: Session, user: User, date_from: Optional[date] = None, date_to: Optional[date] = None) -> AnalyticsResponse:
    summary = get_summary(db, user, date_from, date_to)
    income_breakdown = get_category_breakdown(db, user, TransactionType.INCOME, date_from, date_to)
    expense_breakdown = get_category_breakdown(db, user, TransactionType.EXPENSE, date_from, date_to)
    monthly = get_monthly_totals(db, user)

    recent_query = _base_query(db, user, date_from, date_to)
    recent = recent_query.order_by(Transaction.date.desc()).limit(5).all()
    recent_list = [
        {"id": t.id, "amount": t.amount, "type": t.type, "category": t.category, "date": str(t.date), "notes": t.notes}
        for t in recent
    ]

    return AnalyticsResponse(
        summary=summary,
        income_by_category=income_breakdown,
        expenses_by_category=expense_breakdown,
        monthly_totals=monthly,
        recent_transactions=recent_list,
    )
