"""
Unit tests for FinTrack API.
Run with: pytest tests/ -v
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

# Use an in-memory SQLite DB for tests
TEST_DB_URL = "sqlite:///./test_fintrack.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("test_fintrack.db"):
        os.remove("test_fintrack.db")


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def admin_token(client):
    # Register an admin via direct user creation
    resp = client.post("/api/auth/register", json={
        "username": "testadmin",
        "email": "testadmin@example.com",
        "full_name": "Test Admin",
        "password": "admin123",
    })
    # Manually promote to admin via DB
    db = TestingSessionLocal()
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.username == "testadmin").first()
    user.role = UserRole.ADMIN
    db.commit()
    db.close()

    resp = client.post("/api/auth/login", json={"username": "testadmin", "password": "admin123"})
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def viewer_token(client):
    client.post("/api/auth/register", json={
        "username": "testviewer",
        "email": "testviewer@example.com",
        "full_name": "Test Viewer",
        "password": "viewer123",
    })
    resp = client.post("/api/auth/login", json={"username": "testviewer", "password": "viewer123"})
    return resp.json()["access_token"]


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser99",
            "email": "newuser99@example.com",
            "full_name": "New User",
            "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "viewer"
        assert data["username"] == "newuser99"

    def test_register_duplicate_username(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "testadmin",
            "email": "other@example.com",
            "full_name": "Dupe",
            "password": "password123",
        })
        assert resp.status_code == 400

    def test_register_weak_password(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "weakpwd",
            "email": "weak@example.com",
            "full_name": "Weak",
            "password": "abc",
        })
        assert resp.status_code == 422

    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={"username": "testadmin", "password": "admin123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={"username": "testadmin", "password": "wrong"})
        assert resp.status_code == 401

    def test_me_authenticated(self, client, admin_token):
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "testadmin"

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 403


# ─── Transaction Tests ────────────────────────────────────────────────────────

class TestTransactions:
    def test_create_transaction_as_admin(self, client, admin_token):
        resp = client.post(
            "/api/transactions/",
            json={"amount": 1500.00, "type": "income", "category": "Salary", "date": str(date.today())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["amount"] == 1500.0

    def test_create_transaction_as_viewer_forbidden(self, client, viewer_token):
        resp = client.post(
            "/api/transactions/",
            json={"amount": 100.0, "type": "expense", "category": "Food", "date": str(date.today())},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    def test_create_transaction_negative_amount(self, client, admin_token):
        resp = client.post(
            "/api/transactions/",
            json={"amount": -50.0, "type": "expense", "category": "Food", "date": str(date.today())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_create_transaction_invalid_category(self, client, admin_token):
        resp = client.post(
            "/api/transactions/",
            json={"amount": 100.0, "type": "expense", "category": "NonExistent", "date": str(date.today())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_list_transactions(self, client, admin_token):
        resp = client.get("/api/transactions/", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1

    def test_list_transactions_filter_by_type(self, client, admin_token):
        resp = client.get("/api/transactions/?type=income", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["type"] == "income"

    def test_viewer_can_list_transactions(self, client, viewer_token):
        resp = client.get("/api/transactions/", headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 200

    def test_get_transaction_by_id(self, client, admin_token):
        # Create one first
        create = client.post(
            "/api/transactions/",
            json={"amount": 200.0, "type": "expense", "category": "Food", "date": str(date.today())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        txn_id = create.json()["id"]
        resp = client.get(f"/api/transactions/{txn_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == txn_id

    def test_update_transaction(self, client, admin_token):
        create = client.post(
            "/api/transactions/",
            json={"amount": 300.0, "type": "expense", "category": "Food", "date": str(date.today())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        txn_id = create.json()["id"]
        resp = client.patch(
            f"/api/transactions/{txn_id}",
            json={"amount": 350.0, "notes": "Updated note"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 350.0

    def test_delete_transaction(self, client, admin_token):
        create = client.post(
            "/api/transactions/",
            json={"amount": 50.0, "type": "expense", "category": "Food", "date": str(date.today())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        txn_id = create.json()["id"]
        resp = client.delete(f"/api/transactions/{txn_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 204
        # Confirm it's gone
        get = client.get(f"/api/transactions/{txn_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert get.status_code == 404


# ─── Analytics Tests ──────────────────────────────────────────────────────────

class TestAnalytics:
    def test_summary_viewer(self, client, viewer_token):
        resp = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "balance" in data

    def test_categories_viewer_forbidden(self, client, viewer_token):
        resp = client.get("/api/analytics/categories?type=income", headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403

    def test_categories_admin(self, client, admin_token):
        resp = client.get("/api/analytics/categories?type=income", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200

    def test_monthly_totals(self, client, admin_token):
        resp = client.get("/api/analytics/monthly?months=3", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_full_analytics(self, client, admin_token):
        resp = client.get("/api/analytics/full", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "monthly_totals" in data
        assert "income_by_category" in data
