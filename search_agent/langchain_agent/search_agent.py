#!/usr/bin/env python3
"""
LangChain CLI Agent with MCP Search Integration

A minimal CLI agent that uses LangChain with MCP server for Azure AI Search.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# Load environment variables
load_dotenv()

# Setup debug logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@tool
def search_azure_ai(query: str, max_results: int = 5) -> str:
    """
    Search for information using Azure AI Search via FastMCP client.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Formatted search results as a string
    """
    async def _search():
        try:
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8050/mcp")
            mcp_auth_key = os.getenv("MCP_AUTH_KEY")
            
            logger.debug(f"Starting MCP search with URL: {mcp_server_url}")
            logger.debug(f"Query: {query}, Max results: {max_results}")
            logger.debug(f"Auth key present: {bool(mcp_auth_key)}")
            
            # Create transport with optional authentication header
            if mcp_auth_key:
                logger.debug("Creating transport with X-API-KEY header")
                transport = StreamableHttpTransport(
                    mcp_server_url,
                    headers={"X-API-KEY": mcp_auth_key}
                )
                client = Client(transport=transport)
            else:
                logger.debug("Creating client without authentication")
                client = Client(mcp_server_url)
            
            logger.debug("Attempting to connect to MCP server...")
            # Use the client with proper context management
            async with client:
                logger.debug("Connected successfully, calling search tool...")
                result = await client.call_tool("search", {
                    "query": query,
                    "max_results": max_results
                })
                logger.debug(f"Search completed successfully, result type: {type(result)}")
                return str(result)
                
        except Exception as e:
            logger.error(f"MCP search failed: {str(e)}", exc_info=True)
            return f"Error performing search via FastMCP: {str(e)}"
    
    # Run the async function
    try:
        return asyncio.run(_search())
    except Exception as e:
        return f"Error running search: {str(e)}"

def create_agent():
    """Create a LangChain agent with MCP search tool."""
    
    # Get required Azure OpenAI configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not azure_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
    if not azure_api_key:
        raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
    
    # Debug: List available tools from MCP server
    print("🔍 Checking MCP server tools...")
    try:
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8050/mcp")
        mcp_auth_key = os.getenv("MCP_AUTH_KEY")
        
        async def debug_list_tools():
            try:
                logger.debug(f"Debug: Connecting to MCP server at {mcp_server_url}")
                logger.debug(f"Debug: Auth key present: {bool(mcp_auth_key)}")
                
                if mcp_auth_key:
                    logger.debug("Debug: Creating transport with X-API-KEY header")
                    transport = StreamableHttpTransport(
                        mcp_server_url,
                        headers={"X-API-KEY": mcp_auth_key}
                    )
                    client = Client(transport=transport)
                else:
                    logger.debug("Debug: Creating client without authentication")
                    client = Client(mcp_server_url)
                
                logger.debug("Debug: Attempting to connect and list tools...")
                async with client:
                    logger.debug("Debug: Connected successfully, listing tools...")
                    tools = await client.list_tools()
                    logger.debug(f"Debug: Retrieved {len(tools)} tools")
                    print(f"📋 Found {len(tools)} tools on MCP server:")
                    for tool in tools:
                        print(f"   - {tool.name}: {tool.description}")
                        logger.debug(f"Tool: {tool.name} - {tool.description}")
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            print(f"     Parameters: {tool.inputSchema}")
                            logger.debug(f"Tool {tool.name} parameters: {tool.inputSchema}")
                    print()
                    
            except Exception as e:
                logger.error(f"Debug tool listing failed: {str(e)}", exc_info=True)
                print(f"❌ Failed to list MCP server tools: {str(e)}")
                print()
        
        # Run the debug function
        asyncio.run(debug_list_tools())
        
    except Exception as e:
        print(f"❌ MCP server debug failed: {str(e)}")
        print()
    
    # Initialize the Azure OpenAI chat model
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"), 
        temperature=0,
        azure_endpoint=azure_endpoint,
        azure_ad_token_provider=None,  # Use API key authentication
    )
    
    # Set the API key via environment variable (preferred method)
    os.environ["AZURE_OPENAI_API_KEY"] = azure_api_key
    
    # Create the search tool
    tools = [search_azure_ai]
    
    # Create a system prompt that forces tool usage
    system_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant that answers questions by searching for information using Azure AI Search.

IMPORTANT INSTRUCTIONS:
- You must ALWAYS use the search_azure_ai tool to find information before answering any question
- Never answer questions based on your training data or general knowledge alone
- Always search first, then provide your answer based on the search results
- If the search doesn't return relevant results, say so and suggest refining the search query
- Always rephrase the question 2 times so you perform multiple searches: one time the original and two times rephrased
        
HOW TO ANSWER: provide a list of titles with their URLs; no other information should be returned; ensure urls are unique

Your workflow should be:
1. Use the search_azure_ai tool with the user's question
2. Analyze the search results
3. Provide a comprehensive answer based on the search results"""),
        ("placeholder", "{messages}")
    ])
    
    # Create memory for conversation history
    memory = MemorySaver()
    
    # Create the agent with the tools and system prompt
    agent = create_react_agent(
        llm, 
        tools,
        prompt=system_prompt,
        checkpointer=memory
    )
    
    return agent


def main():
    """Main CLI loop for the agent."""
    
    print("🤖 LangChain Agent with Azure AI Search")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    
    try:
        agent = create_agent()
        
        # Thread configuration for conversation memory
        config = RunnableConfig(configurable={"thread_id": "main_conversation"})
        
        while True:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
                
            if not user_input:
                continue
            
            try:
                # Invoke the agent with the user's message
                response = agent.invoke({
                    "messages": [HumanMessage(content=user_input)]
                }, config=config)
                
                # Get the last AI message from the response
                ai_message = response["messages"][-1]
                print(f"\n🤖 Agent: {ai_message.content}")
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {str(e)}")
        print("Make sure:")
        print("1. AZURE_OPENAI_API_KEY is set in your environment")
        print("2. AZURE_OPENAI_ENDPOINT is set in your environment") 
        print("3. AZURE_OPENAI_DEPLOYMENT is set (or defaults to gpt-4o-mini)")
        print("4. MCP server is running (default: http://localhost:8050/mcp)")


if __name__ == "__main__":
    main()