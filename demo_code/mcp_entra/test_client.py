"""
Simple test client that demonstrates the connection logic without authentication.

This shows what happens when the server is not running.
Run with: python test_client.py
"""

from fastmcp import Client
import asyncio

async def test_connection():
    print("🔗 Testing connection to MCP server...")
    print("🌐 Server URL: http://localhost:8000/mcp/")
    
    try:
        # Try to connect without OAuth first to test basic connectivity
        async with Client("http://localhost:8000/mcp/") as client:
            print("✓ Connected to server (no auth)")
            await client.ping()
            print("✓ Server responded to ping")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 This is expected if the server is not running.")
        print("   Start the server with: python server.py")

if __name__ == "__main__":
    asyncio.run(test_connection())