# 🚂 RAILWAY DEPLOYMENT GUIDE

## Quick Deploy (5 Minutes)

### Option 1: Deploy via Railway Dashboard (Easiest)

1. **Create GitHub Repository**
   ```powershell
   cd "c:\Users\Saahil Tamboli\Desktop\Nexero\nexero-backend"
   git init
   git add .
   git commit -m "Initial commit - Nexero VR Backend"
   ```

2. **Push to GitHub**
   - Create new repo on GitHub: https://github.com/new
   - Name it: `nexero-vr-backend`
   - Then:
   ```powershell
   git remote add origin https://github.com/YOUR-USERNAME/nexero-vr-backend.git
   git branch -M main
   git push -u origin main
   ```

3. **Deploy on Railway**
   - Go to: https://railway.app
   - Click "Start a New Project"
   - Choose "Deploy from GitHub repo"
   - Select `nexero-vr-backend`
   - Railway auto-detects Python and deploys! 🚀

4. **Add Environment Variables**
   - In Railway dashboard, click your project
   - Go to "Variables" tab
   - Add these:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   ENVIRONMENT=production
   LOG_LEVEL=info
   CORS_ORIGINS=["*"]
   API_VERSION=v1
   ```

5. **Get Your URL**
   - Railway provides: `https://nexero-vr-backend-production.up.railway.app`
   - Click "Settings" → "Generate Domain"

---

### Option 2: Deploy via Railway CLI (Advanced)

1. **Install Railway CLI**
   ```powershell
   npm install -g @railway/cli
   # Or
   iwr https://railway.app/install.ps1 | iex
   ```

2. **Login to Railway**
   ```powershell
   railway login
   ```

3. **Initialize Project**
   ```powershell
   cd "c:\Users\Saahil Tamboli\Desktop\Nexero\nexero-backend"
   railway init
   ```

4. **Add Environment Variables**
   ```powershell
   railway variables set SUPABASE_URL=https://your-project.supabase.co
   railway variables set SUPABASE_KEY=your-service-role-key
   railway variables set ENVIRONMENT=production
   railway variables set LOG_LEVEL=info
   railway variables set CORS_ORIGINS='["*"]'
   railway variables set API_VERSION=v1
   ```

5. **Deploy**
   ```powershell
   railway up
   ```

6. **Get URL**
   ```powershell
   railway domain
   ```

---

## 📋 Deployment Checklist

Before deploying, ensure:

- [x] ✅ `railway.toml` created
- [x] ✅ `Procfile` created
- [x] ✅ `runtime.txt` created
- [x] ✅ `requirements.txt` exists
- [x] ✅ `.gitignore` includes `.env`
- [x] ✅ `app/main.py` uses `$PORT` environment variable
- [ ] ⚠️ Update SUPABASE credentials
- [ ] ⚠️ Update CORS_ORIGINS for production

---

## 🔧 Post-Deployment

### 1. Test Your Deployment

```powershell
# Replace with your Railway URL
$RAILWAY_URL = "https://nexero-vr-backend-production.up.railway.app"

# Test health check
curl "$RAILWAY_URL/health"

# View API docs
# Open in browser: $RAILWAY_URL/docs
```

### 2. Update CORS for Production

Once deployed, update CORS to restrict access:

In Railway dashboard → Variables:
```
CORS_ORIGINS=["https://yourdomain.com","https://dashboard.nexero.com"]
```

### 3. Monitor Logs

```powershell
# View live logs
railway logs
```

Or in Railway dashboard → "Logs" tab

---

## 📱 Share with Your Friend

After deployment, send your friend:

**API Base URL:**
```
https://nexero-vr-backend-production.up.railway.app
```

**API Documentation:**
```
https://nexero-vr-backend-production.up.railway.app/docs
```

**Test with remote_test_client.py:**
```python
# Update BASE_URL in remote_test_client.py
BASE_URL = "https://nexero-vr-backend-production.up.railway.app"
```

---

## 💰 Railway Pricing

**Starter Plan (Recommended):**
- $5/month
- 500 hours of usage
- 8GB RAM
- 8GB disk
- Perfect for development/testing

**Free Trial:**
- $5 credit on signup
- Good for 1 month of testing

**Pro Plan:**
- $20/month
- Usage-based pricing
- Better for production

---

## 🔄 Auto-Deploy Setup

Railway auto-deploys on every git push:

```powershell
# Make changes
git add .
git commit -m "Update backend"
git push

# Railway automatically deploys! 🚀
# Watch progress in Railway dashboard
```

---

## 🐛 Troubleshooting

### Issue: Build Failed

**Check logs:**
```powershell
railway logs --deployment
```

**Common fixes:**
- Ensure `requirements.txt` is complete
- Check Python version in `runtime.txt`
- Verify `Procfile` syntax

### Issue: App Crashes on Start

**Check:**
1. Environment variables are set correctly
2. `PORT` variable is used in code
3. All dependencies in `requirements.txt`

**View crash logs:**
```powershell
railway logs
```

### Issue: Health Check Failing

**Verify:**
- `/health` endpoint returns 200
- App starts within healthcheck timeout (100s)

---

## 🔐 Security Notes

⚠️ **IMPORTANT:**

1. **Never commit `.env` file** (already in `.gitignore` ✅)
2. **Use Railway environment variables** for secrets
3. **Rotate Supabase keys** after public deployment
4. **Restrict CORS** in production (change from `["*"]`)
5. **Add authentication** before production use

---

## 📊 Monitoring

Railway provides:
- CPU usage
- Memory usage
- Request metrics
- Error tracking

Access via: Railway Dashboard → Your Project → "Metrics"

---

## 🎯 Quick Commands Reference

```powershell
# Deploy/Update
railway up

# View logs
railway logs

# Open in browser
railway open

# Add environment variable
railway variables set KEY=value

# View all variables
railway variables

# Get deployment URL
railway domain

# Connect to project
railway link

# Restart deployment
railway restart
```

---

## 📚 Additional Resources

- Railway Docs: https://docs.railway.app
- Python on Railway: https://docs.railway.app/guides/python
- FastAPI on Railway: https://railway.app/template/fastapi

---

## ✅ Deployment Complete Checklist

After deployment:

- [ ] ✅ App is accessible at Railway URL
- [ ] ✅ Health check returns 200
- [ ] ✅ API docs work at `/docs`
- [ ] ✅ Environment variables configured
- [ ] ✅ CORS configured correctly
- [ ] ✅ Logs show no errors
- [ ] ✅ Test endpoint with remote_test_client.py
- [ ] ✅ Share URL with friend
- [ ] ✅ Monitor first few requests

---

**Your backend will be live at:**
```
https://nexero-vr-backend-production.up.railway.app
```

**Share with anyone, anywhere!** 🌍
