# 🧩 MODULAR FEATURES GUIDE

This document explains optional features that can be enabled/disabled without breaking core functionality.

---

## 🎯 Core Principle: Resilient Architecture

**The Nexero VR Backend is designed to be modular and fault-tolerant:**

✅ **Core features always work**  
✅ **Optional features can be enabled/disabled**  
✅ **No feature should break the entire system**  
✅ **Graceful degradation over catastrophic failure**

---

## 📦 Optional Feature: Device Type Tracking

### **What It Is**
Track which VR device/platform each customer uses (Quest 3, Quest 2, Unreal Engine, etc.)

### **Status: OPTIONAL (Disabled by Default)**

The core backend **does not require** this feature. It's designed for advanced analytics if you want to track device usage patterns.

### **How to Enable**

#### Step 1: Add Database Column
```sql
-- Run in Supabase SQL Editor
ALTER TABLE public.vr_sessions 
ADD COLUMN IF NOT EXISTS device_type TEXT DEFAULT 'Quest 3';

-- Add index for analytics
CREATE INDEX IF NOT EXISTS idx_sessions_device 
ON public.vr_sessions(device_type);
```

#### Step 2: Update Code to Send Device Type

**Option A: From VR Headset (Meta Quest)**
```python
# In your Unreal Engine / Unity VR client
session_data = {
    "session_start": start_timestamp,
    "session_end": end_timestamp,
    "customer_id": customer_id,
    "property_id": property_id,
    "device_type": "Quest 3"  # ← Add this
}
```

**Option B: Server-Side Detection**
Modify `session_service.py` to include device type:
```python
# In start_session method
session_data = {
    "id": session_id,
    "started_at": started_at.isoformat(),
    "status": "active",
    "customer_id": customer_id,
    "property_id": property_id,
    "device_type": "Quest 3"  # ← Add back if column exists
}
```

### **Use Cases (When Enabled)**

1. **Analytics Dashboard**
   - "80% of tours use Quest 3"
   - "Quest 2 users have 15% shorter sessions"
   - Device performance comparison

2. **Technical Planning**
   - Which devices to prioritize for optimization
   - Hardware recommendations for sales teams
   - ROI per device type

3. **Performance Monitoring**
   - Device-specific crash rates
   - Performance issues per platform
   - Graphics settings optimization

### **Why It's Optional**

- You're providing the VR headsets (controlled environment)
- You already know which devices you use
- Not critical for core tracking functionality
- Simplifies initial setup

---

## 🔮 Future Optional Features

### **1. Session Location Tracking**

**What**: Track which office/location the VR session occurred at

**Database Column**:
```sql
ALTER TABLE public.vr_sessions 
ADD COLUMN IF NOT EXISTS location_id TEXT;
```

**Use Case**: Multi-office real estate agencies

---

### **2. Sales Person Tracking**

**What**: Track which salesperson conducted the VR tour

**Database Column**:
```sql
ALTER TABLE public.vr_sessions 
ADD COLUMN IF NOT EXISTS salesperson_id TEXT;
```

**Use Case**: Commission tracking, performance metrics

---

### **3. Session Recording URLs**

**What**: Store links to recorded VR sessions for replay

**Database Column**:
```sql
ALTER TABLE public.vr_sessions 
ADD COLUMN IF NOT EXISTS recording_url TEXT;
```

**Use Case**: Training, quality assurance, customer follow-ups

---

### **4. Customer Feedback Scores**

**What**: Post-tour satisfaction ratings

**Database Column**:
```sql
ALTER TABLE public.vr_sessions 
ADD COLUMN IF NOT EXISTS feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5);
ADD COLUMN IF NOT EXISTS feedback_comment TEXT;
```

**Use Case**: Customer satisfaction tracking

---

### **5. Session Weather/Time Context**

**What**: Environmental context for outdoor property tours

**Database Column**:
```sql
ALTER TABLE public.vr_sessions 
ADD COLUMN IF NOT EXISTS virtual_time_of_day TEXT; -- "morning", "afternoon", "evening", "night"
ADD COLUMN IF NOT EXISTS virtual_weather TEXT; -- "sunny", "cloudy", "rainy"
```

**Use Case**: A/B testing different environmental conditions

---

## 🛠️ How to Add Your Own Optional Features

### **Design Pattern: Fail-Safe Optionals**

1. **Never include in required fields**
   ```python
   # ✅ GOOD - Optional with default
   session_data = {
       "id": session_id,
       "customer_id": customer_id,
       # Optional fields added only if enabled
   }
   if FEATURE_ENABLED:
       session_data["optional_field"] = value
   ```

2. **Use database defaults**
   ```sql
   -- Column has a sensible default
   ADD COLUMN feature_name TEXT DEFAULT 'default_value';
   ```

3. **Check column existence**
   ```python
   # Query database schema first
   columns = await db.get_table_columns("vr_sessions")
   if "optional_column" in columns:
       session_data["optional_column"] = value
   ```

4. **Feature flags in config**
   ```python
   # app/config.py
   class Settings(BaseSettings):
       ENABLE_DEVICE_TRACKING: bool = False
       ENABLE_LOCATION_TRACKING: bool = False
   ```

---

## ✅ Benefits of Modular Design

1. **Faster Setup** - Core features work immediately
2. **Flexible Deployment** - Enable only what you need
3. **Easier Testing** - Test core functionality first
4. **Graceful Degradation** - System doesn't crash if feature unavailable
5. **Progressive Enhancement** - Add features as you grow
6. **Easier Debugging** - Isolate issues to specific features
7. **Reduced Complexity** - Simpler mental model

---

## 🎓 Examples from Production Systems

### **Stripe (Payment Processing)**
- Core: Process payments
- Optional: Fraud detection, tax calculation, subscription management

### **Sentry (Error Tracking)**
- Core: Log errors
- Optional: Performance monitoring, release tracking, user feedback

### **Supabase (Database)**
- Core: PostgreSQL database
- Optional: Auth, Storage, Edge Functions, Realtime

### **Your Nexero Backend**
- Core: Track VR sessions and events
- Optional: Device tracking, location tracking, recordings

---

## 📋 Current Feature Status

| Feature | Status | Database Required | Code Required |
|---------|--------|------------------|---------------|
| Session tracking | ✅ Core | ✅ Yes | ✅ Yes |
| Event tracking | ✅ Core | ✅ Yes | ✅ Yes |
| Customer IDs | ✅ Core | ✅ Yes | ✅ Yes |
| Property IDs | ✅ Core | ✅ Yes | ✅ Yes |
| Device tracking | ⚪ Optional | ⚠️ No | ⚠️ Removed |
| Location tracking | ⚪ Optional | ❌ No | ❌ No |
| Salesperson tracking | ⚪ Optional | ❌ No | ❌ No |
| Session recordings | ⚪ Optional | ❌ No | ❌ No |
| Feedback scores | ⚪ Optional | ❌ No | ❌ No |

---

## 🚀 Recommendation

**Start with core features only:**
1. Session tracking ✅
2. Event tracking ✅
3. Customer/Property IDs ✅

**Add optionals when needed:**
- Device tracking (if multi-device)
- Location tracking (if multi-office)
- Other features based on business needs

This approach gets you **production-ready faster** while maintaining flexibility for future growth.

---

## 💡 Philosophy

> "Make it work, make it right, make it fast - in that order."  
> — Kent Beck

The Nexero backend follows this principle:
1. **Make it work** ← Core features (you are here)
2. **Make it right** ← Optional features (add as needed)
3. **Make it fast** ← Optimization (later)

Focus on what matters most: **tracking VR sessions reliably**.

---

**Questions?** Check the main README.md or create an issue!
