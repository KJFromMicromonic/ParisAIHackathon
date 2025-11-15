# LiveKit JavaScript Client SDK

## Overview

The LiveKit JavaScript/TypeScript client SDK enables you to add realtime video, audio, and data features to your JavaScript/TypeScript applications. By connecting to LiveKit Cloud or a self-hosted server, you can quickly build applications such as multi-modal AI, live streaming, or video calls with just a few lines of code.

## Installation

### NPM

```shell
npm install livekit-client --save
```

### Yarn

```shell
yarn add livekit-client
```

### Minified JS

To use the SDK without a package manager, you can include it with a script tag:

```html
<script src="https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js"></script>
```

The module will be exported under `LivekitClient` in the global namespace.

## Connecting to a Room

Rooms are identified by their name, which can be any unique string. The room itself is created automatically when the first participant joins, and is closed when the last participant leaves.

You must use a participant identity when you connect to a room. This identity can be any string, but must be unique to each participant.

Connecting to a room always requires two parameters:

- `wsUrl`: The WebSocket URL of your LiveKit server.
  - LiveKit Cloud users can find theirs on the [Project Settings page](https://cloud.livekit.io/projects/p_/settings/project).
  - Self-hosted users can use `ws://localhost:7880` while developing.
- `token`: A unique [access token](https://docs.livekit.io/concepts/authentication/) which each participant must use to connect.

### Basic Connection Example

```typescript
import { Room } from 'livekit-client';

const room = new Room({
  // automatically manage subscribed video quality
  adaptiveStream: true,

  // optimize publishing bandwidth and CPU for published tracks
  dynacast: true,

  // default capture settings
  videoCaptureDefaults: {
    resolution: VideoPresets.h720.resolution,
  },
});

// pre-warm connection, this can be called as early as your page is loaded
room.prepareConnection(wsUrl, token);

// connect to room
await room.connect(wsUrl, token);
console.log('connected to room', room.name);
```

### Using React Components

```typescript
import { LiveKitRoom } from '@livekit/components-react';

<LiveKitRoom audio={true} video={true} token={token} serverUrl={wsUrl}>
  {/* your components here */}
</LiveKitRoom>
```

## Publishing Audio and Video

### Enable Camera and Microphone

```typescript
// Enables the camera and publishes it to a new video track
room.localParticipant.setCameraEnabled(true);

// Enables the microphone and publishes it to a new audio track
room.localParticipant.setMicrophoneEnabled(true);
```

### Enable Camera and Microphone Together

```typescript
// Turn on the local user's camera and mic, this may trigger a browser prompt
await room.localParticipant.enableCameraAndMicrophone();
```

### Screen Sharing

```typescript
// Start sharing the user's screen
await room.localParticipant.setScreenShareEnabled(true);
```

## Subscribing to Tracks

### Setting Up Event Listeners

```typescript
import {
  RoomEvent,
  RemoteTrack,
  RemoteTrackPublication,
  RemoteParticipant,
  Track,
} from 'livekit-client';

room
  .on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
  .on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
  .on(RoomEvent.Disconnected, handleDisconnect);

function handleTrackSubscribed(
  track: RemoteTrack,
  publication: RemoteTrackPublication,
  participant: RemoteParticipant,
) {
  if (track.kind === Track.Kind.Video || track.kind === Track.Kind.Audio) {
    // attach it to a new HTMLVideoElement or HTMLAudioElement
    const element = track.attach();
    parentElement.appendChild(element);
  }
}

function handleTrackUnsubscribed(
  track: RemoteTrack,
  publication: RemoteTrackPublication,
  participant: RemoteParticipant,
) {
  // remove tracks from all attached elements
  track.detach();
}

function handleDisconnect() {
  console.log('disconnected from room');
}
```

### Accessing Remote Participant Tracks

```typescript
// get a RemoteParticipant by their identity
const participant = room.remoteParticipants.get('participant-identity');
if (participant) {
  // if the other user has enabled their camera, attach it to a new HTMLVideoElement
  if (participant.isCameraEnabled) {
    const publication = participant.getTrackPublication(Track.Source.Camera);
    if (publication?.isSubscribed) {
      const videoElement = publication.videoTrack?.attach();
      // do something with the element
    }
  }
}
```

## Device Management

### Listing Devices

```typescript
// list all microphone devices
const devices = await Room.getLocalDevices('audioinput');

// list all camera devices
const cameras = await Room.getLocalDevices('videoinput');
```

### Switching Devices

```typescript
// select a device
const device = devices[devices.length - 1];

// in the current room, switch to the selected device
await room.switchActiveDevice('audioinput', device.deviceId);
```

### Handling Device Failures

```typescript
import { RoomEvent, MediaDeviceFailure } from 'livekit-client';

room.on(RoomEvent.MediaDevicesError, (error) => {
  const failure = MediaDeviceFailure.getFailure(error);
  
  switch (failure) {
    case MediaDeviceFailure.PermissionDenied:
      // the user disallowed capturing devices
      break;
    case MediaDeviceFailure.NotFound:
      // the particular device isn't available
      break;
    case MediaDeviceFailure.DeviceInUse:
      // device is in use by another process (happens on Windows)
      break;
  }
});
```

## Audio Playback

Browsers can be restrictive with regards to audio playback that is not initiated by user interaction. LiveKit will attempt to autoplay all audio tracks when you attach them to audio elements. However, if that fails, we'll notify you via `RoomEvent.AudioPlaybackStatusChanged`.

```typescript
room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
  if (!room.canPlaybackAudio) {
    // UI is necessary.
    button.onclick = () => {
      // startAudio *must* be called in a click/tap handler.
      room.startAudio().then(() => {
        // successful, UI can be removed now
        button.remove();
      });
    }
  }
});
```

## RPC (Remote Procedure Calls)

RPC allows you to perform predefined method calls from one participant to another. This feature is especially powerful when used with Agents, for instance to forward LLM function calls to your client application.

### Registering an RPC Method

```typescript
room.localParticipant?.registerRpcMethod(
  // method name - can be any string that makes sense for your application
  'greet',

  // method handler - will be called when the method is invoked by a RemoteParticipant
  async (data: RpcInvocationData) => {
    console.log(`Received greeting from ${data.callerIdentity}: ${data.payload}`);
    return `Hello, ${data.callerIdentity}!`;
  },
);
```

### Performing an RPC Request

```typescript
try {
  const response = await room.localParticipant!.performRpc({
    destinationIdentity: 'recipient-identity',
    method: 'greet',
    payload: 'Hello from RPC!',
  });
  console.log('RPC response:', response);
} catch (error) {
  console.error('RPC call failed:', error);
}
```

## Events

LiveKit emits various events on the `Room` object. Here are some of the most important ones:

### Room Events

- `ParticipantConnected`: A RemoteParticipant joins after the local participant
- `ParticipantDisconnected`: A RemoteParticipant leaves
- `TrackSubscribed`: The LocalParticipant has subscribed to a track
- `TrackUnsubscribed`: A previously subscribed track has been unsubscribed
- `TrackMuted`: A track was muted
- `TrackUnmuted`: A track was unmuted
- `Disconnected`: Disconnected from room
- `Reconnecting`: The connection to the server has been interrupted
- `Reconnected`: Reconnection has been successful
- `DataReceived`: Data received from another participant or server

### Example Event Handling

```typescript
room
  .on(RoomEvent.ParticipantConnected, (participant) => {
    console.log('Participant connected:', participant.identity);
  })
  .on(RoomEvent.ParticipantDisconnected, (participant) => {
    console.log('Participant disconnected:', participant.identity);
  })
  .on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
    console.log('Track subscribed:', track.kind, 'from', participant.identity);
  })
  .on(RoomEvent.DataReceived, (payload, participant) => {
    console.log('Data received:', payload, 'from', participant?.identity);
  });
```

## Disconnection

Call `Room.disconnect()` to leave the room:

```typescript
await room.disconnect();
```

If you terminate the application without calling `disconnect()`, your participant disappears after 15 seconds.

**Note:** On some platforms, including JavaScript, `Room.disconnect` is called automatically when the application exits.

## Connection Reliability

LiveKit enables reliable connectivity in a wide variety of network conditions. It tries the following WebRTC connection types in descending order:

1. ICE over UDP: ideal connection type, used in majority of conditions
2. TURN with UDP (3478): used when ICE/UDP is unreachable
3. ICE over TCP: used when network disallows UDP (i.e. over VPN or corporate firewalls)
4. TURN with TLS: used when firewall only allows outbound TLS connections

### Network Changes and Reconnection

When network changes occur, LiveKit will attempt to resume the connection automatically. It reconnects to the signaling WebSocket and initiates an ICE restart for the WebRTC connection.

The reconnection sequence:

1. `ParticipantDisconnected` fired for other participants in the room
2. If there are tracks unpublished, you will receive `LocalTrackUnpublished` for them
3. Emits `Reconnecting`
4. Performs full reconnect
5. Emits `Reconnected`
6. For everyone currently in the room, you will receive `ParticipantConnected`
7. Local tracks are republished, emitting `LocalTrackPublished` events

## Logging

This library uses [loglevel](https://github.com/pimterry/loglevel) for its internal logs. You can change the effective log level:

```typescript
import { setLogLevel, LogLevel } from 'livekit-client';

setLogLevel(LogLevel.debug);
```

You can also hook into the logs:

```typescript
import { setLogExtension } from 'livekit-client';

setLogExtension((level: LogLevel, msg: string, context: object) => {
  const enhancedContext = { ...context, timeStamp: Date.now() };
  if (level >= LogLevel.debug) {
    console.log(level, msg, enhancedContext);
  }
});
```

## Browser Support

| Browser | Desktop OS | Mobile OS |
| --- | --- | --- |
| Chrome | Windows, macOS, Linux | Android |
| Firefox | Windows, macOS, Linux | Android |
| Safari | macOS | iOS |
| Edge (Chromium) | Windows, macOS |  |

## Additional Resources

- [SDK Reference](https://docs.livekit.io/reference/client-sdk-js/)
- [GitHub Repository](https://github.com/livekit/client-sdk-js)
- [Connecting to LiveKit](https://docs.livekit.io/home/client/connect/)
- [Publishing Tracks](https://docs.livekit.io/home/client/tracks/publish/)
- [Handling Events](https://docs.livekit.io/home/client/events/)
- [React Components](https://docs.livekit.io/reference/components/react/)

