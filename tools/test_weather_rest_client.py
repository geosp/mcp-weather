#!/usr/bin/env python3
"""
Python-based REST API test client for Weather MCP Server

This script tests all available REST endpoints of the Weather MCP Server.
It requires an Authentik token for authenticated endpoints.

Usage:
    uv run python tools/test_rest_api.py YOUR_AUTHENTIK_TOKEN
"""

import sys
import json
import requests
from datetime import datetime

def print_response(response, endpoint):
    """Print formatted API response"""
    print(f"\nResponse from {endpoint}:")
    print(f"Status: {response.status_code}")
    
    try:
        # Pretty print the JSON response
        data = response.json()
        print("Response Body:")
        print(json.dumps(data, indent=2))
    except:
        # If not JSON, print raw text
        print("Response Body:")
        print(response.text)
    
    print("-" * 70)


def test_rest_api(token):
    """Test all REST API endpoints"""
    base_url = "http://localhost:3000"
    
    print(f"🧪 Testing Weather MCP REST API at {base_url}")
    print("=" * 70)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Using token: {token[:20]}...\n")
    
    # Set up headers for authenticated requests
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Test 1: Health endpoint (no auth required)
    print("\n📡 TEST 1: Health Check Endpoint (No Auth)")
    print(f"GET {base_url}/health")
    
    try:
        response = requests.get(f"{base_url}/health")
        print_response(response, "Health Check")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Service info endpoint
    print("\n📡 TEST 2: Service Info Endpoint")
    print(f"GET {base_url}/")
    
    try:
        response = requests.get(f"{base_url}/", headers=auth_headers)
        print_response(response, "Service Info")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Weather endpoint with query parameter
    location = "Tokyo"
    print("\n📡 TEST 3: Weather Endpoint (GET)")
    print(f"GET {base_url}/weather?location={location}")
    
    try:
        response = requests.get(
            f"{base_url}/weather",
            params={"location": location},
            headers=auth_headers
        )
        print_response(response, f"Weather for {location}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Weather endpoint with JSON body
    location = "Paris"
    print("\n📡 TEST 4: Weather Endpoint (POST)")
    print(f"POST {base_url}/weather")
    print(f'Body: {{"location": "{location}"}}')
    
    try:
        response = requests.post(
            f"{base_url}/weather",
            json={"location": location},
            headers=auth_headers
        )
        print_response(response, f"Weather for {location}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ API testing complete!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Error: Authentik token required")
        print(f"Usage: {sys.argv[0]} YOUR_AUTHENTIK_TOKEN")
        sys.exit(1)
        
    test_rest_api(sys.argv[1])