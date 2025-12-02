"""
Monitor Render deployment status
"""
import requests
import time
import json

print("Monitoring Render deployment...")
print("Waiting for new code to deploy...\n")

for i in range(20):  # Check for 20 iterations (about 3 minutes)
    try:
        # Test with numeric timestamp
        payload = {
            "session_start": int(time.time()),
            "session_end": int(time.time()) + 300
        }
        
        response = requests.post(
            "https://nexero.onrender.com/api/v1/unreal/session",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✅ SUCCESS! Deployment complete! (attempt {i+1})")
            print(f"✅ API now accepts numeric timestamps!")
            print(f"\nResponse:")
            print(json.dumps(response.json(), indent=2))
            break
        elif response.status_code == 422:
            error_detail = response.json().get('detail', [])
            if error_detail and 'string_type' in str(error_detail):
                print(f"⏳ Attempt {i+1}/20: Old code still running (expects strings)...")
            else:
                print(f"⚠️ Attempt {i+1}/20: Got 422 but different error:")
                print(json.dumps(response.json(), indent=2))
        else:
            print(f"⏳ Attempt {i+1}/20: Got status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"⏳ Attempt {i+1}/20: Service timeout (might be deploying)...")
    except Exception as e:
        print(f"⏳ Attempt {i+1}/20: Error: {e}")
    
    time.sleep(10)  # Wait 10 seconds between checks

else:
    print("\n❌ Deployment taking longer than expected.")
    print("Please check Render dashboard: https://dashboard.render.com")
