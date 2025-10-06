# 🚂 RAILWAY DEPLOYMENT - QUICK CHECKLIST

**Follow these steps in order:**

---

## ✅ **PRE-DEPLOYMENT**

- [x] Code pushed to GitHub
- [x] Supabase database set up
- [ ] Have Supabase URL ready
- [ ] Have Supabase service_role key ready

---

## 🚀 **DEPLOYMENT STEPS**

### **STEP 1: Create Account** (2 min)
- [ ] Go to https://railway.app
- [ ] Click "Login with GitHub"
- [ ] Authorize Railway

### **STEP 2: Deploy** (3 min)
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose "SaahilTamboli/Nexero"
- [ ] Wait for build (2-3 minutes)

### **STEP 3: Environment Variables** (5 min)
- [ ] Click "Variables" tab
- [ ] Add: `SUPABASE_URL` = `https://your-project.supabase.co`
- [ ] Add: `SUPABASE_KEY` = `eyJhbGciOiJIUzI...` (service_role key)
- [ ] Add: `ENVIRONMENT` = `production`
- [ ] Add: `LOG_LEVEL` = `info`
- [ ] Add: `CORS_ORIGINS` = `["*"]`
- [ ] Add: `API_VERSION` = `v1`
- [ ] Wait for auto-redeploy

### **STEP 4: Generate Domain** (1 min)
- [ ] Click "Settings" tab
- [ ] Scroll to "Networking"
- [ ] Click "Generate Domain"
- [ ] Copy your URL (e.g., `https://nexero-vr-backend-production.up.railway.app`)

### **STEP 5: Test** (2 min)
- [ ] Open: `https://your-url.up.railway.app/health`
- [ ] Should see: `{"status": "healthy", ...}`
- [ ] Open: `https://your-url.up.railway.app/docs`
- [ ] Should see: FastAPI documentation

---

## ✅ **POST-DEPLOYMENT**

- [ ] Test session creation endpoint
- [ ] Check Railway logs for errors
- [ ] Verify data in Supabase
- [ ] Share URL with friend

---

## 🎯 **YOUR API URL**

Write it here after Step 4:

```
https://___________________________________.up.railway.app
```

---

## 🆘 **TROUBLESHOOTING**

**Build failed?**
- Check Railway logs (Deployments → View logs)
- Look for error messages

**App crashes?**
- Verify all 6 environment variables
- Check Supabase credentials

**502 Error?**
- Wait 30 seconds (app is starting)
- Check logs

---

## 📚 **FULL GUIDE**

See `RAILWAY_DEPLOYMENT_GUIDE.md` for detailed instructions!

---

## ⏱️ **ESTIMATED TIME**

- Account setup: 2 minutes
- Deployment: 3 minutes
- Configuration: 5 minutes
- Testing: 2 minutes
- **Total: 12 minutes**

---

**Ready? Start with Step 1! 🚀**
