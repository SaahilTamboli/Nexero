# Contributing Guide

This guide defines how we ship reliable backend changes in Nexero.

## 1. Workflow

1. Create a feature branch from the latest main.
2. Keep PRs focused (one feature or one bugfix).
3. Update docs and changelog in the same PR.
4. Wait for review approval before merge.

## 2. Branch Naming Convention

Use one of these prefixes:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`
- `refactor/<short-description>`

Examples:
- `feature/dashboard-funnel-metrics`
- `fix/unreal-batch-422`
- `docs/onboarding-update`

## 3. Commit Message Convention

Use concise messages with intent first.

Examples:
- `feat: add lead engagement endpoint`
- `fix: normalize invalid timestamp payloads`
- `docs: add release process guide`

## 4. Pull Request Checklist

Before opening PR:

- [ ] Code compiles (`python -m compileall app`)
- [ ] Tests pass (`pytest`)
- [ ] Routes/behavior verified manually for changed endpoints
- [ ] Docs updated (`docs/*`, README if needed)
- [ ] `CHANGELOG.md` updated under `Unreleased`
- [ ] No secrets added to tracked files

## 5. Review Guidelines

Reviewers should focus on:

- Correctness and regressions
- Security and auth checks
- Database migration safety and reversibility
- API contract stability (especially frontend-facing responses)
- Logging quality and operational observability

## 6. Database Change Rules

- Add new migration files under `supabase/migrations/`.
- Do not rewrite existing applied migrations.
- Prefer idempotent SQL (`IF NOT EXISTS`) where practical.
- Include index changes for new dashboard query patterns.

## 7. API Contract Rules

- Dashboard success responses should keep the existing shape:
  - `{"success": true, "data": ...}`
- Paginated responses should include:
  - `total`, `page`, `limit`, `total_pages`
- Error responses should preserve `message` and `code` keys.

## 8. Security Rules

- Never commit `.env` or secrets.
- Prefer backend service-role access over direct frontend table access.
- Keep RLS enabled on business tables unless explicitly required otherwise.

## 9. Definition of Done

A task is done only when:

- Code is merged
- Docs are updated
- Changelog entry is added
- Deployment notes are clear for the next engineer
