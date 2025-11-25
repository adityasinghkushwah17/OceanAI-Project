# AI-Assisted Document Authoring (Minimal Implementation)

This repository contains a minimal full-stack implementation of an AI-assisted document authoring platform.

Structure:
- `backend/` - FastAPI backend, SQLite via SQLAlchemy, JWT auth, simple LLM wrapper (mock/OpenAI), exporters for `.docx` and `.pptx`.
- `frontend/` - Minimal HTML/CSS/JS UI to interact with the backend.

Quick start (Windows PowerShell):

1. Backend setup

```powershell
cd .\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env to set SECRET_KEY etc.
uvicorn app.main:app --reload --port 8000
```

2. Frontend

Open `frontend/index.html` in a browser (no build step). The frontend contacts the backend at `http://localhost:8000`.

Notes:
- The LLM client is mocked by default. To use OpenAI, set `OPENAI_API_KEY` in `.env` and `LLM_PROVIDER=openai`.
- This is a minimal, extensible scaffold to demonstrate the end-to-end flow in the assignment.
