"""SQLAlchemy domain models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NoteStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class PaperStatus(str, Enum):
    READY = "ready"
    FAILED = "failed"


class AccountType(str, Enum):
    """Per-account limit tier — selects *_ADMIN / *_DEV / *_TESTER env overrides."""

    ADMIN = "ADMIN"
    DEV = "DEV"
    TESTER = "TESTER"
    USER = "USER"


class User(Base):
    """App user keyed by Firebase Auth UID."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )  # YYYY-MM-DD
    preferred_paper_language: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
    )
    account_type: Mapped[str] = mapped_column(
        String(16),
        default=AccountType.USER.value,
        nullable=False,
    )
    onboarding_completed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )  # 0/1 for SQLite ease
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ExamCatalogItem(Base):
    """Shared exam names students can pick (popular + user-added)."""

    __tablename__ = "exam_catalog"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    badge: Mapped[str] = mapped_column(String(32), nullable=False)
    is_popular: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Exam(Base):
    """User exam they are preparing for (multi-exam supported)."""

    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    catalog_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("exam_catalog.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class BatchFolder(Base):
    """Upload batch inside an exam (e.g. 'a', 'Week 1'). 20-page create limit applies here."""

    __tablename__ = "batch_folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    exam_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("exams.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Note(Base):
    """Uploaded study notes PDF owned by a user."""

    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    batch_folder_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("batch_folders.id"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=NoteStatus.UPLOADED.value,
        nullable=False,
    )
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Question(Base):
    """Per-student MCQ pool item (not a global shared bank)."""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    note_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notes.id"),
        index=True,
        nullable=False,
    )
    variant_group_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-3
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_asked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ask_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class QuestionPaper(Base):
    """Generated practice paper for a user from a note or batch."""

    __tablename__ = "question_papers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    note_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("notes.id"),
        index=True,
        nullable=True,
    )
    batch_folder_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("batch_folders.id"),
        index=True,
        nullable=True,
    )
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=PaperStatus.READY.value,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class PaperQuestion(Base):
    """Join: which pool questions appear on a paper, in order."""

    __tablename__ = "paper_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("question_papers.id"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("questions.id"),
        index=True,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)


class PaperBatchLink(Base):
    """Topics (batches) included in a practice paper — supports multi-topic papers."""

    __tablename__ = "paper_batch_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("question_papers.id"),
        index=True,
        nullable=False,
    )
    batch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("batch_folders.id"),
        index=True,
        nullable=False,
    )


class PaperAttempt(Base):
    """One submitted attempt of a practice paper."""

    __tablename__ = "paper_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("question_papers.id"),
        index=True,
        nullable=False,
    )
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AttemptAnswer(Base):
    """Selected option for one question on an attempt."""

    __tablename__ = "attempt_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("paper_attempts.id"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("questions.id"),
        index=True,
        nullable=False,
    )
    selected_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-3
    is_correct: Mapped[int] = mapped_column(Integer, nullable=False)  # 0/1 for SQLite ease
