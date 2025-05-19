# Eye Widget Overlay

This document describes the eye widget overlay system for the AI Assistant that provides a floating, persistent interface for interacting with the AI backend.

## System Overview

The Eye Widget Overlay system consists of several components:

1. **Eye Widget UI** - A floating eye icon that expands into a ChatGPT-like chat interface
2. **Enhanced Bridge Server** - WebSocket server connecting the UI to the AI backend
3. **Memory Integration** - Storing conversations for persistent context

## Components

### Eye Widget UI

The eye widget is a modern, floating interface that provides:

- A draggable eye icon that follows your cursor
- ChatGPT-like chat interface when expanded
- Responsive design that works on all screen sizes
- Dark mode support
- Keyboard shortcuts for quick access

Key files:
- `overlay/src/components/EyeWidget.svelte` - The main widget component
- `overlay/src/services/enhanced_bridge.js` - Robust WebSocket client

### Enhanced Bridge Server

The bridge server connects the UI to the AI backend and provides:

- WebSocket communication on ports 8765 (frontend) and 8766 (backend)
- Memory integration for conversation history
- Context tracking and sharing
- Robust error handling and reconnection
- Heartbeat mechanism to maintain connections

Key files:
- `overlay_bridge_server.py` - The enhanced bridge server

### Memory Integration

Conversations are stored persistently to maintain context:

- Stored in JSON format in the `memory/` directory
- Includes timestamps and user/assistant roles
- Synchronized with the context system
- Accessible to both the UI and backend

## Usage

1. Start the system:
   ```
   ./start_overlay_system.sh
   ```

2. Interact with the eye widget:
   - Click the eye icon to expand/collapse the chat
   - Drag the eye icon to reposition
   - Type messages in the chat interface
   - Use keyboard shortcuts (Ctrl+Alt+E to toggle, Escape to close)

3. The system will automatically:
   - Maintain connections to the backend
   - Store conversations in memory
   - Provide context-aware responses

## Integration with Backend

Backend systems can connect to the bridge server on port 8766:

```python
import websockets
import json

async def connect_to_bridge():
    async with websockets.connect("ws://localhost:8766") as websocket:
        # Send connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client": "ai_backend",
                "version": "1.0.0"
            }
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            # Process user queries
            if data["type"] == "user_interaction" and data["payload"]["type"] == "query":
                query = data["payload"]["query"]
                # Process the query...
                
                # Send response
                await websocket.send(json.dumps({
                    "type": "query_response",
                    "payload": {
                        "response": "AI response here",
                        "conversation_id": data["payload"].get("conversation_id"),
                        "request_id": data["payload"].get("request_id")
                    }
                }))
```

## Technical Details

### Message Format

Messages between components follow this format:

```json
{
  "type": "message_type",
  "payload": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

Common message types:
- `connection_established` - Initial connection
- `user_interaction` - User queries
- `query_response` - AI responses
- `context_update` - Context changes
- `memory_store` - Memory operations

### Conversation Storage

Conversations are stored in `memory/conversation_history.json` with this structure:

```json
{
  "conversation_id": [
    {
      "role": "user",
      "content": "User message",
      "timestamp": 1621234567.89
    },
    {
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": 1621234568.12
    }
  ]
}
```

### Context Integration

Context is stored in `memory/temporal_context.json` and includes:

```json
{
  "summary": "Current context description",
  "active_app": "Application name",
  "active_window": "Window title",
  "timestamp": 1621234567.89
}
```

## Troubleshooting

### Connection Issues

If the eye widget shows as disconnected:

1. Check if the bridge server is running:
   ```
   ps aux | grep overlay_bridge_server.py
   ```

2. Check logs:
   ```
   cat logs/overlay_bridge.log
   ```

3. Restart the system:
   ```
   ./start_overlay_system.sh
   ```

### UI Issues

If the eye widget isn't displaying correctly:

1. Try restarting the Tauri app:
   ```
   cd overlay
   npm run tauri dev
   ```

2. Check browser console for errors

### Memory Issues

If conversations aren't being saved:

1. Ensure the `memory` directory exists:
   ```
   mkdir -p memory
   ```

2. Check permissions:
   ```
   chmod -R 755 memory
   ```

## Development

To modify the eye widget:

1. Edit `overlay/src/components/EyeWidget.svelte`
2. Run in development mode:
   ```
   cd overlay
   npm run tauri dev
   ```

To modify the bridge server:

1. Edit `overlay_bridge_server.py`
2. Restart the server:
   ```
   pkill -f overlay_bridge_server.py
   python3 overlay_bridge_server.py
   ```