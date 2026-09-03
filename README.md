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

## QUICK START

### Prerequisites

- Docker Desktop
- Git

### Startup (Windows PowerShell)

```powershell
Copy-Item .env.example .env
# Edit .env: set POSTGRES_PASSWORD and a unique JWT_SECRET (at least 32 characters).
docker compose config
docker compose up --build
```

Compose waits for a healthy PostgreSQL container, runs Alembic migrations when the backend starts, seeds deterministic demo data, and then starts the frontend. Open `http://localhost:5173` (API and Swagger: `http://localhost:8000` and `http://localhost:8000/docs`). Stop with `docker compose down`; use `docker compose down -v` only when intentionally deleting the demo database.

### Demo login

Use the seeded CISO account:

- **Username:** `ciso`
- **Password:** the value of `DEMO_CISO_PASSWORD` in `.env` (the local template default is `CisoDemo!2026`)
- **Role:** CISO

The analyst and auditor accounts are also seeded from `DEMO_ANALYST_PASSWORD` and `DEMO_AUDITOR_PASSWORD`. These are synthetic local-demo credentials, not production secrets. Never commit `.env`.

## Recommended SIH demonstration sequence

1. **Login as CISO.**
2. **Executive:** show enterprise risk, financial exposure, EAL, 95% VaR, risk trend, top contributors, and the 90-day modelled predictive view.
3. **High-risk asset:** open a contributor to show criticality, vulnerabilities, controls, risk drivers, and financial exposure.
4. **Scenario & optimise:** increase privileged MFA coverage, compare the baseline with the modelled risk/EAL reduction, then run Investment Optimization with a ₹10 lakh budget to show available investments, selected investments, residual budget, and recommendation.
5. **Compliance:** show NIST CSF, ISO/IEC 27001, CIS Controls, RBI Cyber Security Framework, and SEBI Cybersecurity and Cyber Resilience Framework mappings.
6. **Audit Ledger:** show event order, timestamps, hashes, previous hashes, and verification. Call this a **HASH-CHAIN AUDIT LEDGER**, not a blockchain.
7. **AI/Risk Assistant:** ask “Is our cyber risk increasing?”, “What are our top risk contributors?”, “What is our financial exposure?”, “How should we invest a ₹10 lakh security budget?”, and “What happens if privileged MFA coverage increases?”. Responses are read-only, deterministic/modelled decision support.
8. **Predictive ML:** show 90-day incident likelihood, model and feature versions, predictive drivers, and evaluation metrics. Do not describe these synthetic metrics as production accuracy.

All monetary values, likelihoods, risk reductions, framework evidence, incidents, and predictive outputs are synthetic/modelled demonstration data. They are not observed enterprise statistics, guarantees, regulatory certifications, or production-level predictive claims.

## Architecture overview

SentinelLedger is a modular monolith: a React + TypeScript + Vite frontend calls a FastAPI backend; PostgreSQL stores users, telemetry, projections, optimization runs, framework mappings, and audit events. Alembic manages schema upgrades, the deterministic Python risk engine calculates EAL/VaR and explainability, the optimizer evaluates constrained portfolios, and the audit service persists a SHA-256 hash chain. The offline assistant only routes approved read-only intents to structured backend calculations.

See [architecture documentation](docs/architecture.md) for component boundaries and data flow.

## Local development without Compose

For development with SQLite, Python 3.11+, Node.js 20+, and the `py` launcher:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
py scripts\seed_demo_data.py
py -m uvicorn app.main:app --app-dir backend --reload
npm.cmd install --prefix frontend
npm.cmd run dev --prefix frontend
```

## Verification

```powershell
py -m pytest backend\tests
npm.cmd run test --prefix frontend
npm.cmd run build --prefix frontend
docker compose config
git diff --check
```

`LLM_API_KEY` is optional; the deterministic local assistant is the default. `.env` is ignored by Git and `.env.example` contains placeholders only.
