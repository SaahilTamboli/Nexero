"""
Test minimal session payload - only timestamps, no customer/property IDs
"""

import requests
import json
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"

print("=" * 70)
print(" TESTING MINIMAL SESSION PAYLOAD ".center(70))
print(" (Only timestamps, no customer_id or property_id) ".center(70))
print("=" * 70)
print()

# Test 1: Health check
print("1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✓ Health check: {response.status_code}")
except Exception as e:
    print(f"✗ Backend not running: {e}")
    print("\nPlease start the backend first:")
    print("  python -m uvicorn app.main:app --reload")
    exit(1)

print()

# Test 2: Minimal session (ONLY timestamps)
print("2. Testing minimal session payload...")
print()

minimal_session = {
    "session_start": "1727653800",
    "session_end": "1727654100"
    # NO customer_id
    # NO property_id
}

print("Sending:")
print(json.dumps(minimal_session, indent=2))
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/unreal/session",
        json=minimal_session,
        timeout=10
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    print()
    
    if response.status_code == 201:
        print("✓✓✓ SUCCESS! Minimal payload works!")
        print()
        print("Your system is NOT hardcoded!")
        print("You can send sessions with only timestamps for testing.")
        session_id = response.json().get("session_id")
        print(f"\nSession ID: {session_id}")
        
        # Verify in database
        print("\n3. Verifying session status...")
        status_response = requests.get(
            f"{BASE_URL}/api/v1/unreal/session/{session_id}/status",
            timeout=5
        )
        print(f"Response Status: {status_response.status_code}")
        print(json.dumps(status_response.json(), indent=2))
        
    else:
        print("✗ Failed!")
        print("\nThis might mean:")
        print("- Database columns require NOT NULL")
        print("- Pydantic model validation issue")
        
except Exception as e:
    print(f"✗ Error: {e}")

print()
print("=" * 70)
print(" TEST COMPLETE ".center(70))
print("=" * 70)
