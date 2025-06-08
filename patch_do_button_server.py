#!/usr/bin/env python3
"""
Patch the DO button server to support suggestion message types
This script creates a wrapper server that forwards all messages but adds suggestion support
"""
import asyncio
import websockets
import json
import logging
import os
import signal
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("suggestion_server_patch")

# Server configuration
LISTEN_PORT = 8769  # New suggestion-enabled server
DO_BUTTON_PORT = 8765  # Original DO button server
PROXY_PORT = 8766  # Proxy server port

# Connected clients
clients = set()

# Handle termination signals
running = True
def signal_handler(sig, frame):
    global running
    logger.info("Shutting down...")
    running = False
    loop = asyncio.get_event_loop()
    loop.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def forward_to_do_button(message):
    """Forward a message to the DO button server"""
    try:
        async with websockets.connect(f"ws://localhost:{DO_BUTTON_PORT}") as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.debug(f"DO button welcome: {welcome}")
            
            # Send the message
            await ws.send(message)
            
            # Get the response
            response = await ws.recv()
            logger.debug(f"DO button response: {response}")
            
            return response
    except Exception as e:
        logger.error(f"Error forwarding to DO button server: {e}")
        return json.dumps({
            "type": "error",
            "error": f"Failed to forward to DO button server: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

async def handle_client(websocket, path):
    """Handle a client connection"""
    clients.add(websocket)
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "server_version": "1.0.0",
            "capabilities": ["agent_confirmation", "button_action", "do_button", "suggestion"],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                
                # Handle suggestion messages specially
                if msg_type == "suggestion":
                    logger.info(f"Handling suggestion message")
                    
                    # Extract key data from suggestion
                    suggestion_text = data.get("response", "")
                    buttons = data.get("buttons", [])
                    importance = data.get("importance", "medium")
                    play_sound = data.get("play_sound", True)
                    plan_id = data.get("plan_id", f"suggestion_{datetime.now().timestamp()}")
                    
                    # Forward it as a chat message to the client
                    notification = {
                        "type": "chat_message",
                        "sender": "system",
                        "message": suggestion_text,
                        "timestamp": datetime.now().isoformat(),
                        "suggestion": True,
                        "importance": importance,
                        "buttons": buttons,
                        "plan_id": plan_id
                    }
                    
                    await websocket.send(json.dumps(notification))
                    logger.info(f"Sent suggestion notification to client")
                    
                    # Also try to send it as a notification
                    try:
                        alert = {
                            "type": "notification",
                            "title": "Suggestion",
                            "message": suggestion_text,
                            "importance": importance,
                            "buttons": buttons,
                            "plan_id": plan_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send(json.dumps(alert))
                        logger.info(f"Sent suggestion alert to client")
                    except:
                        pass
                
                # Forward other message types to DO button server
                else:
                    logger.info(f"Forwarding message type: {msg_type}")
                    response = await forward_to_do_button(message)
                    await websocket.send(response)
            
            except json.JSONDecodeError:
                logger.error("Invalid JSON")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }))
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    
    finally:
        clients.remove(websocket)

async def main():
    """Start the server"""
    # Check if the port is available
    try:
        server = await websockets.serve(handle_client, "localhost", LISTEN_PORT)
        logger.info(f"🚀 Suggestion-enabled server started on port {LISTEN_PORT}")
        logger.info(f"🔄 Forwarding non-suggestion messages to DO button server on port {DO_BUTTON_PORT}")
        logger.info(f"❗ IMPORTANT: Update the overlay config.js to use port {LISTEN_PORT} instead of {DO_BUTTON_PORT}")
        
        # Keep running
        while running:
            await asyncio.sleep(1)
            
        server.close()
        await server.wait_closed()
        
    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.error(f"Port {LISTEN_PORT} is already in use")
        else:
            logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)