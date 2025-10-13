"""
Demonstrate keyword, vector, hybrid, and hybrid+semantic search on the same index.

This script expects a local .env in this folder (aisearch/.env), same as create_index.py:
- AZURE_SEARCH_ENDPOINT
- AZURE_SEARCH_ADMIN_KEY
- AZURE_SEARCH_INDEX_NAME
- (optional) AZURE_OPENAI_API_VERSION, defaults to 2024-12-01-preview
- For vector queries with local embeddings:
  - AZURE_OPENAI_ENDPOINT
  - AZURE_OPENAI_API_KEY
  - AZURE_OPENAI_EMBEDDING_DEPLOYMENT (should match the index vector dimensions)
"""

import os
from pathlib import Path
from typing import List, Tuple, Any, Dict

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


# No client-side embeddings needed. The index's vectorizer will embed query text at query time.


def collect_results(results, max_items: int = 5) -> Tuple[int | None, List[Any]]:
    total = None
    try:
        total = results.get_count()
    except Exception:
        pass
    items: List[Any] = []
    for i, r in enumerate(results):
        if i >= max_items:
            break
        items.append(r)
    return total, items


def print_results(header: str, total: int | None, items: List[Any]) -> None:
    print(f"\n=== {header} ===")
    if total is not None:
        print(f"Total results: {total}")
    for r in items:
        doc = r
        score = doc.get("@search.score", "N/A")
        reranker = doc.get("@search.reranker_score", "N/A")
        print(f"- id={doc.get('id')} score={score} reranker={reranker}")
        print(f"  title={doc.get('title')}")
        print(f"  url={doc.get('url')}")
        chunk = doc.get("chunk") or ""
        if isinstance(chunk, str) and len(chunk) > 140:
            chunk = chunk[:140] + "..."
        print(f"  chunk={chunk}")


def render_html(sections: List[Dict[str, Any]], output_path: Path) -> None:
    css = """
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; }
    h1 { margin-bottom: 8px; }
    .meta { color: #666; margin-bottom: 24px; }
    section { margin-bottom: 32px; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin: 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
    .title { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
    .url { font-size: 12px; color: #2563eb; margin-bottom: 8px; word-break: break-all; }
    .scores { font-size: 12px; color: #555; margin-bottom: 8px; }
    .chunk { font-size: 14px; color: #111; }
    .count { font-size: 12px; color: #666; }
    """
    html = ["<!doctype html>", "<html>", "<head>", "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<title>Azure AI Search - Query Examples</title>", f"<style>{css}</style>", "</head>", "<body>"]
    html.append("<h1>Azure AI Search - Query Examples</h1>")
    html.append("<div class='meta'>Keyword, vector (integrated), hybrid, and hybrid + semantic results</div>")

    for sec in sections:
        name = sec.get("name")
        total = sec.get("total")
        items = sec.get("items", [])
        html.append(f"<section><h2>{name}</h2>")
        if total is not None:
            html.append(f"<div class='count'>Total results: {total}</div>")
        for doc in items:
            title = doc.get("title") or "(no title)"
            url = doc.get("url") or ""
            chunk = doc.get("chunk") or ""
            if isinstance(chunk, str) and len(chunk) > 240:
                chunk_disp = chunk[:240] + "..."
            else:
                chunk_disp = chunk
            score = doc.get("@search.score", "")
            reranker = doc.get("@search.reranker_score", "")
            html.append("<div class='card'>")
            html.append(f"<div class='title'>{title}</div>")
            if url:
                html.append(f"<div class='url'><a href='{url}' target='_blank' rel='noopener noreferrer'>{url}</a></div>")
            if score or reranker:
                html.append(f"<div class='scores'>score: {score} | reranker: {reranker}</div>")
            html.append(f"<div class='chunk'>{chunk_disp}</div>")
            html.append("</div>")
        html.append("</section>")

    html.append("</body></html>")
    output_path.write_text("\n".join(html), encoding="utf-8")


def main() -> None:
    # Load local .env
    load_dotenv(Path(__file__).with_name(".env"))

    endpoint = get_env("AZURE_SEARCH_ENDPOINT")
    admin_key = get_env("AZURE_SEARCH_ADMIN_KEY")
    index_name = get_env("AZURE_SEARCH_INDEX_NAME")

    # Integrated vectorization at query time uses the vectorizer configured in the index.

    credential = AzureKeyCredential(admin_key)
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

    # Single query string used for keyword and integrated vector queries
    query_text = "spaghetti carbonara"

    # 1) Keyword search only
    kw_results = search_client.search(
        search_text=query_text,
        select=["id", "title", "url", "chunk"],
        include_total_count=True,
        top=5,
    )
    kw_total, kw_items = collect_results(kw_results)
    print_results("Keyword search", kw_total, kw_items)

    # 2) Vector search only (integrated vectorization)
    vq_text = VectorizableTextQuery(text=query_text, k_nearest_neighbors=5, fields="vector")
    vec_results = search_client.search(
        vector_queries=[vq_text],
        select=["id", "title", "url", "chunk"],
        include_total_count=True,
        top=5,
    )
    vec_total, vec_items = collect_results(vec_results)
    print_results("Vector search (integrated)", vec_total, vec_items)

    # 3) Hybrid search (keyword + vector)
    vq_text = VectorizableTextQuery(text=query_text, k_nearest_neighbors=5, fields="vector")
    hybrid_results = search_client.search(
        search_text=query_text,
        vector_queries=[vq_text],
        select=["id", "title", "url", "chunk"],
        include_total_count=True,
        top=5,
    )
    hyb_total, hyb_items = collect_results(hybrid_results)
    print_results("Hybrid search (integrated)", hyb_total, hyb_items)

    # 4) Hybrid + semantic
    vq_text = VectorizableTextQuery(text=query_text, k_nearest_neighbors=5, fields="vector")
    # We set a default semantic configuration in the index; no need to pass name
    hybrid_sem_results = search_client.search(
        search_text=query_text,
        vector_queries=[vq_text],
        query_type="semantic",
        select=["id", "title", "url", "chunk"],
        include_total_count=True,
        top=5,
    )
    hybsem_total, hybsem_items = collect_results(hybrid_sem_results)
    print_results("Hybrid + semantic search (integrated)", hybsem_total, hybsem_items)

    # 5) Hybrid + semantic with reranker cutoff (only results with reranker score > 2.1)
    vq_text = VectorizableTextQuery(text=query_text, k_nearest_neighbors=5, fields="vector")
    hybrid_sem_cut_results = search_client.search(
        search_text=query_text,
        vector_queries=[vq_text],
        query_type="semantic",
        select=["id", "title", "url", "chunk"],
        include_total_count=True,
        top=5,
    )
    cut_total, cut_items_raw = collect_results(hybrid_sem_cut_results)
    # Client-side filter on reranker score > 2.1
    cut_items = []
    for doc in cut_items_raw:
        try:
            rr = float(doc.get("@search.reranker_score", 0))
        except Exception:
            rr = 0.0
        if rr > 2.1:
            cut_items.append(doc)
    # For display, show count after cutoff
    cut_display_total = len(cut_items)
    print_results("Hybrid + semantic (reranker > 2.1)", cut_display_total, cut_items)

    # Write HTML summary
    sections = [
        {"name": "Keyword search", "total": kw_total, "items": kw_items},
        {"name": "Vector search (integrated)", "total": vec_total, "items": vec_items},
        {"name": "Hybrid search (integrated)", "total": hyb_total, "items": hyb_items},
        {"name": "Hybrid + semantic search (integrated)", "total": hybsem_total, "items": hybsem_items},
        {"name": "Hybrid + semantic (reranker > 2.1)", "total": cut_display_total, "items": cut_items},
    ]
    out_path = Path(__file__).with_name("query_results.html")
    render_html(sections, out_path)
    print(f"\nWrote HTML results to: {out_path}")


if __name__ == "__main__":
    main()
