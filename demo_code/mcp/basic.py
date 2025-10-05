#!/usr/bin/env python3
"""
Basic MCP Server and Client using FastMCP with stdio transport

This module demonstrates:
1. Creating an MCP server with tools using stdio transport (default)
2. Creating an MCP client that connects to the server
3. Example usage of both server and client functionality
"""

import asyncio
import sys
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP, Client


# Create the MCP server
mcp = FastMCP(
    name="BasicMCPServer",
    instructions="""
        This is a basic MCP server that provides simple tools for demonstration.
        Available tools:
        - hello: Greet a user by name
        - add: Add two numbers together
        - get_time: Get the current time
    """
)


@mcp.tool
def hello(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}! Welcome to the basic MCP server."


@mcp.tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    result = a + b
    return result


@mcp.tool
def get_time() -> str:
    """Get the current time."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Current time: {current_time}"


@mcp.tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow basic mathematical operations for safety
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic mathematical operations are allowed"
        
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating expression: {str(e)}"


async def run_client_example():
    """Example of how to use the MCP client to connect to the server."""
    print("=== MCP Client Example ===")
    print("Connecting to the MCP server...")
    
    # Create a client that connects to this script as a server
    # Note: In a real scenario, you'd point to a separate server file
    client = Client(__file__)
    
    try:
        async with client:
            # Ping the server
            print("Pinging server...")
            await client.ping()
            print("✓ Server is responsive")
            
            # List available tools
            print("\nListing available tools...")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Call the hello tool
            print("\nCalling hello tool...")
            result = await client.call_tool("hello", {"name": "World"})
            print(f"Result: {result.content[0].text}")
            
            # Call the add tool
            print("\nCalling add tool...")
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"Result: {result.content[0].text}")
            
            # Call the get_time tool
            print("\nCalling get_time tool...")
            result = await client.call_tool("get_time", {})
            print(f"Result: {result.content[0].text}")
            
            # Call the calculate tool
            print("\nCalling calculate tool...")
            result = await client.call_tool("calculate", {"expression": "10 * 2 + 5"})
            print(f"Result: {result.content[0].text}")
            
    except Exception as e:
        print(f"Error running client: {e}")


async def main():
    """Main function to demonstrate both server and client usage."""
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # Run as client
        await run_client_example()
    else:
        print("Usage:")
        print(f"  python {__file__}          - Run as MCP server (stdio transport)")
        print(f"  python {__file__} client   - Run as MCP client example")
        print("\nTo test the server:")
        print(f"  python {__file__} client")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # Run the client example
        asyncio.run(main())
    else:
        # Run as MCP server using stdio transport (default)
        print("Starting MCP server with stdio transport...")
        print("Server is ready to accept connections.")
        mcp.run()  # Uses stdio transport by default
