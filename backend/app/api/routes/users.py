"""Authenticated user profile, onboarding, and home summary."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Exam, Note, PaperAttempt, User
from app.schemas import (
    ExamCatalogCreate,
    ExamCatalogItemResponse,
    ExamResponse,
    HomeActivityItem,
    HomeSummaryResponse,
    OnboardingExamsRequest,
    OnboardingProfileRequest,
    PaperQuotaResponse,
    PhoneAccountStatusResponse,
    UserPreferenceUpdate,
    UserResponse,
)
from app.services import catalog as catalog_service
from app.services import exams as exams_service
from app.services import papers as papers_service

router = APIRouter(tags=["users"])


def _user_response(user: User) -> UserResponse:
    return UserResponse.from_user(user)


@router.get("/auth/phone-status", response_model=PhoneAccountStatusResponse)
def phone_account_status(
    phone: str = Query(..., min_length=8, max_length=20),
    db: Session = Depends(get_db),
) -> PhoneAccountStatusResponse:
    """Public: whether this phone has a completed Examora account (for sign-in)."""
    normalized = phone.strip()
    user = db.scalars(select(User).where(User.phone == normalized).limit(1)).first()
    has_account = bool(user is not None and int(getattr(user, "onboarding_completed", 0) or 0) == 1)
    return PhoneAccountStatusResponse(has_account=has_account)


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.patch("/me/preferences", response_model=UserResponse)
def update_preferences(
    body: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    current_user.preferred_paper_language = body.preferred_paper_language
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)


@router.post("/me/onboarding/profile", response_model=UserResponse)
def save_onboarding_profile(
    body: OnboardingProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    current_user.full_name = body.full_name.strip()[:255]
    current_user.date_of_birth = body.date_of_birth
    current_user.preferred_paper_language = body.preferred_paper_language
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)


@router.post("/me/onboarding/exams", response_model=UserResponse)
def save_onboarding_exams(
    body: OnboardingExamsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    if not current_user.full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete profile (name) before selecting exams",
        )
    catalog_service.ensure_user_exams_from_catalog(
        db,
        user_id=current_user.id,
        catalog_ids=body.catalog_ids,
        custom_names=body.custom_names,
    )
    current_user.onboarding_completed = 1
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)


@router.get("/exam-catalog", response_model=list[ExamCatalogItemResponse])
def list_exam_catalog(
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExamCatalogItemResponse]:
    _ = current_user
    items = catalog_service.list_catalog(db, query=q)
    return [
        ExamCatalogItemResponse(
            id=i.id,
            name=i.name,
            badge=i.badge,
            is_popular=bool(i.is_popular),
        )
        for i in items
    ]


@router.post("/exam-catalog", response_model=ExamCatalogItemResponse, status_code=201)
def create_exam_catalog_item(
    body: ExamCatalogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExamCatalogItemResponse:
    item = catalog_service.add_catalog_item(
        db, user_id=current_user.id, name=body.name
    )
    return ExamCatalogItemResponse(
        id=item.id,
        name=item.name,
        badge=item.badge,
        is_popular=bool(item.is_popular),
    )


@router.get("/me/summary", response_model=HomeSummaryResponse)
def home_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HomeSummaryResponse:
    exams = exams_service.list_exams(db, user_id=current_user.id)
    from app.services import entity_ops

    exam_responses = [
        ExamResponse(
            id=e.id,
            name=e.name,
            created_at=e.created_at,
            batch_count=exams_service.batch_count(db, exam_id=e.id),
            badge=getattr(e, "badge", None),
            can_delete=entity_ops.exam_can_delete(db, exam_id=e.id),
        )
        for e in exams
    ]

    attempts = list(
        db.scalars(
            select(PaperAttempt)
            .where(PaperAttempt.user_id == current_user.id)
            .order_by(PaperAttempt.submitted_at.desc())
        ).all()
    )
    tests_taken = len(attempts)
    avg: int | None = None
    if attempts:
        avg = int(
            round(
                sum(
                    (a.correct_count / a.total_count) * 100
                    if a.total_count
                    else 0
                    for a in attempts
                )
                / tests_taken
            )
        )

    activity: list[HomeActivityItem] = []
    notes = list(
        db.scalars(
            select(Note)
            .where(Note.user_id == current_user.id)
            .order_by(Note.created_at.desc())
            .limit(3)
        ).all()
    )
    for n in notes:
        activity.append(
            HomeActivityItem(
                kind="upload",
                title=f"{n.title} uploaded",
                subtitle=None,
                at=n.created_at,
            )
        )
    for a in attempts[:5]:
        pct = (
            int(round((a.correct_count / a.total_count) * 100))
            if a.total_count
            else 0
        )
        activity.append(
            HomeActivityItem(
                kind="test",
                title=f"Practice test — {pct}%",
                subtitle=None,
                at=a.submitted_at,
            )
        )
    activity.sort(key=lambda x: x.at, reverse=True)
    activity = activity[:3]

    quota = papers_service.paper_quota_for_user(db, user=current_user)

    return HomeSummaryResponse(
        full_name=current_user.full_name,
        exams_count=len(exams),
        tests_taken=tests_taken,
        avg_score_percent=avg,
        exams=exam_responses,
        recent_activity=activity,
        paper_quota=PaperQuotaResponse(**quota),
    )
