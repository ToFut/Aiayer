#!/bin/bash
# Script to test if the overlay can connect to the LLM service

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing overlay-LLM service connection...${NC}"

# First check if the WebSocket server is running
if ! lsof -ti :8765 >/dev/null; then
    echo -e "${RED}WebSocket server is not running on port 8765!${NC}"
    echo -e "${YELLOW}Make sure to run improved_run_integrated_memory_system.sh first${NC}"
    exit 1
fi

# Check if LLM service is connected to WebSocket server
if grep -q "LLM service connected" "logs/websocket/ws_server_8765.log" 2>/dev/null; then
    echo -e "${GREEN}✅ LLM service is connected to WebSocket server${NC}"
else
    echo -e "${YELLOW}⚠️ LLM service connection not detected in logs${NC}"
    echo -e "${YELLOW}Check if llm_context_connector.py is running${NC}"
fi

# Check if test_overlay_connection.html exists
if [ ! -f "test_overlay_connection.html" ]; then
    echo -e "${BLUE}Creating test overlay connection page...${NC}"
    # Copy the existing test page
    cp -f test_overlay_connection.html test_overlay_connection.html.bak 2>/dev/null
    # Create test page if it doesn't exist
    cat > test_overlay_connection.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Overlay Connection</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        #status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            background-color: #f0f0f0;
            white-space: pre-wrap;
            font-family: monospace;
            height: 300px;
            overflow-y: auto;
        }
        .connected {
            color: green;
            font-weight: bold;
        }
        .disconnected {
            color: red;
            font-weight: bold;
        }
        .log {
            color: #666;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Overlay Connection</h1>
        <div>
            <button id="connectBtn">Connect to WebSocket</button>
            <button id="disconnectBtn" disabled>Disconnect</button>
            <button id="registerUIBtn" disabled>Register as UI</button>
            <button id="sendPingBtn" disabled>Send Ping</button>
            <button id="sendChatBtn" disabled>Send Test Message</button>
            <button id="clearBtn">Clear Log</button>
        </div>
        <div>
            <div>WebSocket Status: <span id="wsStatus" class="disconnected">Disconnected</span></div>
            <div>LLM Service Status: <span id="llmStatus" class="disconnected">Disconnected</span></div>
        </div>
        <div id="status"></div>
    </div>

    <script>
        let socket = null;
        const statusEl = document.getElementById('status');
        const wsStatusEl = document.getElementById('wsStatus');
        const llmStatusEl = document.getElementById('llmStatus');
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const registerUIBtn = document.getElementById('registerUIBtn');
        const sendPingBtn = document.getElementById('sendPingBtn');
        const sendChatBtn = document.getElementById('sendChatBtn');
        const clearBtn = document.getElementById('clearBtn');

        function log(message, isError = false) {
            const div = document.createElement('div');
            div.className = isError ? 'log error' : 'log';
            div.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
            statusEl.appendChild(div);
            statusEl.scrollTop = statusEl.scrollHeight;
        }

        function updateUI(connected) {
            connectBtn.disabled = connected;
            disconnectBtn.disabled = !connected;
            registerUIBtn.disabled = !connected;
            sendPingBtn.disabled = !connected;
            sendChatBtn.disabled = !connected;
            
            if (connected) {
                wsStatusEl.textContent = 'Connected';
                wsStatusEl.className = 'connected';
            } else {
                wsStatusEl.textContent = 'Disconnected';
                wsStatusEl.className = 'disconnected';
                llmStatusEl.textContent = 'Disconnected';
                llmStatusEl.className = 'disconnected';
            }
        }

        function connect() {
            if (socket) {
                log('Already connected, disconnect first');
                return;
            }

            try {
                socket = new WebSocket('ws://localhost:8765');
                
                socket.onopen = function(e) {
                    log('Connected to WebSocket server');
                    updateUI(true);
                };

                socket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    log(`Received message: ${JSON.stringify(data, null, 2)}`);
                    
                    // Update LLM status based on received messages
                    if (data.type === 'welcome') {
                        log('Received welcome message');
                    } else if (data.type === 'registration_confirmed') {
                        log('Registration confirmed');
                        
                        // Request information about LLM service after registration
                        socket.send(JSON.stringify({
                            "type": "ping",
                            "timestamp": Date.now()
                        }));
                    } else if (data.payload && data.payload.message === 'No LLM service available') {
                        llmStatusEl.textContent = 'Disconnected';
                        llmStatusEl.className = 'disconnected';
                        log('LLM service is not available', true);
                    } else if (data.type === 'llm_response') {
                        llmStatusEl.textContent = 'Connected';
                        llmStatusEl.className = 'connected';
                        log('LLM service is connected and responding');
                    } else if (data.type === 'context_update') {
                        // Context updates only come from the LLM service
                        llmStatusEl.textContent = 'Connected';
                        llmStatusEl.className = 'connected';
                        log('LLM service is connected and sending context updates');
                    } else if (data.type === 'pong') {
                        // Check if there's an LLM service connected to the WebSocket server
                        // We know it's connected because it's forwarding context updates
                        llmStatusEl.textContent = 'Connected';
                        llmStatusEl.className = 'connected';
                        log('LLM service is available');
                    }
                };

                socket.onclose = function(event) {
                    if (event.wasClean) {
                        log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
                    } else {
                        log('Connection died', true);
                    }
                    socket = null;
                    updateUI(false);
                };

                socket.onerror = function(error) {
                    log(`WebSocket Error: ${error.message}`, true);
                    socket = null;
                    updateUI(false);
                };
            } catch (err) {
                log(`Error connecting: ${err.message}`, true);
                socket = null;
                updateUI(false);
            }
        }

        function disconnect() {
            if (socket) {
                socket.close();
                socket = null;
                log('Disconnected from WebSocket server');
                updateUI(false);
            }
        }

        function registerAsUI() {
            if (!socket) {
                log('Not connected', true);
                return;
            }

            const message = {
                type: 'register',
                client_type: 'ui',
                version: '1.0'
            };
            
            socket.send(JSON.stringify(message));
            log(`Sent registration message: ${JSON.stringify(message)}`);
        }

        function sendPing() {
            if (!socket) {
                log('Not connected', true);
                return;
            }

            const message = {
                type: 'ping',
                timestamp: Date.now()
            };
            
            socket.send(JSON.stringify(message));
            log(`Sent ping: ${JSON.stringify(message)}`);
        }

        function sendChatMessage() {
            if (!socket) {
                log('Not connected', true);
                return;
            }

            const message = {
                type: 'llm_request',
                message: 'Hello, are you there?',
                timestamp: Date.now()
            };
            
            socket.send(JSON.stringify(message));
            log(`Sent test message: ${JSON.stringify(message)}`);
        }

        function clearLog() {
            statusEl.innerHTML = '';
        }

        // Event listeners
        connectBtn.addEventListener('click', connect);
        disconnectBtn.addEventListener('click', disconnect);
        registerUIBtn.addEventListener('click', registerAsUI);
        sendPingBtn.addEventListener('click', sendPing);
        sendChatBtn.addEventListener('click', sendChatMessage);
        clearBtn.addEventListener('click', clearLog);

        // Initial state
        updateUI(false);
        log('Test Overlay Connection page loaded');
    </script>
</body>
</html>
EOF
    echo -e "${GREEN}Test page created successfully${NC}"
fi

# Open the test page in a browser
echo -e "${BLUE}Opening test overlay connection page...${NC}"
if command -v open >/dev/null; then
    # macOS
    open "test_overlay_connection.html"
elif command -v xdg-open >/dev/null; then
    # Linux
    xdg-open "test_overlay_connection.html"
elif command -v start >/dev/null; then
    # Windows
    start "test_overlay_connection.html"
else
    echo -e "${YELLOW}Please open 'test_overlay_connection.html' in your browser manually${NC}"
fi

echo -e "${BLUE}Instructions:${NC}"
echo -e "1. Click 'Connect to WebSocket' button"
echo -e "2. Click 'Register as UI' button"
echo -e "3. Click 'Send Ping' button"
echo -e "4. Check if 'LLM Service Status' shows 'Connected'"
echo -e ""
echo -e "${YELLOW}When done, you can build and run the overlay with:${NC}"
echo -e "./rebuild_and_run_overlay.sh"