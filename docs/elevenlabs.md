# ElevenLabs TTS Plugin

## Overview

This plugin allows you to use [ElevenLabs](https://elevenlabs.io/) as a TTS provider for your voice agents.

**LiveKit Inference**

ElevenLabs TTS is also available in LiveKit Inference, with billing and integration handled automatically. See [the docs](https://docs.livekit.io/agents/models/tts/inference/elevenlabs/) for more information.

## Quick Reference

### Installation

Install the plugin from PyPI or NPM:

**Python:**
```shell
uv add "livekit-agents[elevenlabs]~=1.2"
```

**Node.js:**
```shell
pnpm add @livekit/agents-plugin-elevenlabs@1.x
```

### Authentication

The ElevenLabs plugin requires an [ElevenLabs API key](https://elevenlabs.io/app/settings/api-keys).

Set `ELEVEN_API_KEY` in your `.env` file.

### Usage

Use ElevenLabs TTS within an `AgentSession` or as a standalone speech generator. For example, you can use this TTS in the [Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/).

**Python:**
```python
from livekit.plugins import elevenlabs

session = AgentSession(
   tts=elevenlabs.TTS(
      voice_id="ODq5zmih8GrVes37Dizd",
      model="eleven_multilingual_v2"
   )
   # ... llm, stt, etc.
)
```

**Node.js:**
```typescript
import * as elevenlabs from '@livekit/agents-plugin-elevenlabs';

const session = new voice.AgentSession({
    tts: new elevenlabs.TTS(
      voice: { id: "ODq5zmih8GrVes37Dizd" },
      model: "eleven_multilingual_v2"
    ),
    // ... llm, stt, etc.
});
```

## Parameters

This section describes some of the parameters you can set when you create an ElevenLabs TTS. See the plugin reference links in the Additional resources section for a complete list of all available parameters.

### model
- **Type:** `string`
- **Optional:** Yes
- **Default:** `eleven_flash_v2_5`
- **Description:** ID of the model to use for generation. To learn more, see the [ElevenLabs documentation](https://elevenlabs.io/docs/api-reference/text-to-speech/convert#/docs/api-reference/text-to-speech/convert#request.body.model_id).

### voice_id
- **Type:** `string`
- **Optional:** Yes
- **Default:** `EXAVITQu4vr4xnSDxMaL`
- **Description:** ID of the voice to use for generation. To learn more, see the [ElevenLabs documentation](https://elevenlabs.io/docs/api-reference/text-to-speech/convert).

### voice_settings
- **Type:** `VoiceSettings`
- **Optional:** Yes
- **Description:** Voice configuration. To learn more, see the [ElevenLabs documentation](https://elevenlabs.io/docs/api-reference/text-to-speech/convert#request.body.voice_settings).

Available sub-parameters:
- **stability** (`float`, Optional)
- **similarity_boost** (`float`, Optional)
- **style** (`float`, Optional)
- **use_speaker_boost** (`bool`, Optional)
- **speed** (`float`, Optional)

### language
- **Type:** `string`
- **Optional:** Yes
- **Default:** `en`
- **Description:** Language of output audio in [ISO-639-1](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) format. To learn more, see the [ElevenLabs documentation](https://elevenlabs.io/docs/api-reference/text-to-speech/convert#request.body.language_code).

### streaming_latency
- **Type:** `int`
- **Optional:** Yes
- **Default:** `3`
- **Description:** Latency in seconds for streaming.

### enable_ssml_parsing
- **Type:** `bool`
- **Optional:** Yes
- **Default:** `false`
- **Description:** Enable Speech Synthesis Markup Language (SSML) parsing for input text. Set to `true` to [customize pronunciation](https://docs.livekit.io/agents/models/tts/plugins/elevenlabs/#customizing-pronunciation) using SSML.

### chunk_length_schedule
- **Type:** `list[int]`
- **Optional:** Yes
- **Default:** `[80, 120, 200, 260]`
- **Description:** Schedule for chunk lengths. Valid values range from `50` to `500`.

## Customizing Pronunciation

ElevenLabs supports custom pronunciation for specific words or phrases with SSML `phoneme` tags. This is useful to ensure correct pronunciation of certain words, even when missing from the voice's lexicon. To learn more, see [Pronunciation](https://elevenlabs.io/docs/best-practices/prompting#pronunciation).

## Transcription Timing

ElevenLabs TTS supports aligned transcription forwarding, which improves transcription synchronization in your frontend. Set `use_tts_aligned_transcript=True` in your `AgentSession` configuration to enable this feature. To learn more, see [the docs](https://docs.livekit.io/agents/build/text/#tts-aligned-transcriptions).

## Additional Resources

### Python Plugin
- [Reference](https://docs.livekit.io/reference/python/v1/livekit/plugins/elevenlabs/index.html#livekit.plugins.elevenlabs.TTS)
- [GitHub](https://github.com/livekit/agents/tree/main/livekit-plugins/livekit-plugins-elevenlabs)
- [PyPI](https://pypi.org/project/livekit-plugins-elevenlabs/)

### Node.js Plugin
- [Reference](https://docs.livekit.io/reference/agents-js/classes/plugins_agents_plugin_elevenlabs.TTS.html)
- [GitHub](https://github.com/livekit/agents-js/tree/main/plugins/elevenlabs)
- [NPM](https://www.npmjs.com/package/@livekit/agents-plugin-elevenlabs)

### Related Documentation
- [ElevenLabs docs](https://elevenlabs.io/docs) - ElevenLabs TTS docs
- [Voice AI quickstart](https://docs.livekit.io/agents/start/voice-ai/) - Get started with LiveKit Agents and ElevenLabs TTS

