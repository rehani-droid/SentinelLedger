# SIH 26105 — Project Status

## Current phase
**Phase 7 compliance mapping and audit ledger UI complete**

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

## Environment findings
- Node.js 26.8.1 is installed; use `npm.cmd` in this PowerShell environment because the npm PowerShell shim is blocked by execution policy.
- Python is available through the Windows `py` launcher; the `python` Windows Store alias is not usable.
- Git and Docker are not currently on PATH.

## Phase 7 validation
- Backend tests: 26 passing.
- Frontend tests: 7 passing.
- Frontend production build: passing.

## Phase 7 files changed
- `backend/app/compliance/service.py`
- `backend/app/main.py`
- `backend/tests/test_phase7.py`
- `frontend/src/main.tsx`
- `frontend/src/phase7.ts`
- `frontend/src/phase7.test.ts`
- `frontend/src/styles.css`

## Limitations / deferred
- Scenario assumptions are deterministic and explicitly labelled modelled/synthetic; they do not mutate persisted evidence or risk projections.
- Optimization EAL reduction is derived from the persisted enterprise EAL and optimizer reduction because the existing optimization record stores residual risk rather than a separate EAL field.
- AI/NL, ML, and deployment work remain deferred to later phases.

## Next work
1. Extend multi-scenario, ML, and AI services with integration tests.
2. Complete deployment validation.

## Assumptions
- All demo telemetry and financial results are synthetic/modelled, never presented as observed enterprise data.
- The offline demo uses deterministic query handling; an optional external LLM may only explain verified structured outputs.
- Docker Desktop/Git installation did not complete or become available on PATH; this is an environment blocker, not a reason to stop local application development.
