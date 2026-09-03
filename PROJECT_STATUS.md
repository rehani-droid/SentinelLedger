# SIH 26105 — Project Status

## Current phase
**Phase 12 SIH 2026 demo readiness complete**

## Completed
- Inspected the empty workspace and available development tooling.
- Chosen a modular-monolith architecture: React/Vite UI, FastAPI API, PostgreSQL, and a deterministic Python risk domain.
- Recorded the architecture, risk-model direction, local prerequisites, and delivery plan.
- Scaffolded the React/Vite dashboard, FastAPI service, Docker Compose topology, environment template, and ignored generated outputs.
- Implemented a deterministic, versioned risk/financial engine with asset criticality, evidence-weighted control effectiveness, EAL, empirical Monte Carlo VaR, and ROSI.
- Implemented a genuine budget optimiser that checks cost, dependencies, and exclusions rather than returning a fixed portfolio.
- Implemented a hash-chained audit ledger and API endpoints for assessment finalisation and integrity verification.
- Implemented a deterministic privileged-MFA what-if scenario endpoint with explicit coverage and reduction assumptions.
- Added reproducible synthetic asset generation (100 assets, fixed seed `26105`).
- Installed declared backend/frontend dependencies and verified the backend test suite (8 passing) plus the frontend production build.
- Added SQLAlchemy persistence for users, roles, assets, applications, vulnerabilities, controls, incidents, threat scenarios, investment options, framework mappings, risk records, and audit evidence.
- Added deterministic, idempotent SQLite/PostgreSQL-compatible demo seeding: 100 assets, 150 applications, 600 vulnerabilities, 35 controls, 520 incidents, and 24 threat scenarios.
- Added PBKDF2 password hashing, signed short-lived bearer tokens, seeded CISO/analyst/auditor accounts, and role protection for optimisation.
- Added REST ingestion validation and duplicate source-event rejection.
- Converted assessment audit finalisation from an in-memory object to persistent canonical JSON and SHA-256 chained hashes.
- Completed persisted audit-chain verification: privileged CISO/auditor users can list paginated audit metadata, verify the full chain, and receive the first invalid sequence/reason if an event or link has been altered. Audit creation is limited to CISO/analyst roles.
- Added ledger tests for complete persisted-chain validation and post-event link tampering (backend suite: 10 passing).
- Added Alembic migration management and an initial schema migration covering the existing SQLAlchemy model set plus persistent risk projections.
- Application startup now upgrades the configured database to the Alembic head instead of calling `Base.metadata.create_all()`.
- Added persistent, idempotent risk recalculation for asset, business-unit, application, and enterprise scopes. Stored projections include risk score, likelihood, financial impact, EAL, P95 VaR, drivers, assumptions, confidence, freshness, model version, and calculation time.
- Added focused migration and risk-persistence tests (2 passing).
- Connected normalised CSV/JSON telemetry to persisted assets, applications, vulnerabilities, controls, incidents, and threat scenarios without replacing the existing adapters.
- Added source-event receipt tracking, per-entity latest-event state, duplicate protection, stale-event rejection, partial-batch malformed-record reporting, and automatic persisted-risk recalculation after accepted domain changes.
- Added focused telemetry pipeline tests for valid mapping, duplicates, stale data, malformed/missing fields, and risk recalculation triggers.
- Replaced hard-coded optimisation options with database-backed option records, including descriptions, affected assets/controls, dependencies, and exclusions.
- Added deterministic seeded investment options, durable optimisation-run records, and protected APIs to list options, create runs, list run history, and retrieve a run.
- Added focused persistent-optimisation tests for normal, zero, insufficient-budget, dependency, and exclusion cases.
- Added a real frontend login flow backed by the existing bearer-token API, short-lived session storage, token-expiry validation, logout, and unavailable/invalid-credential handling.
- Added protected role-aware frontend navigation and actions for CISO, analyst, and auditor roles without redesigning the dashboard.
- Added focused Vitest coverage for token/session validation and role capabilities; production frontend build passes.
- Replaced the frontend's hard-coded dashboard metrics and drivers with authenticated, persisted synthetic backend data for executive, technical, and business-unit views.
- Added live asset risk drill-downs covering risk/financial metrics, drivers, vulnerabilities, and investment-linked controls, with loading, error, and empty states.
- Added read-only dashboard API projections and focused backend coverage verifying the projections use persisted synthetic data.
- Added an authenticated generic scenario API that reuses persisted enterprise EAL and investment-option data for MFA coverage, remediation delay, control, and investment what-if assumptions.
- Added the Phase 6 Scenario & optimise workspace with baseline, selected-scenario, and optimized-state cards; scenario configuration/results; investment option cost and risk-reduction visualization; budget handling; ROSI/EAL reduction; and modelled-value assumptions.
- Added Phase 6 frontend helper tests covering scenario payload configuration, scenario reductions, optimization results, and budget limits.
- Added a role-aware compliance and audit assurance workspace using persisted framework mappings and the existing hash-chain APIs.
- Added framework mapping projections with SENTINELEDGER control links, supported coverage, status, risk relevance, and explicit evidence availability.
- Added audit event presentation with timestamps, available resource/action data, hash-chain links, finalisation context, and clear verified/failed/empty/API-error states.
- Added the Phase 8 authenticated AI/Risk Assistant workspace with example questions, loading/error/empty states, and session-expiry handling.
- Added deterministic local intent routing for risk overview, top contributors, asset risk, financial exposure, investment recommendation, budget optimization, scenario simulation, vulnerability prioritization, and control/compliance questions.
- Assistant responses expose separate DATA, CALCULATION, and RECOMMENDATION sections and reuse persisted risk projections, vulnerabilities, controls, investment options, the existing optimizer, and MFA scenario service.
- Kept the provider offline and server-side: no external LLM or API key is required, no natural-language SQL/code execution is allowed, and the assistant endpoint enforces CISO/analyst/auditor RBAC.
- Added Phase 9 deterministic predictive-risk feature engineering over persisted asset, vulnerability, control, threat, and incident data.
- Selected an in-memory NumPy logistic model with fixed optimization settings, an ordered 80/20 evaluation split, model/feature versions, explainable standardized feature contributions, and no binary artifact.
- Added an authenticated `/api/v1/risk/predictive` endpoint and executive dashboard predictive-risk section labelled MODELLED / PREDICTIVE.
- Extended the local AI assistant for future-risk, increasing-risk, forecast, and predicted-incident-likelihood questions while retaining DATA, CALCULATION, and RECOMMENDATION sections.
- Completed Phase 10 hardening: protected every authenticated data/calculation boundary, enforced CISO/analyst/auditor role boundaries, added clean token-expiry/logout handling, bounded pagination and scenario identifiers, rejected non-finite or negative financial inputs, and added safe server-side error logging without stack-trace disclosure.
- Added production configuration safeguards: production JWT secrets must be at least 32 characters, `.env` remains ignored, `.env.example` documents local/PostgreSQL settings without secrets, and the optional local AI fallback remains unchanged.
- Improved database reliability with SQLAlchemy pool pre-ping, SQLite foreign-key enforcement, request rollback handling, database-aware health checks, and preserved Alembic startup upgrades (no `create_all` replacement).
- Hardened Docker Compose with environment-provided credentials, PostgreSQL/backend health checks, dependency ordering, migration-on-backend-start, and a frontend production build during image creation.
- Added audit actor attribution while retaining the verified Hash-Chain Audit Ledger terminology and tamper-detection behavior.

## Environment findings
- Node.js 26.8.1 is installed; use `npm.cmd` in this PowerShell environment because the npm PowerShell shim is blocked by execution policy.
- Python is available through the Windows `py` launcher; the `python` Windows Store alias is not usable.
- Git and Docker are not currently on PATH.

## Phase 7 validation
- Backend tests: 26 passing.
- Frontend tests: 7 passing.
- Frontend production build: passing.

## Phase 8 validation
- Backend and frontend Phase 8 tests added; full backend suite and frontend suite/build run after implementation.

## Phase 7 files changed
- `backend/app/compliance/service.py`
- `backend/app/main.py`
- `backend/tests/test_phase7.py`
- `frontend/src/main.tsx`
- `frontend/src/phase7.ts`
- `frontend/src/phase7.test.ts`
- `frontend/src/styles.css`

## Phase 9 ML implementation
- **Objective/target:** `incident_within_90_days` at asset level, where `0` means no incident and `1` means an incident in the demonstration window. The generator creates 12 monthly observations per persisted asset (1,200 observations total) with deterministic timestamps and probabilistic outcomes.
- **Features:** asset criticality, data sensitivity, internet exposure, vulnerability count, mean CVSS, mean exploitability, mean persisted control effectiveness, and mean persisted threat activity. No fabricated telemetry fields are introduced.
- **Model:** deterministic regularized logistic regression implemented with NumPy to keep the offline application functional without an external ML API or large artifact. The model version is `phase9-logistic-v1`; feature version is `asset-risk-features-v1`.
- **Evaluation:** ordered 80/20 train/evaluation split with precision, recall, F1, and confusion matrix. ROC-AUC is intentionally not reported because the implementation does not claim statistically meaningful probability ranking on this demo split.
- **Synthetic demonstration result:** 1,200 observations contain 588 positive and 612 negative outcomes. The 240-observation time-held-out evaluation returned precision `0.5210`, recall `0.5905`, F1 `0.5536`, and confusion matrix `[[78, 57], [43, 62]]`. These are generated-data metrics, not production validation.
- **Unavailable handling:** the service still returns `available: false` with an explicit reason for insufficient rows, a single target class, a non-representative time split, or an unknown asset.
- **Reproduction:** seed the database, then from `backend/` run `py ../scripts/train_predictive_model.py`. A clean checkout needs only the declared Python dependencies; no model file is committed.
- **Financial boundary:** predictive output never creates financial loss, EAL, or VaR values; those remain owned by the deterministic risk and financial engine.

## Limitations / deferred
- Scenario assumptions are deterministic and explicitly labelled modelled/synthetic; they do not mutate persisted evidence or risk projections.
- Optimization EAL reduction is derived from the persisted enterprise EAL and optimizer reduction because the existing optimization record stores residual risk rather than a separate EAL field.
- Production calibration, time-windowed labels, larger observed datasets, and statistical validation remain future work.

## Phase 8 supported intents and limitations
- Supported intents: risk overview, top risk contributors, asset risk, financial exposure, investment recommendation, budget optimization, scenario simulation, vulnerability prioritization, and control/compliance.
- Provider behavior: deterministic local fallback only; responses are based on current persisted synthetic/modelled data and do not claim predictive accuracy.
- Security controls: authenticated role checks, read-only query routing, bounded Pydantic input, no arbitrary SQL/code, no database mutation from assistant queries.
- Known limitations: intent matching is keyword-based; budget questions mentioning “lakh” use ₹10,00,000 as the deterministic default; scenario questions use 20%-to-100% privileged MFA coverage; outputs remain modelled decision support.

## Next work
1. Future work only: production telemetry, calibration, and operational deployment beyond the SIH demonstration scope.

## Phase 10 validation
- Backend tests: **41 passed** with `py -m pytest backend\tests`.
- Frontend tests: **11 passed** with `npm.cmd run test --prefix frontend`.
- Frontend production build: **passed** with `npm.cmd run build --prefix frontend`.
- Patch hygiene: **passed** with `git diff --check`.

## Phase 10 known limitations
- Bearer tokens remain short-lived stateless tokens; logout clears the browser session and provides a protected logout endpoint, while server-side revocation is intentionally outside the existing modular-monolith scope.
- Docker Desktop was not available during Phase 10; Phase 11 clean-start validation is now complete in the current environment.
- Demo users, telemetry, financial values, scenario assumptions, and predictive metrics remain synthetic/modelled and are not production accuracy claims.

## Phase 11 Docker validation
- Docker Compose clean startup: **passed** with a fresh PostgreSQL volume using `docker compose down -v --remove-orphans` followed by `docker compose up --build -d`.
- PostgreSQL: **healthy** on `postgres:16-alpine`; startup health check passed.
- Backend: **healthy** on port 8000; Alembic upgraded the clean database on startup and opt-in Compose seeding populated deterministic synthetic data.
- Deterministic seed counts verified from PostgreSQL: 100 assets, 150 applications, 600 vulnerabilities, 35 controls, 520 incidents, and 24 threat scenarios.
- Frontend: **healthy** production Vite preview container on port 5173; the image runs the production build and has an IPv4-safe health check.
- Networking/configuration: browser-facing `VITE_API_URL` defaults to `http://localhost:8000`, backend CORS defaults to `http://localhost:5173`, and all credentials remain environment-provided.
- Authentication and workflows exercised with the seeded CISO account: executive dashboard, technical dashboard, asset risk detail, scenario simulation, investment optimization, compliance frameworks, hash-chain audit listing/verification, AI/Risk Assistant, predictive ML, and risk assessment.
- Commands used: `docker compose config`, `docker compose down -v --remove-orphans`, `docker compose up --build -d`, `docker compose ps`, `docker compose logs`, `docker compose exec -T postgres psql ...`, backend `py -m pytest backend\\tests`, frontend `npm.cmd run test --prefix frontend`, and frontend `npm.cmd run build --prefix frontend`.
- Remaining limitations: Docker Compose requires local `POSTGRES_PASSWORD` and a production-length `JWT_SECRET` in the environment (no secrets are committed); demo data and all model outputs remain deterministic synthetic/modelled values.

## Assumptions
- All demo telemetry and financial results are synthetic/modelled, never presented as observed enterprise data.
- The offline demo uses deterministic query handling; an optional external LLM may only explain verified structured outputs.
- Git is available for repository work; Docker Compose was available and validated for this phase.

## Phase 12 final status

Phases 1–12 are complete. No new product phase is planned for the SIH 2026 demonstration scope.

### Final architecture and feature list

- React/Vite frontend with authenticated CISO, analyst, and auditor workspaces.
- FastAPI modular-monolith backend with PostgreSQL persistence and Alembic migrations.
- Deterministic synthetic seed: 100 assets, 150 applications, 600 vulnerabilities, 35 controls, 520 incidents, 24 threat scenarios, framework mappings, investment options, users, and persisted risk projections.
- Executive risk dashboard with enterprise risk, financial exposure, EAL, empirical 95% VaR, trend, contributors, business-unit risk, asset drill-down, and modelled predictive ML.
- What-if scenario simulation, constrained investment optimization, compliance mapping, and persisted SHA-256 hash-chain audit ledger.
- Authenticated read-only AI/Risk Assistant with structured DATA, CALCULATION, and RECOMMENDATION output; no arbitrary SQL, code, filesystem, or mutation capability.

### Final validation

- Backend: **41 tests passed** with `py -m pytest backend\tests`.
- Frontend: **11 tests passed** with `npm.cmd run test --prefix frontend`.
- Frontend production build: **passed** with `npm.cmd run build --prefix frontend`.
- Docker Compose configuration: **passed** when `.env` supplies local credentials.
- Clean Docker startup: **passed** in Phase 11 with healthy PostgreSQL, backend migrations/seed, backend health check, and frontend health check.
- Patch hygiene: **passed** with `git diff --check`.

### Exact demo startup

```powershell
Copy-Item .env.example .env
# Edit .env and set POSTGRES_PASSWORD plus a unique JWT_SECRET (32+ characters).
docker compose up --build
```

Open `http://localhost:5173`. The API is at `http://localhost:8000`; stop with `docker compose down`.
The seeded CISO username is `ciso`; use the `DEMO_CISO_PASSWORD` value in `.env` (the template default is the synthetic local-demo value `CisoDemo!2026`).

### Recommended SIH sequence

1. Login as CISO and open Executive.
2. Show enterprise risk, exposure, EAL, VaR, trend, top contributors, and predictive risk.
3. Open a high-risk asset and show criticality, vulnerabilities, controls, drivers, and exposure.
4. Run the privileged-MFA scenario and compare baseline, assumption, changed risk, and reduction.
5. Run Investment Optimization with a ₹10 lakh budget and show selected investments and EAL reduction.
6. Show NIST CSF, ISO/IEC 27001, CIS Controls, RBI Cyber Security Framework, and SEBI Cybersecurity and Cyber Resilience Framework.
7. Show the **HASH-CHAIN AUDIT LEDGER** event sequence, timestamps, hashes, previous hashes, and verification; it is not a blockchain.
8. Ask the documented AI/Risk Assistant questions and distinguish deterministic/modelled results from unsupported claims.
9. Show the 90-day predictive likelihood, model/feature versions, drivers, and synthetic evaluation metrics without claiming production accuracy.

### Known limitations and disclaimer

Scenario assumptions, financial values, telemetry, framework evidence, incidents, optimization reductions, and predictive metrics are synthetic/modelled demonstration data. They are not real-world statistics, production calibration, guarantees, regulatory certifications, or production-level predictive accuracy. Tokens are short-lived and stateless; server-side revocation remains outside this demo scope.
