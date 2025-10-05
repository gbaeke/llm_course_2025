#!/usr/bin/env python3
"""
Utility script to delete the persistent agent and clean up
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# File to store the agent ID
AGENT_ID_FILE = "agent_id.txt"

def main():
    # Set up the project endpoint
    project_endpoint = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    
    # Check if agent ID file exists
    if not os.path.exists(AGENT_ID_FILE):
        print(f"❌ No agent ID file found ({AGENT_ID_FILE})")
        print("ℹ️  Nothing to clean up.")
        return
    
    # Load agent ID
    try:
        with open(AGENT_ID_FILE, 'r') as f:
            agent_id = f.read().strip()
            if not agent_id:
                print("❌ Agent ID file is empty")
                return
    except Exception as e:
        print(f"❌ Error reading agent ID file: {e}")
        return
    
    print(f"🗑️  Preparing to delete agent: {agent_id}")
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            # Try to delete the agent
            project_client.agents.delete_agent(agent_id)
            print(f"✅ Successfully deleted agent: {agent_id}")
            
            # Remove the agent ID file
            os.remove(AGENT_ID_FILE)
            print(f"🧹 Removed agent ID file: {AGENT_ID_FILE}")
            
    except Exception as e:
        print(f"❌ Error deleting agent: {e}")
        print("⚠️  The agent might have already been deleted or doesn't exist")
        
        # Ask if user wants to remove the file anyway
        response = input("🤔 Remove the agent ID file anyway? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            try:
                os.remove(AGENT_ID_FILE)
                print(f"🧹 Removed agent ID file: {AGENT_ID_FILE}")
            except Exception as e:
                print(f"❌ Error removing file: {e}")

if __name__ == "__main__":
    main()