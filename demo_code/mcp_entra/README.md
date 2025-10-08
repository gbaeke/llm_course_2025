# Azure OBO FastMCP Server & Client

This project demonstrates an **On-Behalf-Of (OBO) authentication flow** using FastMCP, where a client authenticates with Azure AD, sends tokens to an MCP server, and the server exchanges those tokens for Azure ARM access to list subscriptions.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   MCP Server    │    │   Azure AD      │    │   Azure ARM     │
│                 │    │                 │    │                 │    │                 │
│ obo_client.py   │    │ obo_server.py   │    │ (Token Issuer)  │    │ (Resource API)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Flow Diagram

```
┌─────────────┐                          ┌─────────────┐                          ┌─────────────┐
│   Client    │                          │   Server    │                          │ Azure AD/ARM│
└─────────────┘                          └─────────────┘                          └─────────────┘
      │                                        │                                        │
      │ 1. Device Flow Authentication          │                                        │
      │ ──────────────────────────────────────────────────────────────────────────────▶│
      │                                        │                  User Token           │
      │ ◀──────────────────────────────────────────────────────────────────────────────│
      │                                        │                                        │
      │ 2. Bearer Token to MCP                 │                                        │
      │ ──────────────────────────────────────▶│                                        │
      │                                        │ 3. Validate JWT                       │
      │                                        │ ──────────────────────────────────────▶│
      │                                        │                   JWKS Keys           │
      │                                        │ ◀──────────────────────────────────────│
      │                                        │                                        │
      │                                        │ 4. OBO Token Exchange                 │
      │                                        │ ──────────────────────────────────────▶│
      │                                        │                   ARM Token           │
      │                                        │ ◀──────────────────────────────────────│
      │                                        │                                        │
      │                                        │ 5. List Subscriptions                 │
      │                                        │ ──────────────────────────────────────▶│
      │             Subscriptions              │               Subscription Data       │
      │ ◀──────────────────────────────────────│ ◀──────────────────────────────────────│
```

## Requirements

### 1. Azure App Registration

Your Azure AD app must be configured with:

```
✅ Application ID URI: api://{CLIENT_ID}
✅ Exposed API Scope: execute
✅ Public Client Flows: Enabled
✅ Required Permissions:
   - Microsoft Graph: User.Read, email, openid, profile
   - Azure Service Management: user_impersonation (for ARM access)
```

### 2. Environment Variables (.env)

```bash
FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID=040bb7b2-95f2-4acf-86ae-1af181db8237
FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET=your-client-secret
FASTMCP_SERVER_AUTH_AZURE_TENANT_ID=484588df-21e4-427c-b2a5-cc39d6a73281
```

### 3. Python Dependencies

```bash
pip install fastmcp msal requests python-dotenv pydantic
```

## Step-by-Step Flow

### Phase 1: Client Authentication

```
Client (obo_client.py)
├── 1. Load environment variables
├── 2. Create MSAL PublicClientApplication
├── 3. Check token cache for existing valid tokens
├── 4. If no cache: Initiate device flow for scope: api://{CLIENT_ID}/execute
├── 5. User authenticates via browser (device code flow)
└── 6. Receive Azure AD v1.0 JWT token
```

**Key Details:**
- **Scope**: `api://{CLIENT_ID}/execute` (custom API scope)
- **Token Version**: v1.0 (because of custom API scope)
- **Issuer**: `https://sts.windows.net/{TENANT_ID}/`
- **Audience**: `api://{CLIENT_ID}`

### Phase 2: MCP Server Communication

```
Client → Server
├── 7. Connect to http://127.0.0.1:8000/mcp with Bearer token
├── 8. Server validates JWT using FastMCP JWTVerifier
│   ├── Fetches JWKS keys from Azure AD
│   ├── Verifies signature, issuer, audience, expiration
│   └── Checks required scope: "execute"
├── 9. Client calls get_subscriptions tool
└── 10. Server extracts validated token from FastMCP context
```

### Phase 3: OBO Token Exchange

```
Server (obo_server.py)
├── 11. Extract user token from FastMCP authentication context
├── 12. POST to https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token
│   ├── grant_type: urn:ietf:params:oauth:grant-type:jwt-bearer
│   ├── client_id: {CLIENT_ID}
│   ├── client_secret: {CLIENT_SECRET}
│   ├── assertion: {USER_TOKEN}
│   ├── scope: https://management.azure.com/.default
│   └── requested_token_use: on_behalf_of
└── 13. Receive Azure ARM access token
```

### Phase 4: Azure ARM API Call

```
Server → Azure ARM
├── 14. GET https://management.azure.com/subscriptions?api-version=2020-01-01
├── 15. Authorization: Bearer {ARM_TOKEN}
├── 16. Receive subscription list
└── 17. Return formatted results to client
```

## Potential Failure Points

### 🔴 Authentication Failures

| Issue | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Public client flows not enabled | Enable in Azure Portal → App Registration → Authentication |
| `AADSTS500011` | Custom API scope not found | Add `api://{CLIENT_ID}/execute` scope in "Expose an API" |
| `Token expired` | Cached token is stale | Clear `.token_cache.json` file |
| `insufficient_privileges` | User lacks permissions | Ensure user has subscription access |

### 🔴 JWT Validation Failures

| Issue | Cause | Solution |
|-------|-------|----------|
| `Bearer token rejected` | Wrong issuer/audience | Verify v1.0 vs v2.0 endpoint configuration |
| `JWKS fetch failed` | Network/DNS issues | Check connectivity to Azure AD endpoints |
| `Invalid signature` | Wrong JWKS endpoint | Use v1.0 endpoint: `/discovery/keys` not `/discovery/v2.0/keys` |
| `Missing required scope` | Token lacks `execute` scope | Verify scope is properly configured and requested |

### 🔴 OBO Exchange Failures

| Issue | Cause | Solution |
|-------|-------|----------|
| `invalid_grant` | User token invalid for OBO | Ensure app has permission for `user_impersonation` |
| `unauthorized_client` | App not configured for OBO | Add Azure Service Management API permissions |
| `consent_required` | Admin consent missing | Grant admin consent for API permissions |
| `insufficient_scope` | Missing ARM permissions | Add `https://management.azure.com/user_impersonation` |

### 🔴 ARM API Failures

| Issue | Cause | Solution |
|-------|-------|----------|
| `Forbidden (403)` | User lacks subscription access | Assign appropriate RBAC roles |
| `Unauthorized (401)` | ARM token invalid/expired | Check OBO token exchange |
| `Throttling (429)` | Too many requests | Implement retry logic with exponential backoff |

## Token Details

### User Token (v1.0)
```json
{
  "aud": "api://040bb7b2-95f2-4acf-86ae-1af181db8237",
  "iss": "https://sts.windows.net/484588df-21e4-427c-b2a5-cc39d6a73281/",
  "scp": "execute",
  "ver": "1.0"
}
```

### ARM Token (v1.0/v2.0)
```json
{
  "aud": "https://management.azure.com/",
  "iss": "https://sts.windows.net/484588df-21e4-427c-b2a5-cc39d6a73281/",
  "scp": "user_impersonation"
}
```

## Running the Demo

### 1. Start the Server
```bash
cd /path/to/mcp_entra
source .venv/bin/activate
python obo_server.py
```

### 2. Run the Client
```bash
# In another terminal
source .venv/bin/activate
python obo_client.py
```

### 3. Expected Output
```
🚀 Starting Azure OBO MCP Client
🔐 Acquiring Azure token...
✓ Token acquired silently from cache
🎫 Full Bearer Token: eyJ0eXAiOiJKV1QiLCJhbGc...
❓ Continue with MCP server testing? (y/N): y
🔗 Connecting to MCP server: http://127.0.0.1:8000/mcp
✓ Connected to MCP server successfully
📡 Testing server ping...
✓ Server responded to ping
🛠️  Listing available tools...
Available tools: ['get_subscriptions', 'get_user_info']
👤 Getting user information...
✓ User: geert@baeke.info
✓ Name: Geert Baeke
✓ Tenant: 484588df-21e4-427c-b2a5-cc39d6a73281
✓ Scopes: execute
🔧 Calling get_subscriptions tool...
✓ Found 2 subscriptions
📋 Azure Subscriptions:
────────────────────────────────────────────────────────────────────────────────
📌 Name: Inity
   ID: d1d3dadc-bc2a-4495-b8dd-70443d1c70d1
   State: Enabled
   Tenant: 484588df-21e4-427c-b2a5-cc39d6a73281
────────────────────────────────────────────────────────────────────────────────
```

## Security Considerations

- **Client Secret**: Store securely, never in version control
- **Token Cache**: Contains sensitive tokens, secure appropriately
- **HTTPS**: Use HTTPS in production (not HTTP)
- **Token Expiration**: Implement proper token refresh logic
- **Scope Validation**: Server validates required scopes before processing
- **Error Handling**: Don't expose sensitive information in error messages