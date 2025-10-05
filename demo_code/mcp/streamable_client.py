#!/usr/bin/env python3
"""
FastMCP Client for Streamable HTTP Transport

This module demonstrates:
1. Connecting to a FastMCP server using streamable HTTP transport
2. Making requests to the server over HTTP
3. Handling responses from network-based MCP servers
"""

import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def test_server_connection(server_url: str):
    """Test basic server connectivity."""
    print(f"=== Testing Server Connection ===")
    print(f"Connecting to: {server_url}")
    
    # Create client with StreamableHttpTransport
    transport = StreamableHttpTransport(url=server_url)
    client = Client(transport)
    
    try:
        async with client:
            # Test ping
            print("Pinging server...")
            response = await client.ping()
            print(f"✓ Ping successful: {response}")
            return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


async def demonstrate_tools(server_url: str):
    """Demonstrate all available tools on the server."""
    print(f"\n=== Demonstrating Tools ===")
    
    # Create client - FastMCP can infer StreamableHttpTransport from URL
    client = Client(server_url)
    
    try:
        async with client:
            # List available tools
            print("Listing available tools...")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Test each tool
            print("\n--- Testing hello tool ---")
            result = await client.call_tool("hello", {"name": "HTTP Client"})
            print(f"Result: {result.content[0].text}")
            
            print("\n--- Testing add tool ---")
            result = await client.call_tool("add", {"a": 15, "b": 25})
            print(f"Result: {result.content[0].text}")
            
            print("\n--- Testing get_time tool ---")
            result = await client.call_tool("get_time", {})
            print(f"Result: {result.content[0].text}")
            
            print("\n--- Testing calculate tool ---")
            result = await client.call_tool("calculate", {"expression": "20 * 3 + 10"})
            print(f"Result: {result.content[0].text}")
            
            print("\n--- Testing get_server_info tool ---")
            result = await client.call_tool("get_server_info", {})
            print(f"Result: {result.content[0].text}")
            
    except Exception as e:
        print(f"Error during tool demonstration: {e}")


async def demonstrate_resources(server_url: str):
    """Demonstrate resource functionality."""
    print(f"\n=== Demonstrating Resources ===")
    
    client = Client(server_url)
    
    try:
        async with client:
            # List available resources
            print("Listing available resources...")
            resources = await client.list_resources()
            print(f"Found {len(resources)} resources:")
            for resource in resources:
                print(f"  - {resource.uri}: {resource.name}")
                if resource.description:
                    print(f"    Description: {resource.description}")
                print(f"    MIME Type: {resource.mimeType}")
            
            # List resource templates
            print("\nListing available resource templates...")
            templates = await client.list_resource_templates()
            print(f"Found {len(templates)} resource templates:")
            for template in templates:
                print(f"  - {template.uriTemplate}: {template.name}")
                if template.description:
                    print(f"    Description: {template.description}")
            
            # Read the server config resource
            print("\n--- Reading server config resource ---")
            config_content = await client.read_resource("resource://server/config")
            print(f"Config content: {config_content[0].text}")
            
            # Read user profile resources using templates
            print("\n--- Reading user profile resources ---")
            users = ["alice", "bob", "charlie", "unknown"]
            for user in users:
                try:
                    profile_content = await client.read_resource(f"resource://user/{user}/profile")
                    print(f"{user.capitalize()} profile: {profile_content[0].text}")
                except Exception as e:
                    print(f"Error reading profile for {user}: {e}")
            
    except Exception as e:
        print(f"Error during resource demonstration: {e}")


async def test_concurrent_clients(server_url: str):
    """Test multiple concurrent client connections."""
    print(f"\n=== Testing Concurrent Clients ===")
    
    async def client_task(client_id: int):
        """Individual client task."""
        client = Client(server_url)
        try:
            async with client:
                # Each client calls a different tool
                if client_id == 1:
                    result = await client.call_tool("hello", {"name": f"Client-{client_id}"})
                elif client_id == 2:
                    result = await client.call_tool("add", {"a": client_id * 10, "b": 5})
                else:
                    result = await client.call_tool("get_time", {})
                
                print(f"Client {client_id} result: {result.content[0].text}")
                return f"Client-{client_id} completed"
        except Exception as e:
            print(f"Client {client_id} error: {e}")
            return f"Client-{client_id} failed"
    
    # Run multiple clients concurrently
    print("Running 3 concurrent clients...")
    tasks = [client_task(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"Concurrent test results: {results}")


async def interactive_client(server_url: str):
    """Interactive client for manual testing."""
    print(f"\n=== Interactive Client ===")
    print("Available commands:")
    print("  hello <name>")
    print("  add <a> <b>")
    print("  time")
    print("  calc <expression>")
    print("  info")
    print("  list")
    print("  resources")
    print("  resource <uri>")
    print("  profile <user_id>")
    print("  quit")
    
    client = Client(server_url)
    
    try:
        async with client:
            while True:
                try:
                    command = input("\n> ").strip()
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    elif command.lower() == 'list':
                        tools = await client.list_tools()
                        print(f"Available tools: {[tool.name for tool in tools]}")
                    elif command.lower() == 'resources':
                        resources = await client.list_resources()
                        templates = await client.list_resource_templates()
                        print(f"Static resources: {[r.uri for r in resources]}")
                        print(f"Resource templates: {[t.uriTemplate for t in templates]}")
                    elif command.startswith('resource '):
                        uri = command[9:]
                        try:
                            content = await client.read_resource(uri)
                            print(f"Resource content: {content[0].text}")
                        except Exception as e:
                            print(f"Error reading resource: {e}")
                    elif command.startswith('profile '):
                        user_id = command[8:]
                        try:
                            content = await client.read_resource(f"resource://user/{user_id}/profile")
                            print(f"Profile: {content[0].text}")
                        except Exception as e:
                            print(f"Error reading profile: {e}")
                    elif command.startswith('hello '):
                        name = command[6:]
                        result = await client.call_tool("hello", {"name": name})
                        print(result.content[0].text)
                    elif command.startswith('add '):
                        parts = command[4:].split()
                        if len(parts) == 2:
                            a, b = float(parts[0]), float(parts[1])
                            result = await client.call_tool("add", {"a": a, "b": b})
                            print(result.content[0].text)
                        else:
                            print("Usage: add <a> <b>")
                    elif command.lower() in ['time', 'get_time']:
                        result = await client.call_tool("get_time", {})
                        print(result.content[0].text)
                    elif command.startswith('calc '):
                        expression = command[5:]
                        result = await client.call_tool("calculate", {"expression": expression})
                        print(result.content[0].text)
                    elif command.lower() in ['info', 'server_info']:
                        result = await client.call_tool("get_server_info", {})
                        print(result.content[0].text)
                    else:
                        print("Unknown command. Type 'quit' to exit.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    
    except Exception as e:
        print(f"Failed to connect to server: {e}")


async def main():
    """Main function to run the HTTP client tests."""
    server_url = "http://127.0.0.1:8000/mcp"
    
    print("FastMCP Streamable HTTP Client")
    print("=" * 40)
    print(f"Server URL: {server_url}")
    print("\nMake sure the server is running:")
    print("  python streamable.py")
    print("\nStarting client tests...\n")
    
    # Test basic connectivity
    if not await test_server_connection(server_url):
        print("\n⚠️  Server is not running or not accessible.")
        print("Please start the server first: python streamable.py")
        return
    
    # Run demonstrations
    await demonstrate_tools(server_url)
    await demonstrate_resources(server_url)
    await test_concurrent_clients(server_url)
    
    # Interactive mode
    print("\n" + "=" * 40)
    response = input("Enter interactive mode? (y/n): ")
    if response.lower().startswith('y'):
        await interactive_client(server_url)
    
    print("\nClient tests completed!")


if __name__ == "__main__":
    asyncio.run(main())