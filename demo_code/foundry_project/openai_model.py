import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("../../.env")

api_key = os.getenv("FOUNDRY_API_KEY") # API key in project overview; same for all projects
foundry_resource = os.getenv("FOUNDRY_RESOURCE")

# check if we have the values
if not api_key or not foundry_resource:
    print ("Please set the environment variables in the .env file")
    exit(1) 


client = OpenAI(
    api_key=api_key,
    base_url=f"https://{foundry_resource}.openai.azure.com/openai/v1/",
    max_retries=3,
)

res1 = client.responses.create(   
  model="gpt-5-mini", # Replace with your model deployment name 
  input="What is the capital of France?",
  reasoning={"effort": "low"},
  text={"verbosity": "low"},
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
