# Overlay Response Interceptor

This solution addresses the issue where the overlay chat interface is not receiving responses from the LLM service due to timeout issues. The interceptor ensures reliable responses by:

1. Acting as a proxy WebSocket server that intercepts requests to the existing servers
2. Trying to get responses from the actual backend first
3. Using a dedicated LLM interceptor with ollama3.2:latest when the backend times out
4. Providing fallback responses when both backend and LLM requests fail

## How It Works

The system consists of three main components:

1. **WebSocket Interceptor Server** (`overlay_response_interceptor.py`)
   - Listens on port 8766
   - Forwards requests to the original backend servers
   - Intercepts and handles LLM requests when the backend fails
   - Ensures responses are always provided within a reasonable time

2. **LLM Interceptor** (`llm_interceptor.py`)
   - Direct interface to ollama3.2:latest model
   - Optimized with a 30-second timeout
   - Provides fallback mechanisms when LLM fails

3. **Bridge URL Updater** (`update_bridge_url.py`)
   - Updates the WebSocket URL in the overlay to use the interceptor
   - Can reset to the original URL when needed

## Setup and Usage

### Starting the Interceptor

Run the start script to configure and start the interceptor:

```bash
./start_overlay_with_interceptor.sh
```

This will:
- Check if Ollama is running
- Update the overlay bridge URL to use port 8766
- Start the interceptor service
- Provide status information

### Stopping the Interceptor

To stop the interceptor and reset the configuration:

```bash
./stop_overlay_interceptor.sh
```

This will:
- Stop the running interceptor service
- Reset the overlay bridge URL to the original port (8765)

### Manual Usage

You can also control the components individually:

1. Start the interceptor:
   ```bash
   python overlay_response_interceptor.py
   ```

2. Update the bridge URL:
   ```bash
   python update_bridge_url.py --port 8766
   ```

3. Reset the bridge URL:
   ```bash
   python update_bridge_url.py --reset
   ```

## Troubleshooting

- Check the logs in `logs/response_interceptor.log` and `logs/llm_interceptor.log`
- Ensure Ollama is running and has the ollama3.2:latest model available
- Verify that the original backend servers are running (but the solution will work even if they're not)

## Response Types

The interceptor provides three types of responses:

1. **Backend Responses**: Original responses from the backend servers
2. **LLM Responses**: Direct responses from ollama3.2:latest via the interceptor
3. **Fallback Responses**: Predefined responses when both backend and LLM fail

All responses maintain the expected format for compatibility with the overlay chat interface.