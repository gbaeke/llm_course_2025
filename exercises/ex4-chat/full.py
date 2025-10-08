import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

# Enable basic logging for OpenAI HTTP requests
logging.basicConfig(level=logging.ERROR)

load_dotenv("../../.env")

api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_resource = os.getenv("OPENAI_RESOURCE")

# check if we have the values
if not api_key or not azure_resource:
    print ("Please set the environment variables in the .env file")
    exit(1)

client = OpenAI(
    api_key=api_key,
    base_url=f"https://{azure_resource}.openai.azure.com/openai/v1/",
    max_retries=3,
)

# Chat application
print("Minimal Chat Application (type '/exit' to quit)")
print("-" * 50)

messages = []

while True:
    user = input("You: ")
    if user.strip() == "/exit":
        break
    
    if user.strip() == "/messages":
        print("\n--- Messages History ---")
        for i, msg in enumerate(messages, 1):
            role = msg["role"].capitalize()
            content = msg["content"]
            print(f"{i}. {role}: {content}")
        print("--- End History ---\n")
        continue

    # Add user message to history
    messages.append({"role": "user", "content": user})

    # Debug: print what we're sending
    print(f"DEBUG: Sending messages: {messages}")

    resp = client.responses.create(
        model="gpt-5-mini",
        instructions="You are a helpful assistant. You only use the mslearn tool when asked a technical question about Microsoft products or services.",
        tools=[{
            "type": "mcp",
            "server_label": "mslearn",
            "server_url": "https://learn.microsoft.com/api/mcp",
            "require_approval": "never"
        }],
        input=messages
    )

    # The generated response text is in resp.output_text
    print("AI:", resp.output_text)

    # Add AI response to history
    messages.append({"role": "assistant", "content": resp.output_text})

