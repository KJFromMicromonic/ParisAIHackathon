# Environment Variables Setup Guide

## Required Environment Variables for Worker Entrypoint

To get the worker entrypoint to work, you need to set the following **required** environment variables:

### 1. LiveKit Server Connection (REQUIRED)

These are used by LiveKit Agents framework to connect the worker to the LiveKit server:

```bash
# LiveKit server WebSocket URL
LIVEKIT_URL=wss://your-livekit-server.com
# OR for local development:
LIVEKIT_URL=ws://localhost:7880

# LiveKit API credentials (for worker authentication)
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

**Note**: The LiveKit Agents framework automatically reads these from environment variables. Without these, the worker cannot connect to the LiveKit server.

### 2. API Keys for Services (REQUIRED)

These are used by your application code:

```bash
# Google API Key (for Gemini Vision and Realtime API)
GOOGLE_API_KEY=your_google_api_key

# Mistral API Key (for Voxstral STT)
MISTRAL_API_KEY=your_mistral_api_key

# ElevenLabs API Key (for TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 3. Optional Configuration (with defaults)

These have defaults but can be customized:

```bash
# Gemini model (default: gemini-2.0-flash-exp)
# Note: Gemini is configured for text-only output; ElevenLabs TTS handles audio
GEMINI_MODEL=gemini-2.0-flash-exp

# Gemini voice (deprecated - not used when using ElevenLabs TTS)
# This setting is ignored since Gemini outputs text only
# GEMINI_VOICE=Puck

# Voxstral model (default: voxtral-mini-2507)
VOXSTRAL_MODEL=voxtral-mini-2507

# ElevenLabs voice ID (default: EXAVITQu4vr4xnSDxMaL)
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL

# ElevenLabs model (default: eleven_multilingual_v2)
ELEVENLABS_MODEL=eleven_multilingual_v2

# MCP Server URLs (comma-separated, optional)
MCP_SERVER_URLS=https://server1.com,https://server2.com

# MCP Server Headers (JSON, optional)
MCP_SERVER_HEADERS={"https://server1.com": {"Authorization": "Bearer token"}}

# Video processing FPS (default: 2.0)
VIDEO_PROCESSING_FPS=2.0

# JPEG quality (default: 85)
VIDEO_JPEG_QUALITY=85
```

## Quick Setup

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and fill in the required values:
   - `LIVEKIT_URL` - Your LiveKit server URL
   - `LIVEKIT_API_KEY` - Your LiveKit API key
   - `LIVEKIT_API_SECRET` - Your LiveKit API secret
   - `GOOGLE_API_KEY` - Your Google API key
   - `MISTRAL_API_KEY` - Your Mistral API key
   - `ELEVENLABS_API_KEY` - Your ElevenLabs API key

3. **Install MCP dependency** (if using MCP servers):
   ```bash
   pip install 'livekit-agents[mcp]'
   ```

4. **Run from project root**:
   ```bash
   python agent.py dev
   ```

## Minimum Required Variables

The **absolute minimum** to get the worker running:

```bash
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
GOOGLE_API_KEY=your_google_key
MISTRAL_API_KEY=your_mistral_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

Without these, the worker will fail to start or connect.

## Troubleshooting

- **"No module named 'mcp'"**: Install with `pip install 'livekit-agents[mcp]'` or remove MCP server URLs from config
- **"LIVEKIT_URL is required"**: Set `LIVEKIT_URL` environment variable
- **"api_key is required"**: Set `LIVEKIT_API_KEY` environment variable
- **"api_secret is required"**: Set `LIVEKIT_API_SECRET` environment variable

