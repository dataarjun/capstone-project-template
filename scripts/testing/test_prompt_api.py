#!/usr/bin/env python3
"""
Test Prompt API Endpoints

This script tests the prompt management API endpoints to ensure
they work correctly with proper validation.
"""

import requests
import json
from typing import Dict, Any

def test_prompt_api():
    """Test the prompt management API"""
    base_url = "http://localhost:8000/api/prompts"
    
    print("🧪 Testing Prompt Management API")
    print("=" * 40)
    
    # Test 1: List agents
    print("\n1. Testing /agents endpoint...")
    try:
        response = requests.get(f"{base_url}/agents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agents listed: {data.get('agents', {}).keys()}")
        else:
            print(f"❌ Failed to list agents: {response.status_code}")
    except Exception as e:
        print(f"❌ Error listing agents: {e}")
    
    # Test 2: Deploy valid agent
    print("\n2. Testing valid agent deployment...")
    try:
        response = requests.post(f"{base_url}/deploy", json={
            "agent_name": "risk_assessor",
            "description": "Test deployment",
            "tags": ["test"]
        })
        if response.status_code == 200:
            print("✅ Valid agent deployment successful")
        else:
            print(f"❌ Valid agent deployment failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error deploying valid agent: {e}")
    
    # Test 3: Deploy invalid agent
    print("\n3. Testing invalid agent deployment...")
    try:
        response = requests.post(f"{base_url}/deploy", json={
            "agent_name": "invalid_agent",
            "description": "Test deployment",
            "tags": ["test"]
        })
        if response.status_code == 400:
            print("✅ Invalid agent correctly rejected")
        else:
            print(f"❌ Invalid agent not rejected: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing invalid agent: {e}")
    
    # Test 4: Get prompt versions
    print("\n4. Testing prompt versions...")
    try:
        response = requests.get(f"{base_url}/risk_assessor/versions")
        if response.status_code == 200:
            print("✅ Prompt versions retrieved successfully")
        else:
            print(f"❌ Failed to get prompt versions: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting prompt versions: {e}")
    
    # Test 5: Health check
    print("\n5. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('status')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in health check: {e}")
    
    print("\n🎉 API testing completed!")

if __name__ == "__main__":
    test_prompt_api()





