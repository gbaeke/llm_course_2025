#!/usr/bin/env python3
"""
Simple Azure AI Foundry Agent example with persistence
Creates an agent and saves its ID to a file for reuse
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# File to store the agent ID
AGENT_ID_FILE = "agent_id.txt"

def load_agent_id():
    """Load agent ID from file if it exists"""
    if os.path.exists(AGENT_ID_FILE):
        try:
            with open(AGENT_ID_FILE, 'r') as f:
                agent_id = f.read().strip()
                if agent_id:
                    print(f"📁 Found existing agent ID: {agent_id}")
                    return agent_id
        except Exception as e:
            print(f"⚠️  Error reading agent ID file: {e}")
    return None

def save_agent_id(agent_id):
    """Save agent ID to file"""
    try:
        with open(AGENT_ID_FILE, 'w') as f:
            f.write(agent_id)
        print(f"💾 Saved agent ID to {AGENT_ID_FILE}")
    except Exception as e:
        print(f"⚠️  Error saving agent ID: {e}")

def get_or_create_agent(project_client, model_deployment_name):
    """Get existing agent or create a new one"""
    # Try to load existing agent ID
    agent_id = load_agent_id()
    
    if agent_id:
        try:
            # Try to retrieve the existing agent
            agent = project_client.agents.get_agent(agent_id)
            print(f"♻️  Reusing existing agent: {agent.name} (ID: {agent.id})")
            return agent
        except Exception as e:
            print(f"⚠️  Could not retrieve existing agent {agent_id}: {e}")
            print("🔄 Creating a new agent...")
    
    # Create a new agent if no existing one found or failed to retrieve
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="persistent-demo-agent",
        instructions="You are a helpful assistant that provides clear and concise answers. You can remember our conversation history across multiple runs."
    )
    print(f"✅ Created new agent with ID: {agent.id}")
    
    # Save the agent ID for future use
    save_agent_id(agent.id)
    
    return agent

def main():
    # Set up the project endpoint
    project_endpoint = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    
    # You might need to set up a model deployment name - common ones include:
    # gpt-4o, gpt-4o-mini, gpt-35-turbo, etc.
    # Replace this with your actual model deployment name
    model_deployment_name = "gpt-4.1"  # Using available model from the project
    
    print("🚀 Starting Azure AI Foundry Agent with persistence...")
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            # Get existing agent or create a new one
            agent = get_or_create_agent(project_client, model_deployment_name)
            
            # Create a thread for conversation
            thread = project_client.agents.threads.create()
            print(f"✅ Created thread with ID: {thread.id}")
            
            # Add a message to the thread
            user_message = "Hello! Can you tell me something interesting about machine learning?"
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            print(f"📝 User message: {user_message}")
            
            # Create and process an agent run
            print("🤖 Processing agent response...")
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            print(f"✅ Run completed with status: {run.status}")
            
            if run.status == "failed":
                print(f"❌ Run failed: {run.last_error}")
                return
            
            # Retrieve and display all messages
            messages = project_client.agents.messages.list(thread_id=thread.id)
            print("\n" + "="*50)
            print("CONVERSATION:")
            print("="*50)
            
            # Convert to list and reverse to show in chronological order
            messages_list = list(messages)
            for msg in reversed(messages_list):
                role = msg.role.capitalize()
                content = ""
                
                # Handle different content types
                for content_item in msg.content:
                    if hasattr(content_item, 'text'):
                        content += content_item.text.value
                    elif hasattr(content_item, 'image_file'):
                        content += f"[Image: {content_item.image_file.file_id}]"
                
                print(f"\n{role}: {content}")
            
            print("\n" + "="*50)
            print(f"🔄 Agent {agent.id} is preserved for future runs")
            print(f"📁 Agent ID stored in: {AGENT_ID_FILE}")
            print("\n� Run this script again to reuse the same agent!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you:")
        print("   1. Are logged in with 'az login'")
        print("   2. Have the correct model deployment name")
        print("   3. Have proper permissions on the Azure AI project")

if __name__ == "__main__":
    main()
