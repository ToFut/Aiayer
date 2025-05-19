#!/usr/bin/env python3
"""
ABSOLUTELY ISOLATED WebSocket server - no imports from project code
This is a completely standalone implementation with no dependencies 
on any other project files to avoid any import or module cache issues.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets... (this will only happen once)")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,  # Using DEBUG level to catch everything
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/standalone.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("standalone_ws")

# Connected clients
connected_clients = set()

# THE HANDLER FUNCTION - EXPLICITLY REQUIRES BOTH PARAMETERS
async def handler(websocket, path):
    """
    WebSocket connection handler.
    This signature MUST have both websocket and path parameters.
    """
    # Print to both console and log
    msg = f"CLIENT CONNECTED on path: {path}"
    print("\n" + "="*50)
    print(msg)
    print("="*50 + "\n")
    logger.info(msg)
    
    # Add to connected clients
    connected_clients.add(websocket)
    client_id = id(websocket)
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "welcome", 
            "message": f"Connected to the standalone server. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))
        logger.info(f"Sent welcome message to client {client_id}")
        
        # Start data sending task
        data_task = asyncio.create_task(
            send_periodic_data(websocket, client_id)
        )
        
        # Process incoming messages
        async for message in websocket:
            try:
                # Try to parse JSON
                data = json.loads(message)
                msg_type = data.get("type", "unknown") if isinstance(data, dict) else "unknown"
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                print(f"Received: {msg_type}")
                
                # Handle different message types
                if msg_type == "connection_established":
                    client_info = data.get("payload", {})
                    logger.info(f"Client identified: {client_info}")
                    
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    logger.info("Sent server_ready message")
                    
                # Echo back all other messages
                else:
                    await websocket.send(json.dumps({
                        "type": "response",
                        "payload": {
                            "received": data,
                            "message": "Message received successfully",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    logger.info(f"Echoed message back to client {client_id}")
                
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with client {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clean up
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket, client_id):
    """Send periodic simulated data to the client"""
    try:
        import random
        counter = 0
        
        while True:
            # Create simulated data every 5 seconds
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
            
            # Bundle into sensor data package
            sensor_data = {
                "type": "sensor_data",
                "payload": {
                    "processes": processes,
                    "screen": screen_data,
                    "files": [],
                    "timestamp": current_time.isoformat()
                }
            }
            
            # Send the data
            await websocket.send(json.dumps(sensor_data))
            logger.debug(f"Sent data update #{counter} to client {client_id}")
            
            # Occasionally send a suggestion
            if counter % 6 == 0:  # Every 30 seconds
                suggestion = {
                    "type": "suggestions",
                    "payload": [{
                        "id": f"suggestion_{counter}",
                        "title": "System Performance Tip",
                        "content": f"Consider optimizing your workflow in {active_app}.",
                        "urgency": random.randint(1, 5),
                        "category": "performance",
                        "buttons": [
                            {"label": "Apply", "id": "apply"},
                            {"label": "Dismiss", "id": "dismiss"}
                        ]
                    }]
                }
                
                await websocket.send(json.dumps(suggestion))
                logger.debug(f"Sent suggestion to client {client_id}")
            
            counter += 1
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug(f"Data sending task for client {client_id} canceled")
    except websockets.exceptions.ConnectionClosed:
        logger.debug(f"Connection closed while sending data to client {client_id}")
    except Exception as e:
        logger.error(f"Error sending data to client {client_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Main function to run the WebSocket server"""
    # Create required directories
    os.makedirs("pids", exist_ok=True)
    
    host = "localhost"
    port = 8765  # The port expected by the overlay
    
    # Start the server
    print(f"\n\nSTARTING WEBSOCKET SERVER ON {host}:{port}")
    print(f"HANDLER FUNCTION HAS SIGNATURE: async def handler(websocket, path)\n\n")
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Create the server
    server = await websockets.serve(
        handler,  # This handler has signature: handler(websocket, path)
        host, 
        port
    )
    
    # Save PID
    with open('pids/standalone_ws.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info(f"Server started successfully!")
    print(f"\n✅ SERVER STARTED SUCCESSFULLY!")
    print(f"Debug logs at: logs/standalone.log\n")
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        # Run the event loop
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        print("\nServer stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)
