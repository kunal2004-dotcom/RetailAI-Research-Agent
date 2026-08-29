import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/research"

def test_workflow():
    print("Submitting research request...")
    response = requests.post(BASE_URL, json={
        "question": "What are the top 3 AI trends in retail for 2026?"
    })
    
    if response.status_code != 201:
        print(f"Failed to submit: {response.text}")
        sys.exit(1)
        
    session_data = response.json()
    session_id = session_data["id"]
    print(f"Session #{session_id} created successfully. Polling status...")
    
    start_time = time.time()
    
    while True:
        res = requests.get(f"{BASE_URL}/{session_id}")
        if res.status_code != 200:
            print(f"Failed to fetch status: {res.text}")
            break
            
        data = res.json()
        status = data.get("status")
        
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed}s] Status: {status}")
        
        if status in ["completed", "failed"]:
            print("Final Data:")
            if status == "failed":
                print("Error:", data.get("error_message"))
            else:
                print(f"Findings: {len(data.get('findings', []))}")
                print(f"Recommendations: {len(data.get('recommendations', []))}")
            break
            
        time.sleep(5)

if __name__ == "__main__":
    test_workflow()
