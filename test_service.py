#!/usr/bin/env python3
"""
Test script for the JSON transformation service.
This script sends a sample payload to the service and displays the result.
"""

import requests
import json
import sys

# Default test parameters
SERVICE_URL = "http://localhost:8000"
ENDPOINT_ID = "alert-to-sms"
TEST_PAYLOAD = {
    "alert": {
        "recipient": "+12345678900",
        "severity": "critical",
        "message": "Server CPU usage above 90%"
    }
}

def test_service(url, endpoint_id, payload):
    """Send a test request to the service"""
    endpoint_url = f"{url}/{endpoint_id}"
    print(f"Sending test payload to {endpoint_url}:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(endpoint_url, json=payload)
        print(f"\nResponse status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                print("Response JSON:")
                print(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print("Response (not JSON):")
                print(response.text)
        else:
            print(f"Error response: {response.text}")
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        SERVICE_URL = sys.argv[1]
    if len(sys.argv) > 2:
        ENDPOINT_ID = sys.argv[2]
    
    test_service(SERVICE_URL, ENDPOINT_ID, TEST_PAYLOAD)
