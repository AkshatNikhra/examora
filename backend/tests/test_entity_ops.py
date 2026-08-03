"""Delete / rename rules + rolling paper quota window."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models import Note, NoteStatus, PaperStatus, QuestionPaper


def _auth(
    monkeypatch: pytest.MonkeyPatch,
    uid: str = "user-ops-1",
    phone: str = "+919700099001",
) -> None:
    monkeypatch.setattr(
        "app.core.deps.verify_firebase_token",
        lambda _token: {"uid": uid, "phone_number": phone},
    )


def _mock_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.notes.upload_pdf",
        lambda **kwargs: kwargs["key"],
    )
    monkeypatch.setattr(
        "app.services.entity_ops.delete_pdf",
        lambda **kwargs: None,
    )


def test_rename_exam_topic_note_paper(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch)
    _mock_upload(monkeypatch)

    headers = {"Authorization": "Bearer t"}
    exam = client.post("/exams", headers=headers, json={"name": "Old Exam"}).json()
    batch = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "Old Topic"},
    ).json()
    note = client.post(
        "/notes",
        headers=headers,
        files={"file": ("n.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Old Note", "batch_folder_id": batch["id"]},
    ).json()

    renamed_exam = client.patch(
        f"/exams/{exam['id']}", headers=headers, json={"name": "New Exam"}
    )
    assert renamed_exam.status_code == 200
    assert renamed_exam.json()["name"] == "New Exam"

    renamed_batch = client.patch(
        f"/batches/{batch['id']}", headers=headers, json={"name": "New Topic"}
    )
    assert renamed_batch.status_code == 200
    assert renamed_batch.json()["name"] == "New Topic"

    renamed_note = client.patch(
        f"/notes/{note['id']}", headers=headers, json={"title": "New Note"}
    )
    assert renamed_note.status_code == 200
    assert renamed_note.json()["title"] == "New Note"

    # Insert a paper row directly and rename it.
    db = SessionLocal()
    try:
        paper = QuestionPaper(
            id="paper-rename-1",
            user_id="user-ops-1",
            note_id=note["id"],
            batch_folder_id=batch["id"],
            language="en",
            status=PaperStatus.READY.value,
            title="Auto Title",
            question_count=5,
        )
        db.add(paper)
        db.commit()
    finally:
        db.close()

    renamed_paper = client.patch(
        "/papers/paper-rename-1",
        headers=headers,
        json={"title": "My Preferred Name"},
    )
    assert renamed_paper.status_code == 200
    assert renamed_paper.json()["title"] == "My Preferred Name"


def test_delete_rules_for_note_topic_exam(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch, uid="user-ops-2", phone="+919700099002")
    _mock_upload(monkeypatch)
    headers = {"Authorization": "Bearer t"}

    exam = client.post("/exams", headers=headers, json={"name": "E"}).json()
    assert exam["can_delete"] is True

    # Empty exam can be deleted.
    empty = client.post("/exams", headers=headers, json={"name": "Empty"}).json()
    deleted = client.delete(f"/exams/{empty['id']}", headers=headers)
    assert deleted.status_code == 204

    batch = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "T"},
    ).json()
    assert batch["can_delete"] is True

    uploaded = client.post(
        "/notes",
        headers=headers,
        files={"file": ("n.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "U", "batch_folder_id": batch["id"]},
    ).json()
    assert uploaded["can_delete"] is True
    assert uploaded["status"] == "uploaded"

    # Uploaded note can be deleted.
    assert client.delete(f"/notes/{uploaded['id']}", headers=headers).status_code == 204

    ready_upload = client.post(
        "/notes",
        headers=headers,
        files={"file": ("r.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "R", "batch_folder_id": batch["id"]},
    ).json()
    db = SessionLocal()
    try:
        note = db.get(Note, ready_upload["id"])
        assert note is not None
        note.status = NoteStatus.READY.value
        note.canonical_content_en = "Some content"
        db.commit()
    finally:
        db.close()

    ready = client.get(f"/notes/{ready_upload['id']}", headers=headers).json()
    assert ready["can_delete"] is False
    assert client.delete(f"/notes/{ready['id']}", headers=headers).status_code == 409

    # Topic / exam blocked while Ready note exists.
    assert client.get(f"/batches/{batch['id']}", headers=headers).json()["can_delete"] is False
    assert client.delete(f"/batches/{batch['id']}", headers=headers).status_code == 409
    assert client.get(f"/exams/{exam['id']}", headers=headers).json()["can_delete"] is False
    assert client.delete(f"/exams/{exam['id']}", headers=headers).status_code == 409


def test_delete_topic_and_exam_without_ready_notes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _auth(monkeypatch, uid="user-ops-3", phone="+919700099003")
    _mock_upload(monkeypatch)
    headers = {"Authorization": "Bearer t"}

    exam = client.post("/exams", headers=headers, json={"name": "E2"}).json()
    batch = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "T2"},
    ).json()
    note = client.post(
        "/notes",
        headers=headers,
        files={"file": ("f.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Failedish", "batch_folder_id": batch["id"]},
    ).json()
    db = SessionLocal()
    try:
        row = db.get(Note, note["id"])
        assert row is not None
        row.status = NoteStatus.FAILED.value
        row.error_message = "ocr failed"
        db.commit()
    finally:
        db.close()

    assert client.delete(f"/batches/{batch['id']}", headers=headers).status_code == 204
    assert client.get(f"/batches/{batch['id']}", headers=headers).status_code == 404

    batch2 = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "T3"},
    ).json()
    client.post(
        "/notes",
        headers=headers,
        files={"file": ("f2.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Up", "batch_folder_id": batch2["id"]},
    )
    assert client.delete(f"/exams/{exam['id']}", headers=headers).status_code == 204
    assert client.get(f"/exams/{exam['id']}", headers=headers).status_code == 404


def test_rolling_quota_uses_30_day_window(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = "user-ops-quota"
    _auth(monkeypatch, uid=uid, phone="+919700099004")
    monkeypatch.setattr("app.core.limits.settings.PAPER_MONTHLY_CREATE_LIMIT", 2)
    monkeypatch.setattr("app.services.papers.settings.PAPER_CREATE_WINDOW_DAYS", 30)
    monkeypatch.setattr("app.core.limits.settings.PAPER_CREATE_WINDOW_DAYS", 30)

    headers = {"Authorization": "Bearer t"}
    assert client.get("/me", headers=headers).status_code == 200

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        # Two papers: one recent (counts), one older than 30 days (does not).
        db.add(
            QuestionPaper(
                id="qp-old",
                user_id=uid,
                language="en",
                status=PaperStatus.READY.value,
                title="Old",
                question_count=5,
                created_at=now - timedelta(days=31),
            )
        )
        db.add(
            QuestionPaper(
                id="qp-new",
                user_id=uid,
                language="en",
                status=PaperStatus.READY.value,
                title="New",
                question_count=5,
                created_at=now - timedelta(days=1),
            )
        )
        db.commit()
    finally:
        db.close()

    summary = client.get("/me/summary", headers=headers)
    assert summary.status_code == 200
    quota = summary.json()["paper_quota"]
    assert quota["limit"] == 2
    assert quota["used"] == 1
    assert quota["remaining"] == 1
    assert quota["window_days"] == 30
    resets = datetime.fromisoformat(quota["resets_at"].replace("Z", "+00:00"))
    assert resets > now


def test_paper_rename_survives_topics_list(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Custom titles must not be overwritten by Tests-tab title canonicalize."""
    uid = "user-ops-rename-persist"
    _auth(monkeypatch, uid=uid, phone="+919700099005")
    _mock_upload(monkeypatch)
    headers = {"Authorization": "Bearer t"}

    exam = client.post("/exams", headers=headers, json={"name": "E"}).json()
    batch = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "T"},
    ).json()

    db = SessionLocal()
    try:
        import uuid

        from app.models import PaperBatchLink

        db.add(
            QuestionPaper(
                id="paper-custom-title",
                user_id=uid,
                batch_folder_id=batch["id"],
                language="en",
                status=PaperStatus.READY.value,
                title="My Custom Test",
                question_count=5,
            )
        )
        db.add(
            PaperBatchLink(
                id=str(uuid.uuid4()),
                paper_id="paper-custom-title",
                batch_id=batch["id"],
            )
        )
        db.commit()
    finally:
        db.close()

    renamed = client.patch(
        "/papers/paper-custom-title",
        headers=headers,
        json={"title": "Preferred Name"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Preferred Name"

    folders = client.get("/papers/topics", headers=headers)
    assert folders.status_code == 200
    titles = [
        t["title"]
        for f in folders.json()
        for t in f["tests"]
        if t["id"] == "paper-custom-title"
    ]
    assert titles == ["Preferred Name"]

    again = client.get("/papers/paper-custom-title", headers=headers)
    assert again.json()["title"] == "Preferred Name"


def test_delete_topic_keeps_multi_topic_paper(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deleting a topic without Ready notes must not wipe shared multi-topic papers."""
    uid = "user-ops-multi-unlink"
    _auth(monkeypatch, uid=uid, phone="+919700099006")
    _mock_upload(monkeypatch)
    headers = {"Authorization": "Bearer t"}

    exam = client.post("/exams", headers=headers, json={"name": "E"}).json()
    keep = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "Keep"},
    ).json()
    drop = client.post(
        f"/exams/{exam['id']}/batches",
        headers=headers,
        json={"name": "Drop"},
    ).json()

    keep_note = client.post(
        "/notes",
        headers=headers,
        files={"file": ("k.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "K", "batch_folder_id": keep["id"]},
    ).json()
    drop_note = client.post(
        "/notes",
        headers=headers,
        files={"file": ("d.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "D", "batch_folder_id": drop["id"]},
    ).json()

    db = SessionLocal()
    try:
        import uuid

        from app.models import PaperBatchLink

        kn = db.get(Note, keep_note["id"])
        assert kn is not None
        kn.status = NoteStatus.READY.value
        kn.canonical_content_en = "Keep content"
        db.add(
            QuestionPaper(
                id="multi-paper-1",
                user_id=uid,
                batch_folder_id=keep["id"],
                language="en",
                status=PaperStatus.READY.value,
                title="MultiTopic-Test-1",
                question_count=5,
            )
        )
        db.add(
            PaperBatchLink(
                id=str(uuid.uuid4()),
                paper_id="multi-paper-1",
                batch_id=keep["id"],
            )
        )
        db.add(
            PaperBatchLink(
                id=str(uuid.uuid4()),
                paper_id="multi-paper-1",
                batch_id=drop["id"],
            )
        )
        db.commit()
    finally:
        db.close()

    assert drop_note["can_delete"] is True
    assert client.delete(f"/batches/{drop['id']}", headers=headers).status_code == 204

    paper = client.get("/papers/multi-paper-1", headers=headers)
    assert paper.status_code == 200
    assert paper.json()["batch_folder_id"] == keep["id"]

    folders = client.get("/papers/topics", headers=headers).json()
    topic_ids = {f["topic_id"] for f in folders}
    assert keep["id"] in topic_ids
    assert drop["id"] not in topic_ids
    assert any(
        t["id"] == "multi-paper-1"
        for f in folders
        if f["topic_id"] == keep["id"]
        for t in f["tests"]
    )
