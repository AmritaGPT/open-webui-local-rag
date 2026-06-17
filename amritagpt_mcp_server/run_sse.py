"""
Runner script to launch the AmritaGPT Document Intelligence OpenAPI Server.
Runs the FastAPI app via uvicorn.
"""

import sys
import os
import uvicorn

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import app

if __name__ == "__main__":
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    
    print(f"Starting AmritaGPT OpenAPI Server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)
