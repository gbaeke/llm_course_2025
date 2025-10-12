#!/usr/bin/env python3
"""
MCP Search Server

A FastMCP server that provides a search tool returning results as a list of dictionaries
with title, url, and content fields.
"""


from fastmcp import FastMCP
from typing import List, Dict, Any, Annotated
import json
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from dotenv import load_dotenv
import os
from search.search import AzureAISearchClient

# Load environment variables from .env file
load_dotenv()

# check for MCP_AUTH_KEY in environment variables
mcp_auth_key = os.getenv("MCP_AUTH_KEY")
if not mcp_auth_key:
    raise ValueError("MCP_AUTH_KEY environment variable not set")

# Read search configuration from environment variables with defaults
use_semantic_reranker = os.getenv("USE_SEMANTIC_RERANKER", "false").lower() == "true"
reranker_threshold = float(os.getenv("RERANKER_THRESHOLD", "2.5"))


# Create the FastMCP server instance
mcp: FastMCP = FastMCP(
    name="Search Server",
)

# Starlette middleware that requires X-API-KEY header set to MCP_AUTH_KEY env
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-KEY")
        if api_key != mcp_auth_key:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        response = await call_next(request)
        return response

http_app = mcp.http_app(middleware=[Middleware(APIKeyMiddleware)])

@mcp.tool(
    name="search",
    description="Search for information and return a list of results."
)
def search(
    query: Annotated[str, "The search query string to find information about"],
    max_results: Annotated[int, "Maximum number of search results to return"] = 5
) -> List[Dict[str, Any]]:
    
    try:
        # Create Azure AI Search client and perform hybrid search
        search_client = AzureAISearchClient()
        results = search_client.search(query, max_results=max_results, use_semantic_reranker=use_semantic_reranker, reranker_threshold=reranker_threshold)
        
        return results
        
    except Exception as e:
        # Return error message in expected format on failure
        return [{"title": "Search Error", "url": "", "content": f"Could not perform a search at this time: {str(e)}"}]

@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """
    Health check endpoint.

    Returns:
        status: The health status of the service.
    """
    return JSONResponse({"status": "healthy"})

# Make the server runnable
if __name__ == "__main__":
    uvicorn.run(http_app, host="0.0.0.0", port=8050)
    