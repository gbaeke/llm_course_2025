#!/usr/bin/env python3
"""
FastMCP Server with OBO (On-Behalf-Of) flow for Azure ARM operations.

This server:
1. Uses FastMCP JWTVerifier to validate incoming Azure tokens
2. Implements OBO flow to exchange tokens for Azure ARM access
3. Provides a tool to list Azure subscriptions

The server expects clients to send valid Azure JWT tokens.
"""

import os
import asyncio
import requests
from typing import Any, Dict
from dotenv import load_dotenv

from fastmcp import FastMCP, Context
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_TENANT_ID")

# Azure JWT verification configuration
JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/keys"  # v1.0 JWKS endpoint
ISSUER = f"https://sts.windows.net/{TENANT_ID}/"  # v1.0 tokens use sts.windows.net
AUDIENCE = f"api://{CLIENT_ID}"

# Configure JWT verifier for Azure tokens
jwt_verifier = JWTVerifier(
    jwks_uri=JWKS_URI,
    issuer=ISSUER,
    audience=AUDIENCE,
    required_scopes=["execute"]  # Require the execute scope we defined
)

# Create FastMCP server with JWT verification
mcp = FastMCP(name="Azure OBO Server", auth=jwt_verifier)

class SubscriptionInfo(BaseModel):
    """Model for subscription information"""
    name: str
    id: str
    state: str
    tenant_id: str

def get_obo_token(user_token: str) -> str:
    """
    Use OBO flow to exchange user token for Azure ARM token
    
    Args:
        user_token: The validated JWT token from the client
        
    Returns:
        Azure ARM access token
        
    Raises:
        Exception: If OBO token exchange fails
    """
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "assertion": user_token,
        "scope": "https://management.azure.com/.default",
        "requested_token_use": "on_behalf_of"
    }
    
    response = requests.post(token_url, data=data)
    
    if not response.ok:
        error_detail = response.text
        raise Exception(f"OBO token exchange failed: {error_detail}")
    
    return response.json()["access_token"]

def list_azure_subscriptions(arm_token: str) -> list[SubscriptionInfo]:
    """
    List Azure subscriptions using ARM token
    
    Args:
        arm_token: Azure ARM access token
        
    Returns:
        List of subscription information
        
    Raises:
        Exception: If subscription listing fails
    """
    url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
    headers = {
        "Authorization": f"Bearer {arm_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if not response.ok:
        error_detail = response.text
        raise Exception(f"Failed to list subscriptions: {error_detail}")
    
    subscriptions = response.json()["value"]
    
    return [
        SubscriptionInfo(
            name=sub["displayName"],
            id=sub["subscriptionId"],
            state=sub["state"],
            tenant_id=sub["tenantId"]
        )
        for sub in subscriptions
    ]

@mcp.tool()
def get_subscriptions(ctx: Context) -> Dict[str, Any]:
    """
    List Azure subscriptions using OBO flow.
    
    This tool exchanges the incoming user token for an Azure ARM token
    and returns a list of Azure subscriptions the user has access to.
    
    Returns:
        Dictionary containing subscription information
    """
    try:
        # Get the access token from the authentication context
        access_token = get_access_token()
        if not access_token:
            return {
                "success": False,
                "error": "No authentication token provided",
                "subscription_count": 0,
                "subscriptions": []
            }
        
        # Get the raw JWT token
        user_token = access_token.token
        
        # Exchange user token for Azure ARM token using OBO flow
        arm_token = get_obo_token(user_token)
        
        # List subscriptions using the ARM token
        subscriptions = list_azure_subscriptions(arm_token)
        
        return {
            "success": True,
            "subscription_count": len(subscriptions),
            "subscriptions": [
                {
                    "name": sub.name,
                    "id": sub.id,
                    "state": sub.state,
                    "tenant_id": sub.tenant_id
                }
                for sub in subscriptions
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "subscription_count": 0,
            "subscriptions": []
        }

@mcp.tool()
def get_user_info(ctx: Context) -> Dict[str, Any]:
    """
    Get information about the authenticated user from the JWT token.
    
    Returns:
        Dictionary containing user information from the token claims
    """
    try:
        # Get the access token from the authentication context
        access_token = get_access_token()
        if not access_token:
            return {
                "success": False,
                "error": "No authentication token provided",
                "user_info": {}
            }
        
        # Access the JWT claims
        claims = access_token.claims
        
        return {
            "success": True,
            "user_info": {
                "subject": claims.get("sub"),
                "email": claims.get("email"),
                "name": claims.get("name"),
                "tenant_id": claims.get("tid"),
                "object_id": claims.get("oid"),
                "scopes": claims.get("scp", "").split() if claims.get("scp") else [],
                "audience": claims.get("aud"),
                "issuer": claims.get("iss"),
                "issued_at": claims.get("iat"),
                "expires_at": claims.get("exp")
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "user_info": {}
        }

if __name__ == "__main__":
    print("🚀 Starting Azure OBO FastMCP Server")
    print("=" * 60)
    print(f"📋 Server Name: {mcp.name}")
    print(f"🔐 Authentication: JWT Verification")
    print(f"🏢 Tenant ID: {TENANT_ID}")
    print(f"📱 Client ID: {CLIENT_ID}")
    print(f"🎯 Audience: {AUDIENCE}")
    print(f"🔗 JWKS URI: {JWKS_URI}")
    print(f"🛠️  Available Tools: get_subscriptions, get_user_info")
    print("=" * 60)
    print("💡 The server validates Azure JWT tokens and uses OBO flow for ARM access")
    print("📝 Clients must provide: Authorization: Bearer <azure-jwt-token>")
    print("🔍 Required scope: execute")
    print("=" * 60)
    
    # Run the server
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"
    )