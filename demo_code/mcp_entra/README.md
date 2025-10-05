# Azure Entra Protected FastMCP Server

This directory contains a complete example of a FastMCP server protected by Azure Entra (Microsoft) OAuth authentication.

## Files

- `setup.sh` - Script to create Azure App Registration
- `server.py` - MCP server with environment-based Azure credentials
- `server_simple.py` - Alternative simple server implementation  
- `client.py` - MCP client that connects with OAuth authentication
- `test_client.py` - Simple test client for basic connectivity
- `.env` - Environment variables configuration
- `azure_app_config.txt` - Generated Azure configuration
- `requirements.txt` - Python dependencies

## Setup

### 1. Create Azure App Registration

Run the setup script to create the required Azure App Registration:

```bash
./setup.sh
```

This will create an Azure App Registration with:
- Single tenant authentication
- Redirect URI: `http://localhost:8000/auth/callback`
- Required scopes: User.Read, email, openid, profile

### 2. Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Server

Start the Azure-protected MCP server:

```bash
python server.py
```

The server will:
- Load configuration from `.env`
- Start on `http://localhost:8000`
- Provide OAuth endpoints for authentication

### 4. Test with Client

In a separate terminal, run the client:

```bash
python client.py
```

On first connection:
1. Your browser will open to Microsoft's authorization page
2. Sign in with your Microsoft account
3. Grant the requested permissions  
4. The client will connect and call the `get_user_info` tool
5. You'll see your Azure user information displayed

For basic connectivity testing (without OAuth):
```bash
python test_client.py
```

## Available Tools

The server provides one protected tool that requires Azure authentication:

### `get_user_info()`
Returns information about the authenticated Azure user including:
- Azure ID (sub claim)
- Email address
- Display name  
- Tenant ID

## Authentication Flow

1. When a client connects, they're redirected to Microsoft's OAuth page
2. User signs in with their Microsoft account
3. After authorization, user is redirected back to the server
4. Server validates the token and extracts user claims
5. All subsequent tool calls are authenticated and include user context

## Security Notes

- The `.env` file contains sensitive credentials - never commit it to version control
- Client secrets expire after 2 years - monitor and rotate them
- Use HTTPS in production environments
- Consider using Azure Key Vault for credential management in production

## Testing

You can test the authentication by:
1. Starting the server
2. Navigating to `http://localhost:8000` in your browser
3. Following the OAuth flow
4. Using an MCP client to call the protected tools

## Environment Variables

The following environment variables are used by `server_env.py`:

```env
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.azure.AzureProvider
FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID=your-client-id
FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET=your-client-secret
FASTMCP_SERVER_AUTH_AZURE_TENANT_ID=your-tenant-id
FASTMCP_SERVER_AUTH_AZURE_BASE_URL=http://localhost:8000
FASTMCP_SERVER_AUTH_AZURE_REQUIRED_SCOPES=User.Read,email,openid,profile
```