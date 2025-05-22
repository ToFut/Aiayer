# Overlay LLM Integration

This document explains how the overlay system works with the language model integration (Ollama service).

## System Architecture

The system consists of several components working together:

1. **WebSocket Bridge Server** (`simple_bridge_server_fixed.py`)
   - Central communication hub
   - Routes messages between clients and services
   - Handles client connections and disconnections
   - Keeps track of which client is the LLM service

2. **Ollama LLM Service** (`ollama_service.py`)
   - Connects to the Bridge Server as a specialized client
   - Processes language model requests
   - Communicates with the Ollama API
   - Automatically detects and uses available models
   - Falls back to alternative models if the primary one fails

3. **Overlay Chat Interface** (`overlay/src/components/EnhancedNextGenChat.svelte`)
   - User interface for chatting with the AI assistant
   - Connects to the Bridge Server
   - Sends user messages as LLM requests
   - Displays responses from the LLM service

## Message Flow

1. User types a message in the overlay chat interface
2. The message is sent to the Bridge Server as an `llm_request`
3. Bridge Server forwards the request to the Ollama LLM Service
4. Ollama service processes the request using the language model
5. Response is sent back to the Bridge Server as an `llm_response`
6. Bridge Server forwards the response to the overlay client
7. Response is displayed to the user in the chat interface

## How to Start the System

Use the provided script to start all components:

```bash
./start_overlay_with_llm.sh
```

This will start:
- The WebSocket Bridge Server (port 8765)
- The Ollama LLM Service
- HTTP Server for the overlay (port 8000)

## Testing the Integration

You can test the integration with the test script:

```bash
python3 test_overlay_chat.py
```

This script:
- Connects to the Bridge Server
- Sends a test message
- Waits for and verifies the LLM response

## Stopping the System

Use the provided script to stop all components:

```bash
./stop_system.sh
```

## Troubleshooting

If you encounter issues:

1. **Check the logs**:
   - Bridge Server: `logs/bridge_server.log`
   - Ollama Service: `logs/ollama_service.log`
   - HTTP Server: `logs/http_server.log`

2. **Verify Ollama is running**:
   - The Ollama daemon should be running (`ollama serve`)
   - Verify available models with `curl http://localhost:11434/api/tags`

3. **Test components individually**:
   - Test WebSocket connection: `python3 test_bridge_connection.py`
   - Test LLM response: `python3 test_overlay_chat.py`

4. **Common issues**:
   - Timeout: The LLM can take 10+ seconds to respond
   - Model not found: Verify model name in the Ollama service
   - Connection refused: Ensure all servers are running