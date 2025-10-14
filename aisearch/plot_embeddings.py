"""
Generate embeddings for a small list of texts using the Azure OpenAI embedding
deployment specified in .env, reduce to 2D with PCA, and save a scatter plot.

Expected .env variables in this folder (aisearch/.env):
 - AZURE_OPENAI_ENDPOINT
 - AZURE_OPENAI_API_KEY
 - AZURE_OPENAI_EMBEDDING_DEPLOYMENT   # e.g., text-embedding-3-large
 - (optional) AZURE_OPENAI_API_VERSION  # defaults to 2024-12-01-preview

The plot is saved as 'embeddings_plot.png' in this folder.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from openai import AzureOpenAI
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def build_texts() -> List[str]:
    """Return 10 texts with two very similar entries."""
    similar_a = "The quick brown fox jumps over the lazy dog."
    # Very similar to similar_a (minor wording changes)
    similar_b = "A quick brown fox jumps over a lazy dog."
    others = [
        "Azure AI Search enables powerful hybrid search experiences.",
        "Vector databases store high-dimensional numerical representations.",
        "Principal Component Analysis reduces dimensionality for visualization.",
        "Matplotlib is great for creating static plots in Python.",
        "LangChain can orchestrate prompts and tools for LLM apps.",
        "Reranking improves the relevance of retrieved search results.",
        "HNSW is a popular approximate nearest neighbor algorithm.",
        "Embeddings capture semantic meaning of text inputs.",
    ]
    return [similar_a, similar_b, *others]


def embed_texts(client: AzureOpenAI, deployment: str, texts: List[str]) -> List[List[float]]:
    """Create embeddings for all texts using the given Azure OpenAI deployment."""
    vectors: List[List[float]] = []
    for t in texts:
        resp = client.embeddings.create(model=deployment, input=t)
        vectors.append(resp.data[0].embedding)
    return vectors


def reduce_to_2d(vectors: List[List[float]]) -> np.ndarray:
    arr = np.array(vectors, dtype=np.float32)
    pca = PCA(n_components=2, random_state=42)
    reduced = pca.fit_transform(arr)
    return reduced

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    
    return float(np.dot(va, vb))


def plot_points(points_2d: np.ndarray, labels: List[str], output_path: Path) -> None:
    plt.figure(figsize=(7, 6), dpi=120)

    # Highlight the first two points (the similar pair) in a different color
    x, y = points_2d[:, 0], points_2d[:, 1]
    plt.scatter(x[0:2], y[0:2], c=["tab:red", "tab:red"], label="Similar pair", s=60, edgecolors="black")
    plt.scatter(x[2:], y[2:], c="tab:blue", label="Others", s=50, alpha=0.8, edgecolors="black")

    # Annotate points with short labels
    for i, (px, py) in enumerate(points_2d):
        short = labels[i]
        if len(short) > 32:
            short = short[:29] + "..."
        # Nudge text a little to improve readability
        plt.text(px + 0.01, py + 0.01, f"{i}: {short}", fontsize=8)

    plt.title("Embeddings (PCA to 2D)")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.legend(loc="best")
    plt.grid(True, linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def main() -> None:
    # Load .env next to this script
    load_dotenv(Path(__file__).with_name(".env"))

    endpoint = get_env("AZURE_OPENAI_ENDPOINT")
    api_key = get_env("AZURE_OPENAI_API_KEY")
    deployment = get_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version=api_version)

    texts = build_texts()
    vectors = embed_texts(client, deployment, texts)

    # Cosine similarity between the two close texts (indexes 0 and 1)
    sim_close = cosine_similarity(vectors[0], vectors[1])

    # Cosine similarity between two not-so-close texts (pick two different topics)
    # Here we choose indexes 2 and 5 for contrast
    sim_far = cosine_similarity(vectors[2], vectors[5])

    print("Cosine similarities:")
    print(f"  [0] vs [1] (similar pair): {sim_close:.4f}")
    print(f"  [2] vs [5] (dissimilar pair): {sim_far:.4f}")
    points_2d = reduce_to_2d(vectors)

    out = Path(__file__).with_name("embeddings_plot.png")
    plot_points(points_2d, texts, out)
    print(f"Saved plot to: {out}")


if __name__ == "__main__":
    main()
