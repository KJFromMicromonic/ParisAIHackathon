"""Script to run the WhatsApp MCP server using uvicorn."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from app.mcp.whatsapp_server import app


def main():
    """
    Run the WhatsApp MCP server using uvicorn.

    The server will be available at http://localhost:8081 by default.
    Set WHATSAPP_MCP_SERVER_PORT environment variable to change the port.
    """
    port = int(os.getenv("WHATSAPP_MCP_SERVER_PORT", 8081))
    host = os.getenv("WHATSAPP_MCP_SERVER_HOST", "127.0.0.1")

    print(f"Starting WhatsApp MCP Server on {host}:{port}")
    print(f"MCP endpoint: http://{host}:{port}/mcp")
    print("\nMake sure WHATSAPP_API_URL is set in your environment!")

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce noise
        access_log=False,  # Disable access logs for cleaner output
    )


if __name__ == "__main__":
    main()

