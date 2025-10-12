# LangChain Agent with MCP Integration

This directory contains two versions of a LangChain agent that integrates with Model Context Protocol (MCP) servers for Azure AI Search.

## Files

### `search_agent.py` - Manual FastMCP Integration
The original version that manually integrates with an MCP server using the `fastmcp` library directly:
- Creates custom LangChain tools that wrap FastMCP client calls
- Handles MCP server connection and authentication manually
- Uses `asyncio.run()` to bridge sync tool interface with async MCP calls
- More verbose but gives fine-grained control over MCP interactions

### `search_agent_mcp.py` - Native LangChain MCP Support  
The new version using LangChain's built-in MCP adapters:
- Uses `langchain-mcp-adapters` library for seamless integration
- Automatically converts MCP tools to LangChain tools
- Handles async operations natively through LangChain's agent framework
- Cleaner, more maintainable code with less boilerplate

## Key Differences

| Aspect | Manual FastMCP | Native MCP Adapters |
|--------|----------------|-------------------|
| **Dependencies** | `fastmcp` | `langchain-mcp-adapters` |
| **Tool Creation** | Manual `@tool` wrapper | Automatic via `client.get_tools()` |
| **Async Handling** | Manual `asyncio.run()` | Native async support |
| **Code Complexity** | Higher (more boilerplate) | Lower (cleaner integration) |
| **Flexibility** | More control over MCP calls | Standardized LangChain patterns |
| **Error Handling** | Custom implementation | Built-in via LangChain |

## Requirements

Both versions require:
- Azure OpenAI API credentials
- MCP server running (default: `http://localhost:8050/mcp`)
- MCP authentication key

## Environment Variables

```bash
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini  # or your deployment name
MCP_SERVER_URL=http://localhost:8050/mcp
MCP_AUTH_KEY=your_mcp_auth_key
```

## Running

```bash
# Original version
python search_agent.py

# Native MCP version  
python search_agent_mcp.py
```

## Advantages of Native MCP Support

1. **Cleaner Code**: Less boilerplate and more maintainable
2. **Better Integration**: Follows LangChain patterns and conventions
3. **Native Async**: No need for manual async bridging
4. **Automatic Tool Conversion**: MCP tools automatically become LangChain tools
5. **Future-Proof**: Leverages official LangChain MCP support

## When to Use Which

- **Use Native MCP (`search_agent_mcp.py`)** for new projects and when you want clean, maintainable code
- **Use Manual FastMCP (`search_agent.py`)** when you need fine-grained control over MCP interactions or are working with existing FastMCP-based code