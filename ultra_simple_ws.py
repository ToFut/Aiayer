#!/usr/bin/env python3
"""
Ultra-simplified WebSocket server without any external dependencies
except websockets. This script is designed to be entirely self-contained
with minimal dependencies, maximum reliability.
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets... (one-time setup)")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ultra_simple_ws.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ultra_simple_ws")

# Global state
connected_clients = set()
client_counter = 0

# THE HANDLER FUNCTION - MUST HAVE BOTH WEBSOCKET AND PATH ARGUMENTS
async def handler(websocket, path):
    """
    WebSocket connection handler. 
    CRITICAL: This function MUST accept both websocket and path parameters!
    """
    global client_counter
    client_counter += 1
    client_id = f"client_{client_counter}"
    
    # Add to connected clients
    connected_clients.add(websocket)
    
    logger.info(f"New client {client_id} connected on path: {path}")
    print(f"New client {client_id} connected on path: {path}")
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "welcome", 
            "message": f"Connected to ultra simple server on path: {path}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))
        
        # Start data sending task
        data_task = asyncio.create_task(
            send_periodic_data(websocket, client_id)
        )
        
        # Process incoming messages
        async for message in websocket:
            try:
                # Try to parse JSON
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # Handle different message types
                if isinstance(data, dict):
                    msg_type = data.get("type", "")
                    
                    # Handle connection establishment
                    if msg_type == "connection_established":
                        logger.info(f"Client identified: {data.get('payload', {}).get('client', 'unknown')}")
                        await websocket.send(json.dumps({
                            "type": "server_ready",
                            "payload": {
                                "status": "connected",
                                "server_version": "1.0.0",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    
                    # Echo back all other messages
                    else:
                        await websocket.send(json.dumps({
                            "type": "response",
                            "payload": {
                                "received": data,
                                "message": "Message received",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        # Clean up
        connected_clients.remove(websocket)
        data_task.cancel()
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket, client_id):
    """Send periodic simulated data to the client"""
    try:
        counter = 0
        while True:
            # Create simulated data
            import random
            current_time = datetime.now()
            
            # Simulate process data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": random.uniform(5, 20), "memory": 350 + random.uniform(-10, 10)},
                {"name": "Code", "pid": 12346, "cpu": random.uniform(2, 10), "memory": 250 + random.uniform(-20, 20)},
                {"name": "Terminal", "pid": 12347, "cpu": random.uniform(0.5, 5), "memory": 120 + random.uniform(-5, 5)}
            ]
            
            # Simulate screen data
            apps = ["Chrome", "Code", "Terminal", "Finder"]
            active_app = apps[counter % len(apps)]
            
            screen_data = {
                "active_app": active_app,
                "window_title": f"{active_app} - Working on project",
                "timestamp": current_time.isoformat()
            }
            
            # Send data
            payload = {
                "type": "sensor_data",
                "payload": {
                    "processes": processes,
                    "screen": screen_data,
                    "timestamp": current_time.isoformat()
                }
            }
            
            await websocket.send(json.dumps(payload))
            logger.debug(f"Sent data update #{counter} to {client_id}")
            
            # Occasionally send a suggestion
            if counter % 6 == 0:  # Every 30 seconds
                suggestion = {
                    "type": "suggestions",
                    "payload": [{
                        "id": f"suggestion_{counter}",
                        "title": "System Performance Tip",
                        "content": f"Consider optimizing your workflow in {active_app}.",
                        "urgency": random.randint(1, 5),
                        "category": "performance"
                    }]
                }
                await websocket.send(json.dumps(suggestion))
                logger.debug(f"Sent suggestion to {client_id}")
            
            counter += 1
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug(f"Data sending task for {client_id} canceled")
    except websockets.exceptions.ConnectionClosed:
        logger.debug(f"Connection closed while sending data to {client_id}")
    except Exception as e:
        logger.error(f"Error sending data to {client_id}: {e}")

async def main():
    """Main function to run the WebSocket server"""
    host = "localhost"
    port = 8765  # Use port 8765 which the overlay expects
    
    # Create pids directory
    os.makedirs("pids", exist_ok=True)
    
    logger.info(f"Starting ultra-simple WebSocket server on {host}:{port}")
    print(f"Starting ultra-simple WebSocket server on {host}:{port}")
    
    # Notice the handler function is passed directly
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/ultra_simple_ws.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info(f"Server started successfully!")
    print(f"Server started successfully!")
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        print("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
