# Self-Contained WebSocket LLM Server

This implementation provides a standalone solution for connecting the Tauri overlay interface with a local LLM (Ollama) using WebSockets.

## Features

- Single Python script implementation (`self_contained_llm_ws.py`)
- WebSocket server running on port 8765
- Integration with Ollama for local LLM responses
- Compatible with the Tauri overlay interface
- Automatic model selection (prefers llama3 models)
- Proper message format handling for different client types

## Requirements

- Python 3.8+
- Ollama running locally on port 11434 with at least one model installed
- WebSockets Python package (`pip install websockets`)
- aiohttp Python package (`pip install aiohttp`)

## Usage

### Starting the Server

Run the provided shell script:

```bash
./run_self_contained_llm.sh
```

This will:
1. Stop any existing processes on port 8765
2. Start the WebSocket server
3. Show the PID for easy management

### Connecting with the Overlay

Use the Tauri overlay interface configured to connect to `ws://localhost:8765` (already set up in the overlay codebase). The overlay should automatically connect and start sending messages.

### Monitoring

To monitor the server logs in real-time:

```bash
tail -f logs/self_contained_llm_ws.log
```

### Stopping the Server

To stop the server, find the PID and use:

```bash
kill <PID>
```

The PID is displayed when starting the server with the provided script.

## Message Format

### Client to Server

```json
{
  "type": "llm_request",
  "payload": {
    "query": "User message here",
    "timestamp": 1234567890
  }
}
```

### Server to Client

```json
{
  "type": "llm_response",
  "content": "LLM response text here",
  "payload": {
    "response": "LLM response text here",
    "model": "llama3.2:latest",
    "processing_time": 5.74,
    "timestamp": "2025-05-19T11:19:50.599"
  }
}
```

## How It Works

1. The server listens for WebSocket connections on port 8765
2. When a client connects, it identifies itself and requests context
3. The server sends status updates and a welcome message
4. The client sends messages with LLM requests
5. The server forwards these to Ollama and returns the responses
6. Ping messages keep the connection alive

## Troubleshooting

- If the overlay shows "Connection error" - check that the server is running on port 8765
- If the server fails to start - check that Ollama is running on port 11434
- If responses are slow - this is normal for local LLM processing, especially for complex queries
- If no responses appear - check the logs to see if the messages are being processed correctly