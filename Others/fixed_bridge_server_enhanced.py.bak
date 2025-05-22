#!/usr/bin/env python3
"""
Enhanced Bridge Server
Handles communication between sensors and the WebSocket server.
"""
import asyncio
import json
import logging
import os
import signal
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Set
import websockets
from websockets.server import WebSocketServerProtocol

# Import the Enhanced Screen Memory Processor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.enhanced_screen_memory_processor import EnhancedScreenMemoryProcessor

# Configure logging
os.makedirs('logs/bridge', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients: Set[WebSocketServerProtocol] = set()
client_types = {}  # Map client websockets to their types
client_stats = {}  # Track client statistics
registered_clients = set()  # Track registered clients

# Client type mapping
CLIENT_TYPE_MAP = {
    'screen_sensor': 'sensor',
    'process_sensor': 'sensor',
    'total_screen_analyzer': 'sensor',
    'ui': 'ui',
    'application': 'application',
    'sensor': 'sensor'
}

# Initialize the Enhanced Screen Memory Processor
screen_memory_processor = EnhancedScreenMemoryProcessor()

async def handler(websocket: WebSocketServerProtocol):
    """Handle WebSocket connections."""
    client_id = str(uuid.uuid4())
    client_type = "unknown"
    is_registered = False
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "payload": {
                "client_id": client_id,
                "message": "Connected to bridge server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Add to connected clients
        connected_clients.add(websocket)
        
        # Initialize client stats
        client_stats[client_id] = {
            "messages_sent": 0,
            "messages_received": 0,
            "last_message": None,
            "connected_at": datetime.now().isoformat()
        }
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                logger.info(f"Received message type {msg_type} from {client_id}")
                
                # Update client stats
                client_stats[client_id]["messages_received"] += 1
                client_stats[client_id]["last_message"] = datetime.now().isoformat()
                
                if msg_type in ['register', 'connection_established']:
                    # Handle client registration
                    if msg_type == 'register':
                        client_type = data.get('client_type', data.get('payload', {}).get('client_type', 'unknown'))
                    else:  # connection_established
                        client_type = data.get('payload', {}).get('client', 'unknown')
                    
                    # Map client type to standard category
                    mapped_type = CLIENT_TYPE_MAP.get(client_type.lower(), 'unknown')
                    logger.info(f"Client {client_id} registered as {mapped_type} (original: {client_type})")
                    
                    # Store client type and mark as registered
                    client_types[websocket] = mapped_type
                    registered_clients.add(websocket)
                    is_registered = True
                    
                    # Send registration confirmation
                    await websocket.send(json.dumps({
                        "type": "registration_confirmed",
                        "payload": {
                            "client_id": client_id,
                            "client_type": mapped_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Update client stats
                    client_stats[client_id]["messages_sent"] += 1
                
                elif not is_registered:
                    # Reject non-registration messages if not registered
                    logger.warning(f"Received non-registration message as first message: {message[:100]}...")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "payload": {
                            "message": "Registration required before sending other messages",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    logger.info(f"Closed connection due to missing registration from {websocket.remote_address[0]}")
                    break
                
                elif msg_type == 'sensor_data':
                    # Check if this is total_screen_analyzer data
                    sensor_type = data.get('payload', {}).get('sensor_type', '')
                    
                    if sensor_type == 'total_screen_analyzer':
                        # Process through Enhanced Screen Memory Processor
                        try:
                            logger.info(f"Processing total_screen_analyzer data through Enhanced Screen Memory Processor")
                            
                            # Extract the rich analysis data
                            sensor_data = data.get('payload', {})
                            
                            # Process the data to create memory items
                            memory_items = await screen_memory_processor.process_screen_analysis(sensor_data)
                            
                            # Forward each memory item to the WebSocket server
                            uri = "ws://localhost:8765"
                            for memory_item in memory_items:
                                try:
                                    async with websockets.connect(uri) as ws:
                                        # Create enhanced memory message
                                        memory_message = {
                                            "type": "enhanced_memory_data",
                                            "payload": memory_item,
                                            "timestamp": datetime.now().isoformat(),
                                            "processed_by": "enhanced_screen_memory_processor"
                                        }
                                        await ws.send(json.dumps(memory_message))
                                        logger.info(f"Forwarded processed memory item (priority: {memory_item.get('priority', 'unknown')}) to WebSocket server")
                                except Exception as forward_error:
                                    logger.error(f"Error forwarding memory item: {forward_error}")
                            
                            logger.info(f"Successfully processed {len(memory_items)} memory items from total_screen_analyzer")
                            
                            # Update client stats
                            client_stats[client_id]["messages_sent"] += len(memory_items)
                            
                        except Exception as e:
                            logger.error(f"Error processing total_screen_analyzer data: {e}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {
                                    "message": f"Error processing screen analysis data: {str(e)}",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                    else:
                        # Forward regular sensor data to WebSocket server
                        try:
                            # Connect to WebSocket server
                            uri = "ws://localhost:8765"
                            async with websockets.connect(uri) as ws:
                                # Forward the message
                                await ws.send(json.dumps(data))
                                logger.info(f"Forwarded {sensor_type or 'regular'} sensor data to WebSocket server")
                                
                                # Update client stats
                                client_stats[client_id]["messages_sent"] += 1
                                
                        except Exception as e:
                            logger.error(f"Error forwarding to WebSocket server: {e}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {
                                    "message": f"Error forwarding message: {str(e)}",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                
                elif msg_type == 'heartbeat':
                    # Handle heartbeat messages
                    await websocket.send(json.dumps({
                        "type": "heartbeat_ack",
                        "payload": {
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    logger.info(f"Received heartbeat from {client_id}")
                    
                    # Update client stats
                    client_stats[client_id]["messages_sent"] += 1
                
                else:
                    # Forward all other messages to WebSocket server
                    try:
                        uri = "ws://localhost:8765"
                        async with websockets.connect(uri) as ws:
                            await ws.send(json.dumps(data))
                            logger.info(f"Forwarded {msg_type} message to WebSocket server")
                            
                            # Update client stats
                            client_stats[client_id]["messages_sent"] += 1
                            
                    except Exception as e:
                        logger.error(f"Error forwarding message: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": f"Error forwarding message: {str(e)}",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        if websocket in client_types:
            del client_types[websocket]
        if websocket in registered_clients:
            registered_clients.remove(websocket)
        if client_id in client_stats:
            del client_stats[client_id]
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def main():
    """Main function to start the bridge server."""
    try:
        # Use port 8766 to match the sensors' configuration
        port = 8766
        
        # Check if port is in use
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            
            # Try to forcefully release the port by killing any process using it
            os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
            
            # Wait a moment for the port to be released
            await asyncio.sleep(1)
            
            # Check again
            if is_port_in_use(port):
                logger.error(f"Failed to release port {port}")
                sys.exit(1)
        
        # Create PID file
        os.makedirs("pids", exist_ok=True)
        with open('pids/bridge_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start server
        async with websockets.serve(handler, "0.0.0.0", port):
            logger.info(f"Enhanced Bridge Server started on port {port}")
            
            # Keep the server running
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error running bridge server: {e}")
    finally:
        # Clean up
        try:
            os.remove('pids/bridge_server.pid')
        except:
            pass
        logger.info("Enhanced Bridge Server stopped")

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == "__main__":
    asyncio.run(main())