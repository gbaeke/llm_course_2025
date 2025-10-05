"""
Azure AI Foundry Project Properties Retrieval

This script demonstrates how to use the Azure AI Foundry SDK to retrieve 
properties of a project using the project endpoint URL.
"""

import os
import json
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def retrieve_project_properties(project_endpoint):
    """
    Retrieve project properties using the Azure AI Foundry SDK.
    
    Args:
        project_endpoint (str): The project endpoint URL
    
    Returns:
        dict: Project information and properties
    """
    try:
        # Create the AI Project Client
        print(f"Connecting to project: {project_endpoint}")
        
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        # Get project information using the client
        print("\nRetrieving project properties...")
        
        # Get basic project information
        project_info = {
            "endpoint": project_endpoint,
            "client_type": type(project_client).__name__
        }
        
        # Try to get deployments (this will show available models)
        try:
            print("Fetching model deployments...")
            deployments = list(project_client.deployments.list())
            project_info["deployments"] = []
            
            for deployment in deployments:
                deployment_info = {
                    "name": getattr(deployment, 'name', 'N/A'),
                    "type": getattr(deployment, 'type', 'N/A'),
                    "model_name": getattr(deployment, 'model_name', 'N/A'),
                    "model_version": getattr(deployment, 'model_version', 'N/A'),
                    "model_publisher": getattr(deployment, 'model_publisher', 'N/A'),
                    "capabilities": getattr(deployment, 'capabilities', []),
                    "sku": getattr(deployment, 'sku', 'N/A'),
                    "connection_name": getattr(deployment, 'connection_name', 'N/A')
                }
                project_info["deployments"].append(deployment_info)
                
        except Exception as e:
            print(f"Warning: Could not retrieve deployments: {e}")
            project_info["deployments"] = "Access denied or not available"
        
        # Try to get telemetry information
        try:
            print("Fetching telemetry configuration...")
            connection_string = project_client.telemetry.get_application_insights_connection_string()
            project_info["application_insights"] = {
                "connection_string_available": bool(connection_string),
                "connection_string_length": len(connection_string) if connection_string else 0
            }
        except Exception as e:
            print(f"Warning: Could not retrieve telemetry info: {e}")
            project_info["application_insights"] = "Not configured or access denied"
        
        # Extract project details from endpoint
        if "/api/projects/" in project_endpoint:
            parts = project_endpoint.split("/api/projects/")
            if len(parts) == 2:
                base_url = parts[0]
                project_name = parts[1]
                
                project_info.update({
                    "base_url": base_url,
                    "project_name": project_name,
                    "resource_name": base_url.split("//")[1].split(".")[0] if "//" in base_url else "Unknown"
                })
        
        return project_info
        
    except Exception as e:
        print(f"Error retrieving project properties: {e}")
        return {"error": str(e), "endpoint": project_endpoint}


def main():
    """Main function to demonstrate project properties retrieval."""
    
    # Test both projects to diagnose the issue
    default_project = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    second_project = "https://fndry-course.services.ai.azure.com/api/projects/proj-course2"
    
    print("Azure AI Foundry Project Access Diagnostics")
    print("=" * 50)
    
    # Authenticate with Azure (user should be logged in via Azure CLI)
    print("\nNote: Make sure you are authenticated with Azure CLI:")
    print("Run: az login")
    print()
    
    # Test both projects
    for project_name, endpoint in [("Default Project (proj-course1)", default_project), 
                                   ("Second Project (proj-course2)", second_project)]:
        print(f"\n{'='*60}")
        print(f"Testing: {project_name}")
        print(f"Endpoint: {endpoint}")
        print(f"{'='*60}")
        
        # Retrieve project properties
        project_properties = retrieve_project_properties(endpoint)
        
        # Display results
        print(f"\nResults for {project_name}:")
        print("-" * 40)
        
        if "error" in project_properties:
            print(f"❌ ERROR: {project_properties['error']}")
            print("\nTroubleshooting steps:")
            print("1. Check RBAC permissions in Azure Portal:")
            print("   - Navigate to the Azure AI Foundry resource")
            print("   - Go to Access control (IAM)")
            print("   - Check if you have 'Azure AI User' or higher role")
            print("2. Verify the project exists and is fully provisioned")
            print("3. Try using the default project endpoint if this is a secondary project")
            print("4. Wait 5-10 minutes after role assignment for permissions to propagate")
        else:
            print("✅ SUCCESS: Connection established")
            print(f"   Project Name: {project_properties.get('project_name', 'N/A')}")
            print(f"   Resource Name: {project_properties.get('resource_name', 'N/A')}")
            print(f"   Deployments: {len(project_properties.get('deployments', [])) if isinstance(project_properties.get('deployments'), list) else 'N/A'}")
            
        print(json.dumps(project_properties, indent=2, default=str))


if __name__ == "__main__":
    main()