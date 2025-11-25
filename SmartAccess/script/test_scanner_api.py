#!/usr/bin/env python3
"""
Test script for Bus Transportation NFC Scanner API
This script simulates NFC scans from a Raspberry Pi to test the API endpoint.
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"  # Change to your server URL
API_ENDPOINT = f"{API_BASE_URL}/api/transportation/scan/"

# Test data
TEST_SCANS = [
    {
        "name": "Test 1: Valid boarding scan",
        "data": {
            "nfc_uid": "2ae44605",  # SP22-BCS-197 (Shahzaib Akhtar)
            "action": "board",
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "name": "Test 2: Valid alighting scan",
        "data": {
            "nfc_uid": "2ae44605",
            "action": "alight",
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "name": "Test 3: Invalid NFC UID (should fail)",
        "data": {
            "nfc_uid": "999999999",  # Non-existent student
            "action": "board",
            "timestamp": datetime.now().isoformat()
        }
    }
]

def test_api():
    """Run API tests"""
    print("=" * 70)
    print("BUS TRANSPORTATION API TEST SUITE")
    print("=" * 70)
    print(f"API Endpoint: {API_ENDPOINT}")
    print("=" * 70)
    
    for i, test in enumerate(TEST_SCANS, 1):
        print(f"\n[Test {i}] {test['name']}")
        print("-" * 70)
        print(f"Request Data: {json.dumps(test['data'], indent=2)}")
        
        try:
            response = requests.post(
                API_ENDPOINT,
                json=test['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS")
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            elif response.status_code == 201:
                print("✅ CREATED")
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            elif response.status_code == 400:
                print("⚠️  BAD REQUEST")
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2)}")
            elif response.status_code == 404:
                print("❌ NOT FOUND")
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2)}")
            elif response.status_code == 500:
                print("❌ SERVER ERROR")
                print(f"Error: {response.text}")
            else:
                print(f"⚠️  UNEXPECTED STATUS: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR")
            print(f"Cannot connect to {API_BASE_URL}")
            print("Make sure Django server is running!")
            break
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT")
            print("Server took too long to respond")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Before running this test:")
    print("1. Make sure Django development server is running")
    print("2. Update API_BASE_URL if not using localhost:8000")
    print("3. Update nfc_uid with actual student NFC UID from database")
    print("4. Ensure student has an active bus assignment")
    print()
    
    response = input("Ready to run tests? (y/n): ")
    if response.lower() == 'y':
        test_api()
    else:
        print("Test cancelled.")
