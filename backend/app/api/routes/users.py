"""Authenticated user endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import UserPreferenceUpdate, UserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the signed-in user (upserted from Firebase token claims)."""
    return current_user


@router.patch("/me/preferences", response_model=UserResponse)
def update_preferences(
    body: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    current_user.preferred_paper_language = body.preferred_paper_language
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
