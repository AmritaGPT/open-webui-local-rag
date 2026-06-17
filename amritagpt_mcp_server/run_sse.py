"""
Runner script to launch the AmritaGPT Document Intelligence MCP Server in SSE Mode.
Runs the underlying Starlette sse_app using uvicorn directly to allow binding to 0.0.0.0.
"""

import sys
import os
import uvicorn

# Add server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import mcp

if __name__ == "__main__":
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    
    print(f"Starting AmritaGPT MCP Server in SSE mode on {host}:{port}...")
    # Run the Starlette SSE app directly via uvicorn
    uvicorn.run(mcp.sse_app, host=host, port=port)
