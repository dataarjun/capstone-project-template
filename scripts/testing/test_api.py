#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI application is working.
"""

import requests
import json
from typing import Dict, Any

def test_health_endpoint(base_url: str = "http://localhost:8000") -> bool:
    """Test the health endpoint"""
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health endpoint failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_agents_status_endpoint(base_url: str = "http://localhost:8000") -> bool:
    """Test the agents status endpoint"""
    try:
        response = requests.get(f"{base_url}/api/agents/status")
        if response.status_code == 200:
            print("✅ Agents status endpoint working")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Agents status endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Agents status endpoint error: {e}")
        return False

def test_investigations_endpoint(base_url: str = "http://localhost:8000") -> bool:
    """Test the investigations endpoint"""
    try:
        response = requests.get(f"{base_url}/api/investigations/")
        if response.status_code == 200:
            print("✅ Investigations endpoint working")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Investigations endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Investigations endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Multi-Agent AML Investigation System API")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint...")
    health_ok = test_health_endpoint(base_url)
    
    # Test agents status endpoint
    print("\n2. Testing Agents Status Endpoint...")
    agents_ok = test_agents_status_endpoint(base_url)
    
    # Test investigations endpoint
    print("\n3. Testing Investigations Endpoint...")
    investigations_ok = test_investigations_endpoint(base_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Agents Status: {'✅ PASS' if agents_ok else '❌ FAIL'}")
    print(f"Investigations: {'✅ PASS' if investigations_ok else '❌ FAIL'}")
    
    if all([health_ok, agents_ok, investigations_ok]):
        print("\n🎉 All tests passed! The API is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the server logs for details.")
        return False

if __name__ == "__main__":
    main()
