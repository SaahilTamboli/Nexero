# Nexero Supabase Setup Guide

## Quick Setup Steps

### 1. Run the Migration SQL

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Click **SQL Editor** in the left sidebar
4. Copy the contents of `supabase/migrations/001_initial_schema.sql`
5. Paste and click **Run**

### 2. Verify Tables Created

Go to **Table Editor** and confirm these 12 tables exist:

| Table | Purpose |
|-------|---------|
| `properties` | Builder's real estate projects |
| `units` | Individual units (2BHK, 3BHK, etc.) |
| `zones` | Rooms within units |
| `amenities` | Building amenities (pool, gym) |
| `pois` | Points of Interest (furniture, views) |
| `customers` | Lead/customer profiles |
| `vr_sessions` | VR tour sessions |
| `zone_visits` | Time in each zone |
| `poi_interactions` | Object interactions |
| `amenity_views` | Amenity viewing data |
| `tracking_events` | Raw events from Unreal |
| `session_analytics` | Pre-computed analytics |

### 3. Test Connection

```python
from app.core.database_v2 import get_nexero_db

db = get_nexero_db()

# Create a test session
session = await db.create_session(
    session_code="test_001",
    started_at="2025-01-01T10:00:00Z",
    device_type="desktop"
)
print(session)
```

---

## Database Schema Overview

```
┌─────────────────┐      ┌─────────────────┐
│   properties    │──────│     units       │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │                ┌───────┴───────┐
         │                │               │
    ┌────┴────┐      ┌────┴────┐    ┌─────┴─────┐
    │amenities│      │  zones  │────│   pois    │
    └─────────┘      └────┬────┘    └───────────┘
                          │
                          │
┌─────────────────┐      │
│   customers     │◄─────┼─────────────────────┐
└────────┬────────┘      │                     │
         │               │                     │
         │         ┌─────┴─────┐               │
         └────────►│vr_sessions│◄──────────────┤
                   └─────┬─────┘               │
                         │                     │
         ┌───────────────┼───────────────┐     │
         │               │               │     │
    ┌────┴────┐    ┌─────┴─────┐   ┌─────┴─────┐
    │zone_visits│   │poi_interact│  │tracking_  │
    └─────────┘    │   ions     │  │  events   │
                   └───────────┘   └───────────┘
```

---

## Data Flow

### From Unreal Engine:

```
1. Session Start
   POST /api/v1/unreal/session
   → Creates vr_sessions record
   → Creates/links customer record

2. Zone Enter
   POST /api/v1/unreal/tracking (event_type: "zone_enter")
   → Creates zone_visits record
   → Creates tracking_events record

3. POI Interaction
   POST /api/v1/unreal/tracking (event_type: "gaze", "click")
   → Creates poi_interactions record
   → Creates tracking_events record

4. Zone Exit
   POST /api/v1/unreal/tracking (event_type: "zone_exit")
   → Updates zone_visits with duration
   → Creates tracking_events record

5. Session End
   POST /api/v1/unreal/session/end
   → Updates vr_sessions with duration, status
   → Computes session_analytics
   → Updates customer lead_score
```

---

## Key Queries

### Get Hot Leads
```sql
SELECT * FROM customers 
WHERE lead_status = 'hot' 
ORDER BY lead_score DESC 
LIMIT 20;
```

### Session Duration by Unit Type
```sql
SELECT 
    u.unit_type,
    COUNT(*) as sessions,
    AVG(s.duration_seconds)/60 as avg_minutes
FROM vr_sessions s
JOIN units u ON s.unit_id = u.id
GROUP BY u.unit_type;
```

### Zone Heatmap
```sql
SELECT 
    zone_name,
    zone_type,
    COUNT(*) as visits,
    AVG(duration_seconds) as avg_duration,
    SUM(interactions_count) as total_interactions
FROM zone_visits
GROUP BY zone_name, zone_type
ORDER BY avg_duration DESC;
```

### Drop-off Points
```sql
SELECT 
    exit_point,
    COUNT(*) as drop_count
FROM vr_sessions
WHERE status = 'dropped'
GROUP BY exit_point
ORDER BY drop_count DESC;
```

---

## Next Steps

1. ✅ Run SQL migration in Supabase
2. ⬜ Update Unreal Blueprint to send zone events
3. ⬜ Update FastAPI endpoints to use new schema
4. ⬜ Connect dashboard to live data
5. ⬜ Build lead scoring logic
