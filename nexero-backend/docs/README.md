# Nexero Backend Documentation

This folder is the primary reference for onboarding and maintaining the backend.

## Start Here

1. Read [ONBOARDING.md](ONBOARDING.md) for local setup and first-day tasks.
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand service boundaries, routes, and data flow.
3. Read [RELEASE_PROCESS.md](RELEASE_PROCESS.md) for release preparation and deployment checks.
4. Read [../CONTRIBUTING.md](../CONTRIBUTING.md) for branch, PR, and review conventions.
5. Use [templates/HANDOVER_CHECKLIST.md](templates/HANDOVER_CHECKLIST.md) for intern or owner transitions.
6. Read [../CHANGELOG.md](../CHANGELOG.md) to understand historical changes.

## Documentation Rules

- Update docs in the same PR when behavior, routes, schema, or env variables change.
- Keep route examples aligned with actual FastAPI paths.
- Add changelog entries under `Unreleased` before merging.

## Current Backend Scope

- Ingestion APIs for Unreal payloads under `/api/v1/unreal/*`.
- Dashboard/business APIs under `/api/v1/*` (sessions, leads, analytics, properties, follow-ups, campaigns).
- Supabase-backed persistence with service-role access from backend only.
