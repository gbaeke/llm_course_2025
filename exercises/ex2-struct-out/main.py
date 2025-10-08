import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

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

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str

response = client.responses.parse(
    model="gpt-5-mini", # Replace with your model deployment name
    input=[
        {
            "role": "system",
            "content": "You are a helpful math tutor. Guide the user through the solution step by step.",
        },
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    text_format=MathReasoning,
)

math_reasoning = response.output_parsed

print("Steps to solve the equation:")
for step in math_reasoning.steps:
    print(f"- {step.explanation}: {step.output}")
print(f"Final answer: {math_reasoning.final_answer}")

