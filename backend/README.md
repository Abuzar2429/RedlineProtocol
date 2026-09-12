# AI Governance Crisis Simulator — Backend

FastAPI + PostgreSQL backend for the AI Governance Crisis Simulator.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv

# Activate — Windows PowerShell
.venv\Scripts\Activate.ps1
# Activate — Unix/macOS
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start the development server
uvicorn app.main:app --reload
```

## Endpoints (Phase 1)

| Method | Path      | Description       |
|--------|-----------|-------------------|
| GET    | `/`       | API root          |
| GET    | `/health` | Health check      |
| GET    | `/docs`   | Swagger UI (dev)  |

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
app/
├── main.py          # FastAPI app factory
├── config/          # Settings (env vars)
├── core/            # Database session & base
├── api/             # Route handlers (Phase 2+)
├── models/          # SQLAlchemy ORM models (Phase 2+)
├── schemas/         # Pydantic request/response schemas
└── services/        # Business logic (Phase 2+)
```
