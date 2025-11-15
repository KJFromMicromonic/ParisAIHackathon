"""Script to run the Google Maps MCP server."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from app.mcp.google_maps_server import app


def main():
    """
    Run the Google Maps MCP server.

    The server will be available at http://localhost:8080 by default.
    Set PORT environment variable to change the port.
    """
    port = int(os.getenv("GOOGLE_MAPS_MCP_PORT", 8080))
    host = os.getenv("GOOGLE_MAPS_MCP_HOST", "0.0.0.0")

    print(f"Starting Google Maps MCP Server on {host}:{port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Health Check: http://localhost:{port}/health")
    print(f"Tools List: http://localhost:{port}/tools")
    print("\nMake sure GOOGLE_MAPS_API_KEY is set in your environment!")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

