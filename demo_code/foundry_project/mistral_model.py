from dotenv import load_dotenv
load_dotenv("../../.env")


def sample_chat_completions_with_defaults():
    import os

    try:
        endpoint = "https://fndry-course.services.ai.azure.com/models"
        key = os.environ["FOUNDRY_API_KEY"]
    except KeyError:
        print("Missing environment variable FOUNDRY_API_KEY")
        exit()

    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    # Create a client with default chat completions settings
    client = ChatCompletionsClient(
        endpoint=endpoint, credential=AzureKeyCredential(key), temperature=0.5, max_tokens=1000, api_version="2024-05-01-preview"
    )

    # Call the service with the defaults specified above
    response = client.complete(
        stream=True,
        model="mistral-medium-2505",  # Replace with your model deployment name
        messages=[
            SystemMessage("You are a helpful assistant."),
            UserMessage("Tell me a short story about space exploration."),
        ],
    )

    for update in response:
        if update.choices:
            print(update.choices[0].delta.content or "", end="")

    client.close()

if __name__ == "__main__":
    sample_chat_completions_with_defaults()