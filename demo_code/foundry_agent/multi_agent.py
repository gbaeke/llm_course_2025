#!/usr/bin/env python3
"""
Multi-Agent System - Azure AI Foundry Connected Agents
Creates specialized agents that work together:
1. Web Search Agent - Uses Bing tool for real-time web search
2. Weather Agent - Uses silly weather function tool
3. Conversation Agent - Orchestrates and delegates to the other agents
"""

import os
import random
import json
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool, BingGroundingTool, ConnectedAgentTool, MessageRole

def get_weather(location: str) -> str:
    """
    Get silly and random weather information for the specified location.
    
    :param location: The location to get weather for (e.g., "New York", "Paris")
    :return: Weather information as a JSON string with silly and random data
    """
    # Silly weather conditions
    conditions = [
        "Raining rubber ducks", "Sunny with a chance of unicorns", "Cloudy with marshmallow precipitation",
        "Foggy with occasional rainbow bursts", "Windy with flying tacos", "Snowing glitter",
        "Thunderstorms of confetti", "Drizzling chocolate syrup", "Hailing jellybeans",
        "Tornado of pizza slices", "Blizzard of cotton candy", "Hurricane of happy thoughts"
    ]
    
    # Random temperature (silly ranges)
    temp_celsius = random.randint(-50, 150)
    temp_fahrenheit = random.randint(-58, 302)
    
    # Random humidity
    humidity = random.randint(0, 200)  # Over 100% because why not!
    
    # Random wind speed with silly units
    wind_speed = random.randint(1, 999)
    wind_units = random.choice(["mph", "km/h", "snails/hour", "turtle speed", "rocket boosters"])
    
    # Random condition
    condition = random.choice(conditions)
    
    # Fun weather advice
    advice_list = [
        "Perfect weather for indoor activities!", "Don't forget your imagination umbrella!",
        "Great day to practice your superhero landing!", "Ideal conditions for a dance party!",
        "Remember to feed the weather spirits!", "Time to wear your lucky socks!"
    ]
    advice = random.choice(advice_list)
    
    weather_data = {
        "location": location,
        "condition": condition,
        "temperature": {
            "celsius": f"{temp_celsius}°C",
            "fahrenheit": f"{temp_fahrenheit}°F"
        },
        "humidity": f"{humidity}%",
        "wind": f"{wind_speed} {wind_units}",
        "advice": advice,
        "reliability": "100% guaranteed to be completely made up! 🎭"
    }
    
    return json.dumps(weather_data, indent=2)

def create_web_search_agent(project_client, model_deployment_name, bing_connection_id):
    """Create a specialized agent for web searches using Bing tool"""
    
    # Initialize the Bing Grounding tool
    bing_tool = BingGroundingTool(connection_id=bing_connection_id)
    
    # Create the web search agent
    web_search_agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="web-search-specialist",
        instructions="""You are a specialized web search assistant. Your primary function is to search the web for current, accurate information using Bing search capabilities.

Key responsibilities:
- Perform comprehensive web searches for current events, news, facts, and information
- Provide accurate, up-to-date information from reliable sources
- Always cite your sources with proper links
- Focus on providing factual, well-researched answers
- If information is not found or unclear, state this clearly

You should ONLY use web search capabilities - do not attempt to provide information from your training data if recent or current information is requested.""",
        tools=bing_tool.definitions
    )
    print(f"✅ Created Web Search Agent with ID: {web_search_agent.id}")
    return web_search_agent

def create_weather_agent(project_client, model_deployment_name):
    """Create a specialized agent for silly weather information"""
    
    # Define user functions for the agent
    user_functions = {get_weather}
    
    # Initialize the FunctionTool with user-defined functions
    weather_tool = FunctionTool(functions=user_functions)
    
    # Create the weather agent
    weather_agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="weather-specialist",
        instructions="""You are a fun and entertaining weather specialist! Your job is to provide silly, made-up weather information that will make people laugh.

Key responsibilities:
- Use the get_weather function to provide entertaining, fictional weather reports
- Always be upfront that the weather information is completely made up and for entertainment only
- Make the weather reports fun, creative, and amusing
- Encourage users to check real weather services for actual weather information
- Be enthusiastic and playful in your responses

Remember: Your weather data is 100% fictional and designed purely for entertainment purposes!""",
        tools=weather_tool.definitions
    )
    print(f"✅ Created Weather Agent with ID: {weather_agent.id}")
    return weather_agent

def create_conversation_agent(project_client, model_deployment_name, web_search_agent, weather_agent):
    """Create the main conversation agent that can delegate to specialized agents"""
    
    # Create connected agent tools for delegation
    web_search_connected = ConnectedAgentTool(
        id=web_search_agent.id,
        name="web_search_specialist",
        description="Use this agent to search the web for current information, news, facts, or any real-time data. Perfect for questions about current events, recent developments, or factual information that requires web search."
    )
    
    weather_connected = ConnectedAgentTool(
        id=weather_agent.id,
        name="weather_specialist", 
        description="Use this agent to get fun, silly, completely made-up weather information for entertainment purposes. Use this when users ask about weather and want something humorous rather than real weather data."
    )
    
    # Combine the connected agent tools
    connected_tools = web_search_connected.definitions + weather_connected.definitions
    
    # Create the main conversation agent
    conversation_agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="conversation-orchestrator",
        instructions="""You are a helpful conversation orchestrator with access to specialized agents for different types of tasks.

You have access to two specialized agents:
1. **Web Search Specialist**: For real-time web searches, current events, news, and factual information
2. **Weather Specialist**: For fun, silly, made-up weather information (entertainment only)

Guidelines for delegation:
- For questions about current events, news, recent information, or facts that might change over time → use the web_search_specialist
- For weather questions where the user wants entertainment/humor → use the weather_specialist  
- For weather questions where the user wants real information → use the web_search_specialist and search for "weather in [location]"
- For general conversation, advice, or questions you can answer directly → respond yourself without delegation

Always be clear about what type of information you're providing (real vs entertainment) and cite sources when using web search results.

If a user asks about weather, offer both options: "Would you like real weather information (via web search) or silly weather entertainment?"

Be friendly, helpful, and ensure users get the most appropriate response for their needs!""",
        tools=connected_tools
    )
    print(f"✅ Created Conversation Orchestrator Agent with ID: {conversation_agent.id}")
    return conversation_agent

def cleanup_agents(project_client, *agents):
    """Delete all agents to clean up resources"""
    for agent in agents:
        try:
            project_client.agents.delete_agent(agent.id)
            print(f"🗑️  Deleted agent {agent.id}")
        except Exception as e:
            print(f"⚠️  Error deleting agent {agent.id}: {e}")

def main():
    # Set up the project endpoint
    project_endpoint = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    
    # Model deployment name
    model_deployment_name = "gpt-4.1"
    
    # Bing connection ID
    bing_connection_id = "/subscriptions/d1d3dadc-bc2a-4495-b8dd-70443d1c70d1/resourceGroups/rg-course/providers/Microsoft.CognitiveServices/accounts/fndry-course/projects/proj-course1/connections/bingcourse"
    
    print("🚀 Starting Multi-Agent System - Azure AI Foundry Connected Agents...")
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            print(f"✅ Connected to Azure AI Foundry project")
            
            # Create specialized agents
            print("\n🔧 Creating specialized agents...")
            web_search_agent = create_web_search_agent(project_client, model_deployment_name, bing_connection_id)
            weather_agent = create_weather_agent(project_client, model_deployment_name)
            
            # Create the main conversation agent that uses the specialized agents
            print("\n🔧 Creating conversation orchestrator...")
            conversation_agent = create_conversation_agent(project_client, model_deployment_name, web_search_agent, weather_agent)
            
            # Create a thread for conversation
            thread = project_client.agents.threads.create()
            print(f"✅ Created conversation thread with ID: {thread.id}")
            
            # Interactive conversation loop
            print("\n" + "="*80)
            print("🎭🔍🌦️  MULTI-AGENT CONVERSATION SYSTEM IS READY!")
            print("="*80)
            print("💭 I'm your conversation orchestrator with access to specialized agents:")
            print("   🔍 Web Search Specialist - For real-time information and current events")
            print("   🎭 Weather Specialist - For fun, silly weather entertainment")
            print("💡 Try:")
            print("   • 'What's the latest news about AI technology?'")
            print("   • 'Tell me some silly weather for Tokyo'")
            print("   • 'What's the real weather like in Paris?' (I'll search for you)")
            print("   • 'What happened in the world today?'")
            print("🚪 Type 'exit' or 'quit' to end the conversation")
            print("="*80)
            
            while True:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Thanks for using the Multi-Agent System! The agents enjoyed working together! 🤖🤖🤖")
                    break
                
                if not user_input:
                    print("💭 Please ask me something! I can search the web or entertain you with silly weather.")
                    continue
                
                # Add user message to thread
                message = project_client.agents.messages.create(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=user_input
                )
                
                # Create and process run
                print("🤖 Orchestrator is thinking and delegating to specialist agents...")
                run = project_client.agents.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=conversation_agent.id
                )
                
                if run.status == "failed":
                    print(f"❌ Run failed: {run.last_error}")
                    continue
                
                # Get the latest messages
                messages = project_client.agents.messages.list(thread_id=thread.id)
                
                # Find and display the assistant's response
                response_displayed = False
                for msg in list(messages):
                    if msg.role == MessageRole.AGENT and hasattr(msg, 'run_id') and msg.run_id == run.id:
                        # Display text content
                        for content_item in msg.content:
                            if hasattr(content_item, 'text'):
                                content_text = content_item.text.value
                                if content_text:
                                    print(f"\n🤖 Orchestrator: {content_text}")
                                    response_displayed = True
                        
                        # Display citations if available (from web search)
                        if hasattr(msg, 'url_citation_annotations') and msg.url_citation_annotations:
                            print("\n📚 Sources:")
                            for annotation in msg.url_citation_annotations:
                                print(f"   • [{annotation.url_citation.title}]({annotation.url_citation.url})")
                        
                        break
                
                if not response_displayed:
                    print("🤖 Orchestrator: I processed your request, but there might be an issue with the response. Please try again.")
            
            # Clean up - delete all agents
            print("\n🧹 Cleaning up agents...")
            cleanup_agents(project_client, conversation_agent, web_search_agent, weather_agent)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you:")
        print("   1. Are logged in with 'az login'")
        print("   2. Have the correct model deployment name")
        print("   3. Have proper permissions on the Azure AI project")
        print("   4. Have created a Bing connection in Azure AI Foundry portal")

if __name__ == "__main__":
    main()