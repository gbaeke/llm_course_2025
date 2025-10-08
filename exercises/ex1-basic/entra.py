import os
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv("../../.env")

azure_resource = os.getenv("OPENAI_RESOURCE")

# check if we have the values
if not azure_resource:
    print ("Please set the environment variables in the .env file")
    exit(1)

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)


client = OpenAI(
    api_key=token_provider,
    base_url=f"https://{azure_resource}.openai.azure.com/openai/v1/",
)

res1 = client.responses.create(   
  model="gpt-5-mini", # Replace with your model deployment name 
  input="What is the capital of France?",
  reasoning={"effort": "low"},
  text={"verbosity": "low"}
)

print(res1.output_text)

res2 = client.responses.create(   
  model="gpt-5-mini", # Replace with your model deployment name 
  input="How many inhabitants in the city proper?",
  previous_response_id=res1.id,
  reasoning={"effort": "low"},
  text={"verbosity": "low"}
)

print(res2.output_text)
