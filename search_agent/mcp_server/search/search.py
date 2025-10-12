#!/usr/bin/env python3
"""
Azure AI Search Client

A client class for querying Azure AI Search service to retrieve relevant content
from the search index using hybrid search with integrated vectorization.
The index uses built-in vectorization, so no external embedding function is needed.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.exceptions import HttpResponseError

# Load environment variables
load_dotenv()


class AzureAISearchClient:
    """
    Client for querying Azure AI Search service using hybrid search with integrated vectorization.
    
    This class provides hybrid search that combines keyword search with vector similarity search
    using the index's built-in vectorization capabilities. No external embedding function needed.
    """
    
    def __init__(self):
        """Initialize the Azure AI Search client with configuration from environment variables."""
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX")
        
        if not self.search_key:
            raise ValueError("AZURE_SEARCH_KEY environment variable is required")
        if not self.search_endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
        if not self.search_index:
            raise ValueError("AZURE_SEARCH_INDEX environment variable is required")
        
        # Create the search client using Azure SDK
        credential = AzureKeyCredential(self.search_key)
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index,
            credential=credential
        )
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        use_semantic_reranker: bool = False,
        reranker_threshold: float = 2.1
    ) -> List[Dict[str, Any]]:
        """
        Search the Azure AI Search index using hybrid search with integrated vectorization.
        
        This method always performs hybrid search, combining keyword search with vector similarity
        using the index's built-in vectorization capabilities. Optionally enables semantic reranker
        for improved relevance scoring.
        
        Args:
            query (str): The search query string
            max_results (int): Maximum number of results to return (default: 5)
            use_semantic_reranker (bool): Enable semantic reranker for better relevance (default: False)
            reranker_threshold (float): Minimum reranker score to include in results (default: 2.1)
            
        Returns:
            List[Dict[str, Any]]: List of search results with chunk, title, and url fields
        """
        try:
            
            # For semantic reranker, set k to 50 to maximize input to semantic ranker
            # For regular hybrid search, use the requested max_results
            vector_k = 50 if use_semantic_reranker else max_results
            
            # Create vector query using integrated vectorization
            # The index will automatically vectorize the text query using its configured vectorizer
            vector_query = VectorizableTextQuery(
                kind="text",  # Use integrated vectorization  
                text=query,   # Text to be vectorized by the index
                k_nearest_neighbors=vector_k,
                fields="text_vector"  # Vector field in your index
            )
            
            # Build search parameters based on semantic reranker usage
            search_params = {
                "search_text": query,           # Keyword search component
                "vector_queries": [vector_query], # Vector search component 
                "top": 50 if use_semantic_reranker else max_results,  # Get 50 for semantic ranker
                "select": ["chunk", "title", "url"]
            }
            
            # Add semantic reranker configuration if enabled
            if use_semantic_reranker:
                search_params.update({
                    "query_type": "semantic",
                    "semantic_configuration_name": "sops-semantic-configuration",
                    "query_caption": "extractive",  # Include semantic captions
                })
            
            # Perform hybrid search: keyword + vector
            results = self.search_client.search(**search_params)
            
            # Convert SearchItemPaged to list and format results
            raw_results = list(results)
            
            # Filter by reranker score if semantic reranker is enabled
            if use_semantic_reranker:
                filtered_results = []
                for result in raw_results:
                    reranker_score = result.get("@search.reranker_score")  # Fixed: use underscore
                    if reranker_score is not None and reranker_score >= reranker_threshold:
                        filtered_results.append(result)
                
                # Limit to requested max_results
                raw_results = filtered_results[:max_results]
            
            return self._format_results(raw_results)
            
        except HttpResponseError as e:
            print(f"Azure AI Search HTTP error: {e}")
            return []
        except Exception as e:
            print(f"Error performing hybrid search: {str(e)}")
            return []
    
    def _format_results(self, raw_results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format raw search results into the expected format.
        
        Args:
            raw_results (List[Dict]): Raw results from Azure AI Search
            
        Returns:
            List[Dict[str, Any]]: Formatted results with chunk, title, url, and optional semantic info
        """
        formatted_results = []
        
        for result in raw_results:
            formatted_result = {
                "chunk": result.get("chunk", ""),
                "title": result.get("title", "").rsplit('.', 1)[0],
                "url": result.get("url", "")
            }
            formatted_results.append(formatted_result)
        
        return formatted_results


# Quick test that runs when this module is executed directly
if __name__ == "__main__":
    # Test both regular hybrid search and semantic reranker
    try:
        client = AzureAISearchClient()
        
        search_text = "what is the date of effectiveness of the revision 21 of W-MPROD-MET-080"

        # Test regular hybrid search
        print("=== Regular Hybrid Search ===")
        results = client.search(search_text, max_results=1)
        if results:
            r = results[0]
            title = r.get('title') or (r.get('chunk')[:80] if r.get('chunk') else 'result')
            url = r.get('url', '')
            if url:
                print(f"RESULT: found - {title} | {url}")
            else:
                print(f"RESULT: found - {title}")
        else:
            print("RESULT: no results")
        
        print("\n=== Semantic Reranker Search ===")
        # Test semantic reranker search
        results = client.search(search_text, max_results=3, use_semantic_reranker=True, reranker_threshold=2.1)
        if results:
            for i, r in enumerate(results, 1):
                title = r.get('title') or (r.get('chunk')[:80] if r.get('chunk') else 'result')
                score = r.get('reranker_score', 'N/A')
                print(f"RESULT {i}: {title} (score: {score})")
        else:
            print("RESULT: no results above reranker threshold")

    except ValueError as e:
        print(f"CONFIG ERROR: {e}")
    except Exception as e:
        print(f"ERROR: {e}")