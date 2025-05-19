#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
import logging
import os

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fix_query.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def bridge_messages():
    """
    Act as a message bridge between client and server.
    Intercepts messages and fixes formatting if needed.
    """
    # Connect to the server
    try:
        logger.info("Starting message bridge...")
        server_ws = await websockets.connect('ws://localhost:8765')
        logger.info("Connected to server on port 8765")
        
        # Start a local server for the client to connect to
        port = 8766
        logger.info(f"Starting local bridge server on port {port}")
        
        # Store client connections
        clients = set()
        
        async def handle_client(websocket, path):
            logger.info(f"Client connected from {websocket.remote_address}")
            clients.add(websocket)
            
            try:
                # Send initial connection message
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "status": "connected",
                        "bridged": True,
                        "timestamp": time.time()
                    }
                }))
                
                # Handle messages from client
                async for message in websocket:
                    logger.info(f"Received from client: {message[:100]}...")
                    
                    try:
                        data = json.loads(message)
                        
                        # Intercept and fix user_interaction messages
                        if data.get("type") == "user_interaction":
                            payload = data.get("payload", {})
                            
                            # Check and fix the message structure
                            if isinstance(payload, dict) and "query" in payload and "type" not in payload:
                                logger.info("Fixing user_interaction message structure")
                                # Add the missing "type": "query" field
                                data["payload"] = {
                                    "type": "query",
                                    "query": payload["query"]
                                }
                                logger.info(f"Fixed message: {json.dumps(data)}")
                        
                        # Forward the message to the server
                        await server_ws.send(json.dumps(data))
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from client: {message[:100]}...")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Invalid JSON format"
                            }
                        }))
                    except Exception as e:
                        logger.error(f"Error processing client message: {e}")
            
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client disconnected")
            finally:
                clients.remove(websocket)
        
        # Start server
        async with websockets.serve(handle_client, "localhost", port):
            logger.info(f"Bridge server running on ws://localhost:{port}")
            
            # Listen for messages from the server
            while True:
                try:
                    # Wait for server messages
                    message = await server_ws.recv()
                    logger.info(f"Received from server: {message[:100]}...")
                    
                    # Broadcast to all clients
                    if clients:
                        await asyncio.gather(
                            *[client.send(message) for client in clients],
                            return_exceptions=True
                        )
                except websockets.exceptions.ConnectionClosed:
                    logger.error("Server connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error from server: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Bridge startup error: {e}")

if __name__ == "__main__":
    try:
        # Print instructions
        print("\n===== WebSocket Message Bridge =====")
        print("This bridge fixes message formatting issues")
        print("Main server: ws://localhost:8765")
        print("Bridge server: ws://localhost:8766")
        print("Connect your client to the bridge server instead of the main server")
        print("=====================================\n")
        
        asyncio.run(bridge_messages())
    except KeyboardInterrupt:
        print("\nBridge stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")