"""
FastMCP Server protected by Azure Entra OAuth authentication.

This server demonstrates how to secure MCP tools using Azure OAuth.
Run with: python server_simple.py
"""

import os
import httpx
from fastmcp import FastMCP
from fastmcp.server.auth.providers.azure import AzureProvider
from fastmcp.server.dependencies import get_access_token
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a wrapper class to force v2.0 behavior
class PatchedAzureProvider(AzureProvider):
    def _get_resource_url(self, mcp_path):
        return None  # Force v2.0 behavior

    def authorize(self, *args, **kwargs):
        kwargs.pop("resource", None)
        return super().authorize(*args, **kwargs)

# Azure configuration from environment variables
AZURE_CLIENT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_TENANT_ID")
BASE_URL = os.getenv("FASTMCP_SERVER_AUTH_AZURE_BASE_URL", "http://localhost:8000")

# Print all these values
print(f"AZURE_CLIENT_ID: {AZURE_CLIENT_ID}")
print(f"AZURE_CLIENT_SECRET: {'*' * len(AZURE_CLIENT_SECRET) if AZURE_CLIENT_SECRET else None}")
print(f"AZURE_TENANT_ID: {AZURE_TENANT_ID}")
print(f"BASE_URL: {BASE_URL}")


# Validate required environment variables
if not all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

# Create the Azure authentication provider
auth_provider = PatchedAzureProvider(
    client_id=str(AZURE_CLIENT_ID),
    client_secret=str(AZURE_CLIENT_SECRET),
    tenant_id=str(AZURE_TENANT_ID),
    base_url=BASE_URL,
    required_scopes=["User.Read", "email", "openid", "profile"],
    redirect_path="/auth/callback"
)

# Create FastMCP server with Azure authentication
mcp = FastMCP(name="Azure Secured MCP Server", auth=auth_provider)

@mcp.tool
async def get_user_info() -> dict:
    """Returns information about the authenticated Azure user."""
    token = get_access_token()
    
    return {
        "azure_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name"),
        "tenant_id": token.claims.get("tid")
    }

if __name__ == "__main__":
    print("🔐 Starting Azure Entra protected FastMCP server...")
    print(f"🌐 Server will be available at: {BASE_URL}")
    print(f"🔑 Authentication provider: Azure Entra (Tenant: {AZURE_TENANT_ID})")
    print(f"📋 Redirect URI: {BASE_URL}/auth/callback")
    print("🚀 Starting MCP server...")
    print("Server is ready to accept connections.")
    
    # Run the server
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"
    )