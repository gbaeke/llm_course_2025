import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

# Enable basic logging for OpenAI HTTP requests
logging.basicConfig(level=logging.INFO)

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

response = client.responses.create(
    model="gpt-5-mini",
    tools=[{
        "type": "mcp",
        "server_label": "mslearn",
        "server_url": "https://learn.microsoft.com/api/mcp",
        "require_approval": "never"

    }],
    input="Does Azure OpenAI support the responses API with web search. If not, what else can I use in Azure."
)

print("=== RESPONSE OUTPUT TEXT ===")
print(response.output_text)

print("\n=== TOOL USAGE INFORMATION ===")
print(f"Response status: {response.status}")
print(f"Model used: {response.model}")

# Check if tools were used by examining the output array
if hasattr(response, 'output') and response.output:
    print(f"Number of output items: {len(response.output)}")
    for i, item in enumerate(response.output):
        print(f"Output item {i+1}: {type(item).__name__}")
        if hasattr(item, 'type'):
            print(f"  Type: {item.type}")
        if hasattr(item, 'server_label'):
            print(f"  Server: {item.server_label}")
        if hasattr(item, 'name'):
            print(f"  Tool name: {item.name}")

# Check usage statistics
if hasattr(response, 'usage'):
    print(f"\nToken usage:")
    print(f"  Input tokens: {response.usage.input_tokens}")
    print(f"  Output tokens: {response.usage.output_tokens}")
    print(f"  Total tokens: {response.usage.total_tokens}")
    if hasattr(response.usage.output_tokens_details, 'reasoning_tokens'):
        print(f"  Reasoning tokens: {response.usage.output_tokens_details.reasoning_tokens}")

