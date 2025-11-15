# LiveKit JavaScript Client

A simple JavaScript project for streaming video and audio to your LiveKit server using the official LiveKit JavaScript SDK.

## Features

- ✅ **Proper Authentication**: Fetches access tokens from your backend API following LiveKit's authentication protocol
- ✅ **Video Streaming**: Captures and streams video from your camera
- ✅ **Audio Streaming**: Captures and streams audio from your microphone
- ✅ **Real-time Communication**: Connects to LiveKit rooms and receives remote tracks
- ✅ **Modern Build Setup**: Uses Vite for fast development and optimized builds

## Prerequisites

- Node.js 18+ and npm
- LiveKit server running (local Docker or cloud)
- Backend API server running (for token generation)

## Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure the client** (if needed):
   Edit `src/index.js` and update the `CONFIG` object:
   ```javascript
   const CONFIG = {
     LIVEKIT_URL: 'ws://localhost:7880',  // Your LiveKit server URL
     API_BASE_URL: 'http://localhost:8000',  // Your backend API URL
     // ... other settings
   };
   ```

## Usage

### Development Mode

Start the development server:
```bash
npm run dev
```

This will:
- Start Vite dev server on `http://localhost:3000`
- Open the browser automatically
- Enable hot module replacement for fast development

### Production Build

Build for production:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## How It Works

### Authentication Flow

1. **User clicks "Connect"**
2. **Client generates unique identifiers**:
   - Room name (from input or auto-generated)
   - Participant identity (auto-generated)
   - Participant name (from input or auto-generated)

3. **Client requests access token**:
   ```javascript
   POST http://localhost:8000/api/token
   {
     "room_name": "room-1234567890",
     "participant_identity": "user-1234567890-abc123",
     "participant_name": "John Doe"
   }
   ```

4. **Backend generates JWT token**:
   - Uses LiveKit API key and secret from `.env`
   - Creates token with appropriate grants (join, publish, subscribe, publish data)
   - Returns token to client

5. **Client connects to LiveKit**:
   - Uses token to authenticate with LiveKit server
   - Establishes WebRTC connection

### Media Streaming

1. **Video Track**:
   - Creates local video track using `createLocalVideoTrack()`
   - Publishes to room with `SOURCE_CAMERA` source
   - Attaches to local video element for preview

2. **Audio Track**:
   - Creates local audio track using `createLocalAudioTrack()`
   - Publishes to room with `SOURCE_MICROPHONE` source
   - Enables echo cancellation, noise suppression, and auto gain control

3. **Remote Tracks**:
   - Listens for `TrackSubscribed` events
   - Attaches remote video/audio tracks to remote video element
   - Handles track unsubscription and cleanup

### Data Channel

The client listens for data channel messages on the `obstacle_detection` topic:
- Receives obstacle detection results from the agent
- Logs data to console (can be extended to display in UI)

## Project Structure

```
.
├── src/
│   └── index.js          # Main client application
├── index.html            # HTML entry point
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
└── README_JS.md          # This file
```

## Configuration

### Environment Variables

The client reads configuration from `src/index.js`. For production, you may want to use environment variables:

1. Create `.env` file:
   ```env
   VITE_LIVEKIT_URL=ws://localhost:7880
   VITE_API_BASE_URL=http://localhost:8000
   ```

2. Update `src/index.js`:
   ```javascript
   const CONFIG = {
     LIVEKIT_URL: import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880',
     API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
     // ...
   };
   ```

### Video/Audio Constraints

Adjust video and audio quality in `src/index.js`:

```javascript
VIDEO_CONSTRAINTS: {
  width: { ideal: 1280 },
  height: { ideal: 720 },
  facingMode: 'user', // 'user' for front camera, 'environment' for back
},

AUDIO_CONSTRAINTS: {
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
},
```

## Troubleshooting

### Connection Issues

- **"Failed to fetch access token"**:
  - Ensure backend API server is running on `http://localhost:8000`
  - Check CORS settings in FastAPI app
  - Verify API endpoint is `/api/token`

- **"Failed to connect to LiveKit"**:
  - Ensure LiveKit server is running
  - Check `LIVEKIT_URL` matches your server URL
  - Verify WebSocket URL format (`ws://` for local, `wss://` for production)

### Media Issues

- **No video/audio**:
  - Grant camera/microphone permissions in browser
  - Check browser console for errors
  - Verify media devices are available

- **Poor video quality**:
  - Adjust `VIDEO_CONSTRAINTS` in `src/index.js`
  - Check network bandwidth
  - Verify LiveKit server configuration

## API Reference

### Backend Token Endpoint

**POST** `/api/token`

Request body:
```json
{
  "room_name": "string",
  "participant_identity": "string",
  "participant_name": "string (optional)"
}
```

Response:
```json
{
  "token": "jwt_token_string",
  "room_name": "string",
  "participant_identity": "string"
}
```

## LiveKit SDK Documentation

For more details on the LiveKit JavaScript SDK, see:
- [LiveKit JavaScript SDK Docs](https://docs.livekit.io/client-sdk-js/)
- [LiveKit API Reference](https://docs.livekit.io/client-sdk-js/classes/Room.html)
- [LiveKit Authentication Guide](https://docs.livekit.io/home/security/)

## License

MIT

