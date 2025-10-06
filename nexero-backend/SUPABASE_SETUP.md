# 🗄️ SUPABASE SETUP GUIDE

Complete guide to set up your Supabase database for Nexero VR Backend.

---

## 📋 Step 1: Create Supabase Project (5 minutes)

### 1.1 Sign Up / Login

1. Go to: **https://supabase.com**
2. Click **"Start your project"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if needed

### 1.2 Create New Project

1. Click **"New Project"**
2. Fill in:
   - **Name**: `nexero-vr-backend` (or any name you like)
   - **Database Password**: Generate a strong password (SAVE THIS!)
   - **Region**: Choose closest to you (e.g., `us-east-1`, `eu-west-1`)
   - **Pricing Plan**: Start with **Free** (500MB database, 50MB file storage)
3. Click **"Create new project"**
4. Wait 2-3 minutes for setup ⏱️

---

## 🔑 Step 2: Get Your API Credentials (2 minutes)

### 2.1 Find Your Credentials

1. In your project dashboard, click **"Settings"** (gear icon in left sidebar)
2. Click **"API"** under Project Settings
3. You'll see:

```
Project URL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
https://abcdefghijklmnop.supabase.co
```

```
Project API keys
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
anon public    [eye icon to reveal]
service_role   [eye icon to reveal]  ⚠️ This key has admin rights
```

### 2.2 Copy Your Keys

You need:
- ✅ **Project URL** (e.g., `https://abcdefghijklmnop.supabase.co`)
- ✅ **service_role key** (starts with `eyJ...`, very long)

⚠️ **Use `service_role` key, NOT `anon public` key!**
- `service_role` = Full admin access (needed for backend)
- `anon public` = Limited access (for frontend/browser)

---

## 🗃️ Step 3: Create Database Tables (10 minutes)

### 3.1 Open SQL Editor

1. In left sidebar, click **"SQL Editor"**
2. Click **"New query"**

### 3.2 Create `vr_sessions` Table

Copy and paste this SQL:

```sql
-- ================================================
-- VR SESSIONS TABLE
-- Stores each VR tour session with customer info
-- ================================================

CREATE TABLE IF NOT EXISTS public.vr_sessions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Session timestamps
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Customer & Property info
    customer_id TEXT,
    property_id TEXT,
    
    -- Session status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'error')),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for fast queries
    CONSTRAINT duration_check CHECK (duration_seconds IS NULL OR duration_seconds >= 0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_customer ON public.vr_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_property ON public.vr_sessions(property_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start ON public.vr_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON public.vr_sessions(status);

-- Enable Row Level Security (RLS)
ALTER TABLE public.vr_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for service_role
CREATE POLICY "Allow all for service role"
ON public.vr_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_vr_sessions_updated_at
    BEFORE UPDATE ON public.vr_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE public.vr_sessions IS 'Stores VR real estate tour sessions';
```

Click **"Run"** (or press `Ctrl+Enter`)

✅ You should see: `Success. No rows returned`

### 3.3 Create `tracking_events` Table

Create a **new query** and paste:

```sql
-- ================================================
-- TRACKING EVENTS TABLE
-- Stores all VR interactions (gaze, zones, clicks)
-- ================================================

CREATE TABLE IF NOT EXISTS public.tracking_events (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key to session
    session_id UUID NOT NULL REFERENCES public.vr_sessions(id) ON DELETE CASCADE,
    
    -- Event metadata
    event_type TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Event data (JSONB for flexibility)
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Record metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes for fast queries
    CONSTRAINT event_type_check CHECK (event_type IN (
        'gaze', 'zone_enter', 'zone_exit', 'interaction', 
        'teleport', 'hand_tracking', 'voice_command', 'other'
    ))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_session ON public.tracking_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON public.tracking_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON public.tracking_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_data ON public.tracking_events USING GIN (event_data);

-- Enable Row Level Security (RLS)
ALTER TABLE public.tracking_events ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for service_role
CREATE POLICY "Allow all for service role"
ON public.tracking_events
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

COMMENT ON TABLE public.tracking_events IS 'Stores VR interaction tracking events';
```

Click **"Run"**

✅ You should see: `Success. No rows returned`

### 3.4 Verify Tables Created

Run this query:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('vr_sessions', 'tracking_events');
```

You should see:
```
table_name
━━━━━━━━━━━━━━━━
vr_sessions
tracking_events
```

✅ **Tables created successfully!**

---

## 🔧 Step 4: Update Your `.env` File (2 minutes)

### 4.1 Open `.env` file

Located at: `c:\Users\Saahil Tamboli\Desktop\Nexero\nexero-backend\.env`

### 4.2 Replace Placeholder Values

Replace these lines:

```env
# ❌ OLD (placeholders)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here
```

With your actual credentials:

```env
# ✅ NEW (your actual values)
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJl...
```

⚠️ **Important:**
- URL should start with `https://` and end with `.supabase.co`
- Key should be a very long string starting with `eyJ`
- Use the **service_role** key, not anon/public key!

### 4.3 Save the File

Press `Ctrl+S` to save.

---

## 🧪 Step 5: Test Database Connection (5 minutes)

### 5.1 Test with Python Script

Create a test script:

```powershell
cd "c:\Users\Saahil Tamboli\Desktop\Nexero\nexero-backend"
```

Create `test_supabase.py`:

```python
"""Quick test to verify Supabase connection"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("Testing Supabase Connection")
print("=" * 60)
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "Key: None")
print()

try:
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client created")
    
    # Test: Create a test session
    test_session = {
        "customer_id": "test_customer_001",
        "property_id": "test_property_001",
        "session_start": "2025-10-03T12:00:00Z",
        "status": "active"
    }
    
    result = supabase.table("vr_sessions").insert(test_session).execute()
    print("✓ Test session created!")
    print(f"  Session ID: {result.data[0]['id']}")
    
    # Test: Read it back
    session_id = result.data[0]['id']
    read_result = supabase.table("vr_sessions").select("*").eq("id", session_id).execute()
    print("✓ Test session retrieved!")
    print(f"  Customer ID: {read_result.data[0]['customer_id']}")
    
    # Test: Delete it
    supabase.table("vr_sessions").delete().eq("id", session_id).execute()
    print("✓ Test session deleted!")
    
    print()
    print("=" * 60)
    print("✓✓✓ SUCCESS! Supabase is working perfectly!")
    print("=" * 60)
    
except Exception as e:
    print()
    print("=" * 60)
    print("✗✗✗ ERROR!")
    print("=" * 60)
    print(f"Error: {e}")
    print()
    print("Common issues:")
    print("1. Check SUPABASE_URL is correct")
    print("2. Check SUPABASE_KEY is the service_role key")
    print("3. Check tables exist (run SQL queries above)")
    print("4. Check RLS policies allow service_role access")
```

### 5.2 Run the Test

```powershell
python test_supabase.py
```

**Expected output:**
```
============================================================
Testing Supabase Connection
============================================================
URL: https://abcdefghijklmnop.supabase.co
Key: eyJhbGciOiJIUzI1NiIsI...

✓ Supabase client created
✓ Test session created!
  Session ID: 550e8400-e29b-41d4-a716-446655440000
✓ Test session retrieved!
  Customer ID: test_customer_001
✓ Test session deleted!

============================================================
✓✓✓ SUCCESS! Supabase is working perfectly!
============================================================
```

✅ **If you see this, you're all set!**

---

## 🚀 Step 6: Test Your Full Backend (5 minutes)

### 6.1 Start Your Backend

```powershell
cd "c:\Users\Saahil Tamboli\Desktop\Nexero\nexero-backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

### 6.2 Run Test Client

Open a **new terminal**:

```powershell
cd "c:\Users\Saahil Tamboli\Desktop\Nexero\nexero-backend"
.\.venv\Scripts\Activate.ps1
python test_unreal_client.py
```

**Expected output:**
```
✓ Session created! ID: 550e8400-e29b-41d4-a716-446655440000
✓ Events sent successfully!
✓ 15/15 events processed (100% success)
```

✅ **If you see this, your backend + Supabase is fully working!**

---

## 📊 Step 7: View Your Data in Supabase (2 minutes)

### 7.1 Table Editor

1. In Supabase dashboard, click **"Table Editor"** in left sidebar
2. Click **"vr_sessions"**
3. You'll see your test sessions! 🎉
4. Click **"tracking_events"**
5. You'll see all the VR interactions! 🎉

### 7.2 SQL Editor (Advanced Queries)

Try these queries:

**See all sessions:**
```sql
SELECT id, customer_id, property_id, status, duration_seconds
FROM vr_sessions
ORDER BY created_at DESC
LIMIT 10;
```

**See events for a session:**
```sql
SELECT event_type, timestamp, event_data
FROM tracking_events
WHERE session_id = 'YOUR-SESSION-ID-HERE'
ORDER BY timestamp;
```

**Count events by type:**
```sql
SELECT event_type, COUNT(*) as count
FROM tracking_events
GROUP BY event_type
ORDER BY count DESC;
```

---

## 🔐 Step 8: Update Railway Environment Variables

When deploying to Railway, add these environment variables:

1. Go to Railway dashboard
2. Select your project
3. Click **"Variables"**
4. Add:

```
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

⚠️ **Use the same values from your `.env` file!**

---

## 🎓 Supabase Dashboard Overview

### Key Sections:

1. **Table Editor** 📊
   - View/edit data visually
   - Add/delete rows manually
   - Filter and sort data

2. **SQL Editor** 💻
   - Run custom SQL queries
   - Create tables, indexes
   - Saved queries

3. **API Docs** 📚
   - Auto-generated API documentation
   - Shows all table operations
   - Code examples

4. **Database** 🗄️
   - Schema visualization
   - Relationships
   - Indexes

5. **Logs** 📝
   - Query logs
   - Error logs
   - Performance metrics

---

## 🐛 Troubleshooting

### Issue: "Invalid API key"

**Fix:**
- Ensure you're using **service_role** key, not anon/public
- Copy the entire key (very long, starts with `eyJ`)
- Check no extra spaces in `.env` file

### Issue: "relation 'vr_sessions' does not exist"

**Fix:**
- Run the SQL queries in Step 3 again
- Make sure you selected the correct database/schema (should be `public`)
- Check Table Editor to confirm tables exist

### Issue: "permission denied for table vr_sessions"

**Fix:**
- Check RLS policies are created (Step 3)
- Ensure using `service_role` key (has admin rights)
- Run this to disable RLS temporarily:
  ```sql
  ALTER TABLE public.vr_sessions DISABLE ROW LEVEL SECURITY;
  ALTER TABLE public.tracking_events DISABLE ROW LEVEL SECURITY;
  ```

### Issue: "getaddrinfo failed"

**Fix:**
- Check SUPABASE_URL is correct (copy from Settings > API)
- Ensure URL includes `https://`
- Check internet connection

---

## 📈 Free Tier Limits

Supabase Free Plan includes:
- ✅ 500 MB database space
- ✅ 1 GB file storage
- ✅ 50,000 monthly active users
- ✅ 2 GB bandwidth
- ✅ 500 MB egress
- ✅ Social OAuth providers
- ✅ 7-day log retention

**Perfect for development and testing!**

Upgrade to Pro ($25/month) when you need more.

---

## ✅ Setup Complete Checklist

- [ ] ✅ Supabase account created
- [ ] ✅ Project created
- [ ] ✅ API credentials copied
- [ ] ✅ `vr_sessions` table created
- [ ] ✅ `tracking_events` table created
- [ ] ✅ `.env` file updated with real credentials
- [ ] ✅ Test script passed
- [ ] ✅ Backend connects successfully
- [ ] ✅ Test client works end-to-end
- [ ] ✅ Data visible in Table Editor

---

## 🎉 You're Done!

Your Supabase database is fully configured and connected to Nexero VR Backend!

**Next steps:**
1. Deploy to Railway (see `RAILWAY_DEPLOY.md`)
2. Test with real Unreal Engine client
3. Build analytics dashboards
4. Scale as needed!

---

## 📚 Useful Links

- Supabase Dashboard: https://app.supabase.com
- Supabase Docs: https://supabase.com/docs
- Python Client Docs: https://supabase.com/docs/reference/python/introduction
- SQL Tutorial: https://supabase.com/docs/guides/database

---

**Need help?** Check the error messages carefully - they're usually very clear about what's wrong!
