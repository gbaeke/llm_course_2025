#!/bin/bash

# Azure App Registration Setup Script for FastMCP OAuth
# This script creates an Azure App Registration with the required configuration

set -e  # Exit on any error

# Configuration
APP_NAME="FastMCP Server"
REDIRECT_URI="http://localhost:8000/auth/callback"
REQUIRED_SCOPES="User.Read email openid profile"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first:"
        print_info "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
}

# Check if user is logged in to Azure
check_azure_login() {
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
}

# Get current tenant information
get_tenant_info() {
    TENANT_ID=$(az account show --query tenantId -o tsv)
    TENANT_NAME=$(az account show --query name -o tsv)
    print_info "Current tenant: $TENANT_NAME ($TENANT_ID)"
}

# Check if app registration already exists
check_existing_app() {
    local app_id=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)
    if [ "$app_id" != "" ] && [ "$app_id" != "null" ]; then
        print_warning "App registration '$APP_NAME' already exists (ID: $app_id)"
        echo
        read -p "Do you want to remove the existing registration and create a new one? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing app registration..."
            az ad app delete --id "$app_id"
            print_success "Existing app registration removed"
        else
            print_info "Keeping existing registration. Exiting..."
            exit 0
        fi
    fi
}

# Create the app registration
create_app_registration() {
    print_info "Creating Azure App Registration: $APP_NAME"
    
    # Create the app registration with single tenant support
    local app_result=$(az ad app create \
        --display-name "$APP_NAME" \
        --sign-in-audience "AzureADMyOrg" \
        --web-redirect-uris "$REDIRECT_URI" \
        --required-resource-accesses '[
            {
                "resourceAppId": "00000003-0000-0000-c000-000000000000",
                "resourceAccess": [
                    {
                        "id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d",
                        "type": "Scope"
                    },
                    {
                        "id": "64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0",
                        "type": "Scope"
                    },
                    {
                        "id": "14dad69e-099b-42c9-810b-d002981feec1",
                        "type": "Scope"
                    },
                    {
                        "id": "37f7f235-527c-4136-accd-4a02d197296e",
                        "type": "Scope"
                    }
                ]
            }
        ]')
    
    APP_ID=$(echo "$app_result" | jq -r '.appId')
    OBJECT_ID=$(echo "$app_result" | jq -r '.id')
    
    if [ "$APP_ID" == "null" ] || [ "$APP_ID" == "" ]; then
        print_error "Failed to create app registration"
        exit 1
    fi
    
    print_success "App registration created with ID: $APP_ID"
}

# Create client secret
create_client_secret() {
    print_info "Creating client secret..."
    
    local secret_result=$(az ad app credential reset \
        --id "$APP_ID" \
        --display-name "FastMCP Server Secret" \
        --years 2)
    
    CLIENT_SECRET=$(echo "$secret_result" | jq -r '.password')
    
    if [ "$CLIENT_SECRET" == "null" ] || [ "$CLIENT_SECRET" == "" ]; then
        print_error "Failed to create client secret"
        exit 1
    fi
    
    print_success "Client secret created"
}

# Display final configuration
display_configuration() {
    echo
    print_success "Azure App Registration Setup Complete!"
    echo
    echo "=================================================================================="
    echo -e "${GREEN}Configuration Details:${NC}"
    echo "=================================================================================="
    echo "App Name:           $APP_NAME"
    echo "Client ID:          $APP_ID"
    echo "Tenant ID:          $TENANT_ID"
    echo "Client Secret:      $CLIENT_SECRET"
    echo "Redirect URI:       $REDIRECT_URI"
    echo "Account Type:       Single Tenant (AzureADMyOrg)"
    echo "Required Scopes:    $REQUIRED_SCOPES"
    echo "=================================================================================="
    echo
    echo -e "${YELLOW}IMPORTANT SECURITY NOTES:${NC}"
    echo "• Store the client secret securely - it won't be shown again!"
    echo "• Never commit these credentials to version control"
    echo "• Use environment variables or a secrets manager in production"
    echo "• The client secret expires in 2 years"
    echo
    echo -e "${BLUE}Environment Variables for .env file:${NC}"
    echo "FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.azure.AzureProvider"
    echo "FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID=$APP_ID"
    echo "FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET=$CLIENT_SECRET"
    echo "FASTMCP_SERVER_AUTH_AZURE_TENANT_ID=$TENANT_ID"
    echo "FASTMCP_SERVER_AUTH_AZURE_BASE_URL=http://localhost:8000"
    echo "FASTMCP_SERVER_AUTH_AZURE_REQUIRED_SCOPES=User.Read,email,openid,profile"
    echo
    echo -e "${BLUE}Python Configuration Example:${NC}"
    echo "from fastmcp.server.auth.providers.azure import AzureProvider"
    echo ""
    echo "auth_provider = AzureProvider("
    echo "    client_id=\"$APP_ID\","
    echo "    client_secret=\"$CLIENT_SECRET\","
    echo "    tenant_id=\"$TENANT_ID\","
    echo "    base_url=\"http://localhost:8000\","
    echo "    required_scopes=[\"User.Read\", \"email\", \"openid\", \"profile\"]"
    echo ")"
    echo
}

# Save configuration to file
save_configuration() {
    local config_file="azure_app_config.txt"
    {
        echo "Azure App Registration Configuration"
        echo "Generated on: $(date)"
        echo "=================================="
        echo "App Name: $APP_NAME"
        echo "Client ID: $APP_ID"
        echo "Tenant ID: $TENANT_ID"
        echo "Client Secret: $CLIENT_SECRET"
        echo "Redirect URI: $REDIRECT_URI"
        echo "Account Type: Single Tenant (AzureADMyOrg)"
        echo ""
        echo "Environment Variables:"
        echo "FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.azure.AzureProvider"
        echo "FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID=$APP_ID"
        echo "FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET=$CLIENT_SECRET"
        echo "FASTMCP_SERVER_AUTH_AZURE_TENANT_ID=$TENANT_ID"
        echo "FASTMCP_SERVER_AUTH_AZURE_BASE_URL=http://localhost:8000"
        echo "FASTMCP_SERVER_AUTH_AZURE_REQUIRED_SCOPES=User.Read,email,openid,profile"
    } > "$config_file"
    
    print_info "Configuration saved to: $config_file"
}

# Main execution
main() {
    echo "=================================================================================="
    echo -e "${GREEN}Azure App Registration Setup for FastMCP OAuth${NC}"
    echo "=================================================================================="
    echo
    
    check_azure_cli
    check_azure_login
    get_tenant_info
    check_existing_app
    create_app_registration
    create_client_secret
    display_configuration
    save_configuration
    
    echo
    print_success "Setup completed successfully!"
    print_info "You can now use these credentials to configure your FastMCP server with Azure OAuth."
    
    echo
    echo "=================================================================================="
    echo -e "${YELLOW}ADDITIONAL MANUAL CONFIGURATION REQUIRED:${NC}"
    echo "=================================================================================="
    echo "To enable device flow authentication and OBO scenarios, please complete these steps:"
    echo
    echo "1. Enable Public Client Flows:"
    echo "   az ad app update --id $APP_ID --set allowPublicClient=true"
    echo
    echo "2. Set Application ID URI:"
    echo "   az ad app update --id $APP_ID --set identifierUris=[\"api://$APP_ID\"]"
    echo
    echo "3. Add 'execute' scope to exposed API:"
    echo "   - Go to Azure Portal > App Registrations > $APP_NAME"
    echo "   - Navigate to 'Expose an API'"
    echo "   - Add a scope named 'execute' with:"
    echo "     • Scope name: execute"
    echo "     • Admin consent display name: Execute"
    echo "     • Admin consent description: Execute API operations"
    echo "     • User consent display name: Execute"
    echo "     • User consent description: Execute API operations"
    echo "     • State: Enabled"
    echo
    echo "   OR use CLI (requires UUID generation):"
    echo "   SCOPE_ID=\$(uuidgen)"
    echo "   az ad app update --id $APP_ID --set api='{\"oauth2PermissionScopes\":[{\"id\":\"'\$SCOPE_ID'\",\"adminConsentDescription\":\"Execute API operations\",\"adminConsentDisplayName\":\"Execute\",\"userConsentDescription\":\"Execute API operations\",\"userConsentDisplayName\":\"Execute\",\"value\":\"execute\",\"type\":\"User\",\"isEnabled\":true}]}'"
    echo
    echo "4. After completing these steps, your app will support:"
    echo "   • Device code flow authentication"
    echo "   • On-behalf-of (OBO) token exchange"
    echo "   • Custom API scope: api://$APP_ID/execute"
    echo "=================================================================================="
}

# Run the main function
main "$@"
