"""User upsert helpers."""

from sqlalchemy.orm import Session

from app.models import User


def upsert_user(db: Session, *, uid: str, phone: str) -> User:
    user = db.get(User, uid)
    if user is None:
        user = User(id=uid, phone=phone)
        db.add(user)
    elif user.phone != phone and phone:
        user.phone = phone
    db.commit()
    db.refresh(user)
    return user
