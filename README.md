# SentinelLedger — SIH 26105

AI-Powered Continuous Cyber Risk Quantification and Investment Optimization Platform.

SentinelLedger translates normalised cybersecurity telemetry into transparent, **modelled** financial exposure. It prioritises risk drivers, compares mitigations, runs what-if scenarios, chooses an investment portfolio under a budget, maps controls to frameworks, and seals important assessments in a tamper-evident ledger.

> This is decision-support software. All monetary figures, likelihoods, and returns are estimated from synthetic demo data and model assumptions; they are not guarantees or regulatory certifications.

## Architecture

- `frontend/` — React + TypeScript + Vite executive and technical dashboards.
- `backend/` — FastAPI modular monolith, Pydantic contracts, SQLAlchemy persistence, and API routes.
- `backend/app/risk/` — deterministic, versioned criticality, likelihood, EAL, VaR and explainability calculations.
- `backend/app/optimization/` — budget-constrained portfolio selection with dependency/exclusion validation.
- `backend/app/audit/` — append-only hash-chained assessment ledger.
- `data/` — reproducible synthetic telemetry inputs (generated locally, not committed at scale).
- `docs/` — formulae, architecture, security, integration, and demo guidance.

Read [architecture documentation](docs/architecture.md) for the data flow and component boundaries.

## Prerequisites (Windows PowerShell)

- Python 3.11+ available through `py`
- Node.js 20+ (installed: Node 26)
- PostgreSQL 16+ for the full persistent deployment
- Docker Desktop is optional and currently not detected in this environment

## Local setup (Windows PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
# Edit .env and set a unique JWT_SECRET (32+ characters).
py scripts\seed_demo_data.py
py -m uvicorn app.main:app --app-dir backend --reload

npm.cmd install --prefix frontend
npm.cmd run dev --prefix frontend
```

The API Swagger UI will be at `http://localhost:8000/docs`; the Vite UI will be at `http://localhost:5173`.

For PostgreSQL, start only the database with Docker Desktop, set `DATABASE_URL` in `.env`, then apply the versioned migrations before seeding:

```powershell
docker compose up -d postgres
py -m alembic -c backend\alembic.ini upgrade head
py scripts\seed_demo_data.py
```

## Docker demonstration deployment

Copy `.env.example` to `.env`, set `POSTGRES_PASSWORD` and a random `JWT_SECRET` of at least 32 characters, then run:

```powershell
docker compose up --build
```

The compose startup waits for PostgreSQL and the backend health check. Migrations run automatically when the backend starts. Stop services with `docker compose down` (add `-v` only when intentionally deleting demo database data).

## Verification

```powershell
py -m pytest backend\tests
npm.cmd run test --prefix frontend
npm.cmd run build --prefix frontend
git diff --check
```

## Environment

Copy `.env.example` to `.env` only for local development or Docker configuration. Required deployment settings are `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT`, and `CORS_ORIGINS`; Docker additionally uses `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. `LLM_API_KEY` is optional and the deterministic local assistant remains the default. Do not commit `.env`.

## Demo story

Sign in as the seeded CISO, inspect financial cyber risk and its drivers, simulate a privileged MFA rollout, optimise a ₹1 crore budget, review framework coverage, then verify the assessment hash in the audit ledger.
