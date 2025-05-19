#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import psutil
import time
from datetime import datetime
import base64
import io
from PIL import Image
import numpy as np

# Create necessary directories
os.makedirs('logs/sensors', exist_ok=True)
os.makedirs('cache/screen_sensor', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleScreenSensor:
    """
    A simplified screen sensor that doesn't rely on actual screen capture.
    It simulates screen data for the AI system to consume.
    """
    
    def __init__(self):
        self.cache_file = "cache/screen_sensor/screen_cache.json"
        self.interval = 10  # seconds
        self.running = False
        self._stop_event = asyncio.Event()
        self.window_titles = [
            "Visual Studio Code - project.py",
            "Terminal - bash",
            "Chrome - GitHub",
            "Finder - Documents",
            "Safari - AI Research",
            "Slack - General"
        ]
        self.title_index = 0
        
        # Create a sample image for testing
        self._create_sample_image()
    
    def _create_sample_image(self):
        """Create a simple test image with text"""
        try:
            # Create a blank image with light gray background (800x600)
            img = Image.new('RGB', (800, 600), color=(240, 240, 240))
            
            # Store the image data
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            self.sample_image_data = img_byte_arr.getvalue()
            self.sample_image_b64 = base64.b64encode(self.sample_image_data).decode('utf-8')
            
            logger.info("Created sample screen image")
        except Exception as e:
            logger.error(f"Error creating sample image: {str(e)}")
            self.sample_image_data = b''
            self.sample_image_b64 = ''
    
    async def get_data(self):
        """Get the current screen data (simulated)"""
        try:
            # Create simulated screen data with metadata
            current_window = self.window_titles[self.title_index]
            app_name = current_window.split(" - ")[0]
            
            # Rotate through sample window titles
            self.title_index = (self.title_index + 1) % len(self.window_titles)
            
            # Get system stats
            try:
                battery = psutil.sensors_battery().percent if psutil.sensors_battery() else None
            except:
                battery = None
                
            screen_data = {
                "timestamp": datetime.now().isoformat(),
                "window_title": current_window,
                "active_app": app_name,
                "image_data": self.sample_image_b64,
                "screen_size": [800, 600],
                "system_stats": {
                    "cpu": psutil.cpu_percent(),
                    "memory": psutil.virtual_memory().percent,
                    "battery": battery
                },
                "is_unchanged": False
            }
            
            # Save to cache
            self._save_cache(screen_data)
            
            return screen_data
        except Exception as e:
            logger.error(f"Error getting screen data: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "image_data": "",
                "screen_size": [0, 0],
                "is_unchanged": True
            }
    
    def _save_cache(self, data):
        """Save the current screen data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save screen cache: {e}")
    
    async def connect_and_send(self):
        """Connect to the bridge server and send screen data"""
        uri = "ws://localhost:8765"
        
        while not self._stop_event.is_set():
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
                    
                    # Main data sending loop
                    while not self._stop_event.is_set():
                        try:
                            # Get screen data
                            screen_data = await self.get_data()
                            
                            # Send to bridge server
                            await websocket.send(json.dumps({
                                "type": "screen_data",
                                "payload": screen_data,
                                "timestamp": datetime.now().isoformat()
                            }))
                            
                            # Wait before next collection
                            await asyncio.sleep(self.interval)
                            
                        except Exception as e:
                            logger.error(f"Error in data collection: {e}")
                            await asyncio.sleep(5)
                    
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)
                
            if self._stop_event.is_set():
                break
    
    async def start(self):
        """Start the screen sensor"""
        logger.info("Starting screen sensor...")
        self.running = True
        self._stop_event.clear()
        return await self.connect_and_send()
    
    async def stop(self):
        """Stop the screen sensor"""
        logger.info("Stopping screen sensor...")
        self.running = False
        self._stop_event.set()

async def main():
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/screen_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Create and start sensor
    sensor = SimpleScreenSensor()
    
    # Set up graceful shutdown
    loop = asyncio.get_event_loop()
    
    try:
        logger.info("Starting fixed screen sensor service...")
        await sensor.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        logger.info("Stopping screen sensor...")
        await sensor.stop()

if __name__ == "__main__":
    asyncio.run(main())