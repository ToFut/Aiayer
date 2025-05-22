#!/usr/bin/env python3
"""
Direct connection script that connects directly to the overlay WebSocket
using a simple and reliable standalone client implementation.
"""
import asyncio
import json
import logging
import sys
import random
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets module...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('direct_connect.log')
    ]
)
logger = logging.getLogger('direct_connect')

# WebSocket client to connect to the overlay
async def connect_to_overlay():
    """Connect to the overlay WebSocket server and keep the connection alive."""
    uri = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to overlay at {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to overlay WebSocket")
            
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "direct_connector",
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            # Receive and log welcome message
            response = await websocket.recv()
            logger.info(f"Received initial response: {response}")
            
            # Keep sending data periodically
            counter = 0
            while True:
                try:
                    # Generate process data
                    processes = [
                        {"name": "Chrome", "pid": 12345, "cpu": random.uniform(5, 20), "memory": 234.5},
                        {"name": "VS Code", "pid": 12346, "cpu": random.uniform(2, 10), "memory": 412.8},
                        {"name": "Terminal", "pid": 12347, "cpu": random.uniform(0.5, 5), "memory": 78.3}
                    ]
                    
                    # Rotate active app
                    apps = ["Chrome", "VS Code", "Terminal", "Finder"]
                    active_app = apps[counter % len(apps)]
                    
                    # Generate screen data
                    screen_data = {
                        "active_app": active_app,
                        "window_title": f"{active_app} - Working on project",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send sensor data
                    sensor_data = {
                        "type": "sensor_data",
                        "payload": {
                            "processes": processes,
                            "screen": screen_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    await websocket.send(json.dumps(sensor_data))
                    logger.info(f"Sent data update #{counter}")
                    
                    # Wait for response if any
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        logger.info(f"Received: {response[:100]}...")
                    except asyncio.TimeoutError:
                        pass  # No response within timeout, that's OK
                    
                    # Send suggestion occasionally
                    if counter % 6 == 0:
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
                        logger.info(f"Sent suggestion #{counter//6}")
                    
                    counter += 1
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error during data sending: {e}")
                    # Continue the loop - don't break for minor errors
                    await asyncio.sleep(2)
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.warning(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"Connection error: {e}")

async def main():
    """Main function with reconnection logic."""
    while True:
        try:
            await connect_to_overlay()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
        
        logger.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Direct connection stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)