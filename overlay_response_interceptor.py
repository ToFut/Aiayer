#!/usr/bin/env python3
"""
Overlay Response Interceptor

This script creates a WebSocket server that intercepts requests to the existing
WebSocket servers on ports 8765 and 8767, provides immediate fallback responses
for LLM requests, and ensures the overlay chat always gets responses.

Uses ollama3.2:latest model with a 30-second timeout for LLM requests.

Usage:
  python overlay_response_interceptor.py
"""
import asyncio
import json
import logging
import sys
import os
import random
import websockets
from datetime import datetime
import signal
from llm_interceptor import InterceptorLLM

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/response_interceptor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
registered_clients = {}

# Initialize LLM interceptor
llm_interceptor = None

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

async def forward_to_backend(message, target_port):
    """Forward a message to the actual backend server."""
    try:
        uri = f"ws://localhost:{target_port}"
        async with websockets.connect(uri, close_timeout=5) as websocket:
            if message:  # Only send if there's a message
                await websocket.send(message)
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            return response
    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosedError, 
            ConnectionRefusedError, OSError) as e:
        logger.warning(f"Backend connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in forward_to_backend: {e}")
        return None

async def handle_client(websocket):
    """Handle WebSocket client connections."""
    client_id = id(websocket)
    connected_clients.add(websocket)
    target_port = 8765  # Default to main backend port
    
    try:
        logger.info(f"Client {client_id} connected")
        
        # Initially forward the connection_established message from the real backend
        try:
            response = await forward_to_backend("", target_port)
            if response:
                await websocket.send(response)
            else:
                # Send our own connection message if backend is unavailable
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client_id": client_id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "connected",
                        "message": "Connected to fallback service"
                    }
                }))
        except Exception as e:
            logger.error(f"Error during initial connection: {e}")
            # Send fallback connection message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "connected",
                    "message": "Connected to fallback service"
                }
            }))
        
        # Process incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                
                # Special handling for different message types
                if msg_type == 'llm_request':
                    # Extract the query
                    payload = data.get('payload', {})
                    query = payload.get('query', '')
                    
                    if not query:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "Empty query",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                        continue
                    
                    logger.info(f"LLM request from client {client_id}: {query[:50]}...")
                    
                    # First try to forward to the real backend
                    response = None
                    try:
                        response = await forward_to_backend(message, target_port)
                        if response:
                            await websocket.send(response)
                            continue
                    except Exception as e:
                        logger.error(f"Error forwarding to backend: {e}")
                    
                    # If no response from backend, use fallback response
                    fallback_response = get_response_for_query(query)
                    await websocket.send(json.dumps({
                        "type": "query_response",
                        "payload": {
                            "query": query,
                            "response": fallback_response,
                            "timestamp": datetime.now().isoformat(),
                            "source": "fallback"
                        }
                    }))
                elif msg_type == 'register':
                    # Register the client
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client_type', 'unknown')
                    registered_clients[client_id] = client_type
                    
                    logger.info(f"Client {client_id} registered as {client_type}")
                    
                    # Forward to backend if possible
                    response = await forward_to_backend(message, target_port)
                    
                    # Send our response if backend unavailable
                    if not response:
                        response = json.dumps({
                            "type": "registration_successful",
                            "payload": {
                                "client_id": client_id,
                                "client_type": client_type,
                                "timestamp": datetime.now().isoformat(),
                                "message": "Registered with fallback service"
                            }
                        })
                    
                    await websocket.send(response)
                
                elif msg_type == 'context_request':
                    # Try to forward
                    response = await forward_to_backend(message, target_port)
                    
                    # Send minimal context if backend unavailable
                    if not response:
                        response = json.dumps({
                            "type": "context_update",
                            "payload": {
                                "context": {
                                    "window": "Unknown",
                                    "active_apps": [],
                                    "screen_content": "",
                                    "timestamp": datetime.now().isoformat()
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                        })
                    
                    await websocket.send(response)
                
                elif msg_type == 'ping':
                    # Just respond with pong
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "payload": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                
                elif msg_type == 'disconnect':
                    logger.info(f"Client {client_id} requested disconnection")
                    break
                
                else:
                    # Forward other message types to backend
                    response = await forward_to_backend(message, target_port)
                    if response:
                        await websocket.send(response)
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} connection cleaned up")

async def status_broadcaster():
    """Periodically broadcast status updates to all clients."""
    while True:
        if connected_clients:
            try:
                # Create a status message
                message = json.dumps({
                    "type": "status_update",
                    "payload": {
                        "client_count": len(connected_clients),
                        "registered_clients": len(registered_clients),
                        "interceptor_active": True,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                # Send to all clients
                await asyncio.gather(
                    *[client.send(message) for client in connected_clients],
                    return_exceptions=True
                )
            except Exception as e:
                logger.error(f"Error in status broadcaster: {e}")
        
        await asyncio.sleep(30)  # Broadcast every 30 seconds

async def start_server(port=8766):
    """Start the WebSocket server on the specified port."""
    logger.info(f"Starting interceptor server on port {port}")
    
    # Create the server
    server = await websockets.serve(
        handle_client,
        "0.0.0.0",  # Bind to all interfaces
        port,
        ping_interval=30,
        ping_timeout=10
    )
    
    # Save PID to file
    try:
        os.makedirs("pids", exist_ok=True)
        with open('pids/response_interceptor.pid', 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"PID {os.getpid()} saved to pids/response_interceptor.pid")
    except Exception as e:
        logger.error(f"Failed to save PID: {e}")
    
    # Start status broadcaster
    asyncio.create_task(status_broadcaster())
    
    return server

def handle_shutdown(sig, frame):
    """Handle graceful shutdown."""
    logger.info("Shutdown signal received, closing server...")
    # Remove PID file
    try:
        if os.path.exists('pids/response_interceptor.pid'):
            os.remove('pids/response_interceptor.pid')
    except Exception as e:
        logger.error(f"Error removing PID file: {e}")
    sys.exit(0)

async def main():
    """Run the main application."""
    global llm_interceptor
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Initialize the LLM interceptor
    logger.info("Initializing LLM interceptor with llama3.2:latest model")
    try:
        llm_interceptor = InterceptorLLM(model_name="llama3.2:latest")
        await llm_interceptor.initialize()
        logger.info("LLM interceptor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM interceptor: {e}")
        logger.warning("Will continue with only fallback responses available")
    
    # Start the interceptor server on port 8766
    server = await start_server(8766)
    
    logger.info("Response interceptor server is running")
    logger.info("To use this server, connect to ws://localhost:8766 instead of the standard ports")
    
    # Keep the server running
    await asyncio.Future()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())