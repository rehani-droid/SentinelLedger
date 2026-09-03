# SIH 26105 — Project Status

## Current phase
**Phase 5 live dashboard and drill-down views complete; awaiting the next assigned phase**

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

## Environment findings
- Node.js 26.8.1 is installed; use `npm.cmd` in this PowerShell environment because the npm PowerShell shim is blocked by execution policy.
- Python is available through the Windows `py` launcher; the `python` Windows Store alias is not usable.
- Git and Docker are not currently on PATH.

## Next work
1. Extend multi-scenario, optimisation, compliance, ML, and AI services with integration tests.
2. Add the role-aware audit UI and replace the dashboard's starter metric cards with live pages; complete documentation/deployment validation.

## Assumptions
- All demo telemetry and financial results are synthetic/modelled, never presented as observed enterprise data.
- The offline demo uses deterministic query handling; an optional external LLM may only explain verified structured outputs.
- Docker Desktop/Git installation did not complete or become available on PATH; this is an environment blocker, not a reason to stop local application development.
