# Frontend Testing Guide - Video Streaming to LiveKit Agent

This guide provides step-by-step instructions for testing video streaming from a frontend application to your LiveKit agent backend.

## Prerequisites

Before testing, ensure:

1. **LiveKit Server** is running and accessible
   - Cloud: Use your LiveKit Cloud instance URL
   - Self-hosted: Ensure your LiveKit server is running and accessible

2. **Agent Worker** is running:
   ```bash
   python agent.py dev
   ```

3. **FastAPI Server** is running (for token generation):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Environment Variables** are configured in `.env`:
   - `LIVEKIT_URL`: Your LiveKit server WebSocket URL
   - `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`: LiveKit credentials
   - All API keys (Google, Mistral, ElevenLabs)

## Frontend Setup

### Option 1: Simple HTML/JavaScript Example

Create a test HTML file (`test-frontend.html`) with the following:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LiveKit Agent Video Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        video {
            width: 100%;
            border: 2px solid #333;
            border-radius: 8px;
        }
        .controls {
            margin: 20px 0;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            font-size: 16px;
            cursor: pointer;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            background: #f0f0f0;
        }
        .obstacle-detection {
            max-height: 400px;
            overflow-y: auto;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .obstacle-item {
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }
        .obstacle-item.high {
            border-left-color: #dc3545;
        }
        .obstacle-item.medium {
            border-left-color: #ffc107;
        }
        .obstacle-item.low {
            border-left-color: #28a745;
        }
    </style>
</head>
<body>
    <h1>LiveKit Agent Video Streaming Test</h1>
    
    <div class="controls">
        <button id="connectBtn">Connect</button>
        <button id="disconnectBtn" disabled>Disconnect</button>
        <button id="toggleVideoBtn" disabled>Toggle Video</button>
        <button id="toggleAudioBtn" disabled>Toggle Audio</button>
    </div>

    <div class="status" id="status">Disconnected</div>

    <div class="container">
        <div>
            <h2>Local Video</h2>
            <video id="localVideo" autoplay muted playsinline></video>
        </div>
        <div>
            <h2>Agent Audio</h2>
            <video id="remoteVideo" autoplay playsinline></video>
        </div>
    </div>

    <div>
        <h2>Obstacle Detection Results</h2>
        <div class="obstacle-detection" id="obstacleResults">
            <p>No detections yet...</p>
        </div>
    </div>

    <script type="module">
        import { Room, RoomEvent, Track, TrackPublication, RemoteTrack } from 'https://unpkg.com/livekit-client@latest/dist/livekit-client.esm.js';

        // Configuration - Update these values
        const LIVEKIT_URL = 'wss://your-livekit-server.com'; // Your LiveKit server URL
        const API_BASE_URL = 'http://localhost:8000'; // Your FastAPI server URL
        const ROOM_NAME = `test-room-${Date.now()}`; // Unique room name
        const PARTICIPANT_IDENTITY = `user-${Date.now()}`; // Unique participant ID

        let room = null;
        let localVideoTrack = null;
        let localAudioTrack = null;

        // UI Elements
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const toggleVideoBtn = document.getElementById('toggleVideoBtn');
        const toggleAudioBtn = document.getElementById('toggleAudioBtn');
        const statusDiv = document.getElementById('status');
        const localVideo = document.getElementById('localVideo');
        const remoteVideo = document.getElementById('remoteVideo');
        const obstacleResults = document.getElementById('obstacleResults');

        // Update status
        function updateStatus(message, isConnected = false) {
            statusDiv.textContent = message;
            statusDiv.style.background = isConnected ? '#d4edda' : '#f8d7da';
            connectBtn.disabled = isConnected;
            disconnectBtn.disabled = !isConnected;
            toggleVideoBtn.disabled = !isConnected;
            toggleAudioBtn.disabled = !isConnected;
        }

        // Get access token from backend
        async function getAccessToken() {
            const response = await fetch(`${API_BASE_URL}/api/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    room_name: ROOM_NAME,
                    participant_identity: PARTICIPANT_IDENTITY,
                    participant_name: 'Test User',
                    ttl_seconds: 3600,
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to get token: ${response.statusText}`);
            }

            const data = await response.json();
            return data.token;
        }

        // Connect to room
        connectBtn.addEventListener('click', async () => {
            try {
                updateStatus('Connecting...');

                // Get access token
                const token = await getAccessToken();
                console.log('Got access token');

                // Create room instance
                room = new Room({
                    adaptiveStream: true,
                    dynacast: true,
                });

                // Set up event handlers
                room.on(RoomEvent.Connected, () => {
                    console.log('Connected to room:', ROOM_NAME);
                    updateStatus(`Connected to room: ${ROOM_NAME}`, true);
                });

                room.on(RoomEvent.Disconnected, () => {
                    console.log('Disconnected from room');
                    updateStatus('Disconnected');
                    cleanup();
                });

                room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
                    console.log('Track subscribed:', track.kind, 'from', participant.identity);
                    
                    if (track.kind === Track.Kind.Video) {
                        // Attach remote video track
                        const element = track.attach();
                        remoteVideo.srcObject = new MediaStream([element]);
                    } else if (track.kind === Track.Kind.Audio) {
                        // Attach remote audio track
                        const element = track.attach();
                        remoteVideo.srcObject = new MediaStream([element]);
                    }
                });

                room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
                    console.log('Track unsubscribed:', track.kind);
                    track.detach();
                });

                room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
                    console.log('Data received:', topic, payload);
                    
                    if (topic === 'obstacle_detection') {
                        try {
                            const data = JSON.parse(new TextDecoder().decode(payload));
                            displayObstacleDetection(data);
                        } catch (e) {
                            console.error('Error parsing obstacle detection data:', e);
                        }
                    }
                });

                room.on(RoomEvent.ParticipantConnected, (participant) => {
                    console.log('Participant connected:', participant.identity);
                });

                room.on(RoomEvent.ParticipantDisconnected, (participant) => {
                    console.log('Participant disconnected:', participant.identity);
                });

                // Connect to room
                await room.connect(LIVEKIT_URL, token);
                console.log('Room connection initiated');

                // Get user media
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        facingMode: 'user',
                    },
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                    },
                });

                // Create and publish video track
                localVideoTrack = await room.localParticipant.createCameraTrack({
                    resolution: { width: 1280, height: 720 },
                });
                await room.localParticipant.publishTrack(localVideoTrack, {
                    source: Track.Source.SOURCE_CAMERA,
                });

                // Attach local video
                localVideo.srcObject = stream;
                localVideo.srcObject.getVideoTracks().forEach(track => {
                    if (track !== localVideoTrack.mediaStreamTrack) {
                        track.stop();
                    }
                });

                // Create and publish audio track
                localAudioTrack = await room.localParticipant.createMicrophoneTrack();
                await room.localParticipant.publishTrack(localAudioTrack, {
                    source: Track.Source.SOURCE_MICROPHONE,
                });

                console.log('Published video and audio tracks');

            } catch (error) {
                console.error('Connection error:', error);
                updateStatus(`Error: ${error.message}`);
            }
        });

        // Disconnect from room
        disconnectBtn.addEventListener('click', async () => {
            if (room) {
                await room.disconnect();
            }
            cleanup();
        });

        // Toggle video
        toggleVideoBtn.addEventListener('click', async () => {
            if (localVideoTrack) {
                if (localVideoTrack.isMuted) {
                    await localVideoTrack.unmute();
                    toggleVideoBtn.textContent = 'Disable Video';
                } else {
                    await localVideoTrack.mute();
                    toggleVideoBtn.textContent = 'Enable Video';
                }
            }
        });

        // Toggle audio
        toggleAudioBtn.addEventListener('click', async () => {
            if (localAudioTrack) {
                if (localAudioTrack.isMuted) {
                    await localAudioTrack.unmute();
                    toggleAudioBtn.textContent = 'Mute Audio';
                } else {
                    await localAudioTrack.mute();
                    toggleAudioBtn.textContent = 'Unmute Audio';
                }
            }
        });

        // Display obstacle detection results
        function displayObstacleDetection(data) {
            const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();
            
            let html = `<div class="obstacle-item ${data.recommendation?.toLowerCase().includes('caution') ? 'high' : 'medium'}">`;
            html += `<strong>${timestamp}</strong><br>`;
            html += `<p>${data.recommendation || 'No recommendation'}</p>`;
            
            if (data.obstacles && data.obstacles.length > 0) {
                html += `<ul>`;
                data.obstacles.forEach(obstacle => {
                    html += `<li class="${obstacle.severity || 'low'}">`;
                    html += `<strong>${obstacle.type}</strong>: ${obstacle.description} `;
                    html += `(${obstacle.distance_estimate}, ${obstacle.severity})`;
                    html += `</li>`;
                });
                html += `</ul>`;
            }
            
            html += `</div>`;
            
            if (obstacleResults.querySelector('p')) {
                obstacleResults.innerHTML = html;
            } else {
                obstacleResults.insertAdjacentHTML('afterbegin', html);
            }
            
            // Keep only last 10 detections
            const items = obstacleResults.querySelectorAll('.obstacle-item');
            if (items.length > 10) {
                items[items.length - 1].remove();
            }
        }

        // Cleanup
        function cleanup() {
            if (localVideoTrack) {
                localVideoTrack.stop();
                localVideoTrack = null;
            }
            if (localAudioTrack) {
                localAudioTrack.stop();
                localAudioTrack = null;
            }
            if (localVideo.srcObject) {
                localVideo.srcObject.getTracks().forEach(track => track.stop());
                localVideo.srcObject = null;
            }
            if (remoteVideo.srcObject) {
                remoteVideo.srcObject.getTracks().forEach(track => track.stop());
                remoteVideo.srcObject = null;
            }
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (room) {
                room.disconnect();
            }
            cleanup();
        });
    </script>
</body>
</html>
```

### Option 2: React Example

For a React-based frontend, install the LiveKit client:

```bash
npm install livekit-client
```

Create a React component:

```tsx
import React, { useEffect, useRef, useState } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';

interface ObstacleDetection {
  obstacles: Array<{
    type: string;
    description: string;
    distance_estimate: string;
    severity: string;
  }>;
  recommendation: string;
  timestamp: number;
}

const LiveKitVideoTest: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [obstacles, setObstacles] = useState<ObstacleDetection[]>([]);
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const roomRef = useRef<Room | null>(null);

  const LIVEKIT_URL = 'wss://your-livekit-server.com';
  const API_BASE_URL = 'http://localhost:8000';
  const ROOM_NAME = `test-room-${Date.now()}`;
  const PARTICIPANT_IDENTITY = `user-${Date.now()}`;

  const getAccessToken = async (): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/api/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        room_name: ROOM_NAME,
        participant_identity: PARTICIPANT_IDENTITY,
        participant_name: 'Test User',
        ttl_seconds: 3600,
      }),
    });
    const data = await response.json();
    return data.token;
  };

  const connect = async () => {
    try {
      const token = await getAccessToken();
      const room = new Room();
      roomRef.current = room;

      room.on(RoomEvent.Connected, () => {
        console.log('Connected');
        setConnected(true);
      });

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === Track.Kind.Video || track.kind === Track.Kind.Audio) {
          const element = track.attach();
          if (remoteVideoRef.current) {
            remoteVideoRef.current.srcObject = new MediaStream([element]);
          }
        }
      });

      room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
        if (topic === 'obstacle_detection') {
          try {
            const data = JSON.parse(new TextDecoder().decode(payload)) as ObstacleDetection;
            setObstacles(prev => [data, ...prev].slice(0, 10));
          } catch (e) {
            console.error('Error parsing obstacle data:', e);
          }
        }
      });

      await room.connect(LIVEKIT_URL, token);

      // Get user media and publish tracks
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true,
      });

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      const videoTrack = await room.localParticipant.createCameraTrack({
        resolution: { width: 1280, height: 720 },
      });
      await room.localParticipant.publishTrack(videoTrack, {
        source: Track.Source.SOURCE_CAMERA,
      });

      const audioTrack = await room.localParticipant.createMicrophoneTrack();
      await room.localParticipant.publishTrack(audioTrack, {
        source: Track.Source.SOURCE_MICROPHONE,
      });
    } catch (error) {
      console.error('Connection error:', error);
    }
  };

  const disconnect = async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      setConnected(false);
    }
  };

  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  return (
    <div>
      <h1>LiveKit Agent Video Test</h1>
      <button onClick={connected ? disconnect : connect}>
        {connected ? 'Disconnect' : 'Connect'}
      </button>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div>
          <h2>Local Video</h2>
          <video ref={localVideoRef} autoPlay muted playsInline />
        </div>
        <div>
          <h2>Agent Audio</h2>
          <video ref={remoteVideoRef} autoPlay playsInline />
        </div>
      </div>
      <div>
        <h2>Obstacle Detections</h2>
        {obstacles.map((obs, idx) => (
          <div key={idx}>
            <p>{obs.recommendation}</p>
            <ul>
              {obs.obstacles.map((o, i) => (
                <li key={i}>{o.type}: {o.description}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LiveKitVideoTest;
```

## Testing Steps

1. **Start the Backend Services**:
   ```bash
   # Terminal 1: Start agent worker
   python agent.py dev

   # Terminal 2: Start FastAPI server
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Open the Frontend**:
   - For HTML: Open `test-frontend.html` in a browser (or serve via HTTP server)
   - For React: Start your React dev server

3. **Update Configuration**:
   - Update `LIVEKIT_URL` in the frontend code to match your LiveKit server
   - Update `API_BASE_URL` if your FastAPI server is on a different host/port

4. **Connect and Test**:
   - Click "Connect" button
   - Grant camera/microphone permissions when prompted
   - You should see:
     - Your local video feed
     - Agent audio responses (when you speak)
     - Obstacle detection results appearing in the results panel

## Expected Behavior

### Video Streaming
- Local video should appear immediately after connecting
- Video is automatically published to the room
- Agent receives video frames via LiveKit's native Live Video input

### Audio Interaction
- Speak into your microphone
- Agent processes speech via Voxstral STT
- Agent responds via Gemini Live Realtime
- Response is synthesized via ElevenLabs TTS
- You should hear the agent's voice through the remote video element

### Obstacle Detection
- Obstacle detection results appear in the results panel
- Results are published via DataChannel on topic `obstacle_detection`
- Each result includes:
  - Timestamp
  - List of detected obstacles with type, description, distance, severity
  - Navigation recommendation

## Troubleshooting

### Video Not Appearing
- Check browser console for errors
- Verify camera permissions are granted
- Check that `LIVEKIT_URL` is correct
- Ensure agent worker is running and connected

### No Audio Response
- Verify microphone permissions
- Check agent logs for STT/TTS errors
- Verify API keys (Mistral, Google, ElevenLabs) are correct
- Check browser console for connection errors

### No Obstacle Detection
- Verify video track is being published (check browser console)
- Check agent logs for vision processing errors
- Verify `GOOGLE_API_KEY` is valid
- Check DataChannel topic matches (`obstacle_detection`)

### Connection Errors
- Verify LiveKit server is accessible
- Check token generation endpoint is working (`/api/token`)
- Verify `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are correct
- Check network connectivity to LiveKit server

## Testing Different Scenarios

### Test 1: Basic Video Streaming
- Connect and verify video appears
- Move around to generate different video frames
- Check obstacle detection updates

### Test 2: Voice Interaction
- Speak clearly: "What obstacles do you see?"
- Wait for agent response
- Verify audio plays back

### Test 3: Obstacle Detection Accuracy
- Point camera at different objects (people, vehicles, obstacles)
- Verify detection results match what's in frame
- Check severity levels are appropriate

### Test 4: Multiple Participants
- Open multiple browser tabs/windows
- Connect each to the same room
- Verify each participant receives obstacle detections

### Test 5: Network Conditions
- Test with slow network (throttle in browser DevTools)
- Verify graceful degradation
- Check reconnection behavior

## Additional Resources

- [LiveKit JavaScript SDK Documentation](https://docs.livekit.io/client-sdk-js/)
- [LiveKit WebRTC Best Practices](https://docs.livekit.io/guides/client/)
- [Browser Media APIs](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)

