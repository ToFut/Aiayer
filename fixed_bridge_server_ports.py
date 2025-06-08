#!/usr/bin/env python3
"""
Fixed Overlay Bridge Server
- Connects overlay UI to backend server
- Ensures proper WebSocket communication
- Uses fixed ports to avoid conflicts
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/overlay', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay/fixed_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fixed_bridge_server")

# FIXED PORT CONFIGURATION
BRIDGE_PORT = 8766
BACKEND_PORT = 8767
DO_BUTTON_PORT = 8765
NEURAL_UI_PORT = 8768

class OverlayBridgeServer:
    def __init__(self):
        self.clients = set()
        self.backend_uri = f"ws://localhost:{BACKEND_PORT}"  # Enterprise backend port
        self.do_button_uri = f"ws://localhost:{DO_BUTTON_PORT}"  # DO Button port
        logger.info(f"Initializing Bridge Server: backend={self.backend_uri}, do_button={self.do_button_uri}")

    async def forward_to_backend(self, client_ws, message):
        """Forward message to backend and return response"""
        try:
            logger.info(f"Forwarding to backend: {message[:100]}...")
            async with websockets.connect(self.backend_uri, ping_interval=None) as backend_ws:
                await backend_ws.send(message)
                response = await backend_ws.recv()
                logger.info(f"Received from backend: {response[:100]}...")
                return response
        except Exception as e:
            logger.error(f"Error forwarding to backend: {e}")
            return json.dumps({
                "type": "error",
                "message": f"Backend connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def forward_to_do_button(self, client_ws, message):
        """Forward message to DO Button server and return response"""
        try:
            logger.info(f"Forwarding to DO Button: {message[:100]}...")
            async with websockets.connect(self.do_button_uri, ping_interval=None) as do_button_ws:
                await do_button_ws.send(message)
                response = await do_button_ws.recv()
                logger.info(f"Received from DO Button: {response[:100]}...")
                return response
        except Exception as e:
            logger.error(f"Error forwarding to DO Button: {e}")
            return json.dumps({
                "type": "error",
                "message": f"DO Button connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

async def handle_client(websocket, path):
    """Handle client connections"""
    bridge = OverlayBridgeServer()
    logger.info(f"Client connected from {websocket.remote_address}")
    bridge.clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                # Parse the message to determine routing
                data = json.loads(message)
                message_type = data.get("type", "")
                
                # Handle different message types
                if message_type == "execute_plan":
                    # Forward plan execution to DO Button server
                    response = await bridge.forward_to_do_button(websocket, message)
                    await websocket.send(response)
                elif message_type == "agent_confirmation" and data.get("action") == "approve":
                    # Special handling for agent mode confirmations
                    plan_data = data.get("plan", {})
                    plan_id = data.get("plan_id", "")
                    
                    # First, acknowledge receipt of confirmation
                    await websocket.send(json.dumps({
                        "type": "confirmation_received",
                        "plan_id": plan_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Then forward to DO Button for execution
                    execution_message = json.dumps({
                        "type": "execute_plan",
                        "plan_id": plan_id,
                        "plan": plan_data
                    })
                    
                    execution_response = await bridge.forward_to_do_button(websocket, execution_message)
                    await websocket.send(execution_response)
                else:
                    # All other messages go to the backend
                    response = await bridge.forward_to_backend(websocket, message)
                    await websocket.send(response)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Bridge error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {e}")
    finally:
        bridge.clients.remove(websocket)

async def main():
    host = "0.0.0.0"  # Listen on all interfaces
    port = BRIDGE_PORT
    
    logger.info(f"Starting Overlay Bridge Server on port {port}")
    logger.info(f"Backend URI: ws://localhost:{BACKEND_PORT}")
    logger.info(f"DO Button URI: ws://localhost:{DO_BUTTON_PORT}")
    
    # Ensure backend server is running before starting
    backend_available = False
    for _ in range(5):
        try:
            async with websockets.connect(f"ws://localhost:{BACKEND_PORT}", ping_interval=None) as ws:
                backend_available = True
                logger.info("Successfully connected to backend server")
                break
        except:
            logger.warning(f"Backend server not available, retrying in 2 seconds...")
            await asyncio.sleep(2)
    
    if not backend_available:
        logger.warning("Backend server not available after retries, bridge will attempt to connect on demand")
    
    server = await websockets.serve(
        handle_client, 
        host, 
        port, 
        ping_interval=50,
        ping_timeout=300
    )
    
    print(f"Overlay Bridge Server running on ws://{host}:{port}")
    print(f"Connecting to: Backend={BACKEND_PORT}, DO Button={DO_BUTTON_PORT}")
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
