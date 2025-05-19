#!/usr/bin/env python3
"""
Enhanced WebSocket Server with LocalLLM Integration
"""
import asyncio
import json
import logging
import websockets
import sys
import os
from datetime import datetime
from llm.model import LocalLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
llm = None

async def handle_client(websocket, path):
    """Handle a client connection"""
    client_id = f"client_{len(connected_clients) + 1}"
    connected_clients.add(websocket)
    
    logger.info(f"Client connected: {client_id}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "message": "Connected to enhanced LLM server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received {msg_type} message from client {client_id}")
                
                if msg_type == 'user_interaction':
                    # Process LLM request
                    query = data.get('payload', {}).get('query', '')
                    logger.info(f"Processing query: {query[:50]}...")
                    
                    # Generate response using LocalLLM
                    response = await llm.generate_response([{
                        "role": "user",
                        "content": query
                    }])
                    
                    # Send response back
                    await websocket.send(json.dumps({
                        "type": "query_response",
                        "payload": {
                            "response": response,
                            "model": llm.model_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    finally:
        connected_clients.remove(websocket)

async def main():
    """Main function to run the enhanced WebSocket server"""
    global llm
    
    try:
        # Initialize LLM
        llm = LocalLLM(model_name="mistral")
        if not await llm.ensure_model_available():
            logger.error("Failed to initialize LLM")
            return
            
        # Start WebSocket server
        server = await websockets.serve(
            handle_client,
            "localhost",
            8765,
            ping_interval=None,
            ping_timeout=None
        )
        
        logger.info("Enhanced WebSocket server started on ws://localhost:8765")
        
        # Keep server running
        await server.wait_closed()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0) 