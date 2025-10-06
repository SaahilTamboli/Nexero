# 🚂 RAILWAY DEPLOYMENT - STEP-BY-STEP GUIDE

**Time Required**: 10-15 minutes  
**Cost**: Free for first month ($5 credit), then ~$5-10/month  
**Difficulty**: ⭐ Very Easy

---

## ✅ **PRE-DEPLOYMENT CHECKLIST**

Before we start, verify you have:

- [x] ✅ Code pushed to GitHub (https://github.com/SaahilTamboli/Nexero)
- [x] ✅ Supabase database set up
- [x] ✅ Supabase credentials ready (URL and service_role key)
- [x] ✅ Railway configuration files (`railway.toml`, `Procfile`, `runtime.txt`)

**Status**: 🟢 ALL READY! Let's deploy!

---

## 📋 **STEP 1: Create Railway Account** (2 minutes)

### 1.1 Go to Railway
```
🌐 Open: https://railway.app
```

### 1.2 Sign Up with GitHub
1. Click **"Start a New Project"** or **"Login"**
2. Choose **"Login with GitHub"**
3. Click **"Authorize Railway"** when prompted
4. ✅ You're in!

**What you get:**
- $5 free credit (lasts ~1 month)
- No credit card required initially

---

## 🚀 **STEP 2: Deploy from GitHub** (3 minutes)

### 2.1 Create New Project
1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**

### 2.2 Connect Your Repository
1. You'll see a list of your GitHub repositories
2. Find and click **"SaahilTamboli/Nexero"**
3. Railway will ask: "Which folder?" 
   - Select **"nexero-backend"** (or leave as root if it auto-detects)

### 2.3 Railway Auto-Detection
Railway will automatically detect:
- ✅ Python project
- ✅ `requirements.txt`
- ✅ `railway.toml` configuration
- ✅ `Procfile` start command
- ✅ `runtime.txt` (Python 3.11)

**You'll see:**
```
🔍 Detected: Python Application
📦 Installing dependencies...
🚀 Building...
```

⏳ **Wait 2-3 minutes** for initial build

---

## 🔧 **STEP 3: Configure Environment Variables** (5 minutes)

⚠️ **IMPORTANT**: Your app won't work without these!

### 3.1 Open Variables Tab
1. In your Railway project, click **"Variables"** tab (left sidebar)
2. Click **"New Variable"**

### 3.2 Add Required Variables

Add these one by one:

#### **Variable 1: SUPABASE_URL**
```
Name:  SUPABASE_URL
Value: https://your-project.supabase.co
```
**Where to get it:**
- Go to Supabase dashboard → Settings → API → Project URL

#### **Variable 2: SUPABASE_KEY**
```
Name:  SUPABASE_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
**Where to get it:**
- Go to Supabase dashboard → Settings → API → service_role key
- ⚠️ Use `service_role`, NOT `anon public`
- Click the eye icon to reveal the key

#### **Variable 3: ENVIRONMENT**
```
Name:  ENVIRONMENT
Value: production
```

#### **Variable 4: LOG_LEVEL**
```
Name:  LOG_LEVEL
Value: info
```

#### **Variable 5: CORS_ORIGINS**
```
Name:  CORS_ORIGINS
Value: ["*"]
```
**Note**: Update this later to restrict to your domain

#### **Variable 6: API_VERSION**
```
Name:  API_VERSION
Value: v1
```

### 3.3 Save Variables
- Click **"Add"** after each variable
- Railway will automatically redeploy with new variables

---

## 🌐 **STEP 4: Generate Public Domain** (1 minute)

### 4.1 Open Settings
1. Click **"Settings"** tab in left sidebar
2. Scroll to **"Networking"** section

### 4.2 Generate Domain
1. Click **"Generate Domain"**
2. Railway will create a URL like:
   ```
   https://nexero-vr-backend-production.up.railway.app
   ```
3. ✅ Copy this URL - this is your API's public address!

**Optional: Custom Domain**
- Click "Add Custom Domain"
- Enter your domain (e.g., `api.nexero.com`)
- Follow DNS instructions
- (You can do this later)

---

## ✅ **STEP 5: Verify Deployment** (2 minutes)

### 5.1 Check Build Logs
1. Click **"Deployments"** tab
2. Click on the latest deployment
3. Watch logs scroll:
   ```
   ✅ Installing Python 3.11
   ✅ Installing dependencies from requirements.txt
   ✅ Starting uvicorn server
   ✅ Application startup complete
   ```

### 5.2 Test Your API

#### **Test 1: Health Check**
Open in browser:
```
https://your-railway-url.up.railway.app/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T...",
  "environment": "production",
  "database": "connected",
  "version": "1.0.0",
  "uptime": "running"
}
```

✅ If you see this, **SUCCESS!**

#### **Test 2: API Documentation**
Open in browser:
```
https://your-railway-url.up.railway.app/docs
```

You should see:
- ✅ Interactive FastAPI documentation
- ✅ All your endpoints listed
- ✅ Ability to test endpoints

#### **Test 3: Send Test Session**

Using curl or Postman:
```bash
curl -X POST https://your-railway-url.up.railway.app/api/v1/unreal/session \
  -H "Content-Type: application/json" \
  -d '{
    "session_start": "1727653800",
    "session_end": "1727654100",
    "customer_id": "test_customer",
    "property_id": "test_property"
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Session data received and processed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_seconds": 300,
  "received_at": "2025-10-06T..."
}
```

✅ If you see this, **FULLY WORKING!**

---

## 📊 **STEP 6: Monitor Your Deployment**

### 6.1 View Logs
1. Click **"Deployments"** → Click latest deployment
2. See real-time logs:
   ```
   INFO: Application startup complete.
   INFO: 127.0.0.1 - "GET /health HTTP/1.1" 200 OK
   INFO: 127.0.0.1 - "POST /api/v1/unreal/session HTTP/1.1" 201 Created
   ```

### 6.2 Monitor Usage
1. Click **"Metrics"** tab
2. See:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### 6.3 Check Billing
1. Click your profile (top right)
2. Go to **"Usage"**
3. See your $5 credit balance
4. Monitor daily spend (~$0.20/day)

---

## 🔄 **STEP 7: Enable Auto-Deploy** (Already Done!)

Good news: **Auto-deploy is enabled by default!**

### How It Works:
1. You make changes to code locally
2. Push to GitHub: `git push origin main`
3. Railway automatically detects the push
4. Rebuilds and redeploys (2-3 minutes)
5. Your changes are live!

### Test Auto-Deploy:
```bash
# Make a small change
echo "# Updated" >> README.md

# Commit and push
git add .
git commit -m "Test auto-deploy"
git push origin main

# Watch Railway dashboard
# You'll see: "Deploying..." → "Deployed"
```

---

## 🎯 **STEP 8: Share with Your Friend**

Your backend is now live! Share these details:

### **API Base URL:**
```
https://your-railway-url.up.railway.app
```

### **API Documentation:**
```
https://your-railway-url.up.railway.app/docs
```

### **Health Check:**
```
https://your-railway-url.up.railway.app/health
```

### **Test Endpoint:**
```bash
curl -X POST https://your-railway-url.up.railway.app/api/v1/unreal/session \
  -H "Content-Type: application/json" \
  -d '{
    "session_start": "1727653800",
    "session_end": "1727654100"
  }'
```

**Your friend can:**
- ✅ View API docs in browser
- ✅ Test endpoints via `/docs` interface
- ✅ Send requests from their Unreal Engine client
- ✅ Access from anywhere in the world

---

## 🔧 **TROUBLESHOOTING**

### **Problem 1: Build Failed**

**Check:**
1. Railway logs (Deployments → Latest → View logs)
2. Look for error messages

**Common Issues:**
- Missing dependency in `requirements.txt`
- Python version mismatch
- Syntax errors in code

**Fix:**
```bash
# Fix the issue locally
# Push to GitHub
git push origin main
# Railway auto-redeploys
```

### **Problem 2: App Crashes on Start**

**Check:**
1. Logs show: "Application failed to start"
2. Environment variables

**Fix:**
- Verify all 6 environment variables are set
- Check `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Test Supabase connection locally first

### **Problem 3: 502 Bad Gateway**

**Means:**
- App is starting up (wait 30 seconds)
- Or app crashed (check logs)

**Fix:**
- Wait for deployment to complete
- Check logs for errors
- Restart deployment manually

### **Problem 4: Database Connection Failed**

**Error in logs:**
```
Failed to create session: {...}
```

**Fix:**
1. Verify Supabase credentials
2. Check Supabase database tables exist:
   - `vr_sessions`
   - `tracking_events`
3. Run SQL from `SUPABASE_SETUP.md` if needed

### **Problem 5: Out of Free Credit**

**When:**
- After ~25-30 days ($5 credit depleted)

**Fix:**
1. Add payment method to Railway
2. Or migrate to Render free tier
3. Cost is only ~$5-10/month

---

## 💡 **RAILWAY PRO TIPS**

### **Tip 1: Use Railway CLI** (Optional but Powerful)

Install:
```bash
npm install -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

Usage:
```bash
railway login              # Login to Railway
railway link               # Link to your project
railway logs               # View live logs
railway run python main.py # Run commands in Railway environment
railway open               # Open project in browser
railway status             # Check deployment status
```

### **Tip 2: Set Up Webhooks** (Advanced)

Get notified on deployment events:
1. Settings → Webhooks
2. Add your Discord/Slack webhook URL
3. Get notifications on:
   - Successful deploys
   - Failed builds
   - Crashed apps

### **Tip 3: Configure Health Checks**

Already done in your `railway.toml`:
```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
```

Railway pings `/health` to verify app is running.

### **Tip 4: View Database Connections**

In Railway:
1. Add Supabase as a service (optional)
2. Or use environment variables (current method)

### **Tip 5: Custom Domains**

Free with Railway:
1. Settings → Networking → Custom Domain
2. Add your domain (e.g., `api.nexero.com`)
3. Update DNS:
   ```
   CNAME  api  your-railway-url.up.railway.app
   ```
4. Wait for DNS propagation (5-60 minutes)

---

## 📊 **COST ESTIMATION**

### **Month 1:**
- **Cost**: $0 (using $5 credit)
- **Credit used**: ~$4-5
- **Credit left**: $0-1

### **Month 2+:**
- **Daily**: ~$0.20-0.30
- **Monthly**: ~$6-9
- **Includes**: 
  - Hosting
  - Bandwidth
  - Auto-deploy
  - Monitoring
  - Logs

### **Cost Breakdown:**
```
Base compute: $5/month
Memory usage: $0-2/month
Network traffic: $1-2/month
Total: $6-9/month
```

**Worth it?** ✅ YES!
- No server management
- Auto-scaling
- Professional monitoring
- Zero downtime deploys
- Better than managing your own VPS

---

## 🎉 **SUCCESS CHECKLIST**

After deployment, verify:

- [ ] ✅ Railway project created
- [ ] ✅ GitHub connected
- [ ] ✅ Build successful (green checkmark)
- [ ] ✅ 6 environment variables added
- [ ] ✅ Public domain generated
- [ ] ✅ `/health` endpoint returns 200 OK
- [ ] ✅ `/docs` shows API documentation
- [ ] ✅ Test session creation works
- [ ] ✅ Logs show no errors
- [ ] ✅ URL shared with friend

---

## 🚀 **NEXT STEPS**

### **Immediate:**
1. ✅ Test all endpoints via `/docs`
2. ✅ Send test data from your local test client
3. ✅ Verify data appears in Supabase
4. ✅ Share URL with your friend

### **This Week:**
1. Monitor usage and costs
2. Test with real Unreal Engine client
3. Check logs for errors
4. Add custom domain (optional)

### **Long-term:**
1. Implement security fixes (from `SECURITY_FIXES.md`)
2. Add authentication
3. Restrict CORS origins
4. Add rate limiting
5. Set up monitoring alerts

---

## 📚 **USEFUL RESOURCES**

- **Railway Dashboard**: https://railway.app/dashboard
- **Railway Docs**: https://docs.railway.app
- **Python Guide**: https://docs.railway.app/guides/python
- **Your Repo**: https://github.com/SaahilTamboli/Nexero
- **Supabase**: https://app.supabase.com

---

## 🆘 **NEED HELP?**

### **If Something Goes Wrong:**

1. **Check Railway logs first**
   - Deployments → Latest → View logs
   - Look for error messages

2. **Check environment variables**
   - Variables tab
   - Verify all 6 are set correctly

3. **Check Supabase**
   - Test connection locally
   - Verify tables exist
   - Check credentials

4. **Check GitHub**
   - Ensure code is pushed
   - Check for syntax errors

5. **Ask for help**
   - Railway Discord: https://discord.gg/railway
   - Railway Docs: https://docs.railway.app

---

## ✅ **DEPLOYMENT COMPLETE!**

**Your Nexero VR Backend is now LIVE! 🎉**

**API URL**: `https://your-railway-url.up.railway.app`  
**Status**: 🟢 Running  
**Cost**: Free for first month  
**Access**: Available worldwide  

### **What You Achieved:**
✅ Professional backend deployment  
✅ Auto-deploy from GitHub  
✅ Monitoring and logs  
✅ Public API for Unreal Engine  
✅ Scalable infrastructure  

### **What Your Friend Can Do:**
✅ Access API from anywhere  
✅ View documentation at `/docs`  
✅ Test endpoints interactively  
✅ Send VR session data from Unreal  

---

**Congratulations! You've successfully deployed to Railway! 🚂🎉**

**Share your API URL and start collecting VR analytics!**
