# AI Governance Crisis Simulator — Frontend

React + TypeScript + Tailwind CSS frontend for the AI Governance Crisis Simulator.

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Edit .env if needed

# 3. Start development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Scripts

| Command         | Description                   |
|-----------------|-------------------------------|
| `npm run dev`   | Start Vite dev server         |
| `npm run build` | Build production bundle       |
| `npm run lint`  | Run Oxlint                    |
| `npm run preview` | Preview production build    |

## Project Structure

```
src/
├── components/       # Reusable UI components
│   └── StatusIndicator/
├── services/         # API service layer (api.ts)
├── types/            # Shared TypeScript types
├── App.tsx           # Root application shell
├── main.tsx          # React entry point
└── index.css         # Global styles + Tailwind
```

## Environment Variables

| Variable              | Description                  | Default                   |
|-----------------------|------------------------------|---------------------------|
| `VITE_API_BASE_URL`   | Backend FastAPI base URL     | `http://localhost:8000`   |
