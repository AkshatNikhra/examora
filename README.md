# Examora — monorepo

## Examora/
├── mobile/          # Flutter Android app
├── backend/         # FastAPI API
├── PROJECT_SPEC.md  # Product & technical spec
├── README.md
└── .env.example

---

## Prerequisites

- **Flutter** (stable) — this machine uses `C:\Users\lenovo\development\flutter`
- **Python 3.11+**
- **PostgreSQL** (local or [Neon](https://neon.tech)) — required for later phases; Phase 0 health check does not need a live DB

Add Flutter to PATH (PowerShell, current session):

```powershell
$env:PATH = "C:\Users\lenovo\development\flutter\bin;$env:PATH"
```

---

## Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Run tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

---

## Mobile (Flutter)

```powershell
cd mobile
flutter pub get
flutter run
```

API base URL defaults to `http://10.0.2.2:8000` (Android emulator → host machine).

Override when needed:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000
```

---

## Phase 0 done criteria

- [x] App launches to a home screen
- [x] Backend responds on `GET /health`
- [x] Local run docs (this README)

Next: **Phase 1 — Phone login** (see `PROJECT_SPEC.md`).
