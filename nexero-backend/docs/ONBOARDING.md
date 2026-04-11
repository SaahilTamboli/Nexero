# Backend Onboarding Guide

Use this guide when a new intern or engineer joins the project.

## 1. Project Purpose

Nexero backend receives VR behavior data from Unreal Engine, stores it in Supabase, and serves dashboard-ready analytics APIs.

## 2. Repository Layout

- `app/main.py`: FastAPI app entrypoint, middleware, router mounting, global error handling.
- `app/api/v1/unreal.py`: Unreal ingestion and compatibility endpoints.
- `app/api/v1/dashboard.py`: Business/dashboard endpoints used by frontend apps.
- `app/core/database.py`: Supabase client setup and low-level DB operations.
- `app/core/auth.py`: Bearer token verification for dashboard routes.
- `app/models/`: Request/response validation models.
- `app/services/`: Business logic helpers.
- `supabase/migrations/`: SQL migrations.

## 3. Local Setup (Windows PowerShell)

1. Create or activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and fill real values:

Required keys:
- `SUPABASE_URL`
- `SUPABASE_KEY` or `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET` (required when `REQUIRE_DASHBOARD_AUTH=true`)

4. Run API:

```powershell
uvicorn app.main:app --reload
```

5. Verify:
- `GET /health`
- `GET /docs`

## 4. Authentication Model

- Dashboard endpoints use `get_current_user` dependency.
- If `REQUIRE_DASHBOARD_AUTH=false`, auth is bypassed (dev mode).
- If `REQUIRE_DASHBOARD_AUTH=true`, requests need `Authorization: Bearer <supabase_access_token>`.

## 5. Database and Migrations

- Baseline schema: `supabase/migrations/001_initial_schema.sql`
- Dashboard/business extensions: `supabase/migrations/002_dashboard_support.sql`

When changing schema:
1. Add a new migration file (do not edit old migrations already applied).
2. Keep migration idempotent where possible (`IF NOT EXISTS`).
3. Update docs and changelog in the same PR.

## 6. API Conventions Used in This Repo

- Success shape for dashboard endpoints:
  - `{"success": true, "data": ...}`
- Paginated shape:
  - `{"success": true, "data": [...], "total": n, "page": p, "limit": l, "total_pages": t}`
- Error shape (from HTTP exception handler):
  - `{"message": "...", "code": "...", "details": ...}`

## 7. Common Dev Tasks

Run syntax check:

```powershell
python -m compileall app
```

Run tests:

```powershell
pytest
```

## 8. First Good Issues for New Interns

- Add endpoint-level tests for dashboard list and detail APIs.
- Add response schema typing tests for contract stability.
- Improve docs examples for frontend integration flows.
- Add OpenAPI examples for critical endpoints.
