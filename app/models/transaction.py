import enum
from datetime import date, datetime

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction id={self.id} type={self.type} amount={self.amount} category={self.category}>"
