from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserResponse
from app.services.user_service import create_user
from app.schemas.user import UserCreate

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Login and get access token")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=UserResponse, status_code=201, summary="Register a new user (viewer role)")
def register(data: UserCreate, db: Session = Depends(get_db)):
    # Self-registration is always viewer role
    data.role = "viewer"
    return create_user(db, data)


@router.get("/me", response_model=UserResponse, summary="Get current user info")
def me(current_user: User = Depends(get_current_user)):
    return current_user
