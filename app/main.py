from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import engine, Base
from app.routes import auth, transactions, analytics, users
from app.core.seed import seed_database

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinTrack API",
    description="A finance tracking system with role-based access control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.on_event("startup")
async def startup_event():
    seed_database()


@app.get("/", tags=["Health"])
def root():
    return {"message": "FinTrack API is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
