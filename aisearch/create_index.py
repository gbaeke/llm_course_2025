"""
Create or update an Azure AI Search index with integrated vectorization.

Requirements (from .env):
- AZURE_SEARCH_ENDPOINT
- AZURE_SEARCH_ADMIN_KEY
- AZURE_SEARCH_INDEX_NAME
- AZURE_OPENAI_ENDPOINT            # e.g. https://<your-aoai>.openai.azure.com
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT # e.g. text-embedding-3-large (3072 dims)

Index schema:
- id: unique key (string)
- title: text (searchable)
- url: text (filterable)
- chunk: text (searchable)
- vector: vector field (3072 dims) with integrated vectorizer profile

This script uses the Azure SDK for Python as shown in Microsoft docs.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SemanticSearch,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
)
from openai import AzureOpenAI


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def build_index(index_name: str, aoai_endpoint: str, aoai_api_key: str, aoai_embedding_deployment: str) -> SearchIndex:
    """
    Build a SearchIndex with HNSW vector search and an Azure OpenAI vectorizer profile.
    """

    # Names for resources inside the index
    algo_name = "hnsw-default"
    vectorizer_name = "aoai-vectorizer"
    vector_profile_name = "vector-profile"

    # Vector search configuration: HNSW algorithm + profile referencing the vectorizer
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name=algo_name)
        ],
        profiles=[
            VectorSearchProfile(
                name=vector_profile_name,
                algorithm_configuration_name=algo_name,
                vectorizer_name=vectorizer_name,
            )
        ],
        vectorizers=[
            # Integrated vectorizer (query-time vectorization)
            AzureOpenAIVectorizer(
                vectorizer_name=vectorizer_name,
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=aoai_endpoint,
                    deployment_name=aoai_embedding_deployment,
                    api_key=aoai_api_key,
                    model_name="text-embedding-3-large",
                ),
            )
        ],
    )

    # Semantic configuration (for semantic ranker)
    semantic_config_name = "default-semantic"
    semantic_config = SemanticConfiguration(
        name=semantic_config_name,
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="chunk")],
        ),
    )
    semantic_search = SemanticSearch(
        default_configuration_name=semantic_config_name,
        configurations=[semantic_config],
    )

    # Fields
    fields = [
        # Key field
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),

        # Text fields
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="url", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="chunk", type=SearchFieldDataType.String),

        # Vector field (3072 dims)
        SearchField(
            name="vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            stored=True,
            vector_search_dimensions=3072,
            vector_search_profile_name=vector_profile_name,
        ),
    ]

    return SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def embed_text(
    text: str,
    aoai_endpoint: str,
    aoai_api_key: str,
    aoai_embedding_deployment: str,
    aoai_api_version: str,
) -> List[float]:
    """Create an embedding using the same Azure OpenAI deployment set in .env."""
    client = AzureOpenAI(
        api_key=aoai_api_key,
        azure_endpoint=aoai_endpoint,
        api_version=aoai_api_version,
    )
    resp = client.embeddings.create(model=aoai_embedding_deployment, input=text)
    return resp.data[0].embedding


def main() -> None:
    # Load .env from this file's directory to avoid picking up the root .env
    load_dotenv(Path(__file__).with_name(".env"))

    endpoint = get_env("AZURE_SEARCH_ENDPOINT")
    admin_key = get_env("AZURE_SEARCH_ADMIN_KEY")
    index_name = get_env("AZURE_SEARCH_INDEX_NAME")

    aoai_endpoint = get_env("AZURE_OPENAI_ENDPOINT")
    aoai_api_key = get_env("AZURE_OPENAI_API_KEY")
    aoai_embedding_deployment = get_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    # API version optional in local .env; default to a recent preview if not set
    aoai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    credential = AzureKeyCredential(admin_key)
    idx_client = SearchIndexClient(endpoint=endpoint, credential=credential)

    index = build_index(
        index_name=index_name,
        aoai_endpoint=aoai_endpoint,
        aoai_api_key=aoai_api_key,
        aoai_embedding_deployment=aoai_embedding_deployment,
    )

    # Create or update for idempotency
    idx_client.create_or_update_index(index)
    print(f"Index '{index_name}' created/updated successfully.")

    # Upload 10 dummy documents with embeddings generated from the same model
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

    docs = []
    for i in range(1, 11):
        doc_id = str(i)
        title = f"Dummy Title {i}"
        url = f"https://example.com/{i}"
        chunk = f"This is a sample chunk of content for document {i}. It demonstrates vector indexing and semantic ranking."

        vec = embed_text(
            chunk,
            aoai_endpoint=aoai_endpoint,
            aoai_api_key=aoai_api_key,
            aoai_embedding_deployment=aoai_embedding_deployment,
            aoai_api_version=aoai_api_version,
        )

        docs.append({
            "id": doc_id,
            "title": title,
            "url": url,
            "chunk": chunk,
            "vector": vec,
        })

    if docs:
        result = search_client.upload_documents(documents=docs)
        succeeded = sum(1 for r in result if r.succeeded)
        print(f"Uploaded {succeeded}/{len(docs)} dummy documents.")


if __name__ == "__main__":
    main()
