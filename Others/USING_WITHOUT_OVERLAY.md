# Using Local Assistant Without the Overlay

## Background

The Local Assistant system consists of two main components:
1. **Python Backend**: Processes data and runs the AI assistant functionality
2. **Tauri Overlay**: Provides a transparent UI layer on top of applications

Due to configuration issues with the Tauri overlay component, you can still use the system's core functionality without the overlay UI.

## Running the Backend Only

1. First, make sure no existing processes are using port 5002:
   ```
   pkill -f "python.*main"
   ```

2. Start the backend with the overlay bridge:
   ```
   cd /Users/segevbin/Desktop/local_assistant/local_assistant
   source venv/bin/activate
   python main_with_overlay.py
   ```

3. Access the web interface:
   - Main page: http://127.0.0.1:5002/
   - Chat interface: http://127.0.0.1:5002/chat
   - Health check: http://127.0.0.1:5002/health
   - Overlay status: http://127.0.0.1:5002/overlay/status

## User Flow

Without the overlay, you can still:
1. Use the chat interface to interact with the assistant
2. Access all backend API endpoints
3. Receive responses from the AI assistant

## Troubleshooting

If the application doesn't start:
- Check if port 5002 is already in use
- Ensure all dependencies are installed
- Check the logs for any Python errors

## Working with the Backend

- The backend has a WebSocket bridge running on port 8765
- The bridge connects to any clients (like the overlay)
- Without the overlay, the WebSocket will be available but unused

## Next Steps

To fix the overlay in the future, you would need to:
1. Reinstall Tauri CLI and dependencies
2. Update the configuration file to match the installed Tauri version
3. Ensure the WebSocket bridge is running and can be connected to

## Using Sensors Without the Overlay

The system's sensors will still collect data even without the overlay:
- Screen sensor captures screen content
- Process sensor monitors active applications
- File sensor tracks file system changes

This data is analyzed by the backend and can be accessed through the API endpoints.