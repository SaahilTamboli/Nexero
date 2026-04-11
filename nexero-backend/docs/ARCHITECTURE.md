# Architecture and API Reference

## 1. High-Level Data Flow

1. Unreal client sends session and event data to ingestion APIs.
2. Backend validates payloads with Pydantic.
3. Backend writes normalized records to Supabase tables.
4. Dashboard APIs aggregate and serve lead/session/analytics views.

## 2. Runtime Components

- FastAPI application: `app/main.py`
- Router groups:
  - Unreal ingestion router mounted at `/api/v1/unreal`
  - Dashboard router mounted at `/api/v1`
- Supabase access layer: `app/core/database.py`
- Auth layer: `app/core/auth.py`

## 3. Key Environment Variables

- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_KEY`: backward-compatible key.
- `SUPABASE_SERVICE_ROLE_KEY`: preferred backend DB key.
- `SUPABASE_JWT_SECRET`: secret used to verify bearer tokens.
- `REQUIRE_DASHBOARD_AUTH`: toggles auth enforcement for dashboard APIs.
- `CORS_ORIGINS`: allowed origins for browser clients.

## 4. Tables Most Used by APIs

Core telemetry:
- `vr_sessions`
- `tracking_events`
- `poi_visits`
- `view_events`

CRM/dashboard:
- `customers`
- `properties`
- `follow_ups`
- `campaigns`

## 5. Route Surface

### 5.1 Unreal Ingestion (`/api/v1/unreal`)

- `POST /session` and `POST /sessions`
- `POST /tracking/event` and `POST /events`
- `POST /tracking/batch` and `POST /batch`
- `GET /session/{session_id}/status`
- `POST /session/{session_id}/heartbeat` and `POST /heartbeat/{session_id}`

### 5.2 Dashboard APIs (`/api/v1`)

Sessions:
- `GET /sessions/active/count`
- `GET /sessions/stats`
- `GET /sessions`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/events`
- `GET /sessions/{session_id}/poi-visits`

Leads:
- `GET /leads`
- `POST /leads`
- `GET /leads/{lead_id}`
- `PATCH /leads/{lead_id}`
- `GET /leads/{lead_id}/sessions`
- `GET /leads/{lead_id}/engagement`

Analytics:
- `GET /analytics/dashboard`
- `GET /analytics/views`
- `GET /analytics/poi`
- `GET /analytics/zones`
- `GET /analytics/heatmap/{property_id}`
- `GET /analytics/engagement`
- `GET /analytics/engagement-trends`
- `GET /analytics/geo`
- `GET /analytics/geo-distribution`
- `GET /analytics/funnel`

Properties:
- `GET /properties`
- `GET /properties/{property_id}`
- `GET /properties/{property_id}/analytics`

Follow-ups:
- `GET /follow-ups/summary`
- `GET /follow-ups`
- `POST /follow-ups`
- `PATCH /follow-ups/{follow_up_id}`

Campaigns:
- `GET /campaigns`
- `GET /campaigns/{campaign_id}`

## 6. Error Handling Pattern

- Generic errors are trapped by a global exception handler.
- HTTP errors are normalized to:

```json
{
  "message": "Request failed",
  "code": "HTTP_ERROR",
  "details": null
}
```

## 7. Operational Notes

- Prefer backend-only access to Supabase with service role keys.
- Keep RLS enabled for dashboard tables when frontend direct table access is not required.
- Treat route aliases as compatibility contracts once used by clients.
