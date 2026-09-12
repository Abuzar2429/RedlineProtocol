# AI Governance Crisis Simulator

A multi-agent simulation platform demonstrating how international AI governance strategy shapes the outcome of AI crises.

> **"The same crisis, governed differently, produces measurably different outcomes."**

---

## Architecture

```
      React Frontend  (port 5173)
             │
             ▼ HTTP / WebSocket (Phase 8+)
      FastAPI Backend  (port 8000)
             │
             ▼
         PostgreSQL  (port 5432)
```

---

## Requirements

| Software        | Minimum Version | Notes                          |
|-----------------|-----------------|--------------------------------|
| Python          | 3.11            | Backend runtime                |
| Node.js         | 18              | Frontend build tool            |
| npm             | 9               | Package manager                |
| PostgreSQL      | 14              | Via Docker Compose (see below) |
| Docker          | 24              | For local database             |

---

## Quick Start

### 1. Clone & configure

```bash
git clone <repo-url>
cd RedlineProtocol
```

Copy environment templates (do this for both backend and frontend):

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` with your settings (especially `ANTHROPIC_API_KEY` for Phase 3+).

---

### 2. Database (PostgreSQL via Docker)

```bash
docker compose up -d postgres
```

This starts PostgreSQL on `localhost:5432` with:
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `crisis_simulator`

To stop: `docker compose down`
To wipe data: `docker compose down -v`

---

### 3. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate — Windows PowerShell
.venv\Scripts\Activate.ps1

# Activate — Unix/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload
```

API is now available at **http://localhost:8000**

Swagger UI: **http://localhost:8000/docs** (development mode only)

---

### 4. Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend is now available at **http://localhost:5173**

---

## Verification

### Backend health check

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

curl http://localhost:8000/
# Expected: {"message":"AI Governance Crisis Simulator API"}
```

### Backend tests

```bash
cd backend
pytest tests/ -v
```

### Frontend production build

```bash
cd frontend
npm run build
```

---

## Project Structure

```
RedlineProtocol/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app factory
│   │   ├── config/          # Settings (env vars)
│   │   ├── core/            # Database session & base
│   │   ├── api/             # Route handlers (Phase 2+)
│   │   ├── models/          # SQLAlchemy ORM models (Phase 2+)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # Business logic (Phase 2+)
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── services/        # API service layer
│   │   ├── types/           # TypeScript types
│   │   ├── App.tsx          # Root shell
│   │   └── main.tsx         # Entry point
│   ├── .env.example
│   └── README.md
│
├── docs/                    # Project documentation
├── docker-compose.yml       # PostgreSQL for development
├── .gitignore
└── README.md  ← you are here
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable            | Default                               | Description                        |
|---------------------|---------------------------------------|------------------------------------|
| `APP_ENV`           | `development`                         | Runtime environment                |
| `DEBUG`             | `true`                                | Enables Swagger UI                 |
| `DATABASE_URL`      | `postgresql+asyncpg://postgres:postgres@localhost:5432/crisis_simulator` | PostgreSQL connection |
| `API_HOST`          | `0.0.0.0`                             | Uvicorn bind host                  |
| `API_PORT`          | `8000`                                | Uvicorn bind port                  |
| `CORS_ORIGINS`      | `http://localhost:5173,...`           | Allowed frontend origins           |
| `ANTHROPIC_API_KEY` | —                                     | Required for Phase 3+ (LLM agents) |

### Frontend (`frontend/.env`)

| Variable              | Default                   | Description         |
|-----------------------|---------------------------|---------------------|
| `VITE_API_BASE_URL`   | `http://localhost:8000`   | Backend API URL     |

---

## Implementation Phases

| Phase | Goal                                  | Status    |
|-------|---------------------------------------|-----------|
| 1     | Repo & Stack Setup                    | ✅ Done    |
| 2     | Crisis Event Engine                   | ⬜ Planned |
| 3     | LLM Country Agents                    | ⬜ Planned |
| 4     | Negotiation & Coordination            | ⬜ Planned |
| 5     | Deterministic Scoring Engine          | ⬜ Planned |
| 6     | Full Dashboard                        | ⬜ Planned |
| 7     | RAG / Governance Grounding            | ⬜ Planned |
| 8     | WebSocket Live Streaming              | ⬜ Planned |
| 9     | Comparative Runs                      | ⬜ Planned |
| 10    | Polish & Demo Prep                    | ⬜ Planned |
