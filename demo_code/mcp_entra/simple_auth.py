#!/usr/bin/env python3
"""
Simple script that:
1. Gets a token silently using MSAL device flow for custom API
2. Uses OBO flow to get Azure ARM token
3. Lists Azure subscriptions

Requires: pip install msal requests python-dotenv
"""

import os
import msal
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("FASTMCP_SERVER_AUTH_AZURE_TENANT_ID")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
API_SCOPE = f"api://{CLIENT_ID}/execute"

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
    
    # Create MSAL app as public client (like in your code)
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,  # Using same client ID for both
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
            print("Token acquired silently from cache")
            save_cache(cache)
            return result["access_token"]
    
    # If no token in cache, use device flow
    print("No valid token in cache, starting device flow...")
    flow = app.initiate_device_flow(scopes=[API_SCOPE])
    if "user_code" not in flow:
        print(f"Failed to create device flow: {flow.get('error')}")
        return None
    
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)
    save_cache(cache)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"Failed to obtain token: {result.get('error')}")
        return None

def get_obo_token(user_token):
    """Use OBO flow to get Azure ARM token"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "assertion": user_token,
        "scope": "https://management.azure.com/.default",
        "requested_token_use": "on_behalf_of"
    }
    
    try:
        response = requests.post(token_url, data=data)
        if not response.ok:
            print(f"OBO Error Response: {response.text}")
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Error getting OBO token: {e}")
        return None

def list_subscriptions(arm_token):
    """List Azure subscriptions using ARM token"""
    url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
    headers = {
        "Authorization": f"Bearer {arm_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        subscriptions = response.json()["value"]
        
        print("\nAzure Subscriptions:")
        print("-" * 50)
        for sub in subscriptions:
            print(f"Name: {sub['displayName']}")
            print(f"ID: {sub['subscriptionId']}")
            print(f"State: {sub['state']}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error listing subscriptions: {e}")

def main():
    print("Getting token silently...")
    user_token = get_token_silent()
    if not user_token:
        print("Failed to get user token")
        return
    
    print("Getting OBO token for Azure ARM...")
    arm_token = get_obo_token(user_token)
    if not arm_token:
        print("Failed to get OBO token")
        return
    
    print("Listing subscriptions...")
    list_subscriptions(arm_token)

if __name__ == "__main__":
    main()