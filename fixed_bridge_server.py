#!/usr/bin/env python3
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_bridge')

# Track connected clients
connected_clients = set()
llm_service = None
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

# IMPORTANT: The handler MUST accept both websocket AND path parameters
async def handler(websocket, path):
    """WebSocket connection handler with the correct signature including path parameter"""
    global llm_service
    client_id = f"client_{id(websocket)}"
    client_type = "unknown"
    connected_clients.add(websocket)
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
                    
                    # If this is the LLM service connecting, save the reference
                    if 'ollama_llm_service' in client_type:
                        llm_service = websocket
                        logger.info("LLM service connected and registered")
                    
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
                    # Forward to LLM system if we have one connected
                    logger.info(f"LLM request received: {data.get('payload', {}).get('query', 'empty')}")
                    
                    if llm_service and llm_service in connected_clients:
                        # Forward the request to the LLM service
                        logger.info(f"Forwarding request to LLM service")
                        await llm_service.send(json.dumps(data))
                    else:
                        # No LLM service connected, send simulated response
                        logger.warning("No LLM service connected, sending simulated response")
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "response": "This is a simulated LLM response. No LLM service is connected to the system.",
                                "model": "simulator",
                                "context_used": True,
                                "processing_time": 0.5
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                
                elif msg_type == 'llm_response':
                    # Forward LLM response to all clients except the LLM service
                    logger.info("Received LLM response, forwarding to clients")
                    
                    # Forward to all clients except the LLM service
                    for client in connected_clients:
                        if client != llm_service:
                            await client.send(json.dumps(data))
                
                else:
                    # Default echo response
                    response = {
                        "type": "echo",
                        "payload": {
                            "data": data,
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
        if websocket == llm_service:
            llm_service = None
            logger.info("LLM service disconnected")
        logger.info(f"Client {client_id} ({client_type}) disconnected")

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
                    "clients_connected": len(connected_clients),
                    "llm_service_connected": llm_service is not None and llm_service in connected_clients
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    # Bind to localhost on port 8765 (for overlay connections)
    port = 8765
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket bridge server on {host}:{port}")
    
    # Create server with the handler directly
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
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
