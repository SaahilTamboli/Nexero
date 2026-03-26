# Nexero VR Analytics Platform - Technical Pipeline Documentation

## Overview

Nexero is a VR analytics platform that tracks user interactions within Unreal Engine virtual experiences and visualizes the data through a React dashboard.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEXERO VR ANALYTICS PLATFORM                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    HTTP/REST     ┌─────────────────┐    PostgreSQL    ┌─────────────────┐
│                 │ ──────────────▶ │                 │ ──────────────▶ │                 │
│  Unreal Engine  │                 │  FastAPI        │                 │   Supabase      │
│  (VR Experience)│ ◀────────────── │  Backend        │ ◀────────────── │   Database      │
│                 │    JSON Response │                 │    Query Results │                 │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
        │                                   │                                   │
        │                                   │                                   │
        ▼                                   ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐                 ┌─────────────────┐
│  Pixel          │                 │  Render.com     │                 │  Supabase       │
│  Streaming      │                 │  Hosting        │                 │  Cloud          │
│  (Web Delivery) │                 │                 │                 │                 │
└─────────────────┘                 └─────────────────┘                 └─────────────────┘
                                            │
                                            │ REST API
                                            ▼
                                    ┌─────────────────┐
                                    │  React          │
                                    │  Dashboard      │
                                    │  (Next.js)      │
                                    └─────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │  Vercel         │
                                    │  Hosting        │
                                    └─────────────────┘
```

---

## 1. Data Collection Layer (Unreal Engine)

### Technology Stack
- **Engine:** Unreal Engine 5
- **HTTP Plugin:** VaRest (REST API integration)
- **Delivery:** Pixel Streaming for web-based VR access

### Events Tracked

#### 1.1 Session Events
Triggered when a user starts/ends a VR session.

```json
{
  "Session_ID": "uuid-string",
  "Session_Start": "02-Dec-2025, 2:54:12 pm",
  "Session_End": "02-Dec-2025, 3:15:45 pm",
  "Total_Session_Duration": "21m 33s",
  "Device_Type": "VR Headset",
  "Browser": "Chrome",
  "Platform": "Windows"
}
```

#### 1.2 POI (Point of Interest) Events
Triggered when a user interacts with a POI marker.

```json
{
  "Session_ID": "uuid-string",
  "POI_ID": "poi_kitchen_001",
  "POI_Name": "Kitchen Area",
  "POI_Source": "hotspot",
  "Time_Spent": "2m 45s",
  "Visit_Start": "02-Dec-2025, 2:56:00 pm",
  "Visit_End": "02-Dec-2025, 2:58:45 pm"
}
```

#### 1.3 View Events
Triggered when camera angle or view changes.

```json
{
  "Session_ID": "uuid-string",
  "View_ID": "view_living_room",
  "View_Name": "Living Room Panorama",
  "View_Duration": "1m 30s",
  "Timestamp": "02-Dec-2025, 2:55:00 pm"
}
```

#### 1.4 Filter Events (Future)
Triggered when user applies material/finish filters.

```json
{
  "Session_ID": "uuid-string",
  "Filter_Type": "material",
  "Filter_Value": "marble_white",
  "Applied_To": "kitchen_counter",
  "Timestamp": "02-Dec-2025, 2:57:00 pm"
}
```

#### 1.5 Unit Events (Future)
Triggered when user views/interacts with property units.

```json
{
  "Session_ID": "uuid-string",
  "Unit_ID": "unit_2bhk_a101",
  "Unit_Type": "2BHK",
  "Floor": 10,
  "View_Duration": "3m 15s",
  "Timestamp": "02-Dec-2025, 3:00:00 pm"
}
```

---

## 2. Backend API Layer (FastAPI)

### Technology Stack
- **Framework:** FastAPI (Python 3.11+)
- **Validation:** Pydantic v2
- **CORS:** Enabled for cross-origin requests
- **Hosting:** Render.com

### API Endpoints

#### Base URL
```
Production: https://nexero.onrender.com
Local Dev:  http://localhost:8000
```

#### 2.1 Health Check
```
GET /health
Response: { "status": "healthy" }
```

#### 2.2 Universal Session Endpoint
```
POST /api/v1/unreal/session
Content-Type: application/json

Accepts: Session, POI, or View data
Auto-detects data type and routes to appropriate handler
```

#### 2.3 Analytics Endpoints
```
GET /api/v1/analytics/sessions          # All sessions
GET /api/v1/analytics/sessions/{id}     # Single session
GET /api/v1/analytics/poi-stats         # POI engagement stats
GET /api/v1/analytics/view-stats        # View engagement stats
GET /api/v1/analytics/dashboard-summary # Aggregated metrics
```

### Pydantic Models

```python
# app/models/unreal.py

class POIData(BaseModel):
    Session_ID: str
    POI_ID: str
    POI_Name: str
    POI_Source: Optional[str] = None
    Time_Spent: Optional[str] = None
    Visit_Start: Optional[str] = None
    Visit_End: Optional[str] = None

class ViewData(BaseModel):
    Session_ID: str
    View_ID: str
    View_Name: str
    View_Duration: Optional[str] = None
    Timestamp: Optional[str] = None

class UnrealSessionData(BaseModel):
    Session_ID: str
    Session_Start: str
    Session_End: Optional[str] = None
    Total_Session_Duration: Optional[str] = None
    Device_Type: Optional[str] = None
    Browser: Optional[str] = None
    Platform: Optional[str] = None
```

### Data Type Detection Logic

```python
def detect_data_type(data: dict) -> str:
    if "POI_ID" in data:
        return "poi"
    elif "View_ID" in data:
        return "view"
    elif "Session_Start" in data:
        return "session"
    else:
        return "unknown"
```

---

## 3. Database Layer (Supabase)

### Technology Stack
- **Database:** PostgreSQL 15
- **Platform:** Supabase Cloud
- **Auth:** Supabase Auth (future)

### Schema

#### 3.1 vr_sessions
```sql
CREATE TABLE vr_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_start TIMESTAMPTZ,
    session_end TIMESTAMPTZ,
    total_duration_seconds INTEGER,
    device_type VARCHAR(100),
    browser VARCHAR(100),
    platform VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.2 poi_visits
```sql
CREATE TABLE poi_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) REFERENCES vr_sessions(session_id),
    poi_id VARCHAR(255) NOT NULL,
    poi_name VARCHAR(255),
    poi_source VARCHAR(100),
    time_spent_seconds INTEGER,
    visit_start TIMESTAMPTZ,
    visit_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.3 view_events
```sql
CREATE TABLE view_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) REFERENCES vr_sessions(session_id),
    view_id VARCHAR(255) NOT NULL,
    view_name VARCHAR(255),
    view_duration_seconds INTEGER,
    timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.4 tracking_events (Generic)
```sql
CREATE TABLE tracking_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexes
```sql
CREATE INDEX idx_sessions_session_id ON vr_sessions(session_id);
CREATE INDEX idx_poi_visits_session ON poi_visits(session_id);
CREATE INDEX idx_poi_visits_poi ON poi_visits(poi_id);
CREATE INDEX idx_view_events_session ON view_events(session_id);
CREATE INDEX idx_tracking_events_session ON tracking_events(session_id);
CREATE INDEX idx_tracking_events_type ON tracking_events(event_type);
```

---

## 4. Dashboard Layer (React)

### Technology Stack
- **Framework:** Next.js 14 / React 18
- **Build Tool:** Vite
- **Styling:** Tailwind CSS v4
- **Charts:** Recharts
- **Flow Diagrams:** React Flow
- **Icons:** Lucide React
- **Hosting:** Vercel

### Dashboard Views

#### 4.1 Overview Dashboard
- Total sessions count
- Average session duration
- Active users (real-time)
- Session trend chart (line/area)

#### 4.2 POI Analytics
- POI engagement heatmap
- Top POIs by visit count
- Average time per POI
- POI source breakdown (hotspot vs navigation)

#### 4.3 View Analytics
- View popularity rankings
- View duration distribution
- View sequence analysis

#### 4.4 User Journey Flow
- React Flow visualization
- Session path mapping
- Drop-off point analysis

#### 4.5 Unit Analytics (Future)
- Unit popularity by type
- Floor preference distribution
- Unit comparison metrics

### Component Structure
```
src/
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   ├── dashboard/
│   │   ├── StatsCard.tsx
│   │   ├── SessionChart.tsx
│   │   ├── POIHeatmap.tsx
│   │   └── JourneyFlow.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Card.tsx
│       └── ...shadcn components
├── pages/
│   ├── index.tsx (Overview)
│   ├── poi-analytics.tsx
│   ├── view-analytics.tsx
│   └── user-journeys.tsx
├── services/
│   └── api.ts (API client)
├── hooks/
│   └── useAnalytics.ts
└── lib/
    └── utils.ts
```

### API Integration

```typescript
// src/services/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://nexero.onrender.com';

export const analyticsAPI = {
  getSessions: () => fetch(`${API_BASE}/api/v1/analytics/sessions`),
  getSession: (id: string) => fetch(`${API_BASE}/api/v1/analytics/sessions/${id}`),
  getPOIStats: () => fetch(`${API_BASE}/api/v1/analytics/poi-stats`),
  getViewStats: () => fetch(`${API_BASE}/api/v1/analytics/view-stats`),
  getDashboardSummary: () => fetch(`${API_BASE}/api/v1/analytics/dashboard-summary`),
};
```

---

## 5. Data Flow Pipeline

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              COMPLETE DATA FLOW                               │
└──────────────────────────────────────────────────────────────────────────────┘

1. USER INTERACTION
   └─▶ User enters VR experience via Pixel Streaming

2. EVENT CAPTURE (Unreal Engine)
   └─▶ VaRest plugin captures:
       ├─▶ Session start/end
       ├─▶ POI interactions
       ├─▶ View changes
       └─▶ Filter applications

3. HTTP TRANSMISSION
   └─▶ POST request to FastAPI backend
       ├─▶ URL: https://nexero.onrender.com/api/v1/unreal/session
       ├─▶ Method: POST
       ├─▶ Headers: Content-Type: application/json
       └─▶ Body: JSON event data

4. BACKEND PROCESSING (FastAPI)
   └─▶ Receive request
       ├─▶ Detect data type (session/poi/view)
       ├─▶ Validate with Pydantic models
       ├─▶ Parse timestamps (human-readable → ISO)
       ├─▶ Convert durations (string → seconds)
       └─▶ Store in Supabase

5. DATABASE STORAGE (Supabase)
   └─▶ Insert into appropriate table
       ├─▶ vr_sessions
       ├─▶ poi_visits
       ├─▶ view_events
       └─▶ tracking_events

6. DASHBOARD QUERY (React)
   └─▶ Fetch from analytics endpoints
       ├─▶ Aggregate session data
       ├─▶ Calculate POI metrics
       ├─▶ Generate chart data
       └─▶ Render visualizations

7. USER INSIGHTS
   └─▶ Business stakeholders view:
       ├─▶ Engagement metrics
       ├─▶ User behavior patterns
       ├─▶ Feature popularity
       └─▶ Conversion insights
```

---

## 6. Deployment Architecture

### Backend (Render.com)
```yaml
# render.yaml
services:
  - type: web
    name: nexero-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
```

### Database (Supabase)
- Project URL: `https://[project-ref].supabase.co`
- Direct DB connection for migrations
- REST API for application queries

### Dashboard (Vercel)
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://nexero.onrender.com"
  }
}
```

### Version Control (GitHub)
```
nexero/
├── nexero-backend/     # FastAPI backend repo
├── nexero-dashboard/   # React dashboard repo
└── nexero-unreal/      # Unreal project (private)
```

---

## 7. Environment Variables

### Backend (.env)
```env
# Supabase
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=eyJ...service_role_key
SUPABASE_ANON_KEY=eyJ...anon_key

# Server
PORT=8000
ENVIRONMENT=production

# CORS
ALLOWED_ORIGINS=https://nexero-dashboard.vercel.app,http://localhost:3000
```

### Dashboard (.env.local)
```env
NEXT_PUBLIC_API_URL=https://nexero.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://[project-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...anon_key
```

---

## 8. Security Considerations

### API Security
- [x] CORS configuration for allowed origins
- [x] Pydantic validation on all inputs
- [ ] Rate limiting (to implement)
- [ ] API key authentication (to implement)

### Database Security
- [x] Row Level Security (RLS) ready
- [x] Service role key for backend
- [x] Anon key for public read access
- [ ] User-specific policies (when auth added)

### Data Privacy
- [ ] User consent tracking
- [ ] Data retention policies
- [ ] GDPR compliance measures

---

## 9. Future Enhancements

### Phase 1 (Current)
- [x] Session tracking
- [x] POI analytics
- [x] View tracking
- [x] Basic dashboard

### Phase 2 (Next)
- [ ] Unit tracking
- [ ] Filter/material preferences
- [ ] Lead capture integration
- [ ] User authentication

### Phase 3 (Future)
- [ ] Real-time analytics (WebSocket)
- [ ] A/B testing framework
- [ ] ML-based insights
- [ ] Custom report builder
- [ ] Multi-project support

---

## 10. API Reference

### Complete Endpoint List

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/unreal/session` | Universal data ingestion |
| GET | `/api/v1/analytics/sessions` | List all sessions |
| GET | `/api/v1/analytics/sessions/{id}` | Get session details |
| GET | `/api/v1/analytics/poi-stats` | POI engagement metrics |
| GET | `/api/v1/analytics/view-stats` | View engagement metrics |
| GET | `/api/v1/analytics/dashboard-summary` | Aggregated dashboard data |

### Response Formats

#### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-01-17T10:30:00Z"
}
```

#### Error Response
```json
{
  "status": "error",
  "message": "Validation error",
  "details": { ... },
  "timestamp": "2025-01-17T10:30:00Z"
}
```

---

## 11. Contact & Support

- **Project:** Nexero VR Analytics Platform
- **Repository:** GitHub (private)
- **Backend URL:** https://nexero.onrender.com
- **Dashboard:** https://nexero-dashboard.vercel.app

---

*Documentation last updated: January 17, 2026*
