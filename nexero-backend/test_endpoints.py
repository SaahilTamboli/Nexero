"""
Test script for Nexero VR Analytics API endpoints.

This script sends test data to verify:
1. Session data (session_start + session_end)
2. POI data (POI + Parent + POI_Duration)
3. View data (View + TotalDuration)

Run this script after:
1. Backend is deployed to Render
2. Database tables are created in Supabase

Usage:
    python test_endpoints.py
    
    # Test specific endpoint:
    python test_endpoints.py --session
    python test_endpoints.py --poi
    python test_endpoints.py --view
    python test_endpoints.py --all
"""

import requests
import json
import time
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Your Render backend URL
BASE_URL = "https://nexero.onrender.com"
# BASE_URL = "http://localhost:8000"  # Uncomment for local testing

ENDPOINT = f"{BASE_URL}/api/v1/unreal/session"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

# =============================================================================
# TEST DATA - Matches what Unreal Engine sends
# =============================================================================

# Test 1: Session Data
SESSION_DATA = {
    "session_start": str(int(time.time()) - 300),  # 5 minutes ago
    "session_end": str(int(time.time())),           # Now
    "customer_id": "test_customer_001",
    "property_id": "test_property_001"
}

# Test 2: POI Data (Point of Interest)
POI_DATA_SAMPLES = [
    {
        "POI": "Kitchen",
        "Parent": "Unit_A",
        "POI_Duration": "0:45"
    },
    {
        "POI": "Master Bedroom",
        "Parent": "Unit_A", 
        "POI_Duration": "1:30"
    },
    {
        "POI": "",  # Empty POI (just parent zone)
        "Parent": "Amenities",
        "POI_Duration": "0:15"
    },
    {
        "POI": "Swimming Pool",
        "Parent": "Amenities",
        "POI_Duration": "2:00"
    }
]

# Test 3: View Data
VIEW_DATA_SAMPLES = [
    {
        "View": "Amenities",
        "TotalDuration": "0:13"
    },
    {
        "View": "Unit_Overview",
        "TotalDuration": "1:45"
    },
    {
        "View": "Property_View",
        "TotalDuration": "0:30"
    }
]

# Test 4: Invalid Data (should be rejected)
INVALID_DATA_SAMPLES = [
    {
        "random_field": "should fail",
        "another_field": 123
    },
    {
        "POI": "Kitchen"  # Missing Parent and POI_Duration
    },
    {
        "View": "Amenities"  # Missing TotalDuration
    }
]

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def send_request(data, test_name):
    """Send POST request and return result."""
    try:
        print(f"\n{Colors.YELLOW}📤 Sending: {json.dumps(data, indent=2)}{Colors.RESET}")
        
        response = requests.post(
            ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📥 Response: {json.dumps(response_json, indent=2)}")
        except:
            print(f"📥 Response: {response.text}")
        
        return response.status_code, response
        
    except requests.exceptions.Timeout:
        print_error(f"{test_name}: Request timed out (server might be cold starting)")
        return None, None
    except requests.exceptions.ConnectionError:
        print_error(f"{test_name}: Could not connect to {BASE_URL}")
        return None, None
    except Exception as e:
        print_error(f"{test_name}: {str(e)}")
        return None, None


def test_session():
    """Test session data endpoint."""
    print_header("TEST 1: SESSION DATA")
    print_info(f"Endpoint: {ENDPOINT}")
    
    status, response = send_request(SESSION_DATA, "Session")
    
    if status == 201:
        print_success("Session data accepted! (201 Created)")
        return True
    elif status == 200:
        print_success("Session data accepted! (200 OK)")
        return True
    else:
        print_error(f"Session test failed with status {status}")
        return False


def test_poi():
    """Test POI data endpoint."""
    print_header("TEST 2: POI DATA")
    print_info(f"Endpoint: {ENDPOINT}")
    
    success_count = 0
    
    for i, poi_data in enumerate(POI_DATA_SAMPLES):
        print(f"\n--- POI Sample {i+1}/{len(POI_DATA_SAMPLES)} ---")
        status, response = send_request(poi_data, f"POI {i+1}")
        
        if status in [200, 201]:
            print_success(f"POI data accepted!")
            success_count += 1
        else:
            print_error(f"POI test failed with status {status}")
    
    print(f"\n{Colors.BOLD}POI Results: {success_count}/{len(POI_DATA_SAMPLES)} passed{Colors.RESET}")
    return success_count == len(POI_DATA_SAMPLES)


def test_view():
    """Test View data endpoint."""
    print_header("TEST 3: VIEW DATA")
    print_info(f"Endpoint: {ENDPOINT}")
    
    success_count = 0
    
    for i, view_data in enumerate(VIEW_DATA_SAMPLES):
        print(f"\n--- View Sample {i+1}/{len(VIEW_DATA_SAMPLES)} ---")
        status, response = send_request(view_data, f"View {i+1}")
        
        if status in [200, 201]:
            print_success(f"View data accepted!")
            success_count += 1
        else:
            print_error(f"View test failed with status {status}")
    
    print(f"\n{Colors.BOLD}View Results: {success_count}/{len(VIEW_DATA_SAMPLES)} passed{Colors.RESET}")
    return success_count == len(VIEW_DATA_SAMPLES)


def test_invalid():
    """Test that invalid data is rejected."""
    print_header("TEST 4: INVALID DATA (Should be rejected)")
    print_info(f"Endpoint: {ENDPOINT}")
    
    rejected_count = 0
    
    for i, invalid_data in enumerate(INVALID_DATA_SAMPLES):
        print(f"\n--- Invalid Sample {i+1}/{len(INVALID_DATA_SAMPLES)} ---")
        status, response = send_request(invalid_data, f"Invalid {i+1}")
        
        if status == 400:
            print_success(f"Invalid data correctly rejected! (400 Bad Request)")
            rejected_count += 1
        elif status in [200, 201]:
            print_error(f"Invalid data was accepted (should have been rejected)")
        else:
            print_info(f"Got status {status}")
    
    print(f"\n{Colors.BOLD}Validation Results: {rejected_count}/{len(INVALID_DATA_SAMPLES)} correctly rejected{Colors.RESET}")
    return rejected_count == len(INVALID_DATA_SAMPLES)


def test_health():
    """Test if server is running."""
    print_header("HEALTH CHECK")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        if response.status_code == 200:
            print_success(f"Server is running at {BASE_URL}")
            return True
        else:
            print_error(f"Health check returned {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_error("Server timed out (might be cold starting on Render)")
        print_info("Wait 30 seconds and try again")
        return False
    except Exception as e:
        print_error(f"Could not connect: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def run_all_tests():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  NEXERO VR ANALYTICS - API TEST SUITE{Colors.RESET}")
    print(f"{Colors.BOLD}  Target: {BASE_URL}{Colors.RESET}")
    print(f"{Colors.BOLD}  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    results = {}
    
    # Health check first
    results['health'] = test_health()
    
    if not results['health']:
        print_error("\nServer not responding. Aborting tests.")
        print_info("If using Render free tier, the server might be sleeping.")
        print_info("Visit the URL in browser first to wake it up, then run tests again.")
        return
    
    # Run all tests
    results['session'] = test_session()
    time.sleep(1)  # Small delay between tests
    
    results['poi'] = test_poi()
    time.sleep(1)
    
    results['view'] = test_view()
    time.sleep(1)
    
    results['validation'] = test_invalid()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed_test else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name.upper()}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Backend is working correctly.{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Check the output above for details.{Colors.RESET}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--health', '-h']:
            test_health()
        elif arg in ['--session', '-s']:
            test_health() and test_session()
        elif arg in ['--poi', '-p']:
            test_health() and test_poi()
        elif arg in ['--view', '-v']:
            test_health() and test_view()
        elif arg in ['--invalid', '-i']:
            test_health() and test_invalid()
        elif arg in ['--all', '-a']:
            run_all_tests()
        else:
            print("Usage: python test_endpoints.py [--all|--session|--poi|--view|--invalid|--health]")
    else:
        run_all_tests()
