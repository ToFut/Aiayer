# Next Generation AI Assistant Overlay

This document describes the next generation AI assistant overlay that provides a ChatGPT-like user experience with improved connectivity to backend systems and memory integration.

## Key Features

- **Modern ChatGPT-like Interface**: Clean, intuitive chat interface with eye icon for quick access
- **Robust WebSocket Connectivity**: Improved connection reliability with automatic reconnection
- **Memory Integration**: Conversations are saved and can be restored
- **Advanced Bridge Server**: Connects frontend overlay with backend AI systems
- **Context Awareness**: Utilizes current work context to provide relevant assistance
- **Responsive Design**: Works on desktop and mobile devices

## Components

The system consists of several key components:

1. **Futuristic Overlay UI** (`futuristic_overlay.html`)
   - ChatGPT-like user interface with eye icon for access
   - Real-time WebSocket communication
   - Responsive design for all devices
   - Dark mode support

2. **Advanced Bridge Server** (`advanced_bridge.py`)
   - Manages WebSocket connections
   - Routes messages between frontend and backend
   - Handles memory storage and retrieval
   - Provides context awareness

3. **Startup Script** (`start_next_gen_overlay.sh`)
   - Easy one-command startup
   - Launches all required components
   - Opens overlay in browser

## Installation & Setup

### Prerequisites

- Python 3.7+
- websockets package (`pip install websockets`)
- Modern web browser

### Installation

1. Ensure all files are in your project directory:
   - `futuristic_overlay.html`
   - `advanced_bridge.py`
   - `start_next_gen_overlay.sh`

2. Make the startup script executable:
   ```bash
   chmod +x start_next_gen_overlay.sh
   ```

3. Create required directories (or the script will create them):
   ```bash
   mkdir -p logs memory pids
   ```

## Usage

1. Start the system with a single command:
   ```bash
   ./start_next_gen_overlay.sh
   ```

2. The script will:
   - Start the Advanced Bridge Server
   - Launch a simple HTTP server to serve the overlay UI
   - Open the overlay in your default browser

3. Interact with the overlay:
   - Click the eye icon to toggle the chat interface
   - Type messages and press Enter to send
   - The system will automatically connect to backend AI systems if available

4. Stop the system:
   - Press Ctrl+C in the terminal where you ran the startup script
   - This will gracefully shut down all components

## Integration with Backend Systems

The Advanced Bridge Server connects to backend AI systems through WebSocket on port 8766. Backend systems should:

1. Connect to `ws://localhost:8766`
2. Listen for messages of type `user_interaction`
3. Respond with messages of type `query_response`
4. Optionally send `context_update` messages when context changes

Example backend message format:

```json
{
  "type": "query_response",
  "payload": {
    "response": "This is the AI response to the user's query",
    "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "conversation_id": "6c84fb90-12c4-11e1-840d-7b25c5ee775a"
  }
}
```

## Memory Storage

Conversations are stored in JSON format in the `memory/last_context.json` file. Each entry includes:
- Timestamp
- Message content
- User/assistant role
- Current context (when available)

## Customization

### UI Customization

The overlay UI can be customized by modifying the CSS variables in the `:root` section of `futuristic_overlay.html`:

```css
:root {
    --primary-color: #10a37f;
    --primary-hover: #0c8a6b;
    --secondary-color: #f7f7f8;
    --text-color: #202123;
    /* Other variables */
}
```

### Bridge Server Configuration

The bridge server ports can be modified by changing the parameters in the `AdvancedBridge` initialization:

```python
bridge = AdvancedBridge(frontend_port=8765, backend_port=8766)
```

## Troubleshooting

1. **Overlay doesn't connect**
   - Check if the Bridge Server is running (`ps aux | grep advanced_bridge.py`)
   - Verify the WebSocket port (8765) is not used by other applications
   - Check the logs in `logs/bridge.log`

2. **No response from AI**
   - Ensure your backend AI system is connected to the bridge
   - Check the logs for any connection errors
   - Verify message formats are correct

3. **Browser issues**
   - Try a different browser (Chrome, Firefox, Safari)
   - Clear browser cache
   - Check browser console for JavaScript errors

## Logs and Monitoring

Logs are stored in the `logs/` directory:
- `logs/bridge.log` - Bridge server logs
- `logs/bridge_output.log` - Console output from bridge
- `logs/http_server.log` - HTTP server logs
- `logs/startup.log` - System startup logs

## License

This software is provided for internal use only.