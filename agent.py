"""Root-level entry script for LiveKit agent worker.

This script ensures the project root is in the Python path before importing.
Run with: uv run agent.py dev
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables from .env file before importing anything else
# This ensures LiveKit worker can access LIVEKIT_API_KEY, LIVEKIT_API_SECRET, etc.
from dotenv import load_dotenv

# Load .env file from project root
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

# Also ensure our Settings class loads the config (which will set env vars if needed)
# This ensures all environment variables are available to LiveKit worker
from app.core.config import settings

# Set LiveKit environment variables from our settings if they're not already set
# This ensures compatibility with LiveKit's direct environment variable checks
if not os.getenv("LIVEKIT_API_KEY") and hasattr(settings, "livekit_api_key"):
    os.environ["LIVEKIT_API_KEY"] = settings.livekit_api_key
if not os.getenv("LIVEKIT_API_SECRET") and hasattr(settings, "livekit_api_secret"):
    os.environ["LIVEKIT_API_SECRET"] = settings.livekit_api_secret
if not os.getenv("LIVEKIT_URL") and hasattr(settings, "livekit_url"):
    os.environ["LIVEKIT_URL"] = settings.livekit_url

# Now import and run the worker
# The LiveKit CLI will handle command-line arguments (dev, start, etc.)
from app.agent.worker import main

if __name__ == "__main__":
    # Pass through any command-line arguments to LiveKit CLI
    main()

