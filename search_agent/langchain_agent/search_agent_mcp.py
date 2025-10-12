#!/usr/bin/env python3
"""
LangChain CLI Agent with Native MCP Support

A minimal CLI agent that uses LangChain's built-in MCP adapters for Azure AI Search.
This version leverages langchain-mcp-adapters instead of manual FastMCP client integration.
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
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()

# Setup debug logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def create_agent():
    """Create a LangChain agent with native MCP integration."""
    
    # Get required Azure OpenAI configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8050/mcp")
    mcp_auth_key = os.getenv("MCP_AUTH_KEY")
    
    if not azure_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
    if not azure_api_key:
        raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
    if not mcp_auth_key:
        raise ValueError("MCP_AUTH_KEY environment variable is required")
    
    # Configure MCP client with authentication headers
    print("🔗 Connecting to MCP server...")
    client = MultiServerMCPClient(
        {
            "search": {
                "transport": "streamable_http",
                "url": mcp_server_url,
                "headers": {"X-API-KEY": mcp_auth_key}
            }
        }
    )
    
    try:
        # Get tools from MCP server
        print("📋 Loading tools from MCP server...")
        tools = await client.get_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
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
        
        # Create a system prompt that forces tool usage
        system_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions by searching for information using Azure AI Search.

IMPORTANT INSTRUCTIONS:
- You must ALWAYS use the search tool to find information before answering any question
- Never answer questions based on your training data or general knowledge alone
- Always search first, then provide your answer based on the search results
- If the search doesn't return relevant results, say so and suggest refining the search query
- Always perform multiple searches to get comprehensive results:
  1. Search with the original user question
  2. Rephrase the question and search again (at least 2 different rephrasings)
  3. Try different keywords or approaches if needed
  4. This agent's domain is medical information, so focus on that if applicable
            
HOW TO ANSWER: 
- Provide a list of titles with their URLs from the search results
- Ensure URLs are unique (no duplicates)
- No other information should be returned except the titles and URLs
- Use a clear, numbered list format

Your workflow should be:
1. Perform the original search with the user's question
2. Rephrase the question in different ways and search again
3. Compile all unique results
4. Present the final list of titles and URLs"""),
            ("placeholder", "{messages}")
        ])
        
        # Create memory for conversation history
        memory = MemorySaver()
        
        # Create the agent with the MCP tools and system prompt
        agent = create_react_agent(
            llm, 
            tools,
            prompt=system_prompt,
            checkpointer=memory
        )
        
        return agent, client
        
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
        print(f"❌ Failed to connect to MCP server: {str(e)}")
        raise


async def main():
    """Main CLI loop for the agent."""
    
    print("🤖 LangChain Agent with Native MCP Support")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    
    try:
        agent, client = await create_agent()
        
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
                print(f"\n🤔 Agent is thinking and searching...")
                
                # Invoke the agent with the user's message
                response = await agent.ainvoke({
                    "messages": [HumanMessage(content=user_input)]
                }, config=config)
                
                # Get the last AI message from the response
                ai_message = response["messages"][-1]
                print(f"\n📋 Results:")
                print(f"🤖 Agent: {ai_message.content}")
                
            except Exception as e:
                logger.error(f"Agent invocation failed: {str(e)}", exc_info=True)
                print(f"\n❌ Error: {str(e)}")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {str(e)}")
        print("Make sure:")
        print("1. AZURE_OPENAI_API_KEY is set in your environment")
        print("2. AZURE_OPENAI_ENDPOINT is set in your environment") 
        print("3. AZURE_OPENAI_DEPLOYMENT is set (or defaults to gpt-4o-mini)")
        print("4. MCP_AUTH_KEY is set in your environment")
        print("5. MCP server is running (default: http://localhost:8050/mcp)")


if __name__ == "__main__":
    asyncio.run(main())