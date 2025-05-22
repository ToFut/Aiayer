#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import psutil
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('screen_sensor')

async def send_screen_data():
    """Collect and send screen data to the bridge server"""
    uri = "ws://localhost:8765"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to bridge server at {uri}")
                
                # Process initial welcome message
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received from server: {data.get('type')}")
                
                # Send identification
                await websocket.send(json.dumps({
                    "type": "connection_established",
                    "payload": {
                        "client": "screen_sensor",
                        "version": "0.1.0"
                    }
                }))
                
                # Main data collection loop
                window_titles = [
                    "Visual Studio Code - project.py",
                    "Terminal - bash",
                    "Chrome - GitHub",
                    "Finder - Documents",
                    "Safari - AI Research",
                    "Slack - General"
                ]
                title_index = 0
                
                while True:
                    try:
                        # Create simulated screen data
                        # In a real implementation, this would capture actual screen info
                        screen_data = {
                            "window_title": window_titles[title_index],
                            "active_app": window_titles[title_index].split(" - ")[0],
                            "system_stats": {
                                "cpu": psutil.cpu_percent(),
                                "memory": psutil.virtual_memory().percent,
                                "battery": psutil.sensors_battery().percent if psutil.sensors_battery() else None
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Rotate through sample window titles
                        title_index = (title_index + 1) % len(window_titles)
                        
                        # Send to bridge server
                        await websocket.send(json.dumps({
                            "type": "screen_data",
                            "payload": screen_data,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Wait before next collection
                        await asyncio.sleep(10)
                        
                    except Exception as e:
                        logger.error(f"Error in data collection: {e}")
                        await asyncio.sleep(5)
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server failed: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/screen_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info("Starting minimal screen sensor...")
    asyncio.run(send_screen_data())
