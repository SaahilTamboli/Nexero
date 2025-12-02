# 🔧 VaRest 422 Error - Complete Troubleshooting Guide

## Current Status
- ✅ Code updated to accept numeric timestamps (int/float)
- ⏳ Waiting for Render deployment to complete
- 📍 Latest commit: `3abdc61` (Trigger Render redeploy)

---

## For Your Friend: Quick VaRest Checklist

### 1. **VERIFY THE URL** ✅
```
Correct URL: https://nexero.onrender.com/api/v1/unreal/session
Method: POST
Content-Type: application/json
```

**Common mistakes:**
- ❌ Missing `/api/v1` prefix
- ❌ Wrong HTTP method (GET instead of POST)
- ❌ Typo in URL

---

### 2. **VERIFY THE JSON FORMAT** ✅

**Option A: Send as Numbers (Easiest - after deployment)**
```json
{
  "session_start": 1731000000,
  "session_end": 1731000300
}
```

**VaRest Blueprint:**
```
1. Create VaRestRequestObject
2. JsonObject->SetNumberField("session_start", CurrentTime)
3. JsonObject->SetNumberField("session_end", SessionEnd)
4. ProcessRequest
```

**Option B: Send as Strings (Works NOW)**
```json
{
  "session_start": "1731000000",
  "session_end": "1731000300"
}
```

**VaRest Blueprint:**
```
1. Create VaRestRequestObject
2. Convert timestamp to FString:
   FString StartStr = FString::Printf(TEXT("%.0f"), CurrentTime);
3. JsonObject->SetStringField("session_start", StartStr)
4. JsonObject->SetStringField("session_end", EndStr)
5. ProcessRequest
```

---

### 3. **CHECK FOR EXTRA FIELDS** ⚠️

**VALID (minimal):**
```json
{
  "session_start": 1731000000,
  "session_end": 1731000300
}
```

**ALSO VALID (with optional fields):**
```json
{
  "session_start": 1731000000,
  "session_end": 1731000300,
  "customer_id": "cust_123",
  "property_id": "prop_456",
  "device_type": "Meta Quest 3"
}
```

**INVALID (wrong field names):**
```json
{
  "start_time": 1731000000,   ❌ Wrong! Should be "session_start"
  "end_time": 1731000300      ❌ Wrong! Should be "session_end"
}
```

---

### 4. **VERIFY REQUEST HEADERS** ✅

**Required header:**
```
Content-Type: application/json
```

**VaRest automatically sets this**, but double-check in the Unreal Output Log.

---

### 5. **CHECK THE RESPONSE** 📊

**Success (201 Created):**
```json
{
  "status": "success",
  "message": "Session data received and processed",
  "session_id": "abc123-def456...",
  "duration_seconds": 300,
  "received_at": "2025-11-09T12:00:00+00:00"
}
```

**Failure (422 Unprocessable Entity) - Before Deployment:**
```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "session_start"],
      "msg": "Input should be a valid string",
      "input": 1731000000
    }
  ]
}
```
**Fix:** Use **Option B** (strings) from section 2 above, OR wait for deployment.

**Failure (422) - After Deployment - Wrong Field:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "session_start"],
      "msg": "Field required"
    }
  ]
}
```
**Fix:** Check field names (must be `session_start`, not `start_time`)

---

## 6. **DEBUG STEPS** 🐛

### Step 1: Enable Verbose Logging in Unreal
```cpp
// In your VaRest request handler
void UMyClass::OnRequestComplete(UVaRestRequestJSON* Request)
{
    UE_LOG(LogTemp, Warning, TEXT("Status Code: %d"), Request->GetResponseCode());
    UE_LOG(LogTemp, Warning, TEXT("Response: %s"), *Request->GetResponseContentAsString());
}
```

### Step 2: Check Unreal Output Log
Look for:
- ✅ `Status Code: 201` = Success!
- ❌ `Status Code: 422` = Validation error (check JSON format)
- ❌ `Status Code: 404` = Wrong URL
- ❌ `Status Code: 500` = Server error

### Step 3: Test with curl (from PowerShell)
```powershell
# Test with numbers (after deployment)
$body = @{session_start=1731000000; session_end=1731000300} | ConvertTo-Json
Invoke-RestMethod -Uri "https://nexero.onrender.com/api/v1/unreal/session" -Method Post -Body $body -ContentType "application/json"

# Test with strings (works now)
$body = @{session_start="1731000000"; session_end="1731000300"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://nexero.onrender.com/api/v1/unreal/session" -Method Post -Body $body -ContentType "application/json"
```

### Step 4: Verify Timestamp Values
```cpp
// Make sure timestamps are reasonable
double CurrentTime = FDateTime::UtcNow().ToUnixTimestamp();
double SessionEnd = CurrentTime + 300.0;  // 5 minutes later

UE_LOG(LogTemp, Warning, TEXT("session_start: %.0f"), CurrentTime);
UE_LOG(LogTemp, Warning, TEXT("session_end: %.0f"), SessionEnd);

// Should output something like:
// session_start: 1731000000
// session_end: 1731000300
```

---

## 7. **COMMON MISTAKES & FIXES** 🎯

| Problem | Symptom | Fix |
|---------|---------|-----|
| **Wrong URL** | 404 Not Found | Use: `https://nexero.onrender.com/api/v1/unreal/session` |
| **Wrong Method** | 405 Method Not Allowed | Use POST, not GET |
| **Missing Fields** | 422 "Field required" | Include both `session_start` AND `session_end` |
| **Wrong Type** | 422 "should be valid string" | Convert to string OR wait for deployment |
| **Typo in Field** | 422 "Field required" | Use `session_start`, not `start_time` |
| **Server Sleeping** | 502 Bad Gateway | Wait 30 seconds, retry |

---

## 8. **WORKING EXAMPLE (Copy-Paste Ready)** 📋

### VaRest C++ Code:
```cpp
void UMySessionManager::CreateSession()
{
    // Create request
    UVaRestRequestJSON* Request = UVaRestRequestJSON::ConstructRequest(this);
    Request->SetVerb(ERequestVerb::POST);
    Request->SetContentType(ERequestContentType::json);
    Request->SetURL(TEXT("https://nexero.onrender.com/api/v1/unreal/session"));
    
    // Get timestamps
    double CurrentTime = FDateTime::UtcNow().ToUnixTimestamp();
    double SessionEnd = CurrentTime + 300.0;
    
    // OPTION A: After deployment (numbers work)
    Request->GetRequestObject()->SetNumberField(TEXT("session_start"), CurrentTime);
    Request->GetRequestObject()->SetNumberField(TEXT("session_end"), SessionEnd);
    
    // OPTION B: Before deployment (use strings)
    // FString StartStr = FString::Printf(TEXT("%.0f"), CurrentTime);
    // FString EndStr = FString::Printf(TEXT("%.0f"), SessionEnd);
    // Request->GetRequestObject()->SetStringField(TEXT("session_start"), StartStr);
    // Request->GetRequestObject()->SetStringField(TEXT("session_end"), EndStr);
    
    // Optional fields (recommended)
    Request->GetRequestObject()->SetStringField(TEXT("customer_id"), TEXT("cust_test"));
    Request->GetRequestObject()->SetStringField(TEXT("property_id"), TEXT("prop_test"));
    Request->GetRequestObject()->SetStringField(TEXT("device_type"), TEXT("Meta Quest 3"));
    
    // Bind callbacks
    Request->OnRequestComplete.AddDynamic(this, &UMySessionManager::OnCreateSessionComplete);
    Request->OnRequestFail.AddDynamic(this, &UMySessionManager::OnCreateSessionFail);
    
    // Send request
    Request->ProcessURL();
}

void UMySessionManager::OnCreateSessionComplete(UVaRestRequestJSON* Request)
{
    int32 StatusCode = Request->GetResponseCode();
    
    if (StatusCode == 201)
    {
        UE_LOG(LogTemp, Warning, TEXT("✅ Session created successfully!"));
        
        // Parse response
        FString SessionId = Request->GetResponseObject()->GetStringField(TEXT("session_id"));
        UE_LOG(LogTemp, Warning, TEXT("Session ID: %s"), *SessionId);
    }
    else if (StatusCode == 422)
    {
        UE_LOG(LogTemp, Error, TEXT("❌ Validation error (422)"));
        UE_LOG(LogTemp, Error, TEXT("Response: %s"), *Request->GetResponseContentAsString());
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("❌ Unexpected status: %d"), StatusCode);
    }
}

void UMySessionManager::OnCreateSessionFail(UVaRestRequestJSON* Request)
{
    UE_LOG(LogTemp, Error, TEXT("❌ Request failed completely"));
    UE_LOG(LogTemp, Error, TEXT("Check internet connection and URL"));
}
```

---

## 9. **WHEN TO USE WHICH APPROACH** ⏰

### **RIGHT NOW (Before Render deploys):**
Use **OPTION B** (SetStringField with FString conversion)
```cpp
FString StartStr = FString::Printf(TEXT("%.0f"), CurrentTime);
Request->GetRequestObject()->SetStringField(TEXT("session_start"), StartStr);
```

### **AFTER DEPLOYMENT (in ~5 minutes):**
Use **OPTION A** (SetNumberField directly)
```cpp
Request->GetRequestObject()->SetNumberField(TEXT("session_start"), CurrentTime);
```

---

## 10. **HOW TO KNOW DEPLOYMENT IS COMPLETE** ✅

**Test with curl:**
```powershell
# If this succeeds (201), deployment is done:
$body = @{session_start=1731000000; session_end=1731000300} | ConvertTo-Json
Invoke-RestMethod -Uri "https://nexero.onrender.com/api/v1/unreal/session" -Method Post -Body $body -ContentType "application/json"
```

**Or check here:**
https://dashboard.render.com (look for "Deploy succeeded")

---

## 11. **CONTACT INFO** 📞

If still getting 422 after deployment:
1. Screenshot the FULL error from Unreal Output Log
2. Screenshot your VaRest Blueprint/C++ code
3. Share both so we can debug together

---

## 12. **QUICK REFERENCE** 📚

**API Endpoint:**
```
POST https://nexero.onrender.com/api/v1/unreal/session
```

**Minimal JSON (after deployment):**
```json
{"session_start": 1731000000, "session_end": 1731000300}
```

**Minimal JSON (before deployment):**
```json
{"session_start": "1731000000", "session_end": "1731000300"}
```

**Expected Response:**
```json
{
  "status": "success",
  "session_id": "...",
  "duration_seconds": 300
}
```

---

**Last Updated:** November 9, 2025  
**Status:** ⏳ Deployment in progress  
**ETA:** 2-3 minutes
