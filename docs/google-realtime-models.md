# Google Realtime Models (Gemini Live API)

## Overview

Google's [Gemini Live API](https://ai.google.dev/gemini-api/docs/live) enables low-latency, two-way interactions that use text, audio, and video input, with audio and text output. LiveKit's Google plugin includes a `RealtimeModel` class that allows you to use this API to create agents with natural, human-like voice conversations.

## Quick Reference

### Installation

Install the Google plugin:

**Python:**
```shell
uv add "livekit-agents[google]~=1.2"
```

**Node.js:**
```shell
pnpm add "@livekit/agents-plugin-google@1.x"
```

### Authentication

The Google plugin requires authentication based on your chosen service:

- For Vertex AI, you must set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the service account key file. For more information about mounting files as secrets when deploying to LiveKit Cloud, see [File-mounted secrets](https://docs.livekit.io/agents/ops/deployment/secrets/#file-mounted-secrets).
- For the Google Gemini API, set the `GOOGLE_API_KEY` environment variable.

### Usage

Use the Gemini Live API within an `AgentSession`. For example, you can use it in the [Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/).

**Python:**
```python
from livekit.plugins import google

session = AgentSession(
    llm=google.realtime.RealtimeModel(
        model="gemini-2.0-flash-exp",
        voice="Puck",
        temperature=0.8,
        instructions="You are a helpful assistant",
    ),
)
```

**Node.js:**
```typescript
import * as google from '@livekit/agents-plugin-google';

const session = new voice.AgentSession({
   llm: new google.realtime.RealtimeModel({
      model: "gemini-2.5-flash-native-audio-preview-09-2025",
      voice: "Puck",
      temperature: 0.8,
      instructions: "You are a helpful assistant",
   }),
});
```

## Parameters

This section describes some of the available parameters. For a complete reference of all available parameters, see the plugin reference links in the Additional resources section.

### instructions
- **Type:** `string`
- **Optional:** Yes
- **Description:** System instructions to better control the model's output and specify tone and sentiment of responses. To learn more, see [System instructions](https://ai.google.dev/gemini-api/docs/live#system-instructions).

### model
- **Type:** `LiveAPIModels | string`
- **Required:** Yes
- **Default:** `gemini-2.0-flash-exp`
- **Description:** Live API model to use.

### api_key
- **Type:** `string`
- **Required:** Yes
- **Environment Variable:** `GOOGLE_API_KEY`
- **Description:** Google Gemini API key.

### voice
- **Type:** `Voice | string`
- **Required:** Yes
- **Default:** `Puck`
- **Description:** Name of the Gemini Live API voice. For a full list, see [Voices](https://ai.google.dev/gemini-api/docs/live#change-voices).

### modalities
- **Type:** `list[Modality]`
- **Optional:** Yes
- **Default:** `["AUDIO"]`
- **Description:** List of response modalities to use. Set to `["TEXT"]` to use the model in text-only mode with a [separate TTS plugin](https://docs.livekit.io/agents/models/realtime/plugins/gemini/#separate-tts).

### vertexai
- **Type:** `boolean`
- **Required:** Yes
- **Default:** `false`
- **Description:** If set to true, use Vertex AI.

### project
- **Type:** `string`
- **Optional:** Yes
- **Environment Variable:** `GOOGLE_CLOUD_PROJECT`
- **Description:** Google Cloud project ID to use for the API (if `vertextai=True`). By default, it uses the project in the serviceaccount key file (set using the `GOOGLE_APPLICATION_CREDENTIALS` environment variable).

### location
- **Type:** `string`
- **Optional:** Yes
- **Environment Variable:** `GOOGLE_CLOUD_LOCATION`
- **Description:** Google Cloud location to use for the API (if `vertextai=True`). By default, it uses the location from the serviceaccount key file or `us-central1`.

### thinking_config
- **Type:** `ThinkingConfig`
- **Optional:** Yes
- **Description:** Configuration for the model's thinking mode, if supported. For more information, see [Thinking](https://docs.livekit.io/agents/models/realtime/plugins/gemini/#thinking).

### enable_affective_dialog
- **Type:** `boolean`
- **Optional:** Yes
- **Default:** `false`
- **Description:** Enable affective dialog on supported native audio models. For more information, see [Affective dialog](https://ai.google.dev/gemini-api/docs/live-guide#affective-dialog).

### proactivity
- **Type:** `boolean`
- **Optional:** Yes
- **Default:** `false`
- **Description:** Enable proactive audio, where the model can decide not to respond to certain inputs. Requires a native audio model. For more information, see [Proactive audio](https://ai.google.dev/gemini-api/docs/live-guide#proactive-audio).

### _gemini_tools
- **Type:** `list[GeminiTool]`
- **Optional:** Yes
- **Description:** List of built-in Google tools, such as Google Search. For more information, see [Gemini tools](https://docs.livekit.io/agents/models/realtime/plugins/gemini/#gemini-tools).

## Gemini Tools

**Experimental feature**

This integration is experimental and may change in a future SDK release.

The `_gemini_tools` parameter allows you to use built-in Google tools with the Gemini model. For example, you can use this feature to implement [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/live-tools#google-search):

**Python:**
```python
from google.genai import types

session = AgentSession(
    llm=google.realtime.RealtimeModel(
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        _gemini_tools=[types.GoogleSearch()],
    )
)
```

**Node.js:**
```typescript
import * as google from '@livekit/agents-plugin-google';

const session = new voice.AgentSession({
   llm: new google.realtime.RealtimeModel({
      model: "gemini-2.0-flash-exp",
      geminiTools: [new google.types.GoogleSearch()],
   }),
});
```

## Turn Detection

The Gemini Live API includes built-in VAD-based turn detection, enabled by default. To use LiveKit's turn detection model instead, configure the model to disable automatic activity detection. A separate streaming STT model is required in order to use LiveKit's turn detection model.

**Python:**
```python
from google.genai import types
from livekit.agents import AgentSession
from livekit.plugins.turn_detector.multilingual import MultilingualModel

session = AgentSession(
   turn_detection=MultilingualModel(),
   llm=google.realtime.RealtimeModel(
      realtime_input_config=types.RealtimeInputConfig(
      automatic_activity_detection=types.AutomaticActivityDetection(
         disabled=True,
      ),
   ),
   input_audio_transcription=None,
   stt="assemblyai/universal-streaming",
)
```

**Node.js:**
```typescript
import * as google from '@livekit/agents-plugin-google';
import * as livekit from '@livekit/agents-plugin-livekit';

const session = new voice.AgentSession({
   turnDetection: new MultilingualModel(),
   llm: new google.realtime.RealtimeModel({
      model: "gemini-2.0-flash-exp",
      realtimeInputConfig: {
         automaticActivityDetection: {
            disabled: true,
         },
      },
   }),
   stt: "assemblyai/universal-streaming",
   turnDetection: new livekit.turnDetector.MultilingualModel(),
});
```

## Thinking

The latest model, `gemini-2.5-flash-native-audio-preview-09-2025`, supports thinking. You can configure its behavior with the `thinking_config` parameter.

By default, the model's thoughts are forwarded like other transcripts. To disable this, set `include_thoughts=False`:

```python
from google.genai import types

# ...

session = AgentSession(
    llm=google.realtime.RealtimeModel(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
        ),
    ),
)
```

For other available parameters, such as `thinking_budget`, see the [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking).

## Usage with Separate TTS

To use the Gemini Live API with a different [TTS instance](https://docs.livekit.io/agents/models/tts/), configure it with a text-only response modality and include a TTS instance in your `AgentSession` configuration. This configuration allows you to gain the benefits of realtime speech comprehension while maintaining complete control over the speech output.

**Python:**
```python
from google.genai.types import Modality

session = AgentSession(
    llm=google.realtime.RealtimeModel(modalities=[Modality.TEXT]),
    tts="cartesia/sonic-3",
)
```

**Node.js:**
```typescript
import * as google from '@livekit/agents-plugin-google';

const session = new voice.AgentSession({
   llm: new google.realtime.RealtimeModel({
      model: "gemini-2.0-flash-exp",
      modalities: [google.types.Modality.TEXT],
   }),
   tts: "cartesia/sonic-3",
});
```

## Additional Resources

### Python Plugin
- [Reference](https://docs.livekit.io/reference/python/v1/livekit/plugins/google/realtime/index.html)
- [GitHub](https://github.com/livekit/agents/tree/main/livekit-plugins/livekit-plugins-google)
- [PyPI](https://pypi.org/project/livekit-plugins-google/)

### Node.js Plugin
- [Reference](https://docs.livekit.io/reference/agents-js/modules/plugins_agents_plugin_google.html)
- [GitHub](https://github.com/livekit/agents-js/tree/main/plugins/google)
- [NPM](https://www.npmjs.com/package/@livekit/agents-plugin-google)

### Related Documentation
- [Gemini docs](https://ai.google.dev/gemini-api/docs/live) - Gemini Live API documentation
- [Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/) - Get started with LiveKit Agents and Gemini Live API
- [Google AI ecosystem guide](https://docs.livekit.io/agents/integrations/google/) - Overview of the entire Google AI and LiveKit Agents integration

