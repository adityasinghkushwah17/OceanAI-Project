# Backend (FastAPI)

Requirements:
- Python 3.10+
- Install dependencies: `pip install -r requirements.txt`

Environment variables: copy `.env.example` to `.env` and edit values. Key variables:
- `SECRET_KEY` - JWT secret
- `DATABASE_URL` - e.g. `sqlite:///./db.sqlite`
- `OPENAI_API_KEY` - optional, to use OpenAI
- `LLM_PROVIDER` - `mock` or `openai`

Run:
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
