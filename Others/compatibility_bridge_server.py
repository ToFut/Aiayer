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
        logging.FileHandler('logs/compatibility_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('compatibility_bridge')

# Track connected clients
connected_clients = set()
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

llm_clients = set()  # Specifically track LLM service clients

async def handler(websocket):
    """WebSocket connection handler compatible with newer websockets library"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to Aiayer system.",
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
                    
                    # If this is an LLM client, add it to the LLM clients set
                    if client_type == 'ollama_llm_service':
                        llm_clients.add(websocket)
                        logger.info(f"Added {client_id} to LLM clients")
                    
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
                    query = data.get('payload', {}).get('query', '')
                    logger.info(f"LLM request received: '{query[:100]}...' from client {client_id}")
                    logger.info(f"Full request data: {json.dumps(data)}")
                    
                    if llm_clients:
                        # Forward to first LLM client
                        llm_client = next(iter(llm_clients))
                        logger.info(f"Forwarding LLM request to LLM service client: {id(llm_client)}")
                        
                        request_data = {
                            "type": "llm_request",
                            "payload": data.get('payload', {}),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        logger.info(f"Sending data to LLM service: {json.dumps(request_data)}")
                        
                        try:
                            await llm_client.send(json.dumps(request_data))
                            logger.info(f"LLM request successfully forwarded to LLM service")
                        except Exception as e:
                            logger.error(f"Error forwarding request to LLM service: {e}")
                            # Send error response back to client
                            await websocket.send(json.dumps({
                                "type": "llm_response",
                                "payload": {
                                    "response": f"Error forwarding request to LLM service: {str(e)}",
                                    "model": "simulator",
                                    "context_used": False,
                                    "processing_time": 0.1,
                                    "error": True
                                },
                                "timestamp": datetime.now().isoformat()
                            }))
                    else:
                        # No LLM client available, send simulated response
                        logger.warning(f"No LLM clients available to process request")
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "response": "No LLM service is currently connected. Please check if the Ollama service is running.",
                                "model": "simulator",
                                "context_used": False,
                                "processing_time": 0.1,
                                "error": True
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                
                elif msg_type == 'llm_response':
                    # Forward LLM response to all clients except LLM services
                    logger.info(f"LLM response received, broadcasting to all non-LLM clients")
                    for client in connected_clients:
                        if client not in llm_clients:  # Don't send back to LLM services
                            try:
                                await client.send(json.dumps(data))
                            except Exception as e:
                                logger.error(f"Error sending LLM response to client: {e}")
                                
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
        if websocket in llm_clients:
            llm_clients.remove(websocket)
            logger.info(f"Removed {client_id} from LLM clients")
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
                    "clients_connected": len(connected_clients),
                    "llm_clients_connected": len(llm_clients)
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
    
    # Using the newer form of serve() without the path parameter
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    os.makedirs('pids', exist_ok=True)
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