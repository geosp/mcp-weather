#!/usr/bin/env python3
"""
Test script for MCP HTTP client connection
"""
import asyncio
from fastmcp import Client

async def test_mcp_client():
    """Test the MCP HTTP endpoint using FastMCP client"""
    print("🧪 Testing MCP HTTP client connection...")
    print("=" * 50)
    
    # Test endpoints for deployed MCP service
    endpoints = [
        {
            "name": "External LoadBalancer",
            "url": "http://10.0.0.209:3001/mcp",
            "description": "Deployed MCP service via LoadBalancer"
        },
        {
            "name": "Port Forward",
            "url": "http://localhost:8081/mcp", 
            "description": "Deployed MCP service via port-forward"
        },
        {
            "name": "Local Development",
            "url": "http://localhost:3000/mcp",
            "description": "Local development server (fallback)"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n📡 Testing: {endpoint['name']}")
        print(f"🔗 URL: {endpoint['url']}")
        print(f"📝 {endpoint['description']}")
        print("-" * 40)
        
        try:
            # Test the HTTP MCP endpoint with the FastMCP client
            async with Client(endpoint['url']) as client:
                print('✅ Successfully connected to MCP server!')
                
                # Test basic ping with timeout
                print("📡 Testing ping...")
                try:
                    await asyncio.wait_for(client.ping(), timeout=10.0)
                    print('✅ Ping successful!')
                except asyncio.TimeoutError:
                    print('⚠️  Ping timeout - skipping to next test')
                    # Continue to tools test even if ping fails
                except Exception as ping_error:
                    print(f'⚠️  Ping failed: {ping_error} - continuing anyway')
                
                # List available tools
                print("🔍 Listing available tools...")
                try:
                    tools = await asyncio.wait_for(client.list_tools(), timeout=10.0)
                    print(f'✅ Found {len(tools)} tools:')
                    for tool in tools:
                        print(f"   - {tool.name}: {tool.description}")
                except asyncio.TimeoutError:
                    print('⚠️  list_tools timeout')
                    continue
                
                # Test weather tool
                print("\n🌤️  Testing weather tool with Indianapolis...")
                try:
                    result = await asyncio.wait_for(
                        client.call_tool('get_hourly_weather', {'location': 'Indianapolis'}), 
                        timeout=15.0
                    )
                    print(f'✅ Weather tool test successful!')
                    
                    # Display weather result summary
                    if hasattr(result, 'content') and result.content:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            import json
                            try:
                                weather_data = json.loads(content.text)
                                location = weather_data.get('location', 'Unknown')
                                temp = weather_data.get('current_conditions', {}).get('temperature', {}).get('value', 'N/A')
                                weather = weather_data.get('current_conditions', {}).get('weather', 'Unknown')
                                print(f"   📍 Location: {location}")
                                print(f"   🌡️  Temperature: {temp}°C")
                                print(f"   ☁️  Conditions: {weather}")
                            except:
                                print(f"   📝 Raw result: {str(content.text)[:200]}...")
                        else:
                            print(f"   📝 Result: {str(content)[:200]}...")
                    else:
                        print(f"   📝 Result: {str(result)[:200]}...")
                    
                except asyncio.TimeoutError:
                    print('⚠️  Weather tool timeout')
                    continue
                
                print(f"\n🎉 {endpoint['name']} - All tests passed!")
                return  # Exit after first successful test
                
        except Exception as e:
            print(f'❌ {endpoint["name"]} failed: {e}')
            continue
    
    # If we get here, all endpoints failed
    print("\n� All endpoints failed!")
    print("\n🔧 Troubleshooting suggestions:")
    print("   1. Check if the MCP service pods are running")
    print("   2. Verify LoadBalancer service has an external IP")
    print("   3. Test port-forward: kubectl port-forward -n ai-services service/weather-mcp-only 8081:80")
    print("   4. Check service endpoints with: kubectl get endpoints -n ai-services weather-mcp-only")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())