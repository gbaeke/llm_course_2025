#!/usr/bin/env python3
"""
MCP Client for Azure OBO Server

This client:
1. Gets an Azure token using MSAL device flow (same as simple_auth.py)
2. Connects to the OBO MCP server with bearer authentication
3. Calls the get_subscriptions tool to list Azure subscriptions

Requires: pip install fastmcp msal python-dotenv
"""

import os
import msal
import asyncio
from dotenv import load_dotenv
from fastmcp import Client

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID")
TENANT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_TENANT_ID")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
API_SCOPE = f"api://{CLIENT_ID}/execute"

# Token cache file
cache_file = ".token_cache.json"

def load_cache():
    """Load the token cache from file"""
    cache = msal.SerializableTokenCache()
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache_data = f.read()
            if cache_data:
                cache.deserialize(cache_data)
    return cache

def save_cache(cache):
    """Save the token cache to file"""
    if cache.has_state_changed:
        with open(cache_file, "w") as f:
            f.write(cache.serialize())

def get_token_silent():
    """Get token silently from cache or interactively if needed"""
    cache = load_cache()
    
    # Create MSAL app as public client
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache
    )
    
    # Check if there's a token in cache
    accounts = app.get_accounts()
    if accounts:
        print(f"Found {len(accounts)} cached account(s)")
        # Try to get token silently
        result = app.acquire_token_silent([API_SCOPE], account=accounts[0])
        if result and "access_token" in result:
            print("✓ Token acquired silently from cache")
            save_cache(cache)
            return result["access_token"]
    
    # If no token in cache, use device flow
    print("No valid token in cache, starting device flow...")
    flow = app.initiate_device_flow(scopes=[API_SCOPE])
    if "user_code" not in flow:
        print(f"❌ Failed to create device flow: {flow.get('error')}")
        return None
    
    print(f"🔐 {flow['message']}")
    result = app.acquire_token_by_device_flow(flow)
    save_cache(cache)
    
    if "access_token" in result:
        print("✓ Token acquired successfully via device flow")
        return result["access_token"]
    else:
        print(f"❌ Failed to obtain token: {result.get('error')}")
        return None

async def test_mcp_server(token: str):
    """Test the MCP server with the obtained token"""
    server_url = "http://127.0.0.1:8000/mcp"
    
    try:
        print(f"🔗 Connecting to MCP server: {server_url}")
        print(f"🎫 Using bearer token authentication")
        
        async with Client(server_url, auth=token) as client:
            print("✓ Connected to MCP server successfully")
            
            # Test server connectivity
            print("\n📡 Testing server ping...")
            await client.ping()
            print("✓ Server responded to ping")
            
            # List available tools
            print("\n🛠️  Listing available tools...")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Get user information
            print("\n👤 Getting user information...")
            user_result = await client.call_tool("get_user_info")
            if user_result.content:
                import json
                user_data = json.loads(user_result.content[0].text)
                if user_data.get("success"):
                    user_info = user_data["user_info"]
                    print(f"✓ User: {user_info.get('email', 'N/A')}")
                    print(f"✓ Name: {user_info.get('name', 'N/A')}")
                    print(f"✓ Tenant: {user_info.get('tenant_id', 'N/A')}")
                    print(f"✓ Scopes: {', '.join(user_info.get('scopes', []))}")
                else:
                    print(f"❌ Error getting user info: {user_data.get('error')}")
            
            # Call the get_subscriptions tool
            print("\n🔧 Calling get_subscriptions tool...")
            result = await client.call_tool("get_subscriptions")
            
            if result.content:
                import json
                subscription_data = json.loads(result.content[0].text)
                
                if subscription_data.get("success"):
                    print(f"✓ Found {subscription_data['subscription_count']} subscriptions")
                    
                    if subscription_data["subscriptions"]:
                        print("\n📋 Azure Subscriptions:")
                        print("-" * 80)
                        for sub in subscription_data["subscriptions"]:
                            print(f"📌 Name: {sub['name']}")
                            print(f"   ID: {sub['id']}")
                            print(f"   State: {sub['state']}")
                            print(f"   Tenant: {sub['tenant_id']}")
                            print("-" * 80)
                    else:
                        print("ℹ️  No subscriptions found")
                else:
                    print(f"❌ Error calling tool: {subscription_data.get('error')}")
            else:
                print("❌ No response content from tool call")
                
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print("\n🔍 Troubleshooting:")
        print("1. Make sure the OBO server is running: python obo_server.py")
        print("2. Check that the server is listening on http://127.0.0.1:8000/mcp")
        print("3. Verify your .env file has the correct Azure settings")

async def main():
    print("🚀 Starting Azure OBO MCP Client")
    print("=" * 60)
    print(f"🏢 Tenant ID: {TENANT_ID}")
    print(f"📱 Client ID: {CLIENT_ID}")
    print(f"🎯 API Scope: {API_SCOPE}")
    print("=" * 60)
    
    # Get Azure token
    print("\n🔐 Acquiring Azure token...")
    token = get_token_silent()
    
    if not token:
        print("❌ Failed to acquire token. Exiting.")
        return
    
    print(f"✓ Token acquired (length: {len(token)} chars)")
    
    # Display the full bearer token
    print("\n🎫 Full Bearer Token:")
    print("=" * 60)
    print(token)
    print("=" * 60)
    
    # Ask user to continue
    response = input("\n❓ Continue with MCP server testing? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("👋 Exiting...")
        return
    
    # Test MCP server
    await test_mcp_server(token)

if __name__ == "__main__":
    asyncio.run(main())