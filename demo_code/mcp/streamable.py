#!/usr/bin/env python3
"""
FastMCP Server using Streamable HTTP Transport

This module demonstrates:
1. Creating an MCP server with the same tools as basic.py but using streamable HTTP transport
2. Running the server on HTTP for network access
3. Production-ready deployment using the recommended transport
"""

from datetime import datetime
from fastmcp import FastMCP


# Create the MCP server
mcp = FastMCP(
    name="StreamableHTTPServer",
    instructions="""
        This is a FastMCP server using streamable HTTP transport.
        It provides the same tools as the basic stdio server:
        - hello: Greet a user by name
        - add: Add two numbers together
        - get_time: Get the current time
        - calculate: Safely evaluate mathematical expressions
        
        This server is accessible over HTTP for network connections.
    """
)


@mcp.tool
def hello(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}! Welcome to the streamable HTTP MCP server."


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


@mcp.tool
def get_server_info() -> str:
    """Get information about this server."""
    return """
    Server: StreamableHTTPServer
    Transport: Streamable HTTP
    Capabilities: Multi-client support, bidirectional streaming
    Tools: hello, add, get_time, calculate, get_server_info
    Resources: server_config, user_profile templates
    """


# Resources
@mcp.resource("resource://server/config")
def get_server_config() -> dict:
    """Get the server configuration as JSON."""
    return {
        "server_name": "StreamableHTTPServer",
        "version": "1.0.0",
        "transport": "streamable-http",
        "host": "127.0.0.1",
        "port": 8000,
        "endpoint": "/mcp",
        "features": {
            "tools": True,
            "resources": True,
            "prompts": False
        },
        "supported_protocols": ["MCP", "HTTP"],
        "max_connections": 100,
        "created_at": "2025-10-05T17:00:00Z"
    }


@mcp.resource("resource://user/{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """Get user profile information (template resource with parameters)."""
    # In a real implementation, this would fetch from a database
    # Here we simulate different users
    profiles = {
        "alice": {"name": "Alice Smith", "role": "developer", "department": "engineering"},
        "bob": {"name": "Bob Johnson", "role": "manager", "department": "operations"},
        "charlie": {"name": "Charlie Brown", "role": "analyst", "department": "data"}
    }
    
    if user_id.lower() in profiles:
        profile = profiles[user_id.lower()]
        return {
            "user_id": user_id,
            "name": profile["name"],
            "role": profile["role"],
            "department": profile["department"],
            "active": True,
            "last_login": "2025-10-05T16:30:00Z"
        }
    else:
        return {
            "user_id": user_id,
            "name": f"User {user_id}",
            "role": "guest",
            "department": "unknown",
            "active": False,
            "last_login": None
        }


if __name__ == "__main__":
    print("Starting FastMCP server with streamable HTTP transport...")
    print("Server will be available at: http://127.0.0.1:8000/mcp")
    print("Press Ctrl+C to stop the server")
    
    # Run with streamable HTTP transport (recommended for production)
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"
    )