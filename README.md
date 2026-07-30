# Examora

AI exam preparation app for Android. Upload study notes, generate MCQ question papers with AI, attempt them, and see a basic score.

Stack: **Flutter** (mobile) + **FastAPI** (backend).

---

## Setup

### Prerequisites

- Flutter (stable)
- Python 3.11+

```powershell
$env:PATH = "C:\Users\lenovo\development\flutter\bin;$env:PATH"
```

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: http://127.0.0.1:8000/health

### Mobile

```powershell
cd mobile
flutter pub get
flutter run
```

Emulator API URL defaults to `http://10.0.2.2:8000`. On a physical device:

```powershell
flutter run --dart-define=API_BASE_URL=http://YOUR_PC_IP:8000
```
