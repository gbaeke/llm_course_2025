#!/usr/bin/env python3
"""
Tool + Bing Agent - Azure AI Foundry Agent with Custom Tools AND Bing Search
Combines custom weather function tool with Bing grounding search capabilities
Does not persist the agent ID - creates a new agent each time
"""

import os
import random
import json
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool, BingGroundingTool

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

def create_combined_agent(project_client, model_deployment_name, bing_connection_id):
    """Create a new agent with both custom weather tool and Bing grounding search tool"""
    
    # Define user functions for the agent
    user_functions = {get_weather}
    
    # Initialize the FunctionTool with user-defined functions
    weather_tool = FunctionTool(functions=user_functions)
    
    # Initialize the Bing Grounding tool
    bing_tool = BingGroundingTool(connection_id=bing_connection_id)
    
    # Combine both tool definitions
    combined_tools = weather_tool.definitions + bing_tool.definitions
    
    # Create a new agent with both tools
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="weather-bing-agent",
        instructions="""You are a versatile assistant with two powerful capabilities:

1. **Silly Weather Function**: You have access to a fun get_weather function that provides entertainingly absurd weather information for any location. Use this when users ask about weather and want something fun and silly!

2. **Real-time Web Search**: You also have access to Bing Search to find current, real-world information, news, and facts from the web. Use this for serious inquiries that require up-to-date information.

Guidelines:
- For weather requests, offer both options: "Would you like silly weather (fun) or real weather information (via web search)?"
- For current events, news, or factual information, use Bing search
- Always cite your sources when using web search results
- Have fun with the silly weather data but be clear it's made-up entertainment
- Be helpful and engaging in all interactions!""",
        tools=combined_tools
    )
    print(f"✅ Created combined agent with ID: {agent.id}")
    print(f"🛠️  Agent has {len(combined_tools)} tools: Custom Weather + Bing Search")
    
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
    
    # Model deployment name
    model_deployment_name = "gpt-4.1"
    
    # Bing connection ID (from your existing bing_agent.py)
    bing_connection_id = "/subscriptions/d1d3dadc-bc2a-4495-b8dd-70443d1c70d1/resourceGroups/rg-course/providers/Microsoft.CognitiveServices/accounts/fndry-course/projects/proj-course1/connections/bingcourse"
    
    print("🚀 Starting Azure AI Foundry Agent with Custom Weather Tool + Bing Search...")
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            print(f"✅ Using Bing connection: {bing_connection_id}")
            
            # Create a new agent with both custom weather tool and Bing search
            agent = create_combined_agent(project_client, model_deployment_name, bing_connection_id)
            
            # Create a thread for conversation
            thread = project_client.agents.threads.create()
            print(f"✅ Created thread with ID: {thread.id}")
            
            # Interactive conversation loop
            print("\n" + "="*70)
            print("🌦️🔍 WEATHER + WEB SEARCH ASSISTANT IS READY!")
            print("="*70)
            print("💭 I can help you with:")
            print("   🎭 Silly weather information (completely made up and fun!)")
            print("   🌐 Real-time web search for current information and news")
            print("💡 Try:")
            print("   • 'What's the weather like in Tokyo?' (I'll offer both options)")
            print("   • 'What's the latest news about AI?'")
            print("   • 'Search for information about quantum computing'")
            print("🚪 Type 'exit' or 'quit' to end the conversation")
            print("="*70)
            
            while True:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Thanks for using the Weather + Web Search Assistant! Stay curious! 🎭🔍")
                    break
                
                if not user_input:
                    print("💭 Please ask me something! Try weather or web search questions.")
                    continue
                
                # Add user message to thread
                message = project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_input
                )
                
                # Create and process run
                print("🤖 Assistant is thinking and searching...")
                run = project_client.agents.runs.create(
                    thread_id=thread.id,
                    agent_id=agent.id
                )
                
                # Process the run and handle function calls
                while run.status in ["queued", "in_progress", "requires_action"]:
                    run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                    
                    if run.status == "requires_action":
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        tool_outputs = []
                        
                        for tool_call in tool_calls:
                            if tool_call.function.name == "get_weather":
                                # Parse the arguments for weather function
                                import json
                                args = json.loads(tool_call.function.arguments)
                                location = args.get("location", "Unknown Location")
                                
                                # Call our custom weather function
                                output = get_weather(location)
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id, 
                                    "output": output
                                })
                                print(f"🌦️  Generated silly weather data for: {location}")
                        
                        # Submit tool outputs if any custom functions were called
                        if tool_outputs:
                            run = project_client.agents.runs.submit_tool_outputs(
                                thread_id=thread.id, 
                                run_id=run.id, 
                                tool_outputs=tool_outputs
                            )
                
                if run.status == "failed":
                    print(f"❌ Run failed: {run.last_error}")
                    continue
                
                # Get the latest messages
                messages = project_client.agents.messages.list(thread_id=thread.id)
                messages_list = list(messages)
                
                # Find and display the assistant's response
                for msg in messages_list:
                    if msg.role == "assistant":
                        content = ""
                        for content_item in msg.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text.value
                        
                        if content:  # Only print if we have content
                            print(f"\n🤖 Assistant: {content}")
                            
                            # Display citations if available (Bing search results)
                            if hasattr(msg, 'url_citation_annotations') and msg.url_citation_annotations:
                                print("\n📚 Sources:")
                                for annotation in msg.url_citation_annotations:
                                    print(f"   • [{annotation.url_citation.title}]({annotation.url_citation.url})")
                        break
            
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