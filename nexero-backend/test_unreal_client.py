"""
Nexero VR Backend - Test Client Script

Simulates Unreal Engine VR client sending data to the backend.
Use this script to test the backend before Unreal integration is complete.

Usage:
    python test_unreal_client.py

Requirements:
    pip install requests
"""

import json
import random
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import requests


# Configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "v1"


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def test_session_endpoint() -> str:
    """
    Test the /api/v1/unreal/session endpoint.
    
    Simulates Unreal Engine sending session start/end data
    with Unix timestamp strings (legacy format).
    
    Returns:
        str: Session ID from the response
    """
    print_header("TEST 1: Session Endpoint")
    
    try:
        # Create session data with timestamps
        now = datetime.now(timezone.utc)
        session_start = int(now.timestamp())
        session_end = int((now + timedelta(minutes=5)).timestamp())
        
        session_data = {
            "session_start": str(session_start),
            "session_end": str(session_end),
            "customer_id": "cust_test_12345",
            "property_id": "prop_luxury_villa_001"
        }
        
        print_info("Sending session data:")
        print(json.dumps(session_data, indent=2))
        
        # Send POST request
        url = f"{BASE_URL}/api/{API_VERSION}/unreal/session"
        response = requests.post(url, json=session_data)
        
        # Check response
        print(f"\nResponse Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 201:
            session_id = response.json().get("session_id")
            print_success(f"Session created successfully! ID: {session_id}")
            return session_id
        else:
            print_error(f"Failed to create session: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Error testing session endpoint: {e}")
        return None


def test_tracking_event(session_id: str):
    """
    Test sending a single tracking event.
    
    Args:
        session_id: Session ID to associate with the event
    """
    print_header("TEST 2: Single Tracking Event")
    
    if not session_id:
        print_error("No session ID provided, skipping test")
        return
    
    try:
        # Create tracking event
        event_data = {
            "event_type": "zone_enter",
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "session_id": session_id,
            "zone_name": "kitchen",
            "position": {
                "x": 10.5,
                "y": 2.0,
                "z": 15.3
            },
            "rotation": {
                "pitch": 0.0,
                "yaw": 90.0,
                "roll": 0.0
            }
        }
        
        print_info("Sending tracking event:")
        print(json.dumps(event_data, indent=2))
        
        # Send POST request
        url = f"{BASE_URL}/api/{API_VERSION}/unreal/tracking/event"
        response = requests.post(url, json=event_data)
        
        print(f"\nResponse Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 202:
            print_success("Tracking event received successfully!")
        else:
            print_error(f"Failed to send event: {response.status_code}")
            
    except Exception as e:
        print_error(f"Error testing tracking event: {e}")


def generate_realistic_events(session_id: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate realistic tracking events for testing.
    
    Args:
        session_id: Session ID for the events
        count: Number of events to generate
        
    Returns:
        List of event dictionaries
    """
    zones = ["entrance", "living_room", "kitchen", "master_bedroom", "bathroom", "balcony"]
    objects = ["window", "door", "countertop", "cabinet", "lighting_fixture", "flooring"]
    interactions = ["click", "grab", "teleport", "open", "close"]
    
    events = []
    base_time = datetime.now(timezone.utc)
    current_zone = zones[0]
    
    for i in range(count):
        # Vary event types
        event_type = random.choice(["gaze", "gaze", "zone_enter", "interaction"])
        
        # Create base event
        event = {
            "event_type": event_type,
            "timestamp": (base_time + timedelta(seconds=i * 2)).timestamp(),
            "session_id": session_id,
            "zone_name": current_zone,
            "position": {
                "x": random.uniform(-20, 20),
                "y": random.uniform(0, 3),
                "z": random.uniform(-20, 20)
            }
        }
        
        # Add event-specific data
        if event_type == "gaze":
            event["gaze_target"] = random.choice(objects)
            event["dwell_time_ms"] = random.randint(500, 5000)
            
        elif event_type == "zone_enter":
            current_zone = random.choice(zones)
            event["zone_name"] = current_zone
            
        elif event_type == "interaction":
            event["object_name"] = random.choice(objects)
            event["interaction_type"] = random.choice(interactions)
        
        events.append(event)
    
    return events


def test_tracking_batch(session_id: str):
    """
    Test sending a batch of tracking events.
    
    Args:
        session_id: Session ID for the events
    """
    print_header("TEST 3: Batch Tracking Events")
    
    if not session_id:
        print_error("No session ID provided, skipping test")
        return
    
    try:
        # Generate realistic events
        events = generate_realistic_events(session_id, count=10)
        
        batch_data = {
            "session_id": session_id,
            "sent_at": datetime.now(timezone.utc).timestamp(),
            "events": events
        }
        
        print_info(f"Sending batch of {len(events)} events")
        print(f"Event types: {[e['event_type'] for e in events]}")
        
        # Send POST request
        url = f"{BASE_URL}/api/{API_VERSION}/unreal/tracking/batch"
        response = requests.post(url, json=batch_data)
        
        print(f"\nResponse Status: {response.status_code}")
        print("Response Body:")
        response_data = response.json()
        print(json.dumps(response_data, indent=2))
        
        if response.status_code == 202:
            processed = response_data.get("processed", 0)
            total = response_data.get("total_events", 0)
            success_rate = response_data.get("success_rate", 0)
            print_success(
                f"Batch processed! {processed}/{total} events stored "
                f"({success_rate:.1f}% success rate)"
            )
        else:
            print_error(f"Failed to send batch: {response.status_code}")
            
    except Exception as e:
        print_error(f"Error testing tracking batch: {e}")


def test_session_status(session_id: str):
    """
    Test checking session status.
    
    Args:
        session_id: Session ID to check
    """
    print_header("TEST 4: Session Status Check")
    
    if not session_id:
        print_error("No session ID provided, skipping test")
        return
    
    try:
        print_info(f"Checking status for session: {session_id}")
        
        # Send GET request
        url = f"{BASE_URL}/api/{API_VERSION}/unreal/session/{session_id}/status"
        response = requests.get(url)
        
        print(f"\nResponse Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            status_data = response.json()
            print_success(f"Session status: {status_data.get('status')}")
        else:
            print_error(f"Failed to get session status: {response.status_code}")
            
    except Exception as e:
        print_error(f"Error checking session status: {e}")


def test_heartbeat(session_id: str):
    """
    Test session heartbeat endpoint.
    
    Args:
        session_id: Session ID for heartbeat
    """
    print_header("TEST 5: Session Heartbeat")
    
    if not session_id:
        print_error("No session ID provided, skipping test")
        return
    
    try:
        print_info(f"Sending heartbeat for session: {session_id}")
        
        # Send POST request
        url = f"{BASE_URL}/api/{API_VERSION}/unreal/session/{session_id}/heartbeat"
        response = requests.post(url)
        
        print(f"\nResponse Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print_success("Heartbeat received!")
        else:
            print_error(f"Heartbeat failed: {response.status_code}")
            
    except Exception as e:
        print_error(f"Error sending heartbeat: {e}")


def simulate_vr_session():
    """
    Simulate a complete VR tour session with realistic data flow.
    
    This mimics the actual workflow:
    1. Session starts
    2. Customer explores property
    3. Events are collected
    4. Session ends, all data sent
    """
    print_header("SIMULATION: Complete VR Tour Session")
    
    try:
        # Step 1: Start session
        print_info("Step 1: Creating VR session...")
        session_id = test_session_endpoint()
        
        if not session_id:
            print_error("Failed to create session, aborting simulation")
            return
        
        time.sleep(1)
        
        # Step 2: Generate tour events
        print_info("\nStep 2: Simulating 5-minute VR tour with 20 events...")
        events = generate_realistic_events(session_id, count=20)
        
        # Show summary of generated events
        event_types = {}
        for event in events:
            event_type = event["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print(f"Generated events breakdown:")
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count}")
        
        time.sleep(1)
        
        # Step 3: Send all events in batch (current workflow)
        print_info("\nStep 3: Sending all tracking data in batch...")
        batch_data = {
            "session_id": session_id,
            "sent_at": datetime.now(timezone.utc).timestamp(),
            "events": events
        }
        
        url = f"{BASE_URL}/api/{API_VERSION}/unreal/tracking/batch"
        response = requests.post(url, json=batch_data)
        
        if response.status_code == 202:
            result = response.json()
            print_success(
                f"Batch sent! {result['processed']}/{result['total_events']} "
                f"events stored ({result['success_rate']:.1f}% success)"
            )
        else:
            print_error(f"Batch failed: {response.status_code}")
        
        time.sleep(1)
        
        # Step 4: Verify session status
        print_info("\nStep 4: Verifying session status...")
        test_session_status(session_id)
        
        # Summary
        print_header("SIMULATION COMPLETE")
        print_success(f"Session ID: {session_id}")
        print_success(f"Total Events: {len(events)}")
        print_success("Data successfully sent to backend!")
        print_info("\nNext: Check Supabase database to verify data storage")
        
    except Exception as e:
        print_error(f"Error in VR session simulation: {e}")


def test_health_check():
    """Test the health check endpoint."""
    print_header("TEST 0: Health Check")
    
    try:
        url = f"{BASE_URL}/health"
        response = requests.get(url)
        
        print(f"Response Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print_success("Backend is healthy!")
        else:
            print_error("Backend health check failed!")
            
    except Exception as e:
        print_error(f"Cannot connect to backend: {e}")
        print_info("Make sure the backend is running: python app/main.py")


def main():
    """
    Run all tests in sequence.
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("     NEXERO VR BACKEND - TEST CLIENT     ".center(70))
    print("     Simulating Unreal Engine VR Client     ".center(70))
    print("=" * 70)
    print(f"{Colors.ENDC}\n")
    
    # Test 0: Health check
    test_health_check()
    time.sleep(1)
    
    # Test 1: Create session
    session_id = test_session_endpoint()
    time.sleep(1)
    
    if session_id:
        # Test 2: Single event
        test_tracking_event(session_id)
        time.sleep(1)
        
        # Test 3: Batch events
        test_tracking_batch(session_id)
        time.sleep(1)
        
        # Test 4: Session status
        test_session_status(session_id)
        time.sleep(1)
        
        # Test 5: Heartbeat
        test_heartbeat(session_id)
        time.sleep(2)
    
    # Full simulation
    simulate_vr_session()
    
    # Final message
    print_header("ALL TESTS COMPLETE")
    print_info("Check the backend logs and Supabase dashboard for stored data")
    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print("1. Verify data in Supabase tables (vr_sessions, tracking_events)")
    print("2. Check backend logs for any errors")
    print("3. Ready for Unreal Engine integration!")
    print()


if __name__ == "__main__":
    main()
