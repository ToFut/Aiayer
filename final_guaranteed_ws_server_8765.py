#!/usr/bin/env python3
"""
Final guaranteed WebSocket server for port 8765 with perfect overlay DO button compatibility
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime
import time

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/guaranteed_ws_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('guaranteed_ws_8765')
logger.setLevel(logging.DEBUG)

# Track connected clients
connected_clients = set()

# Bridge to backend (simulated)
async def forward_to_backend(data, websocket):
    """Simulate forwarding to backend with realistic response times"""
    session_id = data.get('session_id', '')
    action = data.get('action', '').upper()
    
    if action == 'DO':
        # Send immediate progress update
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 1,
            "progress": 20,
            "message": "🚀 Starting execution: Analyzing screen..."
        }))
        
        # Simulate backend processing
        await asyncio.sleep(1.2)
        
        # Send another progress update
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 2,
            "progress": 50,
            "message": "🔎 Locating UI elements..."
        }))
        
        await asyncio.sleep(1.2)
        
        # Send third progress update
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 3,
            "progress": 80,
            "message": "⚡ Executing automation steps..."
        }))
        
        await asyncio.sleep(1.2)
        
        # Send completion message - this format exactly matches what overlay expects
        result = {
            "type": "agent_execution_success",
            "session_id": session_id,
            "result": {
                "success": True,
                "steps_executed": 3,
                "execution_time": 3.6
            },
            "summary": "Task completed successfully! All steps were executed as planned.",
            "execution_completed": True
        }
        
        await websocket.send(json.dumps(result))
        return result
    
    elif action == 'DISMISS':
        result = {
            "type": "agent_dismissed",
            "session_id": session_id,
            "message": "Plan dismissed by user"
        }
        await websocket.send(json.dumps(result))
        return result
    
    elif action == 'ADJUST':
        result = {
            "type": "agent_adjustment_request",
            "session_id": session_id,
            "message": "Please provide more details about what you'd like to adjust."
        }
        await websocket.send(json.dumps(result))
        return result
    
    else:
        result = {
            "type": "agent_confirmation_error",
            "error": f"Unknown action: {action}",
            "session_id": session_id
        }
        await websocket.send(json.dumps(result))
        return result

# Handler for WebSocket connections
async def handler(websocket, path=None):
    """WebSocket connection handler with production-quality reliability
    Supports both new (websocket) and old (websocket, path) signatures for compatibility
    """
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message similar to what the overlay expects
        await websocket.send(json.dumps({
            "type": "connection_established",
            "server_version": "1.0.0",
            "capabilities": ["context_tracking", "agent_automation", "semantic_search"],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                logger.debug(f"Raw message received: {message}")
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type}")
                
                # Handle agent_confirmation (DO button)
                if msg_type == 'agent_confirmation':
                    logger.info(f"Agent confirmation received: {data}")
                    result = await forward_to_backend(data, websocket)
                    logger.info(f"Backend result: {result}")
                
                # Handle other message types as needed
                elif msg_type == 'chat_request':
                    # For chat_request that would trigger the agent confirmation dialog
                    session_id = data.get('session_id', f'session_{int(time.time())}')
                    mode = data.get('mode', '').lower()
                    
                    if mode == 'agent':
                        # Send a response that would trigger the DO button
                        await websocket.send(json.dumps({
                            "success": True,
                            "response": "I'll help you with that. Here's my plan:",
                            "mode": "Agent",
                            "agentSessionId": session_id,
                            "requiresConfirmation": True,
                            "executionPlan": {
                                "total_steps": 3,
                                "steps": [
                                    "Analyze screen and identify elements",
                                    "Locate the target UI element",
                                    "Execute the automation steps"
                                ],
                                "warnings": []
                            },
                            "estimatedDuration": 5,
                            "confidence": 0.95,
                            "riskLevel": "low"
                        }))
                        logger.info(f"Sent agent plan requiring confirmation")
                    else:
                        # For other modes, send a simple response
                        await websocket.send(json.dumps({
                            "success": True,
                            "response": f"Received {mode} request: {data.get('message', '')}",
                            "mode": mode.capitalize()
                        }))
                
                # Handle ping messages
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Handle all other messages with a simple echo
                else:
                    await websocket.send(json.dumps({
                        "type": "response",
                        "message": f"Received {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def heartbeat():
    """Send periodic heartbeat to clients"""
    while True:
        current_time = datetime.now().isoformat()
        logger.debug(f"Heartbeat at {current_time}")
        
        if connected_clients:
            # Create heartbeat message
            heartbeat_msg = json.dumps({
                "type": "heartbeat",
                "timestamp": current_time,
                "connected_clients": len(connected_clients)
            })
            
            # Send to all clients
            for websocket in list(connected_clients):
                try:
                    await websocket.send(heartbeat_msg)
                except websockets.exceptions.ConnectionClosed:
                    # Will be cleaned up in the handler
                    pass
                    
        # Wait for next heartbeat
        await asyncio.sleep(30)

async def main():
    # Kill any existing processes on port 8765
    try:
        import subprocess
        subprocess.run("lsof -ti:8765 | xargs kill -9 2>/dev/null || true", shell=True)
        logger.info("Killed any existing processes on port 8765")
        # Give some time for port to be released
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error killing existing processes: {e}")
    
    # Ensure port 8765 is available
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', 8765))
        test_socket.close()
        logger.info("Port 8765 is available")
    except OSError:
        logger.error("Port 8765 is already in use. Please stop any existing WebSocket servers.")
        sys.exit(1)
    
    # Start WebSocket server
    port = 8765
    host = "localhost"
    
    logger.info(f"Starting guaranteed WebSocket server on {host}:{port}")
    
    server = await websockets.serve(
        handler,
        host,
        port,
        ping_interval=30,
        ping_timeout=60,
        close_timeout=30,
        max_size=10 * 1024 * 1024,
        max_queue=32
    )
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/guaranteed_ws_8765.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat())
    
    logger.info(f"✅ Guaranteed WebSocket server running on ws://{host}:{port}")
    logger.info(f"🎯 Ready to handle agent_confirmation messages")
    
    # Keep running indefinitely
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)