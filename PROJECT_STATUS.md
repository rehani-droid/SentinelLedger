# SIH 26105 — Project Status

## Current phase
**Phase 12 audit ledger hardening complete; Phase 4 ingestion/risk persistence next**

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

## Environment findings
- Node.js 26.8.1 is installed; use `npm.cmd` in this PowerShell environment because the npm PowerShell shim is blocked by execution policy.
- Python is available through the Windows `py` launcher; the `python` Windows Store alias is not usable.
- Git and Docker are not currently on PATH.

## Next work
1. Add Alembic migration history, complete database-backed risk aggregation and expanded ingestion adapters.
2. Extend multi-scenario, optimisation, compliance, ML, and AI services with integration tests.
3. Add the role-aware audit UI and replace the dashboard's starter metric cards with live pages; complete documentation/deployment validation.

## Assumptions
- All demo telemetry and financial results are synthetic/modelled, never presented as observed enterprise data.
- The offline demo uses deterministic query handling; an optional external LLM may only explain verified structured outputs.
- Docker Desktop/Git installation did not complete or become available on PATH; this is an environment blocker, not a reason to stop local application development.
