# Quick Start Guide - JavaScript Client

Get up and running with the LiveKit JavaScript client in under 5 minutes.

## Prerequisites

- Node.js 18+ installed
- LiveKit server running (local Docker on `ws://localhost:7880`)
- Backend API server running (on `http://localhost:8000`)

## Step 1: Install Dependencies

```bash
npm install
```

This installs:
- `livekit-client` - Official LiveKit JavaScript SDK
- `vite` - Modern build tool for fast development

## Step 2: Start Backend Services

**Terminal 1 - Agent Worker**:
```bash
python agent.py dev
```

**Terminal 2 - FastAPI Server**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see:
- Agent worker: `registered worker {"id": "...", "url": "ws://localhost:7880"}`
- FastAPI server: `Uvicorn running on http://0.0.0.0:8000`

## Step 3: Start JavaScript Client

**Terminal 3 - JavaScript Client**:
```bash
npm run dev
```

This will:
- Start Vite dev server on `http://localhost:3000`
- Open your browser automatically
- Enable hot reload for instant updates

## Step 4: Connect and Stream

1. **Grant Permissions**: When prompted, allow camera and microphone access
2. **Optional Configuration**:
   - Enter a room name (or leave empty for auto-generated)
   - Enter your name (or leave empty for auto-generated)
3. **Click "Connect"**: The client will:
   - Generate unique participant identity
   - Request access token from your backend API
   - Connect to LiveKit server
   - Start streaming video and audio

## What Happens Behind the Scenes

### Authentication Flow

```
Client → POST /api/token → Backend
  ↓
Backend generates JWT token using LiveKit API key/secret
  ↓
Client receives token
  ↓
Client connects to LiveKit server with token
  ↓
LiveKit validates token and establishes WebRTC connection
```

### Media Streaming

```
Client captures video/audio from device
  ↓
Creates LocalVideoTrack and LocalAudioTrack
  ↓
Publishes tracks to LiveKit room
  ↓
Agent receives tracks and processes them
  ↓
Agent publishes response tracks (audio)
  ↓
Client receives and displays remote tracks
```

## Troubleshooting

### "Failed to fetch access token"

**Check**:
- FastAPI server is running on port 8000
- Backend API is accessible at `http://localhost:8000/api/token`
- CORS is enabled in FastAPI (should be configured)

**Fix**:
```bash
# Restart FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### "Failed to connect to LiveKit"

**Check**:
- LiveKit server is running
- URL matches your setup (`ws://localhost:7880` for local Docker)
- Agent worker is registered

**Fix**:
```bash
# Check LiveKit server
docker ps | grep livekit

# Restart agent worker
python agent.py dev
```

### "No video/audio"

**Check**:
- Browser permissions granted for camera/microphone
- No other application using camera/microphone
- Browser console for errors

**Fix**:
- Check browser settings → Privacy → Camera/Microphone
- Close other apps using camera/microphone
- Try a different browser (Chrome/Firefox recommended)

### Port Already in Use

If port 3000 is already in use:

**Option 1**: Change port in `vite.config.js`:
```javascript
server: {
  port: 3001,  // Change to available port
}
```

**Option 2**: Use command-line flag:
```bash
npm run dev -- --port 3001
```

## Configuration

### Change LiveKit Server URL

Edit `src/index.js`:
```javascript
const CONFIG = {
  LIVEKIT_URL: 'ws://your-server:7880',  // Update here
  // ...
};
```

### Change API Server URL

Edit `src/index.js`:
```javascript
const CONFIG = {
  API_BASE_URL: 'http://your-api:8000',  // Update here
  // ...
};
```

### Adjust Video Quality

Edit `src/index.js`:
```javascript
VIDEO_CONSTRAINTS: {
  width: { ideal: 1920 },   // Higher resolution
  height: { ideal: 1080 },
  facingMode: 'user',
},
```

## Next Steps

- Read [README_JS.md](./README_JS.md) for detailed documentation
- Check [FRONTEND_TESTING.md](./FRONTEND_TESTING.md) for testing scenarios
- Explore `src/index.js` to customize the client
- Build for production: `npm run build`

## Production Deployment

Build optimized production bundle:
```bash
npm run build
```

Output will be in `dist/` directory. Deploy to any static hosting:
- Netlify
- Vercel
- GitHub Pages
- AWS S3 + CloudFront
- Your own web server

## Support

- [LiveKit JavaScript SDK Docs](https://docs.livekit.io/client-sdk-js/)
- [LiveKit Authentication Guide](https://docs.livekit.io/home/security/)
- [Project README](./README.md)

