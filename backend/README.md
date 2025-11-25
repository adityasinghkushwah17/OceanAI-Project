# Backend (FastAPI)

Requirements:
- Python 3.10+
- Install dependencies: `pip install -r requirements.txt`

Environment variables: copy `.env.example` to `.env` and edit values. Key variables:
- `SECRET_KEY` - JWT secret
- `DATABASE_URL` - e.g. `sqlite:///./db.sqlite` or Postgres: `postgresql://USER:PASSWORD@HOST:PORT/DBNAME`
- `OPENAI_API_KEY` - optional, to use OpenAI
- `LLM_PROVIDER` - `mock`, `openai`, `gemini`, or `openrouter`

Development Run (local SQLite):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production notes (Postgres + Gunicorn + Uvicorn workers):

1) Set `DATABASE_URL` to a Postgres connection (export in env or set in `.env`). Example:
```env
DATABASE_URL=postgresql://myuser:mypassword@db.example.com:5432/oceandb
```

2) Install dependencies and run migrations (optional):
```bash
pip install -r requirements.txt
# If you use Alembic, configure alembic.ini and run migrations
alembic upgrade head
```

3) Run with Gunicorn + Uvicorn workers (example `Procfile` or systemd):
```bash
# Procfile (Heroku-like):
web: gunicorn -k uvicorn.workers.UvicornWorker "app.main:app" --bind 0.0.0.0:$PORT --workers 4
```

Systemd unit example (`/etc/systemd/system/oceanai.service`):
```ini
[Unit]
Description=OceanAI FastAPI service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/OceanAI-Project/backend
Environment="DATABASE_URL=postgresql://..."
EnvironmentFile=/var/www/OceanAI-Project/backend/.env
ExecStart=/var/www/OceanAI-Project/backend/.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker "app.main:app" --bind 127.0.0.1:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

4) Notes & troubleshooting:
- Ensure `psycopg2-binary` is installed for Postgres connectivity
- If using Docker, you can run Postgres in a separate container and set `DATABASE_URL` accordingly
- Keep secrets out of the repo; use environment variables or a secrets manager

If you want, I can also add a `docker-compose.yml` to run the API + Postgres locally.
