#!/usr/bin/env python3
"""
List all agents in the Azure AI Foundry project
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
            print("📋 Listing all agents in the project:")
            print("-" * 60)
            
            # List all agents
            agents = project_client.agents.list_agents()
            
            agent_count = 0
            for agent in agents:
                agent_count += 1
                print(f"🤖 Agent #{agent_count}:")
                print(f"   ID: {agent.id}")
                print(f"   Name: {agent.name}")
                print(f"   Model: {agent.model}")
                print(f"   Created: {agent.created_at}")
                print(f"   Instructions: {agent.instructions[:100]}..." if len(agent.instructions) > 100 else f"   Instructions: {agent.instructions}")
                print("-" * 60)
            
            if agent_count == 0:
                print("ℹ️  No agents found in the project")
            else:
                print(f"📊 Total agents: {agent_count}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()