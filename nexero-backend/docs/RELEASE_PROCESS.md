# Release Process

Use this process for predictable backend releases.

## 1. Branch and Scope Freeze

1. Create a release branch from main:
   - `release/YYYY-MM-DD` or `release/vX.Y.Z`
2. Freeze scope to bug fixes, docs, and release-blocker items.

## 2. Validation Steps

Run locally in backend root:

```powershell
python -m compileall app
pytest
```

Optional smoke checks:

- `GET /health`
- `GET /docs`
- Representative dashboard endpoints
- Representative unreal ingestion endpoint

## 3. Changelog Update

1. Move release-ready items from `Unreleased` into a dated section in `CHANGELOG.md`.
2. Keep categories clear: Added, Changed, Fixed, Security, Database.
3. Keep entries user-impact oriented, not just implementation details.

## 4. Versioning Guidance

Suggested semantic versioning style:

- MAJOR: breaking API contract changes
- MINOR: backward-compatible features
- PATCH: bug fixes/docs/internal improvements

If version is tracked in code/docs, update it in the same release PR.

## 5. Deployment Checklist

- [ ] Environment variables present in target environment
- [ ] Required migrations applied in Supabase
- [ ] Health endpoint returns healthy status
- [ ] Auth settings align with environment (`REQUIRE_DASHBOARD_AUTH`)
- [ ] CORS origins updated for active frontend domains

## 6. Rollback Plan

Before deploy, define rollback action:

- Revert to prior deployment artifact/image
- Disable new frontend path if required
- Apply DB rollback strategy for non-backward-compatible migrations

## 7. Post-Release Monitoring

For first 30-60 minutes:

- Watch API logs for 4xx/5xx spikes
- Verify ingestion throughput and dashboard response latency
- Validate auth failures are not unexpectedly high

## 8. Release Handoff Note

After release, add a short handoff note including:

- What shipped
- Known limitations
- Follow-up tickets
- Owner for hotfixes
