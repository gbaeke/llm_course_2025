#!/usr/bin/env python3
"""
List available models in Azure AI Foundry project
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def main():
    project_endpoint = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            print("Available model deployments:")
            print("-" * 40)
            
            # List model deployments
            deployments = project_client.deployments.list()
            
            for deployment in deployments:
                print(f"Name: {deployment.name}")
                if hasattr(deployment, 'model'):
                    print(f"Model: {deployment.model}")
                if hasattr(deployment, 'provisioning_state'):
                    print(f"Status: {deployment.provisioning_state}")
                print(f"Deployment object: {deployment}")
                print("-" * 40)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()