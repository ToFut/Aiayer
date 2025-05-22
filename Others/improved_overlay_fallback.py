#!/usr/bin/env python3
"""
Improved Overlay Chat Fallback Service

This script provides a reliable fallback service for the overlay chat
that ensures responses are always provided, even when the LLM service
is unavailable or timing out.

This version specifically handles llm_request messages for the overlay chat.
"""
import asyncio
import websockets
import json
import logging
import sys
import os
import time
import random
from datetime import datetime

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/improved_fallback.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Track client connections
connected_clients = set()
llm_requests = {}  # Track active LLM requests

# Sample fallback responses for different query types
FALLBACK_RESPONSES = {
    "examples": [
        "I can help you with monitoring your screen content, tracking application processes, and providing context-aware assistance. I can analyze what's on your screen, understand your work context, and offer relevant information.",
        "The system can monitor your screen, track running applications, and provide contextual assistance. It uses AI to understand your work environment and help you with relevant information and suggestions.",
        "I can demonstrate capabilities like screen content analysis, process monitoring, and context-aware assistance. The system understands what you're working on and provides relevant information based on your current context."
    ],
    "help": [
        "I can assist you with understanding your screen content, monitoring running applications, and providing context-based assistance. What specific help do you need?",
        "This AI assistant can help you by analyzing your screen, tracking your active programs, and offering contextual assistance. How can I help you specifically?",
        "I'm designed to assist with context-aware tasks by monitoring your screen and running applications. I can provide relevant information based on what you're currently doing."
    ],
    "how_works": [
        "This system works by collecting data from various sensors that monitor your screen content and running processes. It uses this context to provide more relevant assistance tailored to what you're doing.",
        "The system uses screen and process sensors to understand your current context. It then uses this information to provide more relevant and helpful responses based on what you're working on.",
        "This AI assistant monitors your screen content and running applications to understand your work context. This information helps it provide more relevant assistance and suggestions."
    ],
    "default": [
        "I'm your AI assistant designed to understand your work context and provide relevant assistance. I can monitor your screen, track applications, and help with various tasks.",
        "I'm here to assist you with your work by understanding your context and providing relevant information. I can analyze what's on your screen and what applications you're using to offer better assistance.",
        "As your AI assistant, I can help you with various tasks by understanding your current context. I monitor your screen and running applications to provide more relevant assistance."
    ]
}

def get_response_for_query(query):
    """Generate an appropriate response based on the query content."""
    query_lower = query.lower()
    
    # Check for query patterns
    if any(kw in query_lower for kw in ["example", "show me", "what can you do"]):
        return random.choice(FALLBACK_RESPONSES["examples"])
    elif any(kw in query_lower for kw in ["help", "assist"]):
        return random.choice(FALLBACK_RESPONSES["help"])
    elif any(kw in query_lower for kw in ["how", "work"]):
        return random.choice(FALLBACK_RESPONSES["how_works"])
    else:
        return random.choice(FALLBACK_RESPONSES["default"])

async def handle_client(websocket, path):
    """Handle incoming WebSocket client connections."""
    client_id = id(websocket)
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to fallback service"
            }
        }))
        
        # Process incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                
                # Handle specific message types
                if msg_type == "register":
                    # Process registration message
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client_type', 'unknown')
                    logger.info(f"Client {client_id} registered as {client_type}")
                    
                    # Send response
                    await websocket.send(json.dumps({
                        "type": "registration_successful",
                        "payload": {
                            "client_id": client_id,
                            "client_type": client_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                elif msg_type == "llm_request":
                    # Process LLM request
                    await handle_llm_request(websocket, client_id, data)
                    
                elif msg_type == "ping":
                    # Respond to ping
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "payload": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                else:
                    # Echo other message types
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "payload": {
                            "original_message": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        if client_id in llm_requests:
            del llm_requests[client_id]
        logger.info(f"Client {client_id} removed from tracking")

async def handle_llm_request(websocket, client_id, data):
    """Handle an LLM request message."""
    # Extract the query from the request
    payload = data.get('payload', {})
    query = payload.get('query', '')
    
    if not query:
        logger.warning(f"Empty query from client {client_id}")
        await websocket.send(json.dumps({
            "type": "error",
            "payload": {
                "message": "Empty query",
                "timestamp": datetime.now().isoformat()
            }
        }))
        return
    
    # Log the request
    logger.info(f"LLM request from client {client_id}: {query[:50]}...")
    
    # Track the request
    llm_requests[client_id] = {
        "query": query,
        "timestamp": time.time(),
        "websocket": websocket,
        "responded": False
    }
    
    # Generate and send a response
    response_text = get_response_for_query(query)
    
    await websocket.send(json.dumps({
        "type": "query_response",
        "payload": {
            "query": query,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "is_fallback": True
        }
    }))
    
    logger.info(f"Sent fallback response to client {client_id}")
    llm_requests[client_id]["responded"] = True

async def start_server(host="0.0.0.0", port=8765):
    """Start the WebSocket server."""
    try:
        server = await websockets.serve(
            handle_client, 
            host, 
            port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"Fallback service started on ws://{host}:{port}")
        return server
    except Exception as e:
        logger.error(f"Error starting server on port {port}: {e}")
        return None

async def main():
    """Run the improved fallback service."""
    # Try to start on primary port (8765)
    primary_server = await start_server(port=8765)
    
    # Start on secondary port (8767) regardless
    secondary_server = await start_server(port=8767)
    
    if primary_server or secondary_server:
        # Save PID to file
        try:
            with open('pids/improved_fallback.pid', 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"PID {os.getpid()} saved to pids/improved_fallback.pid")
        except Exception as e:
            logger.error(f"Failed to save PID: {e}")
        
        # Wait forever
        await asyncio.Future()
    else:
        logger.error("Failed to start servers on all ports")
        sys.exit(1)

if __name__ == "__main__":
    os.makedirs("pids", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        sys.exit(1)