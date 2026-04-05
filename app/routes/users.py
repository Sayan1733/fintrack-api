from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import create_user, get_user, list_users, update_user, delete_user

router = APIRouter()


@router.get("/", response_model=List[UserResponse], summary="List all users (admin only)")
def get_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list_users(db)


@router.post("/", response_model=UserResponse, status_code=201, summary="Create a user with any role (admin only)")
def create_user_admin(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return create_user(db, data)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (admin only)")
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user (admin only)")
def update_user_by_id(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return update_user(db, user, data)


@router.delete("/{user_id}", status_code=204, summary="Delete user (admin only)")
def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(db, user)
