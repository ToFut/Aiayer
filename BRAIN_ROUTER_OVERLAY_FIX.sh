#!/bin/bash
# Brain Router Overlay Fix
# This script connects the overlay directly to the brain router backend

# Bold and colored output
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${GREEN}BRAIN ROUTER OVERLAY FIX${RESET}"
echo "This will connect the overlay directly to the brain router for proper mode responses"
echo ""

# Step 1: Stop direct overlay handler
echo -e "${YELLOW}1. Stopping direct overlay handler...${RESET}"
pkill -f "direct_overlay_handler.py"
sleep 2

# Step 2: Create brain router connector
echo -e "${YELLOW}2. Creating brain router connector...${RESET}"
cat > brain_router_connector.py <<'EOF'
#!/usr/bin/env python3
"""
Brain Router Connector for Overlay
This script creates a WebSocket server on port 8766 that forwards messages to the brain router
backend on port 8767 and properly formats responses for the overlay.
"""
import asyncio
import websockets
import json
import logging
import sys
import time
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/brain_router_connector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Settings
BACKEND_URI = "ws://localhost:8767"
CONNECTOR_PORT = 8766

# Connected clients
connected_clients = {}
backend_connections = {}

async def forward_to_backend(client_ws, message_data):
    """Forward message to brain router backend and handle response"""
    try:
        client_id = connected_clients.get(client_ws)
        if not client_id:
            logger.error("No client ID for websocket")
            return False
            
        logger.info(f"Forwarding to brain router: {message_data[:100]}...")
        
        # Create backend connection if needed
        if client_ws not in backend_connections:
            logger.info(f"Creating new backend connection for client {client_id}")
            backend_ws = await websockets.connect(
                BACKEND_URI, 
                ping_interval=30,
                ping_timeout=300
            )
            backend_connections[client_ws] = backend_ws
            
            # Start listener for backend messages
            asyncio.create_task(listen_to_backend(client_ws, backend_ws))
        else:
            backend_ws = backend_connections[client_ws]
            
        # Send to backend
        await backend_ws.send(message_data)
        return True
        
    except Exception as e:
        logger.error(f"Error forwarding to backend: {e}")
        logger.error(traceback.format_exc())
        
        # Send error to client
        try:
            error_message = {
                "type": "error",
                "payload": {
                    "message": f"Error connecting to backend: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            }
            await client_ws.send(json.dumps(error_message))
        except:
            pass
            
        return False

async def listen_to_backend(client_ws, backend_ws):
    """Listen for responses from the backend and forward to client"""
    try:
        while True:
            # Wait for message from backend
            response = await backend_ws.recv()
            
            # Process response if needed
            try:
                response_data = json.loads(response)
                logger.info(f"Received from backend: {response_data.get('type', 'unknown')} message")
                
                # If this is a query response, ensure it's in the right format for the overlay
                if response_data.get('type') in ['chat_response', 'llm_response', 'final_response']:
                    # Reformat to query_response if needed for better overlay compatibility
                    if 'response' in response_data and 'payload' not in response_data:
                        response_data = {
                            "type": "query_response",
                            "payload": {
                                "response": response_data['response'],
                                "mode": response_data.get('mode', 'Ask'),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        response = json.dumps(response_data)
            except:
                # Just forward as-is if we can't parse
                pass
                
            # Forward to client
            await client_ws.send(response)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("Backend connection closed")
    except Exception as e:
        logger.error(f"Error in backend listener: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up this backend connection
        if client_ws in backend_connections:
            if backend_connections[client_ws] == backend_ws:
                del backend_connections[client_ws]

async def handle_client(websocket, path=None):
    """Handle WebSocket client connections"""
    client_id = f"client_{int(time.time() * 1000)}"
    connected_clients[websocket] = client_id
    
    try:
        logger.info(f"Client {client_id} connected")
        
        # Send immediate connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "message": "Brain Router Connector for Overlay",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                
                # Check if it's a query
                if msg_type in ['llm_request', 'chat_request']:
                    # Format for brain router if needed
                    if msg_type == 'llm_request' and 'payload' in data:
                        # Convert to chat_request format that brain router expects
                        chat_request = {
                            "type": "chat_request",
                            "message": data['payload'].get('query', ''),
                            "mode": data['payload'].get('mode', 'ask'),
                            "session_id": data['payload'].get('session_id', client_id),
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        await forward_to_backend(websocket, json.dumps(chat_request))
                    else:
                        # Forward as-is
                        await forward_to_backend(websocket, message)
                    
                    # Send typing indicator for better UX
                    await websocket.send(json.dumps({
                        "type": "typing_start",
                        "message": "AI is thinking...",
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    # Forward all other messages
                    await forward_to_backend(websocket, message)
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                logger.error(traceback.format_exc())
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up
        if websocket in connected_clients:
            del connected_clients[websocket]
        
        # Close backend connection if exists
        if websocket in backend_connections:
            try:
                await backend_connections[websocket].close()
            except:
                pass
            del backend_connections[websocket]

async def main():
    """Start the brain router connector"""
    # Start WebSocket server
    logger.info(f"Starting Brain Router Connector on port {CONNECTOR_PORT}")
    async with websockets.serve(handle_client, "0.0.0.0", CONNECTOR_PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
EOF
chmod +x brain_router_connector.py

# Step 3: Start the brain router connector
echo -e "${YELLOW}3. Starting brain router connector...${RESET}"
python3 brain_router_connector.py > logs/brain_router_connector.log 2>&1 &
CONNECTOR_PID=$!
echo "Connector PID: $CONNECTOR_PID"
mkdir -p pids
echo $CONNECTOR_PID > pids/brain_router_connector.pid
sleep 2

# Step 4: Verify the connector is running
echo -e "${YELLOW}4. Verifying connector is running...${RESET}"
if ps -p $CONNECTOR_PID > /dev/null; then
    echo -e "${GREEN}✓ Brain router connector is running on port 8766${RESET}"
else
    echo -e "${RED}✗ Failed to start brain router connector${RESET}"
    exit 1
fi

# Step 5: Create a test client
echo -e "${YELLOW}5. Creating test client for brain router...${RESET}"
cat > test_brain_router_client.py <<'EOF'
#!/usr/bin/env python3
"""
Test client for brain router connector
"""
import asyncio
import websockets
import json
import sys

async def send_test_message():
    """Send a test message to the brain router connector"""
    try:
        uri = "ws://localhost:8766"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as ws:
            print("Connected")
            
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Welcome message: {welcome}")
            
            # Register
            registration = {
                "type": "register",
                "payload": {
                    "client_type": "test_client",
                    "client_id": "test_client",
                    "version": "1.0",
                    "capabilities": ["text"]
                }
            }
            print("Sending registration...")
            await ws.send(json.dumps(registration))
            
            # Wait for registration confirmation
            try:
                reg_response = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"Registration response: {reg_response}")
            except asyncio.TimeoutError:
                print("No registration response (this is normal)")
            
            # Send test query
            query = "This is a test query"
            if len(sys.argv) > 1:
                query = " ".join(sys.argv[1:])
                
            test_query = {
                "type": "llm_request",
                "payload": {
                    "query": query,
                    "mode": "ask",
                    "session_id": "test_session",
                    "user_id": "test_user"
                }
            }
            print(f"Sending test query: {query}")
            await ws.send(json.dumps(test_query))
            
            # Wait for typing indicator
            try:
                typing = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"Typing indicator: {typing}")
            except asyncio.TimeoutError:
                print("No typing indicator received")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=15)
                print(f"Response: {response}")
            except asyncio.TimeoutError:
                print("No response received after 15 seconds")
            
            print("Test completed")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())
EOF
chmod +x test_brain_router_client.py

# Step 6: Test the brain router connector
echo -e "${YELLOW}6. Testing brain router connector...${RESET}"
python3 test_brain_router_client.py "Testing the brain router connection"

# Step 7: Restart the overlay
echo -e "${YELLOW}7. Restarting the overlay...${RESET}"
cd "$(dirname "$0")/overlay"
npm run tauri > /dev/null 2>&1 &
OVERLAY_PID=$!
echo "Overlay PID: $OVERLAY_PID"
mkdir -p ../pids
echo $OVERLAY_PID > ../pids/overlay.pid
cd ..

echo ""
echo -e "${BOLD}${GREEN}BRAIN ROUTER OVERLAY FIX COMPLETED${RESET}"
echo ""
echo "The overlay should now connect directly to the brain router and show proper mode-based responses."
echo ""
echo "If you still have issues:"
echo "1. Press Cmd+Shift+A to toggle the chat window"
echo "2. Type a message and press Enter"
echo "3. You should see a response from the brain router with the proper mode structure"
echo ""
echo "To test manually, run:"
echo "./test_brain_router_client.py \"Your test message here\""
echo ""
echo "To monitor logs:"
echo "tail -f logs/brain_router_connector.log"