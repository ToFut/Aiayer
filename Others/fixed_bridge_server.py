#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime
import time
from logging.handlers import RotatingFileHandler
import argparse

# Configure logging
os.makedirs('logs', exist_ok=True)

# Create a custom filter to prevent duplicate logs
class DuplicateFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_log = None
        self.last_time = None
        self.min_interval = 30  # Minimum seconds between similar logs
        self.connection_logs = set()  # Track unique connections

    def filter(self, record):
        # Skip connection logs for already logged connections
        if "WebSocket connection established" in record.getMessage():
            client_id = record.getMessage().split("from ")[-1]
            if client_id in self.connection_logs:
                return False
            self.connection_logs.add(client_id)
            return True

        # Handle other logs
        current_log = (record.levelno, record.getMessage())
        current_time = time.time()
        
        if current_log != self.last_log:
            self.last_log = current_log
            self.last_time = current_time
            return True
            
        if current_time - self.last_time >= self.min_interval:
            self.last_time = current_time
            return True
            
        return False

# Configure logging with rotation
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/bridge_server.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=2
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_bridge')
logger.addFilter(DuplicateFilter())

# Reduce logging level for all modules
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('uvicorn').setLevel(logging.ERROR)
logging.getLogger('fastapi').setLevel(logging.ERROR)

# WebSocket server configuration
WS_HOST = "localhost"
WS_PORT = 8767

# Track connected clients
connected_clients = set()
llm_service = None
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

async def handler(websocket):
    """WebSocket connection handler"""
    global llm_service
    client_id = f"client_{id(websocket)}"
    client_type = "unknown"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Aiayer system",
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

def main():
    parser = argparse.ArgumentParser(description='Bridge Server for Memory System')
    parser.add_argument('--port', type=int, default=8768, help='Port to run the server on')
    args = parser.parse_args()
    
    # Start the server
    start_server = websockets.serve(handler, 'localhost', args.port)
    print(f"Starting bridge server on port {args.port}")
    
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
