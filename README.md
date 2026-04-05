# FinTrack API

A production-ready **FastAPI** finance tracking system with JWT authentication, role-based access control, analytical summaries, and a clean layered architecture.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Roles & Permissions](#roles--permissions)
- [Setup & Running](#setup--running)
- [API Reference](#api-reference)
- [Seed Data / Demo Accounts](#seed-data--demo-accounts)
- [Running Tests](#running-tests)
- [Design Decisions & Assumptions](#design-decisions--assumptions)

---

## Features

- **Full CRUD** for financial transactions (income & expense)
- **JWT authentication** — Bearer token via `/api/auth/login`
- **Role-based access control** — Viewer, Analyst, Admin with enforced route guards
- **Filtering** by type, category, and date range
- **Pagination** on all list endpoints
- **Analytics** — summary, category breakdown, monthly totals, full dashboard
- **Input validation** with descriptive error messages and correct HTTP status codes
- **Seed data** — auto-seeded on startup with 90 days of realistic transactions
- **Unit tests** — 24 tests covering auth, CRUD, filters, role restrictions, edge cases

---

## Architecture

The project follows a clean **layered architecture**:

```
Request → Route (FastAPI router)
             ↓
          Service (business logic)
             ↓
          Model (SQLAlchemy ORM)
             ↓
          Database (SQLite / PostgreSQL)
```

- **Routes** handle HTTP concerns: parsing, validation, status codes, dependency injection
- **Services** contain all business logic: filtering, aggregation, role checks on data
- **Models** define the DB schema with SQLAlchemy ORM
- **Schemas** (Pydantic) handle serialization and input validation separately from models
- **Core** contains shared utilities: database session, security helpers, config, seeding

---

## Tech Stack

| Component     | Choice              | Reason                                          |
|---------------|---------------------|-------------------------------------------------|
| Framework     | FastAPI             | Fast, async-ready, auto docs, Pydantic native   |
| ORM           | SQLAlchemy 2.x      | Mature, flexible, works with any DB             |
| Database      | SQLite (default)    | Zero-setup for dev; swap URL for PostgreSQL     |
| Auth          | JWT via python-jose | Stateless, standard, easy to verify             |
| Passwords     | bcrypt via passlib  | Industry-standard secure hashing                |
| Validation    | Pydantic v2         | Fast, declarative, great error messages         |
| Tests         | pytest + httpx      | Clean fixtures, TestClient for end-to-end       |

---

## Project Structure

```
fintrack/
├── app/
│   ├── main.py                  # FastAPI app, router registration, startup
│   ├── core/
│   │   ├── config.py            # Settings via pydantic-settings (.env support)
│   │   ├── database.py          # SQLAlchemy engine, session factory, get_db
│   │   ├── security.py          # JWT, password hashing, role dependency guards
│   │   └── seed.py              # Auto-seed users and 90 days of transactions
│   ├── models/
│   │   ├── user.py              # User ORM model + UserRole enum
│   │   └── transaction.py       # Transaction ORM model + TransactionType enum
│   ├── schemas/
│   │   ├── user.py              # Pydantic schemas for user I/O
│   │   ├── transaction.py       # Pydantic schemas for transaction I/O
│   │   └── analytics.py         # Pydantic schemas for analytics responses
│   ├── services/
│   │   ├── transaction_service.py  # CRUD + filtering logic
│   │   ├── analytics_service.py    # Summary, category breakdown, monthly totals
│   │   └── user_service.py         # User CRUD
│   └── routes/
│       ├── auth.py              # Login, register, /me
│       ├── users.py             # Admin user management
│       ├── transactions.py      # Transaction CRUD endpoints
│       └── analytics.py        # Analytics endpoints
├── tests/
│   └── test_api.py              # 24 unit/integration tests
├── requirements.txt
├── .env.example
└── README.md
```

---

## Roles & Permissions

| Action                          | Viewer | Analyst | Admin |
|---------------------------------|--------|---------|-------|
| Login / Register                | ✅     | ✅      | ✅    |
| View own transactions (list)    | ✅     | ✅      | ✅    |
| View all transactions (list)    | ❌     | ❌      | ✅    |
| Create / Update / Delete txns   | ❌     | ❌      | ✅    |
| View financial summary          | ✅     | ✅      | ✅    |
| Category breakdown & monthly    | ❌     | ✅      | ✅    |
| Full analytics dashboard        | ❌     | ✅      | ✅    |
| Manage users (CRUD)             | ❌     | ❌      | ✅    |

---

## Setup & Running

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd fintrack
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env to change DATABASE_URL or SECRET_KEY
```

To use **PostgreSQL** instead of SQLite, set:
```
DATABASE_URL=postgresql://user:password@localhost:5432/fintrack
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The database is auto-created and seeded on first startup.

---

## API Reference

### Authentication

| Method | Endpoint              | Description                    | Auth Required |
|--------|-----------------------|--------------------------------|---------------|
| POST   | `/api/auth/login`     | Login, returns JWT token       | No            |
| POST   | `/api/auth/register`  | Register (viewer role)         | No            |
| GET    | `/api/auth/me`        | Get current user profile       | Yes           |

### Transactions

| Method | Endpoint                    | Description                          | Min Role |
|--------|-----------------------------|--------------------------------------|----------|
| GET    | `/api/transactions/`        | List transactions (paginated)        | Viewer   |
| POST   | `/api/transactions/`        | Create transaction                   | Admin    |
| GET    | `/api/transactions/{id}`    | Get single transaction               | Viewer   |
| PATCH  | `/api/transactions/{id}`    | Update transaction                   | Admin    |
| DELETE | `/api/transactions/{id}`    | Delete transaction                   | Admin    |

**Query parameters for GET /api/transactions/:**
- `type` — `income` or `expense`
- `category` — e.g. `Salary`, `Food`
- `date_from` — `YYYY-MM-DD`
- `date_to` — `YYYY-MM-DD`
- `page` — default `1`
- `page_size` — default `20`, max `100`

### Analytics

| Method | Endpoint                    | Description                          | Min Role |
|--------|-----------------------------|--------------------------------------|----------|
| GET    | `/api/analytics/summary`    | Total income, expenses, balance      | Viewer   |
| GET    | `/api/analytics/categories` | Category breakdown by type           | Analyst  |
| GET    | `/api/analytics/monthly`    | Monthly income vs expense            | Analyst  |
| GET    | `/api/analytics/full`       | Full dashboard analytics             | Analyst  |

### Users (Admin only)

| Method | Endpoint           | Description         |
|--------|--------------------|---------------------|
| GET    | `/api/users/`      | List all users      |
| POST   | `/api/users/`      | Create user         |
| GET    | `/api/users/{id}`  | Get user by ID      |
| PATCH  | `/api/users/{id}`  | Update user         |
| DELETE | `/api/users/{id}`  | Delete user         |

---

## Seed Data / Demo Accounts

On first startup, the database is populated automatically:

| Username   | Password     | Role     |
|------------|--------------|----------|
| `admin`    | `admin123`   | Admin    |
| `analyst`  | `analyst123` | Analyst  |
| `viewer`   | `viewer123`  | Viewer   |

The `admin` account comes with ~200 transactions spread across 90 days, covering all income and expense categories — ideal for testing filters and analytics.

### Quick test via curl:

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Get summary
curl http://localhost:8000/api/analytics/summary \
  -H "Authorization: Bearer $TOKEN"

# List transactions with filter
curl "http://localhost:8000/api/transactions/?type=expense&category=Food&page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN"

# Full analytics
curl http://localhost:8000/api/analytics/full \
  -H "Authorization: Bearer $TOKEN"
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use an isolated in-memory SQLite database and cover:
- Auth: register, login, token validation, duplicate checks
- Transactions: CRUD, filters, pagination, role enforcement
- Validation: negative amounts, invalid categories, future dates
- Analytics: summary, categories, monthly, full dashboard
- Role access: viewer/analyst/admin restrictions

---

## Design Decisions & Assumptions

**Role assignment on register:** Self-registration always creates a `viewer`. Only admins can create `analyst` or `admin` accounts via `POST /api/users/`.

**Transaction ownership:** Viewers and Analysts see only their own transactions. Admins see all. This is enforced in the service layer, not just the route layer.

**Validation at the schema level:** All input validation (amount > 0, valid category list, date not in future, password length) happens in Pydantic schemas so the service layer always receives clean data.

**Categories are enumerated:** A fixed list of valid categories is enforced. This prevents data inconsistency in analytics groupings. The list can be easily extended in `schemas/transaction.py`.

**SQLite for simplicity, PostgreSQL-ready:** The `DATABASE_URL` env var is the only change needed to switch. SQLAlchemy abstracts everything else.

**No soft deletes:** Hard deletes are used for simplicity. If audit history is needed, a `deleted_at` timestamp column can be added to the model.

**UTC timestamps:** All `created_at` / `updated_at` fields store UTC. Timezone conversion is left to the client or a future middleware layer.
