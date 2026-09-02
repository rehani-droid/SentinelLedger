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

## Planned local setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
py scripts\seed_demo_data.py
py -m uvicorn app.main:app --app-dir backend --reload

npm.cmd install --prefix frontend
npm.cmd run dev --prefix frontend
```

The API Swagger UI will be at `http://localhost:8000/docs`; the Vite UI will be at `http://localhost:5173`.

## Verification

```powershell
py -m pytest backend\tests tests
npm.cmd run test --prefix frontend
```

## Environment

Copy `.env.example` to `.env` only for local development and set `DATABASE_URL` and a secure `JWT_SECRET`. Do not commit `.env`.

## Demo story

Sign in as the seeded CISO, inspect financial cyber risk and its drivers, simulate a privileged MFA rollout, optimise a ₹1 crore budget, review framework coverage, then verify the assessment hash in the audit ledger.
