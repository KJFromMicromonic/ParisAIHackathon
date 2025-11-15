# LiveKit Agents Vision

Enhance your agent with visual understanding from images and live video.

## Overview

LiveKit Agents has tools for adding raw images from disk, the network, or uploaded directly from your frontend into your agent's chat context to utilize the vision features of your LLM. Additionally, you can use live video either with sampled frames in an STT-LLM-TTS pipeline model or true video input with a realtime model such as Gemini Live.

This guide includes an overview of the vision features and code samples for each use case.

## Images

The agent's chat context supports images as well as text. You can add as many images as you want to the chat context, but keep in mind that larger context windows contribute to slow response times.

To add an image to the chat context, create an `ImageContent` object and include it in a chat message. The image content can be a base 64 data URL, an external URL, or a frame from a video track.

### Load into Initial Context

The following example shows an agent initialized with an image at startup. This example uses an external URL, but you can modify it to load a local file using a base 64 data URL instead:

**Python:**

```python
from livekit.agents import AgentSession, ChatContext, ImageContent

async def entrypoint(ctx: JobContext):
    # ctx.connect, etc.
    
    session = AgentSession(
        # ... stt, tts, llm, etc.
    )
    
    initial_ctx = ChatContext()
    initial_ctx.add_message(
        role="user",
        content=[
            "Here is a picture of me", 
            ImageContent(image="https://example.com/image.jpg")
        ],
    )
    
    await session.start(
        room=ctx.room,
        agent=Agent(chat_ctx=initial_ctx,),
        # ... room_input_options, etc.
    )
```

**Note:** Not every LLM provider supports external image URLs. Consult their documentation for details.

### Upload from Frontend

To upload an image from your frontend app, use the `sendFile` method of the LiveKit SDK. Add a byte stream handler to your agent to receive the image data and add it to the chat context. Here is a simple agent capable of receiving images from the user on the byte stream topic `"images"`:

**Python:**

```python
import asyncio
import base64
from livekit.agents import Agent, ImageContent
from livekit.agents import get_job_context
import livekit.rtc as rtc

class Assistant(Agent):
    def __init__(self) -> None:
        self._tasks = []  # Prevent garbage collection of running tasks
        super().__init__(instructions="You are a helpful voice AI assistant.")
    
    async def on_enter(self):
        def _image_received_handler(reader, participant_identity):
            task = asyncio.create_task(
                self._image_received(reader, participant_identity)
            )
            self._tasks.append(task)
            task.add_done_callback(lambda t: self._tasks.remove(t))
        
        # Add the handler when the agent joins
        get_job_context().room.register_byte_stream_handler("images", _image_received_handler)
    
    async def _image_received(self, reader, participant_identity):
        image_bytes = bytes()
        async for chunk in reader:
            image_bytes += chunk
        
        chat_ctx = self.chat_ctx.copy()
        
        # Encode the image to base64 and add it to the chat context
        chat_ctx.add_message(
            role="user",
            content=[
                ImageContent(
                    image=f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                )
            ],
        )
        await self.update_chat_ctx(chat_ctx)
```

### Sample Video Frames

LLMs can process video in the form of still images, but many LLMs are not trained for this use case and can produce suboptimal results in understanding motion and other changes through a video feed. Realtime models, like Gemini Live, are trained on video and you can enable live video input for automatic support.

If you are using an STT-LLM-TTS pipeline, you can still work with video by sampling the video track at suitable times. For instance, in the following example the agent always includes the latest video frame on each conversation turn from the user. This provides the model with additional context without overwhelming it with data or expecting it to interpret many sequential frames at a time:

**Python:**

```python
import asyncio
from livekit.agents import Agent, ImageContent
from livekit.agents import get_job_context
import livekit.rtc as rtc

class Assistant(Agent):
    def __init__(self) -> None:
        self._latest_frame = None
        self._video_stream = None
        self._tasks = []
        super().__init__(instructions="You are a helpful voice AI assistant.")
    
    async def on_enter(self):
        room = get_job_context().room
        
        # Find the first video track (if any) from the remote participant
        remote_participant = list(room.remote_participants.values())[0]
        video_tracks = [
            publication.track 
            for publication in list(remote_participant.track_publications.values()) 
            if publication.track.kind == rtc.TrackKind.KIND_VIDEO
        ]
        
        if video_tracks:
            self._create_video_stream(video_tracks[0])
        
        # Watch for new video tracks not yet published
        @room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.RemoteTrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)
    
    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        # Add the latest video frame, if any, to the new message
        if self._latest_frame:
            new_message.content.append(ImageContent(image=self._latest_frame))
            self._latest_frame = None
    
    # Helper method to buffer the latest video frame from the user's track
    def _create_video_stream(self, track: rtc.Track):
        # Close any existing stream (we only want one at a time)
        if self._video_stream is not None:
            self._video_stream.close()
        
        # Create a new stream to receive frames
        self._video_stream = rtc.VideoStream(track)
        
        async def read_stream():
            async for event in self._video_stream:
                # Store the latest frame for use later
                self._latest_frame = event.frame
        
        # Store the async task
        task = asyncio.create_task(read_stream())
        task.add_done_callback(lambda t: self._tasks.remove(t))
        self._tasks.append(task)
```

#### Video Frame Encoding

By default, the `ImageContent` encodes video frames as JPEG at their native size. To adjust the size of the encoded frames, set the `inference_width` and `inference_height` parameters. Each frame is resized to fit within the provided dimensions while maintaining the original aspect ratio. For more control, use the `encode` method of the `livekit.agents.utils.images` module and pass the result as a data URL:

**Python:**

```python
import base64
from livekit.agents.utils.images import encode, EncodeOptions, ResizeOptions
from livekit.agents import ImageContent

image_bytes = encode(
    event.frame,
    EncodeOptions(
        format="PNG",
        resize_options=ResizeOptions(
            width=512, 
            height=512, 
            strategy="scale_aspect_fit"
        )
    )
)

image_content = ImageContent(
    image=f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
)
```

### Inference Detail

If your LLM provider supports it, you can set the `inference_detail` parameter to `"high"` or `"low"` to control the token usage and inference quality applied. The default is `"auto"`, which uses the provider's default.

## Live Video

**ONLY Available in Python**

**Supported models:** Live video input requires a realtime model with video support, such as Gemini Live or the OpenAI Realtime API.

Set the `video_enabled` parameter to `True` in `RoomInputOptions` to enable live video input. Your agent automatically receives frames from the user's camera or screen sharing tracks, if available. Only the single most recently published video track is used.

By default the agent samples one frame per second while the user speaks, and one frame every three seconds otherwise. Each frame is fit into 1024x1024 and encoded to JPEG. To override the frame rate, set `video_sampler` on the `AgentSession` with a custom instance.

Video input is passive and has no effect on turn detection. To leverage live video input in a non-conversational context, use manual turn control and trigger LLM responses or tool calls on a timer or other schedule.

The following example shows how to add Gemini Live vision to your voice AI quickstart agent:

**Python:**

```python
from livekit.agents import AgentSession, RoomInputOptions
from livekit.plugins import google

class VideoAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant with live video input from your user.",
            llm=google.realtime.RealtimeModel(
                voice="Puck",
                temperature=0.8,
            ),
        )

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    
    await session.start(
        agent=VideoAssistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            # ... noise_cancellation, etc.
        ),
    )
```

## Additional Resources

The following documentation and examples can help you get started with vision in LiveKit Agents:

- [Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/) - Use the quickstart as a starting base for adding vision code
- [Byte streams](https://docs.livekit.io/agents/build/workflows/#byte-streams) - Send images from your frontend to your agent with byte streams
- [RoomIO](https://docs.livekit.io/agents/build/workflows/#roomio) - Learn more about RoomIO and how it manages tracks
- [Vision Assistant](https://github.com/livekit-examples/python-agents-examples/tree/main/vision-assistant) - A voice AI agent with video input powered by Gemini Live
- [Camera and microphone](https://docs.livekit.io/home/client/tracks/publish/) - Publish camera and microphone tracks from your frontend
- [Screen sharing](https://docs.livekit.io/home/client/tracks/publish/#screen-sharing) - Publish screen sharing tracks from your frontend

## Source

This documentation is based on the official [LiveKit Agents Vision documentation](https://docs.livekit.io/agents/build/vision).

