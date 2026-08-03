"""User upsert helpers."""

from sqlalchemy.orm import Session

from app.models import AccountType, User


def upsert_user(db: Session, *, uid: str, phone: str) -> User:
    user = db.get(User, uid)
    if user is None:
        user = User(id=uid, phone=phone, account_type=AccountType.USER.value)
        db.add(user)
    elif user.phone != phone and phone:
        user.phone = phone
    if not (user.account_type or "").strip():
        user.account_type = AccountType.USER.value
    db.commit()
    db.refresh(user)
    return user
