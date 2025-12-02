# 🚀 NEXERO DEPLOYMENT OPTIONS - RAILWAY FREE PLAN EXPIRED

**Date:** November 8, 2025  
**Current Status:** Railway free plan expired  
**Need:** Free or low-cost deployment alternative  

---

## 📊 QUICK COMPARISON

| Platform | Free Tier | Python Support | PostgreSQL | Deployment | Best For |
|----------|-----------|----------------|------------|------------|----------|
| **Render** | ✅ Yes | ✅ FastAPI | ✅ Free DB | Git auto-deploy | **RECOMMENDED** |
| **Fly.io** | ✅ Yes | ✅ Python | ✅ Free DB | CLI deploy | Advanced users |
| **Railway** | ❌ Trial only | ✅ FastAPI | ✅ Included | Git auto-deploy | Paid ($5/mo) |
| **Vercel** | ✅ Yes | ⚠️ Serverless | ❌ External | Git auto-deploy | Frontend heavy |
| **Heroku** | ❌ Paid only | ✅ FastAPI | ✅ Paid addon | Git deploy | Legacy apps |

---

## 🎯 RECOMMENDED: RENDER (100% FREE)

### Why Render?
- ✅ **Generous Free Tier** - 750 hours/month (enough for 1 app 24/7)
- ✅ **Free PostgreSQL** - 1GB database included
- ✅ **Auto-deploy from GitHub** - Like Railway
- ✅ **No credit card required**
- ✅ **FastAPI friendly** - Native Python support
- ✅ **Free SSL certificate** - HTTPS automatic
- ✅ **Similar to Railway** - Easy migration

### Free Tier Limits
- **Web Service:** 750 hours/month (31 days = 744 hours) ✅
- **PostgreSQL:** 1GB storage, expires after 90 days of inactivity
- **Bandwidth:** 100GB/month
- **Build time:** Unlimited
- **Auto-sleep:** After 15 minutes of inactivity (wakes on request)

### Limitations
⚠️ **Auto-sleep:** App goes to sleep after 15 min inactivity
- First request after sleep: ~30 seconds to wake up
- Subsequent requests: Normal speed (<200ms)
- **Solution:** Use a free uptime monitor (UptimeRobot) to ping every 14 minutes

---

## 🚀 DEPLOYMENT GUIDE: RENDER

### **Step 1: Create Render Account (2 minutes)**

1. Go to **https://render.com**
2. Click **"Sign Up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Render to access your repositories

---

### **Step 2: Create PostgreSQL Database (3 minutes)**

1. Dashboard → Click **"New +"**
2. Select **"PostgreSQL"**
3. Fill in:
   ```
   Name: nexero-db
   Database: nexero
   User: nexero
   Region: Singapore (or closest to you)
   ```
4. Click **"Create Database"**
5. **Copy the connection details:**
   - Internal Database URL (starts with `postgres://`)
   - External Database URL (for local testing)

**Important:** Save the external URL for Supabase migration!

---

### **Step 3: Migrate Supabase Data (Optional - 10 minutes)**

#### Option A: Start Fresh (Recommended)
- Skip this step
- Render PostgreSQL will be empty
- Tables will be created automatically

#### Option B: Migrate Existing Data

**Export from Supabase:**
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Export data
supabase db dump --project-ref uutpfpottowcfxxymtoy > supabase_backup.sql
```

**Import to Render:**
```bash
# Connect to Render PostgreSQL (use external URL)
psql "postgres://nexero_user:password@oregon-postgres.render.com/nexero_db"

# Import schema and data
\i supabase_backup.sql
```

**OR Use GUI Tool (Easier):**
1. Download **pgAdmin** or **DBeaver**
2. Connect to Supabase (old database)
3. Export tables as SQL
4. Connect to Render (new database)
5. Import SQL file

---

### **Step 4: Update Code for Render PostgreSQL (5 minutes)**

**Current:** Your code uses Supabase client  
**Change to:** Direct PostgreSQL connection

**Install PostgreSQL library:**
```bash
pip install asyncpg psycopg2-binary
```

**Update `requirements.txt`:**
```txt
fastapi==0.118.0
uvicorn[standard]==0.37.0
pydantic==2.11.10
pydantic-settings==2.11.0
asyncpg==0.29.0
psycopg2-binary==2.9.9
python-dotenv==1.1.1
httpx==0.28.1
```

**Update `app/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Render PostgreSQL
    DATABASE_URL: str  # NEW: Render provides this
    
    # Application settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: list = ["*"]
    API_VERSION: str = "v1"
    
    class Config:
        env_file = ".env"
```

**Update `app/core/database.py`:**
```python
import asyncpg
from typing import Optional, List, Dict

class PostgresDB:
    def __init__(self):
        self.database_url = get_settings().DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url)
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def create_session(self, session_data: dict) -> Optional[dict]:
        """Insert session into PostgreSQL"""
        query = """
            INSERT INTO vr_sessions (started_at, ended_at, customer_id, property_id, device_type)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, started_at, ended_at, status
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                session_data["started_at"],
                session_data.get("ended_at"),
                session_data.get("customer_id"),
                session_data.get("property_id"),
                session_data.get("device_type")
            )
            return dict(row) if row else None
    
    async def insert_tracking_event(self, event_data: dict) -> bool:
        """Insert tracking event"""
        query = """
            INSERT INTO tracking_events (session_id, event_type, timestamp, event_data)
            VALUES ($1, $2, $3, $4)
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    event_data["session_id"],
                    event_data["event_type"],
                    event_data["timestamp"],
                    event_data.get("event_data")
                )
                return True
            except Exception as e:
                print(f"Error inserting event: {e}")
                return False
```

**Update `app/main.py`:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to database
    db = get_database()
    await db.connect()
    yield
    # Shutdown: Close database connection
    await db.close()

app = FastAPI(
    title="Nexero VR Backend",
    version="1.0.0",
    lifespan=lifespan
)
```

---

### **Step 5: Create Render Web Service (5 minutes)**

1. Dashboard → Click **"New +"**
2. Select **"Web Service"**
3. Connect your GitHub repository: **SaahilTamboli/Nexero**
4. Fill in:

```
Name: nexero-backend
Region: Singapore (or closest)
Branch: production
Root Directory: nexero-backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Click **"Advanced"**
6. Add **Environment Variables:**

```
DATABASE_URL = [Paste Internal Database URL from Step 2]
ENVIRONMENT = production
LOG_LEVEL = info
CORS_ORIGINS = ["*"]
API_VERSION = v1
```

7. Click **"Create Web Service"**

---

### **Step 6: Wait for Deployment (3-5 minutes)**

Render will:
1. Clone your repository
2. Install dependencies
3. Start uvicorn server
4. Assign a URL: `https://nexero-backend.onrender.com`

**Watch the logs for:**
```
✓ Build successful
✓ Starting service
✓ Application startup complete
✓ Uvicorn running on 0.0.0.0:10000
```

---

### **Step 7: Test Your Deployed API**

**Health Check:**
```bash
curl https://nexero-backend.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T...",
  "environment": "production",
  "database": "connected"
}
```

**Test Session Creation:**
```powershell
$body = @{session_start="1731000000"; session_end="1731000300"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://nexero-backend.onrender.com/api/v1/unreal/session" -Method Post -Body $body -ContentType "application/json"
```

---

### **Step 8: Prevent Auto-Sleep (Optional)**

**Problem:** Free tier sleeps after 15 minutes of inactivity

**Solution: Use UptimeRobot (Free)**

1. Go to **https://uptimerobot.com**
2. Sign up (free account)
3. Add Monitor:
   ```
   Monitor Type: HTTP(s)
   Friendly Name: Nexero Health Check
   URL: https://nexero-backend.onrender.com/health
   Monitoring Interval: 5 minutes
   ```
4. Click **"Create Monitor"**

**Result:** Your app will never sleep! ✅

---

## 💰 COST COMPARISON

### Option 1: Render Free Tier (RECOMMENDED)
```
Web Service: FREE (with auto-sleep)
PostgreSQL: FREE (1GB, 90 days)
SSL Certificate: FREE
Custom Domain: FREE

Total: $0/month ✅
```

**Limitations:**
- Auto-sleep after 15 min (use UptimeRobot to prevent)
- PostgreSQL expires after 90 days inactivity
- 750 hours/month web service

---

### Option 2: Render Paid Plan
```
Web Service: $7/month (no auto-sleep)
PostgreSQL: $7/month (256MB, no expiry)
SSL Certificate: FREE
Custom Domain: FREE

Total: $14/month
```

**Benefits:**
- No auto-sleep
- More reliable database
- Better performance

---

### Option 3: Fly.io Free Tier
```
3 shared-cpu VMs: FREE
256MB RAM per VM: FREE
3GB persistent storage: FREE
160GB bandwidth: FREE

Total: $0/month ✅
```

**Benefits:**
- No auto-sleep
- Better performance
- Multi-region support

**Drawbacks:**
- More complex setup
- CLI-based deployment
- Requires Dockerfile

---

### Option 4: Railway Hobby Plan
```
$5/month base + usage
Includes: $5 credit (~550 hours)

Total: $5-10/month
```

**Benefits:**
- Same setup as before
- Familiar dashboard
- No auto-sleep

**Drawbacks:**
- Not free
- Credit card required

---

## 🎯 MY RECOMMENDATION

### **For Your Use Case:**

**Go with Render Free Tier + UptimeRobot**

**Why?**
1. ✅ **100% Free** - No credit card needed
2. ✅ **Easy Migration** - Similar to Railway
3. ✅ **Auto-deploy** - Push to GitHub = automatic deployment
4. ✅ **Free Database** - PostgreSQL included
5. ✅ **No Auto-sleep** - With UptimeRobot ping
6. ✅ **FastAPI Friendly** - Native Python support

**Setup Time:** ~30 minutes total

---

## 📋 MIGRATION CHECKLIST

### Phase 1: Prepare Code (15 minutes)
- [ ] Install asyncpg and psycopg2-binary
- [ ] Update requirements.txt
- [ ] Replace Supabase client with PostgreSQL client
- [ ] Update config.py for DATABASE_URL
- [ ] Update database.py with asyncpg
- [ ] Test locally with PostgreSQL connection
- [ ] Commit and push to GitHub

### Phase 2: Setup Render (10 minutes)
- [ ] Create Render account
- [ ] Create PostgreSQL database
- [ ] Copy database connection URL
- [ ] Create Web Service
- [ ] Link GitHub repository
- [ ] Configure environment variables
- [ ] Set build and start commands

### Phase 3: Deploy & Test (10 minutes)
- [ ] Trigger deployment
- [ ] Watch build logs
- [ ] Test health endpoint
- [ ] Test session creation
- [ ] Verify database connection
- [ ] Check API documentation (/docs)

### Phase 4: Optimize (5 minutes)
- [ ] Setup UptimeRobot monitoring
- [ ] Configure custom domain (optional)
- [ ] Update CORS_ORIGINS (restrict if needed)
- [ ] Share new URL with team

---

## 🆘 TROUBLESHOOTING

### **Issue: "Database connection failed"**
**Solution:**
```python
# Make sure DATABASE_URL is set in Render environment variables
# Format: postgres://user:password@host:port/database
```

### **Issue: "Module not found: asyncpg"**
**Solution:**
```bash
# Add to requirements.txt:
asyncpg==0.29.0
psycopg2-binary==2.9.9
```

### **Issue: "App sleeps after 15 minutes"**
**Solution:**
- Use UptimeRobot to ping every 5 minutes
- OR upgrade to Render paid plan ($7/mo, no sleep)

### **Issue: "Build failed"**
**Solution:**
```bash
# Check Render logs
# Common fix: Update Python version in render.yaml
```

---

## 🚀 ALTERNATIVE: FLY.IO (FOR ADVANCED USERS)

### Why Fly.io?
- ✅ **No auto-sleep** (better than Render free tier)
- ✅ **Better performance** (dedicated resources)
- ✅ **Multi-region** (deploy close to users)
- ✅ **Free tier generous** (3 VMs, 3GB storage)

### Setup Fly.io (20 minutes)

**1. Install Fly.io CLI:**
```powershell
# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

**2. Login:**
```bash
fly auth login
```

**3. Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY nexero-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nexero-backend/app ./app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**4. Create fly.toml:**
```toml
app = "nexero-backend"
primary_region = "sin"

[build]
  dockerfile = "Dockerfile"

[env]
  ENVIRONMENT = "production"
  LOG_LEVEL = "info"
  API_VERSION = "v1"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

**5. Create PostgreSQL:**
```bash
fly postgres create --name nexero-db --region sin
```

**6. Attach Database:**
```bash
fly postgres attach nexero-db --app nexero-backend
```

**7. Deploy:**
```bash
fly deploy
```

**8. Get URL:**
```bash
fly info
# URL: https://nexero-backend.fly.dev
```

---

## 📊 FINAL RECOMMENDATION MATRIX

| Your Priority | Best Choice | Cost | Setup Time |
|---------------|-------------|------|------------|
| **Easiest migration** | Render | Free | 30 min |
| **Best performance** | Fly.io | Free | 45 min |
| **Most familiar** | Railway | $5/mo | 5 min |
| **Zero setup** | Keep Railway | $5/mo | 0 min |

---

## 🎯 ACTION PLAN

### **I recommend: Render Free Tier**

**Reasons:**
1. Same workflow as Railway
2. 100% free (no credit card)
3. Easy GitHub integration
4. Free PostgreSQL included
5. Can upgrade later if needed

**Next Steps:**
1. Create Render account (2 min)
2. I'll help you update the code for PostgreSQL (15 min)
3. Deploy to Render (10 min)
4. Setup UptimeRobot (5 min)
5. Test and verify (5 min)

**Total time: 37 minutes to be back online!**

---

**Ready to migrate? Tell me which option you prefer and I'll guide you through the exact steps!** 🚀

Options:
1. **Render (Easy & Free)** - My recommendation
2. **Fly.io (Better performance)** - For advanced users
3. **Pay for Railway ($5/mo)** - Keep current setup
4. **Something else?** - Tell me your constraints
