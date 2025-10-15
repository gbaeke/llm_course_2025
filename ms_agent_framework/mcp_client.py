"""
MCP client with debug logging.

Env:
- LOG_LEVEL: DEBUG to enable verbose logs (defaults to INFO)
"""

# Copyright (c) Microsoft. All rights reserved.

import os
import logging

from agent_framework import ChatAgent, MCPStreamableHTTPTool
from dotenv import load_dotenv
from pathlib import Path
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.devui import serve

# Load environment variables from .env file
load_dotenv(Path(__file__).with_name(".env"))

# Module-level logger
logger = logging.getLogger(__name__)


def ensure_logger_configured() -> None:
    """Ensure this module's logger always emits to console.

    Works even if another framework (e.g., Uvicorn) already configured logging
    or when this module is imported and used indirectly (not via __main__).
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # If root has no handlers, do a minimal basicConfig so levels are respected
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Attach a stream handler to this module logger if missing
    if not logger.handlers:
        _handler = logging.StreamHandler()
        _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        _handler.setLevel(level)
        logger.addHandler(_handler)
        # Avoid duplicate propagation to root
        logger.propagate = False

    logger.setLevel(level)
    # Emit one banner line at INFO so users notice logging is active
    if level <= logging.INFO:
        logger.info("Log level: %s", level_name)


# Configure immediately on import so debug from build_agent appears even if not run as __main__
ensure_logger_configured()


def build_agent() -> ChatAgent:
    """Builds and returns the ChatAgent configured to use the MCP HTTP tool."""
    ensure_logger_configured()
    logger.debug("Starting build_agent()")
    # Configuration
    mcp_server_url = os.getenv("MCP_SERVER_URL", "https://f0f0b233e8d0.ngrok-free.app/mcp")
    logger.debug("MCP_SERVER_URL resolved: %s", mcp_server_url)

    # Prepare auth headers (expects MCP_AUTH_KEY to be set)
    auth_key = os.getenv("MCP_AUTH_KEY", "")
    if not auth_key:
        # Keep simple and explicit error to match prior behavior
        logger.error("MCP_AUTH_KEY not set in environment")
        raise ValueError("MCP_AUTH_KEY environment variable not set")

    auth_headers = {
        "X-API-KEY": auth_key,
    }

    logger.debug("Auth headers prepared (key present: %s)", bool(auth_key))

    # Create MCP tool (no async context needed for DevUI usage)
    mcp_tool = MCPStreamableHTTPTool(
        name="search",
        description="Tools to search for information using Azure AI Search.",
        url=mcp_server_url,
        headers=auth_headers,
    )
    logger.debug("MCPStreamableHTTPTool created: name=search, url=%s", mcp_server_url)

    # Build the chat agent, keeping the AzureOpenAIChatClient configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")

    logger.debug(
        "Azure OpenAI config (api_key present: %s, deployment_name: %s, endpoint set: %s)",
        bool(api_key),
        bool(deployment_name),
        bool(endpoint),
    )

    agent = ChatAgent(
        chat_client=AzureOpenAIChatClient(
            api_key=api_key,
            deployment_name=deployment_name,
            # Endpoint optional; include if set in env
            endpoint=endpoint,
        ),
        name="Agent",
        instructions=(
            """
            You are a helpful assistant that only answers questions with the search tool.
            When querying, do not add extra context.

            Example:
            - if user asks about "cleaning lenses" do not query "cleaning lenses for cameras" or similar.

            """
        ),
        tools=mcp_tool,
    )

    logger.debug("ChatAgent constructed with tool 'search' and name 'Agent'")

    return agent


def main():
    """Launch the agent in the DevUI, similar to devui.py."""
    ensure_logger_configured()
    logger.debug("Logging initialized (module handler attached)")

    agent = build_agent()

    logger.info("Starting MCP Client Agent")
    logger.info("Available at: http://localhost:8090")
    logger.info("Entity ID: agent_Agent")

    # Launch server with the agent (synchronous, like devui.py)
    try:
        logger.debug("Invoking DevUI server serve() with port=8090, auto_open=True")
        serve(entities=[agent], port=8090, auto_open=True)
    except Exception:
        logger.exception("DevUI server encountered an error")
        raise

if __name__ == "__main__":
    main()