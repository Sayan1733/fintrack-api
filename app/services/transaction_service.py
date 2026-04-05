from datetime import date
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def create_transaction(db: Session, data: TransactionCreate, user: User) -> Transaction:
    txn = Transaction(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
        user_id=user.id,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_transaction(db: Session, txn_id: int, user: User) -> Optional[Transaction]:
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        return None
    # Non-admins can only see their own transactions
    if user.role != UserRole.ADMIN and txn.user_id != user.id:
        return None
    return txn


def list_transactions(
    db: Session,
    user: User,
    txn_type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Transaction], int]:
    query = db.query(Transaction)

    # Role-based filtering: non-admin users see only their own records
    if user.role != UserRole.ADMIN:
        query = query.filter(Transaction.user_id == user.id)

    if txn_type:
        query = query.filter(Transaction.type == txn_type)
    if category:
        query = query.filter(Transaction.category == category)
    if date_from:
        query = query.filter(Transaction.date >= date_from)
    if date_to:
        query = query.filter(Transaction.date <= date_to)

    total = query.count()
    items = (
        query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_transaction(db: Session, txn: Transaction, data: TransactionUpdate) -> Transaction:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(txn, field, value)
    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, txn: Transaction) -> None:
    db.delete(txn)
    db.commit()
