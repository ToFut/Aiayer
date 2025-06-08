#!/usr/bin/env python3
"""
Simple Backend Server - Fallback for the enhanced enterprise backend
This server provides a simpler version that doesn't hang on startup
"""

import asyncio
import json
import logging
import websockets
import time
import os
from datetime import datetime

# Setup logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/simple_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_backend")

# Track connected clients
connected_clients = set()

async def handle_client(websocket, path=None):
    """Handle WebSocket client connection with path parameter support"""
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected on path: {path}")
    connected_clients.add(websocket)
    
    # Send welcome message
    welcome_msg = {
        "type": "welcome",
        "message": "Connected to Simple Backend Server (Fallback)",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
    await websocket.send(json.dumps(welcome_msg))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data.get('mode', 'unknown')} - {data.get('message', '')}")
                
                # Process message based on mode
                response = await process_message(data, client_id)
                
                # Send response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    
    finally:
        connected_clients.remove(websocket)

async def process_message(data, client_id):
    """Process message from client"""
    mode = data.get("mode", "General")
    message = data.get("message", "")
    session_id = data.get("session_id", str(client_id))
    
    logger.info(f"Processing {mode} message: {message}")
    
    # Simple mock responses based on mode
    if mode.lower() == "agent":
        return {
            "type": "agent_automation_plan",
            "mode": mode,
            "response": "⚠️ **Simple Fallback Mode**\n\nThe enhanced enterprise backend is currently unavailable. This is a simple fallback response.\n\nYour command was: " + message,
            "client_id": str(client_id),
            "timestamp": datetime.now().isoformat(),
            "ai_powered": False,
            "success": True,
            "requiresConfirmation": True,
            "agentSessionId": session_id,
            "buttons": [
                {"text": "⚠️ Restart System", "action": "restart_system", "style": "warning-btn"},
                {"text": "❌ Cancel", "action": "cancel_plan", "style": "cancel-btn"}
            ],
            "plan_id": f"fallback_{int(time.time())}"
        }
    elif mode.lower() == "ask":
        return {
            "type": "ask_response",
            "mode": mode,
            "response": "⚠️ **Simple Fallback Mode**\n\nThe enhanced enterprise backend is currently unavailable. This is a simple fallback response.\n\nYour question was: " + message,
            "client_id": str(client_id),
            "timestamp": datetime.now().isoformat()
        }
    elif mode.lower() == "suggest":
        return {
            "type": "suggestion",
            "mode": mode,
            "response": "⚠️ **Simple Fallback Mode**\n\nThe enhanced enterprise backend is currently unavailable. This is a simple fallback response.\n\nYour request was: " + message,
            "client_id": str(client_id),
            "timestamp": datetime.now().isoformat()
        }
    else:  # General mode or any other
        return {
            "type": "chat_response",
            "mode": mode,
            "response": "⚠️ **Simple Fallback Mode**\n\nThe enhanced enterprise backend is currently unavailable. This is a simple fallback response.\n\nYour message was: " + message,
            "client_id": str(client_id),
            "timestamp": datetime.now().isoformat()
        }

async def start_server():
    """Start WebSocket server"""
    logger.info("Starting Simple Backend Server on port 8767")
    
    # Create server with proper handler that accepts path parameter
    server = await websockets.serve(
        handle_client,  # This will now properly receive path parameter
        "0.0.0.0",  # Listen on all interfaces for external connections
        8767,
        ping_interval=50,
        ping_timeout=300
    )
    
    # Print status
    print(f"Simple Backend Server running on ws://0.0.0.0:8767")
    print(f"This is a fallback server when the enhanced enterprise backend fails")
    
    # Keep server running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        # Start server
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")