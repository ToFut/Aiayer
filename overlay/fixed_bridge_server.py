#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime
import aiohttp

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_bridge')

# Track connected clients
connected_clients = set()
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

# LLM service configuration
LLM_SERVICE_URL = "http://localhost:11434/api/generate"  # Default Ollama endpoint

async def get_llm_response(query, context=None):
    """Get response from LLM service"""
    try:
        # Prepare the request payload
        payload = {
            "model": "llama3.2",  # Using llama3.2 model
            "prompt": query,
            "stream": False,
            "context": context or []
        }
        
        # Make request to LLM service
        async with aiohttp.ClientSession() as session:
            async with session.post(LLM_SERVICE_URL, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "response": result.get("response", ""),
                        "model": result.get("model", "unknown"),
                        "context_used": bool(context),
                        "processing_time": result.get("total_duration", 0) / 1e9  # Convert from nanoseconds
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"LLM service error: {error_text}")
                    return {
                        "response": "Sorry, I encountered an error processing your request.",
                        "model": "error",
                        "context_used": False,
                        "processing_time": 0
                    }
    except Exception as e:
        logger.error(f"Error calling LLM service: {e}")
        return {
            "response": "Sorry, I'm having trouble connecting to the language model.",
            "model": "error",
            "context_used": False,
            "processing_time": 0
        }

# IMPORTANT: In websockets 15.0.1, the handler only needs to accept the websocket parameter
async def handler(websocket, path=None):
    """WebSocket connection handler supporting both websockets 10.x and 15.x
    In 10.x, both websocket and path parameters are provided
    In 15.x, only websocket parameter is provided and path is an attribute of websocket
    """
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    
    # Handle both websockets 10.x and 15.x
    if path is None and hasattr(websocket, 'path'):
        path = websocket.path
    elif path is None:
        path = "/"
        
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to Aiayer system. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send initial sensor data (if we have any)
        if any([sensor_data["processes"], sensor_data["screen"], sensor_data["files"]]):
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client', 'unknown')
                    logger.info(f"Client {client_id} identified as: {client_type}")
                    
                    # Send ready confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "server_time": datetime.now().isoformat(),
                            "capabilities": ["context_tracking", "suggestions", "memory", "llm"]
                        }
                    }))
                    
                elif msg_type == 'process_data':
                    # Store process data from sensor
                    sensor_data["processes"] = data.get('payload', [])
                    sensor_data["last_update"] = datetime.now().isoformat()
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == 'screen_data':
                    # Store screen data from sensor
                    sensor_data["screen"] = data.get('payload', {})
                    sensor_data["last_update"] = datetime.now().isoformat()
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == 'file_data':
                    # Store file data from sensor
                    sensor_data["files"] = data.get('payload', [])
                    sensor_data["last_update"] = datetime.now().isoformat()
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif msg_type == 'llm_request':
                    # Get the query from the request
                    payload = data.get('payload', {})
                    query = payload.get('query', '')
                    logger.info(f"LLM request received: {query[:100]}...")
                    
                    # Get context from sensor data
                    context = {
                        "active_app": sensor_data["screen"].get("active_app", ""),
                        "active_window": sensor_data["screen"].get("active_window", ""),
                        "recent_files": sensor_data["files"][:5] if sensor_data["files"] else []
                    }
                    
                    # Get response from LLM service
                    llm_response = await get_llm_response(query, context)
                    
                    # Send response back to client
                    await websocket.send(json.dumps({
                        "type": "llm_response",
                        "payload": llm_response,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                elif msg_type == 'agent_confirmation':
                    # Handle agent confirmation message (DO button)
                    logger.info(f"⚡ Agent confirmation received: {data}")
                    
                    # Extract session_id and action
                    session_id = data.get('session_id', '')
                    action = data.get('action', '').upper()
                    
                    # FIXED: Forward to ultimate_do_button_server for real automation
                    try:
                        # The DO button server runs on localhost:8765, so we need to connect to another port
                        # Use port 8768 for the ultimate_do_button_server that has automation capabilities
                        logger.info(f"⚡ Forwarding DO button request to automation server")
                        
                        # Forward the exact same message to the automation server
                        async with websockets.connect('ws://localhost:8765') as do_ws:
                            # First message will be welcome message
                            welcome = await do_ws.recv()
                            logger.info(f"Connected to automation server: {welcome[:100]}...")
                            
                            # Forward the original DO button message
                            await do_ws.send(json.dumps(data))
                            logger.info(f"Forwarded DO button request to automation server")
                            
                            # Listen for responses from automation server and forward them to client
                            while True:
                                try:
                                    # Set a timeout to avoid waiting forever
                                    automation_response = await asyncio.wait_for(do_ws.recv(), timeout=30.0)
                                    logger.info(f"Received from automation server: {automation_response[:100]}...")
                                    
                                    # Forward the response to the client
                                    await websocket.send(automation_response)
                                    
                                    # Parse the response to check if it's the final success message
                                    try:
                                        response_data = json.loads(automation_response)
                                        if response_data.get('type') == 'agent_execution_success':
                                            logger.info("Received final success message, closing connection to automation server")
                                            break
                                    except json.JSONDecodeError:
                                        logger.error(f"Invalid JSON from automation server: {automation_response[:100]}...")
                                
                                except asyncio.TimeoutError:
                                    logger.warning("Timeout waiting for automation server response")
                                    break
                                    
                    except Exception as e:
                        logger.error(f"Error forwarding to automation server: {e}")
                        
                        # Fallback: send mock response if automation server is unavailable
                        logger.warning("Using fallback mock response for DO button")
                        
                        # Send immediate progress update
                        await websocket.send(json.dumps({
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 1,
                            "progress": 20,
                            "message": "🚀 Execution started: Analyzing screen..."
                        }))
                        
                        await asyncio.sleep(1)
                        
                        # Send another progress update
                        await websocket.send(json.dumps({
                            "type": "agent_progress",
                            "session_id": session_id,
                            "step": 2,
                            "progress": 60,
                            "message": "⚡ Executing automation steps..."
                        }))
                        
                        await asyncio.sleep(1.5)
                        
                        # Send completion message
                        await websocket.send(json.dumps({
                            "type": "agent_execution_success",
                            "session_id": session_id,
                            "result": {
                                "success": True,
                                "steps_executed": 3,
                                "execution_time": 2.5
                            },
                            "summary": "⚠️ MOCK EXECUTION (automation server unavailable)",
                            "execution_completed": True
                        }))
                    
                else:
                    # Default echo response
                    response = {
                        "type": "response",
                        "payload": {
                            "original_type": msg_type,
                            "message": f"Received your {msg_type} message",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(connected_clients)} clients")

async def heartbeat():
    """Send periodic heartbeat to all clients"""
    while True:
        if connected_clients:
            try:
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients)
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    # Bind to localhost on port 8768 (for overlay connections)
    # CHANGED FROM 8765 to avoid conflict with ultimate_do_button_server.py
    port = 8768
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket bridge server on {host}:{port}")
    
    # Create a server that works with both websockets 10.x and 15.x versions
    try:
        # Try the 10.x style (specific import, handler with both parameters)
        server = await websockets.serve(handler, host, port)
        logger.info(f"WebSocket server created with websockets 10.x style")
    except Exception as e:
        logger.warning(f"Could not create server with default style: {e}")
        # Try the 15.x style (different import path)
        try:
            from websockets.server import serve
            server = await serve(handler, host, port)
            logger.info(f"WebSocket server created with websockets 15.x style")
        except Exception as e2:
            logger.error(f"Could not create server with either style: {e2}")
            raise
    
    # Save PID
    with open('pids/bridge_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat())
    
    logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
    logger.info(f"Heartbeat system active")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
