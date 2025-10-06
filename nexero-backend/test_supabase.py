"""
Quick test to verify Supabase connection
Run this after setting up your Supabase database
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("Testing Supabase Connection")
print("=" * 60)
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "Key: None")
print()

try:
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client created")
    
    # Test: Create a test session
    test_session = {
        "customer_id": "test_customer_001",
        "property_id": "test_property_001",
        "session_start": "2025-10-03T12:00:00Z",
        "status": "active"
    }
    
    print("\nCreating test session...")
    result = supabase.table("vr_sessions").insert(test_session).execute()
    print("✓ Test session created!")
    print(f"  Session ID: {result.data[0]['id']}")
    
    # Test: Read it back
    session_id = result.data[0]['id']
    print("\nReading test session...")
    read_result = supabase.table("vr_sessions").select("*").eq("id", session_id).execute()
    print("✓ Test session retrieved!")
    print(f"  Customer ID: {read_result.data[0]['customer_id']}")
    print(f"  Property ID: {read_result.data[0]['property_id']}")
    
    # Test: Insert a tracking event
    print("\nCreating test tracking event...")
    test_event = {
        "session_id": session_id,
        "event_type": "gaze",
        "timestamp": "2025-10-03T12:01:00Z",
        "event_data": {
            "zone_name": "living_room",
            "gaze_target": "window",
            "dwell_time_ms": 2500
        }
    }
    event_result = supabase.table("tracking_events").insert(test_event).execute()
    print("✓ Test event created!")
    print(f"  Event ID: {event_result.data[0]['id']}")
    
    # Test: Clean up
    print("\nCleaning up test data...")
    supabase.table("vr_sessions").delete().eq("id", session_id).execute()
    print("✓ Test data deleted!")
    
    print()
    print("=" * 60)
    print("✓✓✓ SUCCESS! Supabase is working perfectly!")
    print("=" * 60)
    print()
    print("Your database is ready to use! 🎉")
    print()
    print("Next steps:")
    print("1. Start your backend: python -m uvicorn app.main:app --reload")
    print("2. Run test client: python test_unreal_client.py")
    print("3. Check data in Supabase Table Editor")
    
except Exception as e:
    print()
    print("=" * 60)
    print("✗✗✗ ERROR!")
    print("=" * 60)
    print(f"Error: {e}")
    print()
    print("Common issues:")
    print("1. Check SUPABASE_URL is correct (from Settings > API)")
    print("2. Check SUPABASE_KEY is the service_role key (long string starting with eyJ)")
    print("3. Check tables exist (run SQL queries from SUPABASE_SETUP.md)")
    print("4. Check internet connection")
    print()
    print("See SUPABASE_SETUP.md for detailed troubleshooting")
