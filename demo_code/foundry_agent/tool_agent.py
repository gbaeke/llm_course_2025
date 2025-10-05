#!/usr/bin/env python3
"""
Azure AI Foundry Agent with Custom Tool Functions (No Persistence)
Creates a new agent with custom weather function tool for each run
"""

import os
import random
import json
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool

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

def main():
    # Set up the project endpoint
    project_endpoint = "https://fndry-course.services.ai.azure.com/api/projects/proj-course1"
    
    # Model deployment name
    model_deployment_name = "gpt-4.1"
    
    print("🚀 Starting Azure AI Foundry Agent with Custom Weather Tool...")
    
    try:
        # Create the AI Project Client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        with project_client:
            # Define user functions for the agent
            user_functions = {get_weather}
            
            # Initialize the FunctionTool with user-defined functions
            functions = FunctionTool(functions=user_functions)
            
            # Create a new agent with the custom weather tool (no persistence)
            agent = project_client.agents.create_agent(
                model=model_deployment_name,
                name="weather-tool-agent",
                instructions="""You are a fun and entertaining weather assistant with access to a special weather function! 
                
When users ask about weather, use the get_weather function to provide them with delightfully silly and random weather information. 
Present the information in an engaging and humorous way. Feel free to play along with the absurd weather conditions and give creative commentary!
                
Remember: The weather data is completely made up and meant to be entertaining, so have fun with it!""",
                tools=functions.definitions,
            )
            print(f"✅ Created agent with ID: {agent.id}")
            
            # Create a thread for conversation
            thread = project_client.agents.threads.create()
            print(f"✅ Created thread with ID: {thread.id}")
            
            # Interactive conversation loop
            print("\n" + "="*60)
            print("🌦️  SILLY WEATHER ASSISTANT IS READY!")
            print("="*60)
            print("💬 Ask me about the weather in any location!")
            print("💡 Try: 'What's the weather like in Tokyo?' or 'How's the weather in Mars?'")
            print("🚪 Type 'exit' or 'quit' to end the conversation")
            print("="*60)
            
            while True:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Thanks for using the Silly Weather Assistant! Stay silly! 🎭")
                    break
                
                if not user_input:
                    print("💭 Please ask me something about the weather!")
                    continue
                
                # Add user message to thread
                message = project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_input
                )
                
                # Create and process run
                print("🤖 Weather Assistant is thinking...")
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
                                # Parse the arguments
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
                        
                        # Submit tool outputs
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
                            print(f"\n🤖 Weather Assistant: {content}")
                        break
            
            # Clean up - delete the agent (no persistence)
            project_client.agents.delete_agent(agent.id)
            print(f"\n🧹 Cleaned up - deleted agent {agent.id}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you:")
        print("   1. Are logged in with 'az login'")
        print("   2. Have the correct model deployment name")
        print("   3. Have proper permissions on the Azure AI project")

if __name__ == "__main__":
    main()