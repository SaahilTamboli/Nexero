"""
Test script to verify the API accepts both numeric and string timestamps.
This tests the fix for the VaRest 422 error.
"""

import requests
import time

BASE_URL = "https://nexero.onrender.com/api/v1"

def test_numeric_timestamps():
    """Test with numeric timestamps (VaRest format)"""
    print("\n" + "="*60)
    print("TEST: Numeric Timestamps (VaRest Plugin Format)")
    print("="*60)
    
    current_time = time.time()
    session_end = current_time + 300  # 5 minutes later
    
    payload = {
        "session_start": int(current_time),  # INTEGER
        "session_end": int(session_end),      # INTEGER
        "customer_id": "cust_numeric_test",
        "property_id": "prop_numeric_test"
    }
    
    print(f"\nSending payload: {payload}")
    
    response = requests.post(
        f"{BASE_URL}/unreal/session",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    
    if response.status_code == 201:
        print("✅ SUCCESS: Numeric timestamps accepted!")
        return True
    else:
        print("❌ FAILED: Numeric timestamps rejected")
        return False


def test_string_timestamps():
    """Test with string timestamps (original format)"""
    print("\n" + "="*60)
    print("TEST: String Timestamps (Original Format)")
    print("="*60)
    
    current_time = time.time()
    session_end = current_time + 300
    
    payload = {
        "session_start": str(int(current_time)),  # STRING
        "session_end": str(int(session_end)),      # STRING
        "customer_id": "cust_string_test",
        "property_id": "prop_string_test"
    }
    
    print(f"\nSending payload: {payload}")
    
    response = requests.post(
        f"{BASE_URL}/unreal/session",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    
    if response.status_code == 201:
        print("✅ SUCCESS: String timestamps accepted!")
        return True
    else:
        print("❌ FAILED: String timestamps rejected")
        return False


def test_float_timestamps():
    """Test with float timestamps (with decimals)"""
    print("\n" + "="*60)
    print("TEST: Float Timestamps (With Decimals)")
    print("="*60)
    
    current_time = time.time()
    session_end = current_time + 300
    
    payload = {
        "session_start": current_time,      # FLOAT with decimals
        "session_end": session_end,          # FLOAT with decimals
        "customer_id": "cust_float_test",
        "property_id": "prop_float_test"
    }
    
    print(f"\nSending payload: {payload}")
    
    response = requests.post(
        f"{BASE_URL}/unreal/session",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")
    
    if response.status_code == 201:
        print("✅ SUCCESS: Float timestamps accepted!")
        return True
    else:
        print("❌ FAILED: Float timestamps rejected")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING NUMERIC TIMESTAMP SUPPORT")
    print("Testing fix for VaRest 422 error")
    print("="*60)
    
    # Test all three formats
    results = []
    results.append(("Numeric (int)", test_numeric_timestamps()))
    results.append(("String", test_string_timestamps()))
    results.append(("Float", test_float_timestamps()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - API now accepts numeric timestamps!")
        print("Your friend's VaRest code will work without changes!")
    else:
        print("⚠️ SOME TESTS FAILED - Check the output above")
    print("="*60)
