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
    
    try:
        # Test the HTTP MCP endpoint with the FastMCP client
        print("🔗 Connecting to http://localhost:3000/mcp...")
        async with Client('http://localhost:3000/mcp') as client:
            print('✅ Successfully connected to MCP server!')
            
            # Test basic ping
            print("📡 Testing ping...")
            await client.ping()
            print('✅ Ping successful!')
            
            # List available tools
            print("🔍 Listing available tools...")
            tools = await client.list_tools()
            print(f'✅ Found {len(tools)} tools:')
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
            
            # Test weather tool
            print("\n🌤️  Testing weather tool with Indianapolis...")
            result = await client.call_tool('get_hourly_weather', {'location': 'Indianapolis'})
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
            
            print("\n🎉 All tests passed! MCP HTTP transport is working correctly.")
            
    except Exception as e:
        print(f'❌ Error: {e}')
        print(f'   Error type: {type(e).__name__}')
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        
        # Provide troubleshooting suggestions
        print("\n🔧 Troubleshooting suggestions:")
        print("   1. Make sure the server is running on port 3000")
        print("   2. Check if the MCP endpoint is mounted at /mcp")
        print("   3. Verify the server shows 'StreamableHTTP session manager started'")
        print("   4. Try connecting to http://localhost:3000 to test basic connectivity")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())