#!/usr/bin/env python3
"""
Fixed WebSocket Server for Port 8765
- Compatible with latest WebSockets API
- Enhanced for perception queries
- Includes memory integration
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import socket
import traceback
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_ws_server')

# Track connected clients
connected_clients = set()
memory_state = {}

def load_memory_state():
    """Load memory state from file"""
    global memory_state
    memory_file = "memory/memory_state.json"
    try:
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_state = json.load(f)
                logger.info(f"Loaded memory state: {len(str(memory_state))} chars")
                
                # Check for screen content
                if "context" in memory_state and "screen_content" in memory_state["context"]:
                    content_len = len(memory_state["context"]["screen_content"])
                    logger.info(f"Memory has screen content: {content_len} chars")
                else:
                    logger.warning("Memory missing screen content")
    except Exception as e:
        logger.error(f"Error loading memory state: {e}")
        logger.error(traceback.format_exc())

def save_pid():
    """Save PID to file"""
    try:
        os.makedirs("pids", exist_ok=True)
        with open('pids/fixed_ws_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Error saving PID: {e}")
        return False

def is_port_in_use(port, host='localhost'):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        if host == 'localhost':
            host = '127.0.0.1'
        return s.connect_ex((host, port)) == 0

async def handle_perception_query(query):
    """Handle perception-related queries"""
    global memory_state
    
    logger.info(f"Processing perception query: {query}")
    
    # Check memory for screen content
    if "context" in memory_state and "screen_content" in memory_state["context"]:
        screen_content = memory_state["context"]["screen_content"]
        if screen_content:
            response = f"Based on your screen, I can see: {screen_content}"
            logger.info(f"Responding with screen content ({len(screen_content)} chars)")
            return response
    
    # Check for screen data in sensor_data section
    if "sensor_data" in memory_state and "screen" in memory_state["sensor_data"]:
        screens = memory_state["sensor_data"]["screen"]
        if screens:
            # Get the most recent screen data
            latest_key = sorted(screens.keys())[-1] if screens else None
            if latest_key:
                latest_screen = screens[latest_key]
                screen_desc = latest_screen.get("content", "")
                if screen_desc:
                    response = f"Based on your screen, I can see: {screen_desc}"
                    logger.info(f"Responding with latest screen data")
                    return response
    
    # Fallback response
    logger.warning("No screen content available for perception query")
    return "I'm unable to see your screen right now. Please make sure screen capture is enabled and working properly."

async def handler(websocket):
    """Handle WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    client_info = websocket.remote_address if hasattr(websocket, 'remote_address') else "Unknown"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected from {client_info}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Hello client {client_id}!",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send fake system context periodically
        context_task = asyncio.create_task(send_context_updates(websocket, client_id))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    logger.info(f"Client initialized: {data.get('payload', {})}")
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "capabilities": ["context_tracking", "suggestions", "screen_capture", "perception_queries"]
                        }
                    }))
                
                elif msg_type == 'context_request':
                    # Load latest memory state
                    load_memory_state()
                    
                    # Send context from memory
                    context = memory_state.get("context", {})
                    await websocket.send(json.dumps({
                        "type": "context_response",
                        "payload": context
                    }))
                    logger.info(f"Sent context to {client_id}")
                
                elif msg_type == 'message' or msg_type == 'user_interaction':
                    # Check if this is a perception query
                    payload = data.get('payload', {})
                    if isinstance(payload, dict):
                        query = payload.get('message', payload.get('query', ''))
                        
                        # Check for perception-related keywords
                        perception_keywords = ["see", "seeing", "look", "screen", "showing"]
                        is_perception = any(kw in query.lower() for kw in perception_keywords)
                        
                        if is_perception:
                            # Handle as perception query
                            response = await handle_perception_query(query)
                            
                            await websocket.send(json.dumps({
                                "type": "response",
                                "payload": {
                                    "content": response,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                            logger.info(f"Sent perception response to {client_id}")
                            
                        else:
                            # Regular response
                            await websocket.send(json.dumps({
                                "type": "response",
                                "payload": {
                                    "content": f"You said: {query}",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                            logger.info(f"Sent regular response to {client_id}")
                    
                elif msg_type == 'sensor_data':
                    # Process sensor data
                    payload = data.get('payload', {})
                    sensor_type = payload.get('sensor_type', 'unknown')
                    
                    logger.info(f"Received {sensor_type} sensor data from {client_id}")
                    
                    # Acknowledge receipt
                    await websocket.send(json.dumps({
                        "type": "sensor_data_received",
                        "payload": {
                            "sensor_type": sensor_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Refresh memory state
                    load_memory_state()
                
                else:
                    # Default echo response
                    response = {
                        "type": "response",
                        "payload": {
                            "message": f"Received {msg_type} message",
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
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                logger.error(traceback.format_exc())
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": f"Error: {str(e)}"}
                }))
                
        # Cancel context task when the loop breaks
        context_task.cancel()
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except asyncio.CancelledError:
        logger.info(f"Tasks for {client_id} cancelled")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_context_updates(websocket, client_id):
    """Send periodic context updates with real data from memory"""
    try:
        while True:
            # Load latest memory state
            load_memory_state()
            
            # Create context data from memory
            context_data = {
                "type": "context_update",
                "payload": {
                    "timestamp": datetime.now().isoformat(),
                    "context": memory_state.get("context", {}),
                    "screen_content": memory_state.get("context", {}).get("screen_content", "")
                }
            }
            
            try:
                await websocket.send(json.dumps(context_data))
                logger.debug(f"Sent context update to {client_id}")
            except Exception as e:
                logger.error(f"Error sending context to {client_id}: {e}")
                raise
                
            # Send every 10 seconds
            await asyncio.sleep(10)
            
    except asyncio.CancelledError:
        logger.debug(f"Context updates for {client_id} stopped")
        raise
    except Exception as e:
        logger.error(f"Error in context updates for {client_id}: {e}")
        logger.error(traceback.format_exc())

async def main():
    """Main function"""
    # Load initial memory state
    load_memory_state()
    
    # Save PID for process management
    save_pid()
    
    # Bind to all interfaces for maximum compatibility
    port = 8765
    hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # Check if port is already in use
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use")
        
        # Try to find what's using it
        try:
            result = os.popen(f"lsof -i :{port}").read()
            logger.warning(f"Port usage: {result}")
        except Exception as e:
            logger.error(f"Error checking port usage: {e}")
    
    # Try each host until one works
    for host in hosts:
        try:
            logger.info(f"Starting WebSocket server on {host}:{port}")
            server = await websockets.serve(handler, host, port)
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            
            # Keep running forever
            await asyncio.Future()
            
        except OSError as e:
            logger.error(f"Failed to bind to {host}:{port}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error starting server on {host}: {e}")
            logger.error(traceback.format_exc())
            continue

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print(f"\n=== Fixed WebSocket Server (Port 8765) ===")
    print(f"Starting server with perception query support...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        print(f"\nError starting server: {e}")
        sys.exit(1)