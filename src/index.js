/**
 * LiveKit Video and Audio Streaming Client
 * 
 * This client connects to the LiveKit server, captures video/audio from the user's
 * device, and streams it to the room. It follows LiveKit's authentication protocol
 * by fetching tokens from the backend API.
 */

import { Room, RoomEvent, Track, createLocalVideoTrack, createLocalAudioTrack } from 'livekit-client';

// Configuration - Update these to match your setup
const CONFIG = {
  // LiveKit server WebSocket URL (from .env: LIVEKIT_URL)
  LIVEKIT_URL: 'ws://localhost:7880',
  
  // Backend API URL for token generation (from .env: API_HOST and API_PORT)
  API_BASE_URL: 'http://localhost:8000',
  
  // Default room name (will be auto-generated if not provided)
  DEFAULT_ROOM_NAME: null,
  
  // Video constraints
  VIDEO_CONSTRAINTS: {
    width: { ideal: 1280 },
    height: { ideal: 720 },
    facingMode: 'user', // 'user' for front camera, 'environment' for back camera
  },
  
  // Audio constraints
  AUDIO_CONSTRAINTS: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  },
};

/**
 * Fetches a LiveKit access token from the backend API.
 * 
 * @param {string} roomName - Name of the room to join
 * @param {string} participantIdentity - Unique identity for the participant
 * @param {string} participantName - Display name for the participant
 * @returns {Promise<string>} JWT access token
 */
async function fetchAccessToken(roomName, participantIdentity, participantName) {
  const response = await fetch(`${CONFIG.API_BASE_URL}/api/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      room_name: roomName,
      participant_identity: participantIdentity,
      participant_name: participantName,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch access token: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  return data.token;
}

/**
 * Generates a unique participant identity.
 * 
 * @returns {string} Unique participant identity
 */
function generateParticipantIdentity() {
  return `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Generates a unique room name if not provided.
 * 
 * @param {string|null} roomName - Optional room name
 * @returns {string} Room name
 */
function generateRoomName(roomName) {
  return roomName || `room-${Date.now()}`;
}

/**
 * Main application class for managing LiveKit room connection and media streaming.
 */
class LiveKitStreamClient {
  constructor() {
    this.room = null;
    this.localVideoTrack = null;
    this.localAudioTrack = null;
    this.isConnected = false;
    
    // UI elements
    this.elements = {
      connectBtn: document.getElementById('connectBtn'),
      disconnectBtn: document.getElementById('disconnectBtn'),
      toggleVideoBtn: document.getElementById('toggleVideoBtn'),
      toggleAudioBtn: document.getElementById('toggleAudioBtn'),
      statusText: document.getElementById('statusText'),
      localVideo: document.getElementById('localVideo'),
      remoteVideo: document.getElementById('remoteVideo'),
      roomNameInput: document.getElementById('roomName'),
      participantNameInput: document.getElementById('participantName'),
    };

    this.setupEventListeners();
  }

  /**
   * Sets up event listeners for UI controls.
   */
  setupEventListeners() {
    this.elements.connectBtn?.addEventListener('click', () => this.connect());
    this.elements.disconnectBtn?.addEventListener('click', () => this.disconnect());
    this.elements.toggleVideoBtn?.addEventListener('click', () => this.toggleVideo());
    this.elements.toggleAudioBtn?.addEventListener('click', () => this.toggleAudio());
  }

  /**
   * Updates the UI status display.
   * 
   * @param {string} message - Status message
   * @param {boolean} connected - Whether connected to room
   */
  updateStatus(message, connected = false) {
    if (this.elements.statusText) {
      this.elements.statusText.textContent = message;
    }
    
    this.isConnected = connected;
    
    // Update button states
    if (this.elements.connectBtn) {
      this.elements.connectBtn.disabled = connected;
    }
    if (this.elements.disconnectBtn) {
      this.elements.disconnectBtn.disabled = !connected;
    }
    if (this.elements.toggleVideoBtn) {
      this.elements.toggleVideoBtn.disabled = !connected;
    }
    if (this.elements.toggleAudioBtn) {
      this.elements.toggleAudioBtn.disabled = !connected;
    }
  }

  /**
   * Connects to the LiveKit room and starts streaming video/audio.
   */
  async connect() {
    try {
      this.updateStatus('Connecting...', false);

      // Get room name and participant name from UI or generate defaults
      const roomName = generateRoomName(
        this.elements.roomNameInput?.value.trim() || CONFIG.DEFAULT_ROOM_NAME
      );
      const participantIdentity = generateParticipantIdentity();
      const participantName = 
        this.elements.participantNameInput?.value.trim() || participantIdentity;

      console.log('Connecting to room:', roomName);
      console.log('Participant identity:', participantIdentity);

      // Fetch access token from backend
      const token = await fetchAccessToken(roomName, participantIdentity, participantName);
      console.log('Access token received');

      // Create room instance
      this.room = new Room({
        adaptiveStream: true,
        dynacast: true,
        publishDefaults: {
          videoCodec: 'vp8',
          videoResolution: { width: 1280, height: 720 },
        },
      });

      // Set up room event handlers
      this.setupRoomEventHandlers();

      // Connect to room
      await this.room.connect(CONFIG.LIVEKIT_URL, token);
      console.log('Connected to room:', this.room.name);

      // Create and publish video track
      this.localVideoTrack = await createLocalVideoTrack({
        resolution: { width: 1280, height: 720 },
        facingMode: CONFIG.VIDEO_CONSTRAINTS.facingMode,
      });
      
      await this.room.localParticipant.publishTrack(this.localVideoTrack, {
        source: Track.Source.SOURCE_CAMERA,
      });

      // Attach local video track to video element
      if (this.elements.localVideo) {
        this.localVideoTrack.attach(this.elements.localVideo);
      }

      // Create and publish audio track
      this.localAudioTrack = await createLocalAudioTrack({
        echoCancellation: CONFIG.AUDIO_CONSTRAINTS.echoCancellation,
        noiseSuppression: CONFIG.AUDIO_CONSTRAINTS.noiseSuppression,
        autoGainControl: CONFIG.AUDIO_CONSTRAINTS.autoGainControl,
      });
      
      await this.room.localParticipant.publishTrack(this.localAudioTrack, {
        source: Track.Source.SOURCE_MICROPHONE,
      });

      console.log('Published video and audio tracks');
      this.updateStatus(`Connected to room: ${roomName}`, true);

    } catch (error) {
      console.error('Connection error:', error);
      this.updateStatus(`Error: ${error.message}`, false);
      alert(`Connection failed: ${error.message}\n\nPlease check:\n1. LiveKit server is running\n2. API server is running\n3. URLs are correct\n4. Camera/microphone permissions are granted`);
    }
  }

  /**
   * Sets up event handlers for room events.
   */
  setupRoomEventHandlers() {
    if (!this.room) return;

    // Handle connection events
    this.room.on(RoomEvent.Connected, () => {
      console.log('Room connected');
    });

    this.room.on(RoomEvent.Disconnected, (reason) => {
      console.log('Room disconnected:', reason);
      this.updateStatus('Disconnected', false);
      this.cleanup();
    });

    // Handle track subscriptions (remote participants)
    this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log('Track subscribed:', track.kind, 'from', participant.identity);
      
      if (track.kind === Track.Kind.Video || track.kind === Track.Kind.Audio) {
        const element = track.attach();
        
        if (this.elements.remoteVideo) {
          if (this.elements.remoteVideo.srcObject) {
            // Add track to existing stream
            const stream = this.elements.remoteVideo.srcObject;
            stream.addTrack(element);
          } else {
            // Create new stream
            this.elements.remoteVideo.srcObject = new MediaStream([element]);
          }
        }
      }
    });

    this.room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      console.log('Track unsubscribed:', track.kind);
      track.detach();
    });

    // Handle data channel messages (for obstacle detection)
    this.room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
      console.log('Data received:', topic, 'from', participant?.identity);
      
      if (topic === 'obstacle_detection') {
        try {
          const data = JSON.parse(new TextDecoder().decode(payload));
          this.handleObstacleDetection(data);
        } catch (e) {
          console.error('Error parsing obstacle detection data:', e);
        }
      }
    });

    // Handle participant events
    this.room.on(RoomEvent.ParticipantConnected, (participant) => {
      console.log('Participant connected:', participant.identity);
      if (participant.identity.startsWith('agent-')) {
        this.updateStatus(`Agent connected to room: ${this.room.name}`, true);
      }
    });

    this.room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      console.log('Participant disconnected:', participant.identity);
    });
  }

  /**
   * Handles obstacle detection data received via DataChannel.
   * 
   * @param {Object} data - Obstacle detection data
   */
  handleObstacleDetection(data) {
    console.log('Obstacle detection:', data);
    // You can extend this to display obstacle detection results in the UI
    // For example, update a results panel or show notifications
  }

  /**
   * Toggles video track on/off.
   */
  async toggleVideo() {
    if (!this.localVideoTrack) return;

    try {
      if (this.localVideoTrack.isMuted) {
        await this.localVideoTrack.unmute();
        if (this.elements.toggleVideoBtn) {
          this.elements.toggleVideoBtn.textContent = '📹 Disable Video';
        }
      } else {
        await this.localVideoTrack.mute();
        if (this.elements.toggleVideoBtn) {
          this.elements.toggleVideoBtn.textContent = '📹 Enable Video';
        }
      }
    } catch (error) {
      console.error('Error toggling video:', error);
    }
  }

  /**
   * Toggles audio track on/off.
   */
  async toggleAudio() {
    if (!this.localAudioTrack) return;

    try {
      if (this.localAudioTrack.isMuted) {
        await this.localAudioTrack.unmute();
        if (this.elements.toggleAudioBtn) {
          this.elements.toggleAudioBtn.textContent = '🎤 Mute Audio';
        }
      } else {
        await this.localAudioTrack.mute();
        if (this.elements.toggleAudioBtn) {
          this.elements.toggleAudioBtn.textContent = '🎤 Unmute Audio';
        }
      }
    } catch (error) {
      console.error('Error toggling audio:', error);
    }
  }

  /**
   * Disconnects from the room and cleans up resources.
   */
  async disconnect() {
    if (this.room) {
      await this.room.disconnect();
    }
    this.cleanup();
    this.updateStatus('Disconnected', false);
  }

  /**
   * Cleans up all tracks and resources.
   */
  cleanup() {
    if (this.localVideoTrack) {
      this.localVideoTrack.stop();
      this.localVideoTrack.detach();
      this.localVideoTrack = null;
    }

    if (this.localAudioTrack) {
      this.localAudioTrack.stop();
      this.localAudioTrack.detach();
      this.localAudioTrack = null;
    }

    if (this.elements.localVideo?.srcObject) {
      this.elements.localVideo.srcObject.getTracks().forEach(track => track.stop());
      this.elements.localVideo.srcObject = null;
    }

    if (this.elements.remoteVideo?.srcObject) {
      this.elements.remoteVideo.srcObject.getTracks().forEach(track => track.stop());
      this.elements.remoteVideo.srcObject = null;
    }
  }
}

// Initialize the client when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('LiveKit Stream Client initialized');
  window.liveKitClient = new LiveKitStreamClient();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.liveKitClient) {
    window.liveKitClient.disconnect();
  }
});

