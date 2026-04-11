# Changelog

All notable changes to this project should be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Documentation set for team onboarding and architecture:
  - `docs/README.md`
  - `docs/ONBOARDING.md`
  - `docs/ARCHITECTURE.md`
- Contribution and engineering process documentation:
  - `CONTRIBUTING.md`
  - `docs/RELEASE_PROCESS.md`
  - `docs/templates/HANDOVER_CHECKLIST.md`
- Central project changelog file for ongoing change tracking.

## [2026-04-11]

### Added
- Dashboard/business API surface under `/api/v1` for:
  - sessions, leads, analytics, properties, follow-ups, campaigns
- Route aliases for Unreal compatibility:
  - `/sessions`, `/events`, `/batch`, `/heartbeat/{session_id}`
- Backend auth utility to validate Supabase JWT bearer tokens.
- Dashboard request models for leads, follow-ups, and session creation.
- Environment template file `.env.example` with production-relevant keys.

### Changed
- Supabase database client now prefers `SUPABASE_SERVICE_ROLE_KEY` with fallback to `SUPABASE_KEY`.
- FastAPI app now includes dashboard router and normalized HTTP error responses.
- Dependency list updated with:
  - `python-jose[cryptography]`
  - `email-validator`

### Database
- Added migration `supabase/migrations/002_dashboard_support.sql` with:
  - dashboard-support columns on `vr_sessions`
  - new tables: `customers`, `properties`, `follow_ups`, `campaigns`
  - index additions for dashboard query patterns

### Security
- Enabled and forced RLS on `customers`, `properties`, `follow_ups`, `campaigns`.
- Revoked direct table privileges for `anon` and `authenticated` on those tables.

## [2026-04-10]

### Added
- Universal Unreal ingestion endpoint behavior (session, POI, view payload support).
- Timestamp and duration parsing support for multiple payload formats.

### Notes
- Earlier historical changes before formal changelog adoption may be summarized and backfilled later.
