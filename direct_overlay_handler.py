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
