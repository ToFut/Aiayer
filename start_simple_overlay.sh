#!/bin/bash
# start_simple_overlay.sh
# A simplified script to start just the most basic overlay UI

echo "====================================================="
echo "    Starting Simple Overlay UI                       "
echo "====================================================="

# Change to project root directory
cd "$(dirname "$0")"

# Create required directories
mkdir -p logs/overlay
mkdir -p pids

# Check if WebSocket server is running
if ! nc -z localhost 8765 2>/dev/null; then
    echo "⚠️ Warning: WebSocket server not detected on port 8765"
    echo "The overlay needs a WebSocket server to function."
    echo "Starting a minimal WebSocket server..."
    
    # Create a simple WebSocket server
    cat > ./simple_ws_server.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay/ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_ws_server')

# Track connected clients
connected_clients = set()

# Handle WebSocket connections
async def handler(websocket, path):
    """Handle incoming WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to simple WebSocket server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type}")
                
                # Handle different message types
                if msg_type == 'connection_established':
                    # Respond with server ready
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                elif msg_type == 'user_interaction':
                    # Simulate a response for user queries
                    query = data.get('payload', {}).get('query', '')
                    logger.info(f"Received query: {query}")
                    
                    await websocket.send(json.dumps({
                        "type": "query_response",
                        "response": f"This is a simulated response to your query: '{query}'. The full backend system will provide more intelligent responses.",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                else:
                    # Echo back for other message types
                    await websocket.send(json.dumps({
                        "type": "response",
                        "payload": {
                            "original_type": msg_type,
                            "message": f"Received your {msg_type} message"
                        },
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message[:100]}...")
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

# Send periodic sensor data to simulate the full system
async def send_periodic_data():
    """Send periodic sensor data to all clients"""
    while True:
        try:
            if connected_clients:
                # Create simple sensor data
                sensor_data = {
                    "type": "sensor_data",
                    "payload": {
                        "process": {
                            "app": "Terminal",
                            "title": "Running Aiayer System",
                            "timestamp": datetime.now().isoformat()
                        },
                        "screen": {
                            "text": "Sample screen text for demo purposes",
                            "timestamp": datetime.now().isoformat()
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send to all clients
                for client in connected_clients:
                    try:
                        await client.send(json.dumps(sensor_data))
                    except Exception as e:
                        logger.error(f"Error sending to client: {e}")
                        
                logger.debug(f"Sent sensor data to {len(connected_clients)} clients")
            
            # Send every 10 seconds
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in periodic sender: {e}")
            await asyncio.sleep(10)  # Wait and try again

async def main():
    # Start WebSocket server
    port = 8765
    host = "localhost"
    
    # Create server
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/ws_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Start periodic sender
    sender_task = asyncio.create_task(send_periodic_data())
    
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    
    # Keep running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
EOF

    # Make the script executable
    chmod +x ./simple_ws_server.py
    
    # Start the WebSocket server
    echo "Starting WebSocket server on port 8765..."
    python3 ./simple_ws_server.py > logs/overlay/ws_server.log 2>&1 &
    WS_PID=$!
    echo $WS_PID > pids/ws_server.pid
    echo "WebSocket server started with PID $WS_PID"
    
    # Wait for server to initialize
    sleep 2
fi

# Create a simple HTML file for the overlay
cat > ./simple_overlay.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Assistant Overlay</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: transparent;
            overflow: hidden;
        }
        
        .assistant-widget {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            transition: all 0.3s ease;
        }
        
        .widget-icon {
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #4CAF50;
            color: white;
            border-radius: 50%;
            cursor: pointer;
            border: none;
            font-size: 24px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }
        
        .widget-icon:hover {
            transform: scale(1.05);
        }
        
        .connection-status {
            position: absolute;
            bottom: 0;
            right: 0;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #999;
            border: 2px solid white;
        }
        
        .connected .connection-status {
            background-color: #4CAF50;
        }
        
        .connecting .connection-status {
            background-color: #FFC107;
            animation: pulse 1.5s infinite;
        }
        
        .error .connection-status {
            background-color: #F44336;
        }
        
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
        
        .widget-content {
            display: none;
            width: 350px;
            max-height: 500px;
            background-color: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            margin-top: 60px;
        }
        
        .widget-expanded .widget-content {
            display: flex;
            flex-direction: column;
        }
        
        .widget-header {
            padding: 15px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .widget-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }
        
        .close-button {
            background: none;
            border: none;
            cursor: pointer;
            color: #666;
            font-size: 20px;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 350px;
        }
        
        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.5;
        }
        
        .message.user {
            background-color: #E3F2FD;
            color: #0D47A1;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant {
            background-color: #F5F5F5;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100px;
            color: #666;
            text-align: center;
            font-style: italic;
        }
        
        .input-area {
            padding: 15px;
            display: flex;
            gap: 10px;
            border-top: 1px solid #eee;
        }
        
        #query-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
        }
        
        #query-input:focus {
            border-color: #4CAF50;
        }
        
        #send-button {
            padding: 0 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            font-weight: 600;
        }
        
        #send-button:hover {
            background-color: #45a049;
        }
        
        #send-button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div id="assistant-widget" class="assistant-widget">
        <button id="widget-icon" class="widget-icon">🤖
            <span id="connection-status" class="connection-status"></span>
        </button>
        
        <div id="widget-content" class="widget-content">
            <div class="widget-header">
                <h3>AI Assistant</h3>
                <button id="close-button" class="close-button">×</button>
            </div>
            
            <div id="messages" class="messages">
                <div class="empty-state">
                    <p>Ask me anything about what you're working on!</p>
                </div>
            </div>
            
            <div class="input-area">
                <input type="text" id="query-input" placeholder="Type your message..." />
                <button id="send-button">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        // Elements
        const widgetElement = document.getElementById('assistant-widget');
        const widgetIcon = document.getElementById('widget-icon');
        const connectionStatus = document.getElementById('connection-status');
        const widgetContent = document.getElementById('widget-content');
        const closeButton = document.getElementById('close-button');
        const messagesContainer = document.getElementById('messages');
        const queryInput = document.getElementById('query-input');
        const sendButton = document.getElementById('send-button');
        
        // State
        let ws = null;
        let isExpanded = false;
        let connectionState = 'disconnected';
        let messages = [];
        
        // Toggle expanded state
        function toggleExpanded() {
            isExpanded = !isExpanded;
            if (isExpanded) {
                widgetElement.classList.add('widget-expanded');
            } else {
                widgetElement.classList.remove('widget-expanded');
            }
        }
        
        // Add a message to the chat
        function addMessage(type, content) {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', type);
            
            const contentElement = document.createElement('div');
            contentElement.classList.add('message-content');
            contentElement.textContent = content;
            
            messageElement.appendChild(contentElement);
            messagesContainer.appendChild(messageElement);
            
            // Remove empty state if present
            const emptyState = messagesContainer.querySelector('.empty-state');
            if (emptyState) {
                messagesContainer.removeChild(emptyState);
            }
            
            // Auto-scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Store message
            messages.push({ type, content });
        }
        
        // Send a message to the server
        function sendMessage() {
            const query = queryInput.value.trim();
            if (!query || connectionState !== 'connected') return;
            
            // Add user message to chat
            addMessage('user', query);
            
            // Send to server
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'user_interaction',
                    payload: {
                        type: 'query',
                        query: query
                    }
                }));
            }
            
            // Clear input
            queryInput.value = '';
        }
        
        // Update connection status UI
        function updateConnectionStatus(status) {
            connectionState = status;
            widgetElement.classList.remove('connected', 'connecting', 'error');
            
            switch(status) {
                case 'connected':
                    widgetElement.classList.add('connected');
                    sendButton.disabled = false;
                    break;
                case 'connecting':
                    widgetElement.classList.add('connecting');
                    sendButton.disabled = true;
                    break;
                case 'error':
                case 'disconnected':
                    widgetElement.classList.add('error');
                    sendButton.disabled = true;
                    break;
            }
        }
        
        // Connect to WebSocket
        function connect() {
            updateConnectionStatus('connecting');
            
            // Create WebSocket connection
            ws = new WebSocket('ws://localhost:8765');
            
            ws.onopen = () => {
                console.log('Connected to WebSocket server');
                updateConnectionStatus('connected');
                
                // Send initial connection message
                ws.send(JSON.stringify({
                    type: 'connection_established',
                    payload: {
                        client: 'simple_overlay',
                        version: '0.1.0',
                        timestamp: Date.now()
                    }
                }));
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    const type = data.type;
                    
                    console.log('Received message:', type);
                    
                    // Handle different message types
                    if (type === 'welcome' || type === 'server_ready') {
                        console.log('Server ready:', data);
                    } else if (type === 'query_response') {
                        addMessage('assistant', data.response);
                    } else if (type === 'sensor_data') {
                        // Just log sensor data for now
                        console.log('Sensor data:', data.payload);
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };
            
            ws.onclose = () => {
                console.log('Connection closed');
                updateConnectionStatus('disconnected');
                
                // Try to reconnect after 3 seconds
                setTimeout(connect, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateConnectionStatus('error');
            };
        }
        
        // Event listeners
        widgetIcon.addEventListener('click', toggleExpanded);
        closeButton.addEventListener('click', toggleExpanded);
        
        sendButton.addEventListener('click', sendMessage);
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Initialize
        updateConnectionStatus('connecting');
        connect();
    </script>
</body>
</html>
EOF

# Start a simple HTTP server to serve the overlay
echo "Starting the overlay..."

if command -v open &> /dev/null; then
    # macOS approach
    echo "Opening overlay in browser..."
    open ./simple_overlay.html
elif command -v xdg-open &> /dev/null; then
    # Linux approach
    echo "Opening overlay in browser..."
    xdg-open ./simple_overlay.html
else
    echo "To see the overlay, open this file in your browser:"
    echo "$(pwd)/simple_overlay.html"
fi

echo "
===================================================
Simple Overlay Started!

- You can see the overlay by opening simple_overlay.html in your browser
- It connects to a WebSocket server on port 8765
- Look for the green robot icon (🤖) in the top-right corner
- Click the icon to expand or collapse the chat interface

To stop the WebSocket server:
  kill \$(cat pids/ws_server.pid)
===================================================
"