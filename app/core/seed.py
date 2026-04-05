from datetime import date, timedelta
import random

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType


SEED_USERS = [
    {"username": "admin", "email": "admin@fintrack.io", "full_name": "Admin User", "role": UserRole.ADMIN, "password": "admin123"},
    {"username": "analyst", "email": "analyst@fintrack.io", "full_name": "Jane Analyst", "role": UserRole.ANALYST, "password": "analyst123"},
    {"username": "viewer", "email": "viewer@fintrack.io", "full_name": "Bob Viewer", "role": UserRole.VIEWER, "password": "viewer123"},
]

CATEGORIES = ["Salary", "Freelance", "Investment", "Food", "Rent", "Transport", "Entertainment", "Utilities", "Healthcare", "Shopping"]
INCOME_CATEGORIES = ["Salary", "Freelance", "Investment"]
EXPENSE_CATEGORIES = ["Food", "Rent", "Transport", "Entertainment", "Utilities", "Healthcare", "Shopping"]

SAMPLE_NOTES = {
    "Salary": "Monthly salary payment",
    "Freelance": "Freelance project payment",
    "Investment": "Dividend income",
    "Food": "Groceries and dining",
    "Rent": "Monthly rent",
    "Transport": "Fuel and commute",
    "Entertainment": "Movies, streaming, events",
    "Utilities": "Electricity, water, internet",
    "Healthcare": "Medical expenses",
    "Shopping": "Clothing and accessories",
}


def seed_database():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # Already seeded

        # Create users
        users = []
        for u in SEED_USERS:
            user = User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                hashed_password=hash_password(u["password"]),
            )
            db.add(user)
            users.append(user)
        db.flush()

        # Create 90 days of transactions for admin user
        admin = users[0]
        today = date.today()
        for i in range(90):
            txn_date = today - timedelta(days=i)

            # 1-2 income entries per week
            if i % 7 == 0:
                category = random.choice(INCOME_CATEGORIES)
                amount = round(random.uniform(800, 5000), 2)
                db.add(Transaction(
                    amount=amount,
                    type=TransactionType.INCOME,
                    category=category,
                    date=txn_date,
                    notes=SAMPLE_NOTES[category],
                    user_id=admin.id,
                ))

            # 1-3 expense entries per day
            for _ in range(random.randint(1, 3)):
                category = random.choice(EXPENSE_CATEGORIES)
                amount = round(random.uniform(10, 500), 2)
                db.add(Transaction(
                    amount=amount,
                    type=TransactionType.EXPENSE,
                    category=category,
                    date=txn_date,
                    notes=SAMPLE_NOTES[category],
                    user_id=admin.id,
                ))

        db.commit()
        print("Database seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seeding skipped or failed: {e}")
    finally:
        db.close()
