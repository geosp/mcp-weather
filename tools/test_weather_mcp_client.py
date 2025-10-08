#!/usr/bin/env python3
"""
Test script for Weather MCP Server with Authentik authentication.

Tests MCP protocol connection and weather tool functionality.

Requirements:
    - Server running in MCP mode
    - AUTHENTIK_TOKEN environment variable set
    
Usage:
    # Set up environment with uv
    uv venv .venv
    uv pip install -e .
    
    # Run with the convenience script (recommended):
    ./test-mcp.sh YOUR_AUTHENTIK_TOKEN [LOCATION]
    
    # Or run directly with the token as a parameter:
    AUTHENTIK_TOKEN="your-token-here" python tools/test_weather_mcp_client.py [LOCATION]
    
    # Examples:
    ./test-mcp.sh YOUR_TOKEN "Tallahassee, FL, USA"
    ./test-mcp.sh YOUR_TOKEN "Vancouver, Canada"
    ./test-mcp.sh YOUR_TOKEN "Paris, France"
"""

import os
import sys
import asyncio
import json
import argparse
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def test_weather_mcp(location: str = None):
    """
    Test the Weather MCP Server
    
    Args:
        location: Optional location to test (default: "Tallahassee, FL, USA")
    """
    
    # Get authentication token
    auth_token = os.getenv("AUTHENTIK_TOKEN")
    if not auth_token and len(sys.argv) > 1:
        auth_token = sys.argv[1]
    
    if not auth_token:
        print("❌ ERROR: AUTHENTIK_TOKEN environment variable not set")
        print("\nSet your token: export AUTHENTIK_TOKEN='your-token-here'")
        return False
        
    # Default location if none specified
    if not location and len(sys.argv) > 2:
        location = sys.argv[2]
        
    if not location:
        location = "Tallahassee, FL, USA"
    
    print("🧪 Testing Weather MCP Server")
    print("=" * 70)
    print(f"🔐 Token: {auth_token[:20]}...")
    print(f"🔗 URL: http://localhost:3000/mcp")
    print()
    
    try:
        # Create authenticated transport
        transport = StreamableHttpTransport(
            url="http://localhost:3000/mcp",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        async with Client(transport=transport) as client:
            print('✅ Connected successfully')
            
            # Test 1: List Tools
            print("\n" + "=" * 70)
            print("📋 Available Tools")
            print("-" * 70)
            
            tools_response = await asyncio.wait_for(client.list_tools(), timeout=10.0)
            tools = tools_response.tools if hasattr(tools_response, 'tools') else tools_response
            
            for tool in tools:
                print(f"🔧 {tool.name}")
                if hasattr(tool, 'description') and tool.description:
                    desc = tool.description.split('\n')[0]
                    print(f"   {desc[:100]}")
            
            # Test 2: Call Weather Tool
            print("\n" + "=" * 70)
            print("🌤️  Testing Weather Tool")
            print("-" * 70)
            
            print(f"📍 Location: {location}")
            
            result = await asyncio.wait_for(
                client.call_tool('get_hourly_weather', {'location': location}),
                timeout=15.0
            )
            
            # Parse response
            if hasattr(result, 'content') and result.content:
                weather_data = json.loads(result.content[0].text)
                
                # Display results
                location = weather_data['location']
                country = weather_data.get('country', '')
                current = weather_data['current_conditions']
                
                print(f"\n📊 Current Weather")
                print(f"{'─' * 70}")
                print(f"📍 {location}, {country}")
                print(f"🌡️  {current['temperature']['value']}°C (feels like {current['feels_like']['value']}°C)")
                print(f"☁️  {current['weather']}")
                print(f"💧 Humidity: {current['humidity']['value']}%")
                print(f"💨 Wind: {current['wind']['speed']} km/h {current['wind']['direction']}")
                
                # Forecast
                forecast = weather_data['hourly_forecast'][:3]
                print(f"\n📅 Next 3 Hours")
                print(f"{'─' * 70}")
                for hour in forecast:
                    print(f"{hour['time']}: {hour['temperature']['value']}°C, {hour['weather']}")
                
                print(f"\n✅ All tests passed!")
                return True
            else:
                print("❌ No weather data returned")
                return False
                
    except asyncio.TimeoutError:
        print('\n❌ Timeout - server not responding')
        return False
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Weather MCP Server")
    parser.add_argument("token", nargs="?", help="Authentik token")
    parser.add_argument("location", nargs="?", help="Location to test")
    args = parser.parse_args()
    
    # Set token from args if provided
    if args.token:
        os.environ["AUTHENTIK_TOKEN"] = args.token
    
    # Run the test
    success = asyncio.run(test_weather_mcp(args.location))
    sys.exit(0 if success else 1)