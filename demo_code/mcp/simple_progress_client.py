#!/usr/bin/env python3
"""
Simple FastMCP Client with Progress Handling

Shows how to receive progress updates from the server with Rich formatting.
"""

import asyncio
from fastmcp import Client
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live

# Create Rich console
console = Console()

# Global progress bar instance
progress_bar = None
task_id = None

async def my_progress_handler(progress: float, total: float, message: str):
    """Handle progress updates from the server with Rich formatting."""
    global progress_bar, task_id
    
    if progress_bar and task_id is not None:
        # Update existing progress bar
        progress_bar.update(task_id, completed=progress, description=message)
    else:
        # This shouldn't happen in our simple example, but just in case
        console.print(f"[green]Progress:[/green] {progress}/{total} - {message}")

async def main():
    global progress_bar, task_id
    
    server_url = "http://127.0.0.1:8002/mcp"
    
    console.print("[bold blue]FastMCP Simple Progress Client[/bold blue]")
    console.print(f"Connecting to: {server_url}")
    
    # Create client with our progress handler
    client = Client(server_url, progress_handler=my_progress_handler)
    
    try:
        async with client:
            console.print("[green]✓[/green] Connected to server")
            console.print("Calling count_slowly tool...\n")
            
            # Create Rich progress bar
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TextColumn("[blue]{task.completed}/{task.total}[/blue]"),
                "•",
                TimeElapsedColumn(),
                console=console,
                transient=False
            ) as progress:
                # Set global progress bar reference
                progress_bar = progress
                task_id = progress.add_task("Starting...", total=10)
                
                # Call the tool - progress updates will be handled automatically
                result = await client.call_tool("count_slowly", {"max_count": 10})
                
                # Mark as complete
                progress.update(task_id, description="[green]Completed!")
            
            console.print(f"\n[bold green]Final result:[/bold green] {result.content[0].text}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("[yellow]Make sure the server is running:[/yellow] python simple_progress.py")

if __name__ == "__main__":
    asyncio.run(main())