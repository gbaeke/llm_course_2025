"""
FastMCP Client for Azure Entra protected server.

This client demonstrates how to connect to a FastMCP server protected by Azure OAuth.
Run with: python client.py
"""

from fastmcp import Client
import asyncio

async def main():
    print("🔗 Connecting to Azure protected MCP server...")
    print("🌐 Server URL: http://localhost:8000/mcp/")
    
    try:
        # The client will automatically handle Azure OAuth
        async with Client("http://localhost:8000/mcp/", auth="oauth") as client:
            # First-time connection will open Azure login in your browser
            print("✓ Authenticated with Azure!")
            
            # Test the server connection
            print("\n📡 Testing server connection...")
            await client.ping()
            print("✓ Server is responsive")
            
            # List available tools
            print("\n🔧 Listing available tools...")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Test the protected tool
            print("\n👤 Getting user information...")
            result = await client.call_tool("get_user_info")
            
            # Extract the result content
            if result.content and len(result.content) > 0:
                user_data = result.content[0].text
                print(f"User data: {user_data}")
                
                # If the result is a dict, we can access specific fields
                try:
                    import json
                    user_info = json.loads(user_data) if isinstance(user_data, str) else user_data
                    if isinstance(user_info, dict):
                        print(f"✓ Azure user: {user_info.get('email', 'N/A')}")
                        print(f"✓ Name: {user_info.get('name', 'N/A')}")
                        print(f"✓ Azure ID: {user_info.get('azure_id', 'N/A')}")
                        print(f"✓ Tenant: {user_info.get('tenant_id', 'N/A')}")
                    else:
                        print(f"✓ User info: {user_info}")
                except (json.JSONDecodeError, TypeError):
                    print(f"✓ Raw user info: {user_data}")
            else:
                print("⚠️ No content returned from get_user_info")
                
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("\n🔍 Troubleshooting:")
        print("1. Make sure the server is running: python server.py")
        print("2. Check that the server is listening on http://localhost:8000")
        print("3. Verify your Azure credentials are configured correctly")
        print("4. Check your .env file has the correct Azure settings")

if __name__ == "__main__":
    print("🚀 Starting FastMCP Client for Azure protected server")
    print("=" * 60)
    asyncio.run(main())