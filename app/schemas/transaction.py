from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator

from app.models.transaction import TransactionType


VALID_CATEGORIES = {
    "income": ["Salary", "Freelance", "Investment", "Bonus", "Gift", "Other Income"],
    "expense": ["Food", "Rent", "Transport", "Entertainment", "Utilities",
                "Healthcare", "Shopping", "Education", "Travel", "Other Expense"],
}

ALL_CATEGORIES = VALID_CATEGORIES["income"] + VALID_CATEGORIES["expense"]


class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    category: str
    date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        if round(v, 2) != v:
            raise ValueError("Amount can have at most 2 decimal places")
        return v

    @field_validator("category")
    @classmethod
    def category_valid(cls, v):
        if v not in ALL_CATEGORIES:
            raise ValueError(f"Invalid category. Choose from: {ALL_CATEGORIES}")
        return v

    @field_validator("date")
    @classmethod
    def date_not_future(cls, v):
        if v > date.today():
            raise ValueError("Transaction date cannot be in the future")
        return v

    @field_validator("notes")
    @classmethod
    def notes_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("Notes cannot exceed 500 characters")
        return v


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @field_validator("category")
    @classmethod
    def category_valid(cls, v):
        if v is not None and v not in ALL_CATEGORIES:
            raise ValueError(f"Invalid category. Choose from: {ALL_CATEGORIES}")
        return v


class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: str
    date: date
    notes: Optional[str]
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
