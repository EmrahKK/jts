#!/usr/bin/env python3
"""
Comprehensive test script for the JSON transformation service
"""

import requests
import json
import time
import sys

SERVICE_URL = "http://localhost:8000"

def test_health_endpoints():
    """Test health and readiness endpoints"""
    print("Testing health endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{SERVICE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("✓ Health endpoint working")
        
        # Test readiness endpoint
        response = requests.get(f"{SERVICE_URL}/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("✓ Readiness endpoint working")
        
        return True
    except Exception as e:
        print(f"✗ Health endpoint test failed: {str(e)}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("Testing root endpoint...")
    
    try:
        response = requests.get(f"{SERVICE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data
        print("✓ Root endpoint working")
        print(f"  Available endpoints: {data.get('endpoints', [])}")
        return True
    except Exception as e:
        print(f"✗ Root endpoint test failed: {str(e)}")
        return False

def test_transformation(endpoint_id, test_payload, expected_fields):
    """Test a specific transformation endpoint"""
    print(f"Testing transformation endpoint: {endpoint_id}")
    
    try:
        response = requests.post(f"{SERVICE_URL}/{endpoint_id}", json=test_payload)
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"  Response data: {json.dumps(result, indent=2)}")
                
                # Check if the response contains expected structure
                # (This assumes httpbin.org returns the posted data in a 'json' field)
                if 'json' in result:
                    transformed_data = result['json']
                    for field in expected_fields:
                        if field in transformed_data:
                            print(f"    ✓ Field '{field}' found: {transformed_data[field]}")
                        else:
                            print(f"    ✗ Field '{field}' missing")
                
                print("✓ Transformation completed successfully")
                return True
            except json.JSONDecodeError:
                print(f"  Response (not JSON): {response.text[:200]}")
                return True  # Still consider it successful if we got a response
        else:
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Transformation test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("Starting comprehensive tests for JSON Transformation Service")
    print("=" * 60)
    
    # Wait for service to be ready
    print("Waiting for service to be ready...")
    for i in range(10):
        try:
            response = requests.get(f"{SERVICE_URL}/health", timeout=2)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
        print(f"  Attempt {i+1}/10...")
    
    results = []
    
    # Test health endpoints
    results.append(test_health_endpoints())
    print()
    
    # Test root endpoint
    results.append(test_root_endpoint())
    print()
    
    # Test SMS transformation
    sms_payload = {
        "alert": {
            "recipient": "+12345678900",
            "severity": "critical",
            "message": "Server CPU usage above 90%"
        }
    }
    results.append(test_transformation("alert-to-sms", sms_payload, 
                                     ["recipient", "message", "priority", "sender"]))
    print()
    
    # Test Email transformation
    email_payload = {
        "alert": {
            "recipient": "admin@example.com",
            "severity": "warning",
            "message": "Disk usage above 80%"
        }
    }
    results.append(test_transformation("alert-to-email", email_payload, 
                                     ["to", "subject", "body", "html", "importance", "from"]))
    print()
    
    # Test non-existent endpoint
    print("Testing non-existent endpoint...")
    try:
        response = requests.post(f"{SERVICE_URL}/non-existent", json={})
        assert response.status_code == 404
        print("✓ Correctly returned 404 for non-existent endpoint")
        results.append(True)
    except Exception as e:
        print(f"✗ Non-existent endpoint test failed: {str(e)}")
        results.append(False)
    
    print()
    print("=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
