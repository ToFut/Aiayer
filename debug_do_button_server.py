#\!/usr/bin/env python3
"""
Debug DO Button WebSocket Server
Echoes back any button_action messages to help debug the DO button issue
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_do_button_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('debug_do_button_server')

# Track connected clients
connected_clients = set()

# Handler for WebSocket connections
async def handler(websocket, path=None):
    """WebSocket connection handler"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "server_version": "1.0.0",
            "capabilities": ["debug", "echo", "button_action"],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                logger.info(f"Received raw message: {message}")
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type}")
                
                # Echo back all messages
                await websocket.send(json.dumps({
                    "type": "echo",
                    "original_message": data,
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Handle button_action messages
                if msg_type == 'button_action':
                    logger.info(f"🔥 BUTTON ACTION RECEIVED: {data}")
                    action = data.get('action', '').upper()
                    plan_id = data.get('plan_id', '')
                    
                    # Send immediate acknowledgment
                    await websocket.send(json.dumps({
                        "type": "button_action_received",
                        "action": action,
                        "plan_id": plan_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Simulate execution progress
                    await websocket.send(json.dumps({
                        "type": "agent_progress",
                        "progress": 20,
                        "message": "Starting execution...",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    await asyncio.sleep(1)
                    
                    await websocket.send(json.dumps({
                        "type": "agent_progress",
                        "progress": 50,
                        "message": "Processing action...",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    await asyncio.sleep(1)
                    
                    await websocket.send(json.dumps({
                        "type": "agent_progress",
                        "progress": 100,
                        "message": "Execution complete\!",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Send success response
                    await websocket.send(json.dumps({
                        "type": "agent_execution_success",
                        "summary": f"Successfully executed {action} for plan {plan_id}",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Handle other message types
                else:
                    # Just acknowledge receipt
                    await websocket.send(json.dumps({
                        "type": "message_received",
                        "message_type": msg_type,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
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
        logger.info(f"Client {client_id} disconnected")
    
    finally:
        connected_clients.remove(websocket)

async def main():
    """Start the WebSocket server"""
    port = 8765
    
    try:
        # First check if port is in use
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is already in use. Killing existing process...")
            try:
                import subprocess
                subprocess.run(f"lsof -t -i:{port} | xargs kill -9", shell=True)
                logger.info(f"Killed process on port {port}")
                await asyncio.sleep(2)  # Wait for port to be released
            except Exception as kill_error:
                logger.error(f"Failed to kill process on port {port}: {kill_error}")
                port = 8766  # Use alternative port
                logger.info(f"Using alternative port {port}")
    
    # Start server
    logger.info(f"Starting WebSocket server on port {port}")
    server = await websockets.serve(handler, "localhost", port)
    logger.info(f"WebSocket server running on ws://localhost:{port}")
    
    # Write port to file for clients to discover
    with open("logs/debug_server_port.txt", "w") as f:
        f.write(str(port))
    
    # Keep server running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped by user")
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")
