from datetime import date
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, require_any_role
from app.models.transaction import TransactionType
from app.models.user import User, UserRole
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate,
    TransactionResponse, TransactionListResponse,
)
from app.services.transaction_service import (
    create_transaction, get_transaction,
    list_transactions, update_transaction, delete_transaction,
)

router = APIRouter()


@router.get(
    "/",
    response_model=TransactionListResponse,
    summary="List transactions with optional filters and pagination",
)
def get_transactions(
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    date_from: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be before date_to")

    items, total = list_transactions(
        db, current_user, type, category, date_from, date_to, page, page_size
    )
    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=201,
    summary="Create a new transaction (admin only)",
)
def add_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return create_transaction(db, data, current_user)


@router.get(
    "/{txn_id}",
    response_model=TransactionResponse,
    summary="Get a single transaction by ID",
)
def get_one_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    txn = get_transaction(db, txn_id, current_user)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.patch(
    "/{txn_id}",
    response_model=TransactionResponse,
    summary="Update a transaction (admin only)",
)
def edit_transaction(
    txn_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    txn = get_transaction(db, txn_id, current_user)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return update_transaction(db, txn, data)


@router.delete(
    "/{txn_id}",
    status_code=204,
    summary="Delete a transaction (admin only)",
)
def remove_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    txn = get_transaction(db, txn_id, current_user)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    delete_transaction(db, txn)
