# OpenAI Realtime Voice API - Frontend Integration Guide

## Overview

This API provides real-time, bidirectional voice conversations using OpenAI's Realtime API.
Users can speak naturally and receive spoken AI responses in real-time.

## Architecture

```
┌─────────────────┐                    ┌─────────────────────────┐
│    Frontend     │                    │   OpenAI Realtime API   │
│    (Browser)    │◄──── WebSocket ───►│  wss://api.openai.com   │
└────────┬────────┘     (Audio Stream) └─────────────────────────┘
         │
         │ REST API (Get Session Token)
         ▼
┌─────────────────┐
│  Your Backend   │
│  /api/v1/voice  │
└─────────────────┘
```

## Quick Start

### Step 1: Get Session Token from Backend

```javascript
const response = await fetch('/api/v1/voice/realtime/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        instructions: "You are a helpful AI assistant for Balasore Alloys.",
        voice: "alloy"  // Options: alloy, echo, fable, onyx, nova, shimmer
    })
});

const session = await response.json();
// session.client_secret - Use this to authenticate WebSocket
// session.websocket_url - Connect to this URL
// session.expires_at    - Token expiry (Unix timestamp)
```

### Step 2: Connect WebSocket to OpenAI

```javascript
const ws = new WebSocket(session.websocket_url, {
    headers: {
        'Authorization': `Bearer ${session.client_secret}`,
        'OpenAI-Beta': 'realtime=v1'
    }
});

// For browsers (headers not supported), use URL params or send auth after connect
const ws = new WebSocket(session.websocket_url);
ws.onopen = () => {
    // Session is already authenticated via ephemeral token
    console.log('Connected to OpenAI Realtime');
};
```

### Step 3: Set Up Audio Capture

```javascript
// Audio configuration (MUST match these settings)
const SAMPLE_RATE = 24000;  // 24kHz
const CHANNELS = 1;          // Mono
const FORMAT = 'pcm16';      // 16-bit PCM

// Get microphone access
const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
        sampleRate: SAMPLE_RATE,
        channelCount: CHANNELS,
        echoCancellation: true,
        noiseSuppression: true
    }
});

// Create AudioContext for processing
const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
const source = audioContext.createMediaStreamSource(stream);
const processor = audioContext.createScriptProcessor(4096, 1, 1);

source.connect(processor);
processor.connect(audioContext.destination);

processor.onaudioprocess = (e) => {
    const inputData = e.inputBuffer.getChannelData(0);

    // Convert Float32 to Int16 PCM
    const pcm16 = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
    }

    // Send audio to OpenAI
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: arrayBufferToBase64(pcm16.buffer)
        }));
    }
};
```

### Step 4: Handle Responses

```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
        case 'session.created':
            console.log('Session ready:', message.session.id);
            break;

        case 'input_audio_buffer.speech_started':
            console.log('User started speaking');
            break;

        case 'input_audio_buffer.speech_stopped':
            console.log('User stopped speaking');
            break;

        case 'conversation.item.input_audio_transcription.completed':
            console.log('User said:', message.transcript);
            break;

        case 'response.audio.delta':
            // AI is speaking - play this audio
            playAudioChunk(message.delta);  // Base64 PCM16 audio
            break;

        case 'response.audio_transcript.delta':
            // Real-time transcript of AI response
            console.log('AI saying:', message.delta);
            break;

        case 'response.done':
            console.log('AI finished speaking');
            break;

        case 'error':
            console.error('Error:', message.error);
            break;
    }
};
```

### Step 5: Play Audio Response

```javascript
// Audio playback queue
let audioQueue = [];
let isPlaying = false;

function playAudioChunk(base64Audio) {
    const audioData = base64ToArrayBuffer(base64Audio);
    audioQueue.push(audioData);

    if (!isPlaying) {
        playNextChunk();
    }
}

async function playNextChunk() {
    if (audioQueue.length === 0) {
        isPlaying = false;
        return;
    }

    isPlaying = true;
    const audioData = audioQueue.shift();

    // Convert PCM16 to Float32 for Web Audio API
    const pcm16 = new Int16Array(audioData);
    const float32 = new Float32Array(pcm16.length);
    for (let i = 0; i < pcm16.length; i++) {
        float32[i] = pcm16[i] / 32768;
    }

    // Create and play audio buffer
    const audioBuffer = audioContext.createBuffer(1, float32.length, SAMPLE_RATE);
    audioBuffer.getChannelData(0).set(float32);

    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.onended = playNextChunk;
    source.start();
}
```

---

## API Reference

### POST /api/v1/voice/realtime/session

Create a new realtime voice session.

**Request Body:**
```json
{
    "instructions": "You are a helpful assistant...",  // Optional
    "voice": "alloy",                                   // Optional: alloy|echo|fable|onyx|nova|shimmer
    "tools": [...],                                     // Optional: Function calling tools
    "temperature": 0.8                                  // Optional: 0.6 to 1.2
}
```

**Response:**
```json
{
    "success": true,
    "session_id": "sess_ABC123",
    "client_secret": "ek_abc123...",
    "expires_at": 1734567890,
    "websocket_url": "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
    "model": "gpt-4o-realtime-preview-2024-12-17",
    "voice": "alloy",
    "config": {
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "sample_rate": 24000,
        "channels": 1,
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500
        }
    }
}
```

### GET /api/v1/voice/realtime/info

Get connection requirements and available options.

**Response:**
```json
{
    "websocket_url": "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
    "model": "gpt-4o-realtime-preview-2024-12-17",
    "audio_config": {
        "sample_rate": 24000,
        "channels": 1,
        "format": "pcm16",
        "bits_per_sample": 16
    },
    "available_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
    "default_voice": "alloy",
    "turn_detection_modes": ["server_vad", "none"],
    "documentation": "https://platform.openai.com/docs/guides/realtime"
}
```

---

## WebSocket Message Types

### Client → OpenAI

| Message Type | Description |
|--------------|-------------|
| `input_audio_buffer.append` | Send audio chunk (base64 PCM16) |
| `input_audio_buffer.commit` | Manually commit audio buffer |
| `input_audio_buffer.clear` | Clear audio buffer |
| `response.create` | Manually trigger response |
| `response.cancel` | Cancel current response |
| `conversation.item.create` | Add text/audio to conversation |

### OpenAI → Client

| Message Type | Description |
|--------------|-------------|
| `session.created` | Session initialized |
| `session.updated` | Session config changed |
| `input_audio_buffer.speech_started` | VAD detected speech start |
| `input_audio_buffer.speech_stopped` | VAD detected speech end |
| `input_audio_buffer.committed` | Audio buffer committed |
| `conversation.item.created` | New conversation item |
| `conversation.item.input_audio_transcription.completed` | User speech transcribed |
| `response.created` | AI response started |
| `response.audio.delta` | Audio chunk from AI |
| `response.audio.done` | Audio stream complete |
| `response.audio_transcript.delta` | Real-time transcript |
| `response.text.delta` | Text response chunk |
| `response.done` | Response complete |
| `error` | Error occurred |

---

## Audio Format Requirements

| Parameter | Value |
|-----------|-------|
| Sample Rate | 24000 Hz (24kHz) |
| Channels | 1 (Mono) |
| Bit Depth | 16-bit |
| Format | PCM (Linear) |
| Encoding | Little-endian |

---

## Complete Example Component (React)

```jsx
import React, { useState, useRef, useCallback } from 'react';

const RealtimeVoice = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [aiResponse, setAiResponse] = useState('');

    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const streamRef = useRef(null);

    const startSession = async () => {
        // 1. Get session token
        const res = await fetch('/api/v1/voice/realtime/session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                instructions: "You are a helpful assistant.",
                voice: "alloy"
            })
        });
        const session = await res.json();

        if (!session.success) {
            alert('Failed to create session: ' + session.error);
            return;
        }

        // 2. Connect WebSocket
        const ws = new WebSocket(session.websocket_url);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            startAudioCapture();
        };

        ws.onmessage = handleMessage;
        ws.onclose = () => setIsConnected(false);
        ws.onerror = (e) => console.error('WebSocket error:', e);
    };

    const startAudioCapture = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: 24000, channelCount: 1 }
        });
        streamRef.current = stream;

        audioContextRef.current = new AudioContext({ sampleRate: 24000 });
        // ... audio processing setup

        setIsListening(true);
    };

    const handleMessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'conversation.item.input_audio_transcription.completed') {
            setTranscript(msg.transcript);
        }
        if (msg.type === 'response.audio_transcript.delta') {
            setAiResponse(prev => prev + msg.delta);
        }
        if (msg.type === 'response.audio.delta') {
            // Play audio...
        }
    };

    const endSession = () => {
        wsRef.current?.close();
        streamRef.current?.getTracks().forEach(t => t.stop());
        audioContextRef.current?.close();
        setIsConnected(false);
        setIsListening(false);
    };

    return (
        <div>
            <button onClick={isConnected ? endSession : startSession}>
                {isConnected ? 'End Call' : 'Start Voice Chat'}
            </button>

            {isListening && <p>🎤 Listening...</p>}

            <div>
                <h4>You said:</h4>
                <p>{transcript}</p>
            </div>

            <div>
                <h4>AI Response:</h4>
                <p>{aiResponse}</p>
            </div>
        </div>
    );
};

export default RealtimeVoice;
```

---

## Utility Functions

```javascript
// Convert ArrayBuffer to Base64
function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

// Convert Base64 to ArrayBuffer
function base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}
```

---

## Error Handling

```javascript
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'error') {
        switch (msg.error.code) {
            case 'session_expired':
                // Re-create session
                startSession();
                break;
            case 'rate_limit_exceeded':
                // Back off and retry
                setTimeout(retry, 5000);
                break;
            case 'invalid_audio':
                console.error('Audio format issue:', msg.error.message);
                break;
            default:
                console.error('Error:', msg.error);
        }
    }
};
```

---

## Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome 89+ | ✅ Full support |
| Firefox 85+ | ✅ Full support |
| Safari 15+ | ✅ Full support |
| Edge 89+ | ✅ Full support |

**Note:** Requires HTTPS for microphone access (except localhost).

---

## Resources

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [MediaDevices.getUserMedia()](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
