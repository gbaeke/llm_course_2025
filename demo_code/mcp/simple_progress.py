#!/usr/bin/env python3
"""
Simple FastMCP Server with Progress Handling

Just one example of a long-running operation with progress reporting.
"""

import asyncio
from fastmcp import FastMCP, Context

mcp = FastMCP("SimpleProgressServer")

@mcp.tool
async def count_slowly(max_count: int, ctx: Context) -> str:
    """Count from 1 to max_count with progress updates."""
    
    for i in range(1, max_count + 1):
        # Report progress: current number, total count, and a message
        await ctx.report_progress(
            progress=i, 
            total=max_count, 
            message=f"Counting: {i}"
        )
        
        # Simulate slow work
        await asyncio.sleep(0.5)
    
    return f"Finished counting to {max_count}!"

if __name__ == "__main__":
    print("Simple Progress Server running on http://127.0.0.1:8002/mcp")
    mcp.run(transport="http", host="127.0.0.1", port=8002, path="/mcp")