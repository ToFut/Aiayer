#!/usr/bin/env python3
"""
Fixed Epiphany Mode Connector

This script serves as a bridge between the memory suggestion system and the overlay frontend.
It maintains a persistent WebSocket connection to the overlay and ensures that
suggestions are properly delivered to the Epiphany Mode component.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/epiphany_mode_connector.log')
    ]
)

logger = logging.getLogger('epiphany_mode_connector')

# Configuration
WS_PORT = 8765  # The port that the overlay connects to for suggestions
SUGGESTION_CHECK_INTERVAL = 5  # How often to check for new suggestions (seconds)
MEMORY_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory/conscious.json")

# State
connected_clients = {}
suggestion_queue = []
last_suggestion_id = None
suggestion_id_counter = 0

async def send_suggestion_to_clients(suggestion):
    """Send a suggestion to all connected epiphany mode clients"""
    global connected_clients
    
    if not connected_clients:
        logger.warning("No connected clients to send suggestion to")
        return False
    
    # Create a proper suggestion message payload
    payload = {
        "type": "suggestion",
        "suggestion_id": f"sugg_{int(time.time() * 1000)}_{suggestion_id_counter}",
        "title": suggestion.get("title", "Suggestion"),
        "message": suggestion.get("message", "I have a suggestion for you"),
        "confidence": suggestion.get("confidence", 0.9),
        "timestamp": datetime.now().isoformat(),
    }
    
    # Add action buttons if available
    if "actions" in suggestion:
        payload["actions"] = suggestion["actions"]
    
    success = False
    clients_to_remove = []
    
    for client_id, client in connected_clients.items():
        if client["client_type"] in ["epiphany_mode", "epiphany_mode_handler", "autonomous_suggestion_handler"]:
            try:
                if client["websocket"].open:
                    await client["websocket"].send(json.dumps(payload))
                    logger.info(f"Sent suggestion to client {client_id}")
                    success = True
                else:
                    logger.warning(f"Client {client_id} websocket is not open")
                    clients_to_remove.append(client_id)
            except Exception as e:
                logger.error(f"Failed to send suggestion to client {client_id}: {e}")
                clients_to_remove.append(client_id)
    
    # Clean up disconnected clients
    for client_id in clients_to_remove:
        if client_id in connected_clients:
            del connected_clients[client_id]
    
    return success

async def check_memory_for_suggestions():
    """Check the conscious memory file for new suggestions"""
    global last_suggestion_id, suggestion_id_counter
    
    try:
        if not os.path.exists(MEMORY_FILE_PATH):
            logger.warning(f"Memory file not found: {MEMORY_FILE_PATH}")
            return
        
        with open(MEMORY_FILE_PATH, 'r') as f:
            try:
                memory_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse memory file: {MEMORY_FILE_PATH}")
                return
        
        # Look for suggestion patterns in memory
        for memory in memory_data:
            if isinstance(memory, dict) and "content" in memory and "memory_type" in memory:
                content = memory.get("content", "")
                memory_id = memory.get("memory_id", "")
                
                if "SUGGESTION:" in content and memory_id != last_suggestion_id:
                    # Found a new suggestion
                    logger.info(f"Found new suggestion in memory: {memory_id}")
                    last_suggestion_id = memory_id
                    
                    # Parse the suggestion content
                    # Format: SUGGESTION: Title | Message | Confidence
                    parts = content.split("SUGGESTION:")[1].strip().split("|")
                    
                    suggestion = {
                        "title": parts[0].strip() if len(parts) > 0 else "New Suggestion",
                        "message": parts[1].strip() if len(parts) > 1 else "I've detected a pattern that might be helpful.",
                        "confidence": float(parts[2].strip()) if len(parts) > 2 and parts[2].strip().replace('.', '', 1).isdigit() else 0.9
                    }
                    
                    # Add to suggestion queue
                    suggestion_queue.append(suggestion)
                    
                    # Send immediately if clients are connected
                    suggestion_id_counter += 1
                    await send_suggestion_to_clients(suggestion)
    except Exception as e:
        logger.error(f"Error checking memory for suggestions: {e}")

async def process_suggestion_queue():
    """Process any queued suggestions"""
    global suggestion_queue, suggestion_id_counter
    
    if not suggestion_queue:
        return
    
    logger.info(f"Processing suggestion queue: {len(suggestion_queue)} items")
    
    # Try to send each suggestion
    suggestions_to_keep = []
    for suggestion in suggestion_queue:
        suggestion_id_counter += 1
        success = await send_suggestion_to_clients(suggestion)
        
        if not success:
            # Keep in queue to retry later
            suggestions_to_keep.append(suggestion)
    
    suggestion_queue = suggestions_to_keep

async def handle_client(websocket, path):
    """Handle a websocket client connection"""
    client_id = f"client_{id(websocket)}"
    client_type = "unknown"
    
    try:
        # Add the client to our connected clients
        connected_clients[client_id] = {
            "websocket": websocket,
            "client_type": client_type,
            "connected_at": time.time()
        }
        
        logger.info(f"Client {client_id} connected from {websocket.remote_address[0]}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type", "")
                
                logger.info(f"Received message type: {message_type}")
                
                # Handle client registration
                if message_type == "register":
                    client_type = data.get("client_type", "unknown")
                    connected_clients[client_id]["client_type"] = client_type
                    
                    logger.info(f"Client {client_id} registered as {client_type}")
                    
                    # Send a welcome message
                    await websocket.send(json.dumps({
                        "type": "welcome",
                        "message": f"Welcome to the Epiphany Mode system",
                        "server_time": datetime.now().isoformat()
                    }))
                    
                    # Send any queued suggestions immediately
                    if client_type in ["epiphany_mode", "epiphany_mode_handler", "autonomous_suggestion_handler"]:
                        if suggestion_queue:
                            logger.info(f"Sending {len(suggestion_queue)} queued suggestions to new client")
                            for suggestion in suggestion_queue[:]:
                                success = await send_suggestion_to_clients(suggestion)
                                if success:
                                    suggestion_queue.remove(suggestion)
                
                # Handle ping messages
                elif message_type == "ping":
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }))
                
                # Handle suggestion response (when user approves or rejects)
                elif message_type == "suggestion_response":
                    suggestion_id = data.get("suggestion_id")
                    approved = data.get("approved", False)
                    
                    logger.info(f"Suggestion {suggestion_id} {'approved' if approved else 'rejected'}")
                    
                    # Here you would handle any backend actions in response to the user's decision
                    
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} connection closed")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        # Remove client from connected clients
        if client_id in connected_clients:
            del connected_clients[client_id]
        logger.info(f"Client {client_id} disconnected")

async def send_test_suggestion():
    """Send a test suggestion to all connected clients"""
    suggestion = {
        "title": "Epiphany Mode Test",
        "message": "This is a test suggestion from the fixed Epiphany Mode Connector. If you're seeing this, the system is working correctly!",
        "confidence": 0.95,
        "actions": [
            {
                "action_id": "test_action",
                "action_text": "Test Action"
            }
        ]
    }
    
    await send_suggestion_to_clients(suggestion)
    logger.info("Sent test suggestion to all clients")

async def background_tasks():
    """Run periodic background tasks"""
    while True:
        try:
            # Process any queued suggestions
            await process_suggestion_queue()
            
            # Check memory for new suggestions
            await check_memory_for_suggestions()
            
            # Log status
            logger.info(f"Server status: {len(connected_clients)} clients connected, {len(suggestion_queue)} suggestions queued")
            
        except Exception as e:
            logger.error(f"Error in background tasks: {e}")
        
        await asyncio.sleep(SUGGESTION_CHECK_INTERVAL)

async def main():
    """Main entry point"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Start WebSocket server
    logger.info(f"Starting Epiphany Mode Connector server on port {WS_PORT}")
    
    stop_event = asyncio.Event()
    
    def signal_handler(*args):
        logger.info("Shutdown signal received, stopping server...")
        stop_event.set()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, signal_handler)
    
    # Start the WebSocket server
    async with websockets.serve(handle_client, "localhost", WS_PORT):
        # Start background tasks
        bg_task = asyncio.create_task(background_tasks())
        
        # Send a test suggestion after a short delay
        await asyncio.sleep(5)
        await send_test_suggestion()
        
        # Wait for shutdown signal
        await stop_event.wait()
        
        # Cancel background task
        bg_task.cancel()
        
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())