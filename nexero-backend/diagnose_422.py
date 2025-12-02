"""
Diagnostic script to debug 422 error from VaRest
This simulates EXACTLY what VaRest sends
"""

import requests
import json
import time

BASE_URL = "https://nexero.onrender.com/api/v1"

print("="*70)
print("DIAGNOSTIC: VaRest 422 Error Troubleshooting")
print("="*70)

# Test 1: What your friend is sending (numbers)
print("\n[TEST 1] Sending NUMERIC timestamps (like VaRest SetNumberField)")
print("-" * 70)

current_time = int(time.time())
session_end = current_time + 300

payload1 = {
    "session_start": current_time,      # NUMBER (int)
    "session_end": session_end            # NUMBER (int)
}

print(f"Payload Type Check:")
print(f"  session_start type: {type(payload1['session_start']).__name__}")
print(f"  session_end type: {type(payload1['session_end']).__name__}")
print(f"\nJSON Payload:")
print(json.dumps(payload1, indent=2))
print(f"\nSending to: {BASE_URL}/unreal/session")

try:
    response = requests.post(
        f"{BASE_URL}/unreal/session",
        json=payload1,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n✓ Response Status: {response.status_code}")
    print(f"✓ Response Headers: {dict(response.headers)}")
    
    try:
        response_json = response.json()
        print(f"✓ Response Body:")
        print(json.dumps(response_json, indent=2))
    except:
        print(f"✗ Response Body (raw text):")
        print(response.text)
    
    if response.status_code == 201:
        print("\n✅ SUCCESS! API accepted numeric timestamps!")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test 2: With float timestamps (more precise)
print("\n\n[TEST 2] Sending FLOAT timestamps (with decimals)")
print("-" * 70)

payload2 = {
    "session_start": float(current_time),      # FLOAT
    "session_end": float(session_end)          # FLOAT
}

print(f"Payload Type Check:")
print(f"  session_start type: {type(payload2['session_start']).__name__}")
print(f"  session_end type: {type(payload2['session_end']).__name__}")
print(f"\nJSON Payload:")
print(json.dumps(payload2, indent=2))

try:
    response = requests.post(
        f"{BASE_URL}/unreal/session",
        json=payload2
    )
    
    print(f"\n✓ Response Status: {response.status_code}")
    
    try:
        print(f"✓ Response Body:")
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"✗ Response Body (raw):")
        print(response.text)
    
    if response.status_code == 201:
        print("\n✅ SUCCESS! API accepted float timestamps!")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test 3: String timestamps (original format)
print("\n\n[TEST 3] Sending STRING timestamps (original format)")
print("-" * 70)

payload3 = {
    "session_start": str(current_time),      # STRING
    "session_end": str(session_end)          # STRING
}

print(f"Payload Type Check:")
print(f"  session_start type: {type(payload3['session_start']).__name__}")
print(f"  session_end type: {type(payload3['session_end']).__name__}")
print(f"\nJSON Payload:")
print(json.dumps(payload3, indent=2))

try:
    response = requests.post(
        f"{BASE_URL}/unreal/session",
        json=payload3
    )
    
    print(f"\n✓ Response Status: {response.status_code}")
    print(f"✓ Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 201:
        print("\n✅ SUCCESS! API accepted string timestamps!")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test 4: Ask your friend to send this EXACT JSON
print("\n\n[TEST 4] Exact JSON your friend should send from VaRest")
print("-" * 70)
print("Tell your friend to send THIS exact JSON:")
print(json.dumps(payload1, indent=2))
print("\nIn VaRest Blueprint:")
print("1. Create RequestObject")
print("2. Use SetNumberField for both session_start and session_end")
print("3. ProcessRequest to this URL:", f"{BASE_URL}/unreal/session")

# Summary
print("\n\n" + "="*70)
print("SUMMARY")
print("="*70)
print("If all tests pass, the API is working correctly.")
print("If your friend still gets 422, the problem is:")
print("  1. Wrong URL")
print("  2. Missing/wrong headers")
print("  3. Extra fields in the JSON")
print("  4. Wrong HTTP method (should be POST)")
print("="*70)
