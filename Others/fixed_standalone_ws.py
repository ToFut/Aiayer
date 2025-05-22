#!/usr/bin/env python3
"""
Standalone WebSocket server with proper handler signature
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fixed_ws.log')
    ]
)
logger = logging.getLogger('fixed_ws')

# Connected clients
connected_clients = set()

# Handler function with correct signature
async def handler(websocket, path):
    """Handler function with the REQUIRED path parameter"""
    client_id = f"client_{id(websocket)}"
    logger.info(f"Client {client_id} connected at path: {path}")
    connected_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to fixed WebSocket server. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Handle "connection_established" message from overlay
                if isinstance(data, dict) and data.get("type") == "connection_established":
                    logger.info(f"Client identified: {data.get('payload', {}).get('client', 'unknown')}")
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_time": datetime.now().isoformat()
                        }
                    }))
                    
                    # Start sending periodic data
                    asyncio.create_task(send_periodic_data(websocket, client_id))
                else:
                    # Echo other messages
                    await websocket.send(json.dumps({
                        "type": "response",
                        "payload": {
                            "message": "Received your message",
                            "original": data
                        }
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error", 
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed with {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket, client_id):
    """Send periodic data updates"""
    try:
        import random
        
        # Sample apps for rotation
        apps = [
            {"name": "Terminal", "title": "bash - Aiayer"},
            {"name": "Chrome", "title": "WebSocket API - MDN"},
            {"name": "Visual Studio Code", "title": "overlay_bridge.py - Aiayer"},
            {"name": "Finder", "title": "Documents"}
        ]
        
        counter = 0
        while True:
            # Generate process data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": 10 + random.random() * 10, "memory": 234.5},
                {"name": "VS Code", "pid": 12346, "cpu": 5 + random.random() * 5, "memory": 412.8},
                {"name": "Terminal", "pid": 12347, "cpu": 1 + random.random() * 2, "memory": 78.3},
                {"name": "Finder", "pid": 12348, "cpu": 0.5 + random.random() * 1, "memory": 45.6}
            ]
            
            # Rotate active app every 15 seconds
            app_index = (counter // 3) % len(apps)
            active_app = apps[app_index]
            
            # Create screen data
            screen_data = {
                "active_app": active_app["name"],
                "window_title": active_app["title"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to client
            sensor_data = {
                "processes": processes,
                "screen": screen_data,
                "files": [],
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data
            }))
            
            # Send occasional suggestions (every 30 seconds)
            if counter % 6 == 0:
                suggestion = {
                    "id": f"suggest_{counter}",
                    "title": "System Performance Tip",
                    "content": f"Consider optimizing your workflow based on current {active_app['name']} usage.",
                    "category": "performance",
                    "urgency": random.randint(1, 5),
                    "buttons": [
                        {"label": "Apply", "action": "apply"},
                        {"label": "Dismiss", "action": "dismiss"}
                    ]
                }
                
                await websocket.send(json.dumps({
                    "type": "suggestions",
                    "payload": [suggestion]
                }))
            
            counter += 1
            await asyncio.sleep(5)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed during updates for {client_id}")
    except Exception as e:
        logger.error(f"Error sending periodic data: {e}")

async def main():
    """Main function"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting fixed WebSocket server on {host}:{port}")
    
    # IMPORTANT: use the handler function with path parameter
    async with websockets.serve(handler, host, port):
        logger.info(f"WebSocket server running at ws://{host}:{port}")
        
        # Save PID
        with open('pids/fixed_ws.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        # Run forever
        await asyncio.Future()

if __name__ == "__main__":
    try:
        # Create pids directory if it doesn't exist
        os.makedirs("pids", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
