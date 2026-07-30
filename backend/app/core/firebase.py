"""Firebase Admin initialization and ID token verification."""

from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, status

from app.core.config import settings


def init_firebase() -> None:
    """Initialize the Firebase Admin SDK once per process."""
    if firebase_admin._apps:
        return

    cred_path = Path(settings.FIREBASE_CREDENTIALS_PATH)
    if not cred_path.is_file():
        raise RuntimeError(
            f"Firebase credentials not found at '{cred_path.resolve()}'. "
            "Download a service account key from Firebase Console → Project settings → "
            "Service accounts, save it as backend/firebase-service-account.json, "
            "and set FIREBASE_CREDENTIALS_PATH if needed."
        )

    credential = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(
        credential,
        options={"projectId": settings.FIREBASE_PROJECT_ID},
    )


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return its decoded claims."""
    try:
        return auth.verify_id_token(id_token)
    except Exception as exc:  # noqa: BLE001 - Firebase raises many auth errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
