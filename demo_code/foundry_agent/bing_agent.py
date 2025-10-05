#!/usr/bin/env python3
"""
Bing Search Agent - Azure AI Foundry Agent with Bing Search integration
Creates a temporary agent with Bing grounding search capabilities
Does not persist the agent ID - creates a new agent each time
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool

def create_bing_agent(project_client, model_deployment_name, bing_connection_id):
    """Create a new agent with Bing grounding search tool"""
    
    # Initialize the Bing Grounding tool
    bing = BingGroundingTool(connection_id=bing_connection_id)
    
    # Create a new agent with Bing search capabilities
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="bing-search-agent",
        instructions="""You are a helpful assistant with access to real-time web information through Bing Search. 
        You can search the web to provide current information, recent news, and up-to-date facts. 
        Always cite your sources and provide links when referencing web content.""",
        tools=bing.definitions
    )
    print(f"✅ Created new Bing agent with ID: {agent.id}")
    
    return agent

def cleanup_agent(project_client, agent_id):
    """Delete the agent to clean up resources"""
    try:
        project_client.agents.delete_agent(agent_id)
        print(f"🗑️  Deleted agent {agent_id}")
    except Exception as e:
        print(f"⚠️  Error deleting agent: {e}")

def main():
    # Set up the project endpoint
    project_endpoint = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    
    # Model deployment name - adjust as needed
    model_deployment_name = "gpt-4.1"
    
    # Bing connection ID (created in Azure AI Foundry portal)
    bing_connection_id = "/subscriptions/d1d3dadc-bc2a-4495-b8dd-70443d1c70d1/resourceGroups/rg-course/providers/Microsoft.CognitiveServices/accounts/fndry-course/projects/proj-course1/connections/bingcourse"
    
    print("🚀 Starting Azure AI Foundry Agent with Bing Search...")
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            print(f"✅ Using Bing connection: {bing_connection_id}")
            
            # Create a new agent with Bing search capabilities
            agent = create_bing_agent(project_client, model_deployment_name, bing_connection_id)
            
            # Create a thread for conversation
            thread = project_client.agents.threads.create()
            print(f"✅ Created thread with ID: {thread.id}")
            
            # Add a message to the thread - asking for current information
            user_message = "What are the latest developments in artificial intelligence this week? Please search for recent news."
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            print(f"📝 User message: {user_message}")
            
            # Create and process an agent run
            print("🤖 Processing agent response with Bing search...")
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
                
                # Display citations if available (Bing search results)
                if hasattr(msg, 'url_citation_annotations') and msg.url_citation_annotations:
                    print("\n📚 Sources:")
                    for annotation in msg.url_citation_annotations:
                        print(f"   • [{annotation.url_citation.title}]({annotation.url_citation.url})")
            
            print("\n" + "="*50)
            print("🔍 Bing search integration enabled")
            print("🔄 Agent will be deleted after this run (no persistence)")
            
            # Clean up - delete the agent since we don't persist it
            cleanup_agent(project_client, agent.id)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you:")
        print("   1. Are logged in with 'az login'")
        print("   2. Have the correct model deployment name")
        print("   3. Have proper permissions on the Azure AI project")
        print("   4. Have created a Bing connection in Azure AI Foundry portal")

if __name__ == "__main__":
    main()