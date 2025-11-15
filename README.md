# LiveKit Agent Backend - Visually-Impaired Video Voice Assistant

A production-ready LiveKit Python agent backend that provides real-time video obstacle detection and voice assistance for visually impaired users. The agent processes video frames for obstacle detection using Gemini Vision and provides bidirectional voice interaction using Voxstral STT, Gemini Live Realtime, and ElevenLabs TTS.

## Architecture Overview

The agent uses **LiveKit's native Live Video input** with Gemini Live Realtime, enabling the model to see and understand video frames automatically. The architecture integrates:

1. **Live Video Input**: Enabled via `RoomInputOptions(video_enabled=True)` - Gemini Live automatically receives video frames
   - 1 frame/second while user speaks
   - 1 frame every 3 seconds otherwise
   - Frames are fit into 1024x1024 and encoded to JPEG
2. **Obstacle Detection**: Custom `VisionAgent` hooks into video frames for additional processing
   - Processes frames using Gemini Vision API
   - Publishes results via DataChannel for frontend consumption
3. **Audio Pipeline**: Voxstral STT → Gemini Live Realtime → MCP Tools → ElevenLabs TTS

```
Mobile (WebRTC) → LiveKit Room → LiveKit Agent (Python)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
        Gemini Live (with Live Video)      VisionAgent (obstacle detection)
                    ↓                               ↓
            MCP Tools → TTS              Gemini Vision → DataChannel
                    ↓
            WebRTC Audio Out
```

## Features

- **Native Live Video Input**: Uses LiveKit's built-in Live Video input with Gemini Live Realtime
  - Automatic video frame sampling and processing
  - Gemini Live can see and understand video in real-time
- **Real-time Video Obstacle Detection**: Processes video frames using Gemini Vision API
  - Custom VisionAgent hooks for additional obstacle detection
  - Results published via DataChannel for frontend
- **Bidirectional Voice Interaction**: Natural voice conversation using Gemini Live Realtime
- **MCP Tool Integration**: Extensible tool system via Model Context Protocol (MCP) servers
- **Production-Ready**: Error handling, logging, graceful shutdown, and Docker support
- **LiveKit Native**: All media processing uses LiveKit SDK (no custom WebRTC servers)

## Prerequisites

- Python 3.12+
- LiveKit Server (Cloud or self-hosted)
- API Keys:
  - Google API Key (for Gemini Vision and Realtime API)
  - Mistral API Key (for Voxstral STT)
  - ElevenLabs API Key (for TTS)
  - LiveKit API Key and Secret

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ParisAIHackathon
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Or using `uv` (recommended):
```bash
uv pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options. Key variables:

- `LIVEKIT_URL`: LiveKit server WebSocket URL
- `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`: LiveKit credentials
- `GOOGLE_API_KEY`: Google API key for Gemini
- `MISTRAL_API_KEY`: Mistral API key for Voxstral STT
- `ELEVENLABS_API_KEY`: ElevenLabs API key for TTS
- `MCP_SERVER_URLS`: Comma-separated list of MCP server URLs

### MCP Server Configuration

MCP servers are hosted separately (e.g., on Cloud Run). Configure them in `.env`:

```env
MCP_SERVER_URLS=https://maps-mcp-server.com,https://airbnb-mcp-server.com
MCP_SERVER_HEADERS={"https://maps-mcp-server.com": {"Authorization": "Bearer token"}}
```

## Usage

### Running the Agent Worker

**Development mode** (with hot reload):
```bash
uv run agent.py dev
```

**Production mode**:
```bash
uv run agent.py start
```

**Alternative**: If you're running from the project root with PYTHONPATH set:
```bash
# Set PYTHONPATH (Linux/Mac)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or on Windows PowerShell
$env:PYTHONPATH = "$(Get-Location);$env:PYTHONPATH"

# Then run
python -m app.agent.worker dev
```

### Running the FastAPI Server (Optional)

The FastAPI server provides token generation endpoints:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- `GET /health`: Health check endpoint
- `POST /api/token`: Generate LiveKit access token
  ```json
  {
    "room_name": "my-room",
    "participant_identity": "user-123",
    "participant_name": "John Doe"
  }
  ```

### Testing with Frontend

**Option 1: JavaScript Project (Recommended for Development)**

A proper JavaScript project using LiveKit JS SDK with Vite:

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Start backend services:
   ```bash
   # Terminal 1: Agent worker
   python agent.py dev
   
   # Terminal 2: FastAPI server
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. Open `http://localhost:3000` in your browser

The JavaScript project (`src/index.js`) provides:
- ✅ Proper LiveKit authentication protocol
- ✅ Modern ES6 modules with Vite
- ✅ Video and audio streaming
- ✅ Real-time track management
- ✅ Data channel support for obstacle detection
- ✅ Production-ready build setup

See [README_JS.md](./README_JS.md) for detailed documentation.

**Option 2: Quick Test (Standalone HTML File)**:
1. Start agent worker: `python agent.py dev`
2. Start FastAPI server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Open `test-frontend.html` in your browser
4. Configure LiveKit URL and API URL (if needed)
5. Click "Connect" and grant camera/microphone permissions

The test frontend (`test-frontend.html`) provides:
- ✅ One-click video streaming setup
- ✅ Real-time obstacle detection display
- ✅ Voice interaction with the agent
- ✅ Video/audio controls
- ✅ Beautiful, responsive UI

For more details, see the [Frontend Testing Guide](./FRONTEND_TESTING.md) which includes:
- Complete HTML/JavaScript example
- React component example
- Step-by-step testing instructions
- Troubleshooting guide

## Project Structure

```
ParisAIHackathon/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── agent/
│   │   ├── worker.py           # LiveKit agent entrypoint
│   │   ├── vision_agent.py     # Custom Agent with video hooks for obstacle detection
│   │   ├── audio_pipeline.py   # Audio processing with Live Video input
│   │   └── session.py          # Session manager
│   ├── mcp/
│   │   ├── router.py           # MCP tool router
│   │   └── schemas.py          # MCP schemas
│   ├── services/
│   │   ├── gemini.py           # Gemini Vision service
│   │   ├── voxstral.py         # Voxstral STT wrapper
│   │   └── elevenlabs.py       # ElevenLabs TTS wrapper
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   └── security.py         # JWT token generation
│   └── api/
│       └── token.py            # Token API endpoints
├── docker/
│   └── Dockerfile              # Production Docker image
├── src/                         # JavaScript client source
│   └── index.js                # LiveKit client implementation
├── index.html                   # JavaScript client HTML entry
├── package.json                 # JavaScript dependencies
├── vite.config.js              # Vite build configuration
├── test-frontend.html           # Standalone HTML test frontend
├── FRONTEND_TESTING.md          # Frontend testing guide
├── README_JS.md                 # JavaScript client documentation
├── .env.example                 # Environment variable template
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Docker Deployment

### Build the Docker image:
```bash
docker build -f docker/Dockerfile -t livekit-agent-backend .
```

### Run the container:
```bash
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  livekit-agent-backend
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy app/
```

## Key Implementation Details

### Live Video Input

- **Native Integration**: Uses `RoomInputOptions(video_enabled=True)` to enable LiveKit's built-in video input
- **Automatic Sampling**: LiveKit automatically samples video frames:
  - 1 frame/second while user speaks
  - 1 frame every 3 seconds otherwise
- **Gemini Live Processing**: Video frames are automatically sent to Gemini Live Realtime
  - Frames are fit into 1024x1024 and encoded to JPEG
  - Gemini Live can see and understand the video context
- **Custom Processing**: `VisionAgent` hooks into video frames for additional obstacle detection
  - Processes frames at configurable FPS (default: 2 FPS)
  - Uses Gemini Vision API for detailed obstacle analysis
  - Publishes results via DataChannel for frontend consumption

### Audio Pipeline

- Uses LiveKit's `AgentSession` with `VisionAgent` for integrated video/audio processing
- MCP servers are configured in the `AgentSession` constructor
- Audio output is automatically published to the room
- Gemini Live receives both audio and video input simultaneously

### Error Handling

- Errors in video pipeline don't affect audio pipeline
- External API calls include retry logic
- Graceful shutdown on SIGTERM/SIGINT

## Troubleshooting

### Agent Not Connecting

- Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` are correct
- Check LiveKit server is accessible
- Review agent logs for connection errors

### Video Processing Not Working

- Ensure participant is publishing video track
- Check `GOOGLE_API_KEY` is valid
- Verify video processing FPS is not too high (causing rate limits)

### MCP Tools Not Available

- Verify MCP server URLs are correct and accessible
- Check MCP server headers include authentication if required
- Review MCP router logs for connection errors

### Audio Issues

- Verify all API keys (Mistral, Google, ElevenLabs) are valid
- Check agent logs for STT/TTS errors
- Ensure microphone permissions are granted on client

## Additional Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Gemini Live API](https://ai.google.dev/gemini-api/docs/live)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Worker Entrypoint Best Practices](./docs/worker-entrypoint-best-practices.md)
- [Frontend Testing Guide](./FRONTEND_TESTING.md) - Complete guide for testing video streaming from frontend

## License

Apache-2.0

## Contributing

Contributions are welcome! Please ensure all code follows the project's style guidelines and includes appropriate tests.

