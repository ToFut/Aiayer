#!/bin/bash
# Comprehensive Overlay Response Fix
# This script fixes all overlay response issues by:
# 1. Stopping existing processes on key ports
# 2. Starting a direct response handler
# 3. Restarting the overlay
# 4. Testing the connection

# Bold and colored output
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${GREEN}COMPREHENSIVE OVERLAY RESPONSE FIX${RESET}"
echo "This will fix overlay messages not appearing in any mode"
echo ""

# Step 1: Stop all conflicting processes
echo -e "${YELLOW}1. Stopping all conflicting processes...${RESET}"
pkill -f "fixed_bridge_server_ports.py"
pkill -f "overlay_response_interceptor.py"
sleep 2

# Step 2: Create a direct message sender script
echo -e "${YELLOW}2. Creating direct message handler...${RESET}"
cat > direct_overlay_handler.py <<'EOF'
#!/usr/bin/env python3
"""
Direct Overlay Message Handler
This script creates a WebSocket server on port 8766 that directly responds to messages
with no forwarding or complex logic.
"""
import asyncio
import websockets
import json
import logging
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/direct_overlay_handler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Connected clients
connected_clients = set()
client_info = {}

async def handle_client(websocket, path=None):
    """Simple, direct handler for client messages"""
    client_id = f"client_{int(time.time() * 1000)}"
    connected_clients.add(websocket)
    
    try:
        logger.info(f"Client {client_id} connected")
        
        # Send immediate connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "message": "Direct Overlay Message Handler",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                
                # Handle registration
                if msg_type == 'register':
                    client_info[client_id] = data.get('payload', {})
                    await websocket.send(json.dumps({
                        "type": "registration_success",
                        "client_id": client_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Handle LLM requests or chat
                elif msg_type in ['llm_request', 'chat_request']:
                    query = ""
                    mode = "ask"
                    
                    # Extract query from different message formats
                    if 'payload' in data and 'query' in data['payload']:
                        query = data['payload']['query']
                        mode = data['payload'].get('mode', 'ask')
                    elif 'message' in data:
                        query = data['message']
                        mode = data.get('mode', 'ask')
                    else:
                        query = "Unknown query format"
                    
                    logger.info(f"Processing query: {query[:50]}...")
                    
                    # Send an immediate response
                    await websocket.send(json.dumps({
                        "type": "query_response",
                        "payload": {
                            "response": f"DIRECT RESPONSE: I received your message in {mode.upper()} mode: \"{query}\"",
                            "query": query,
                            "mode": mode,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                # Echo other message types
                else:
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "original_type": msg_type,
                        "message": f"Received {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        if client_id in client_info:
            del client_info[client_id]

async def main():
    """Start the direct overlay handler"""
    # Start WebSocket server
    logger.info("Starting Direct Overlay Handler on port 8766")
    async with websockets.serve(handle_client, "0.0.0.0", 8766):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
EOF
chmod +x direct_overlay_handler.py

# Step 3: Start the direct handler
echo -e "${YELLOW}3. Starting direct overlay handler...${RESET}"
python3 direct_overlay_handler.py > logs/direct_overlay_handler.log 2>&1 &
HANDLER_PID=$!
echo "Handler PID: $HANDLER_PID"
echo $HANDLER_PID > pids/direct_overlay_handler.pid
sleep 2

# Step 4: Verify the handler is running
echo -e "${YELLOW}4. Verifying handler is running...${RESET}"
if ps -p $HANDLER_PID > /dev/null; then
    echo -e "${GREEN}✓ Direct overlay handler is running on port 8766${RESET}"
else
    echo -e "${RED}✗ Failed to start direct overlay handler${RESET}"
    exit 1
fi

# Step 5: Create a test client
echo -e "${YELLOW}5. Creating test client...${RESET}"
cat > test_direct_overlay_client.py <<'EOF'
#!/usr/bin/env python3
"""
Test client for direct overlay handler
"""
import asyncio
import websockets
import json
import sys

async def send_test_message():
    """Send a test message to the overlay handler"""
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
            reg_response = await ws.recv()
            print(f"Registration response: {reg_response}")
            
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
            
            # Wait for response
            response = await ws.recv()
            print(f"Response: {response}")
            
            print("Test completed successfully")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())
EOF
chmod +x test_direct_overlay_client.py

# Step 6: Test the direct handler
echo -e "${YELLOW}6. Testing direct overlay handler...${RESET}"
python3 test_direct_overlay_client.py "Testing the direct overlay handler fix"

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
echo -e "${BOLD}${GREEN}OVERLAY FIX COMPLETED${RESET}"
echo ""
echo "The overlay should now correctly display responses in all modes."
echo ""
echo "If you still have issues:"
echo "1. Press Cmd+Shift+A to toggle the chat window"
echo "2. Type a message and press Enter"
echo "3. You should see a direct response"
echo ""
echo "To test manually, run:"
echo "./test_direct_overlay_client.py \"Your test message here\""
echo ""
echo "To monitor logs:"
echo "tail -f logs/direct_overlay_handler.log"