#!/usr/bin/env python3
"""
Robust Screen Sensor
Captures screenshots every 10 seconds and sends them to the bridge server.
With improved error handling and continuous operation.
"""
import asyncio
import websockets
import json
import logging
import os
import time
import io
import base64
import threading
import signal
from datetime import datetime
from PIL import Image
import mss
import mss.tools
import hashlib

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

# Global variables
running = True
capture_interval = 10  # seconds
cache_dir = "cache/screen_sensor"
os.makedirs(cache_dir, exist_ok=True)
cache_file = f"{cache_dir}/last_screen.json"

class ScreenCapture:
    def __init__(self):
        self.sct = None
        try:
            self.sct = mss.mss()
            logger.info("Screen capture initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing screen capture: {e}")
        
    def capture(self):
        """Capture the current screen"""
        try:
            if not self.sct:
                self.sct = mss.mss()
                
            # Get primary monitor (usually monitor 1)
            monitor = self.sct.monitors[1]
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Calculate image hash for change detection
            img_hash = self._calculate_hash(img)
            
            # Compress and convert to base64
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=70)
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "image_data": img_base64,
                "image_hash": img_hash,
                "screen_size": img.size,
                "changed": True  # Assume it's changed for simplicity
            }
        except Exception as e:
            logger.error(f"Error during screen capture: {e}")
            # Try to reinitialize
            try:
                if self.sct:
                    self.sct.close()
                self.sct = mss.mss()
                logger.info("Re-initialized screen capture")
            except Exception as re_e:
                logger.error(f"Failed to reinitialize screen capture: {re_e}")
            return None
            
    def _calculate_hash(self, image):
        """Calculate a hash of the image for change detection"""
        return hashlib.md5(image.tobytes()).hexdigest()
        
    def close(self):
        """Clean up resources"""
        if self.sct:
            try:
                self.sct.close()
                logger.info("Screen capture resources released")
            except Exception as e:
                logger.error(f"Error closing screen capture: {e}")

def websocket_thread():
    """Thread for handling WebSocket connections"""
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the WebSocket client
    loop.run_until_complete(websocket_client())

async def websocket_client():
    """WebSocket client that handles reconnection"""
    uri = "ws://localhost:8765"
    screen_capture = ScreenCapture()
    last_image_hash = None
    
    logger.info("Starting WebSocket client")
    
    while running:
        try:
            logger.info(f"Connecting to {uri}...")
            async with websockets.connect(uri, ping_interval=30, ping_timeout=60) as websocket:
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
                        "version": "1.0.0"
                    }
                }))
                
                # Capture and send loop
                while running:
                    try:
                        # Capture screen
                        screen_data = screen_capture.capture()
                        
                        if screen_data:
                            # Update last hash
                            last_image_hash = screen_data["image_hash"]
                            
                            # Save to cache file
                            try:
                                with open(cache_file, 'w') as f:
                                    json.dump({
                                        'timestamp': screen_data["timestamp"],
                                        'image_hash': screen_data["image_hash"],
                                        'screen_size': screen_data["screen_size"]
                                    }, f)
                            except Exception as cache_e:
                                logger.warning(f"Error writing to cache: {cache_e}")
                            
                            # Send to bridge server
                            await websocket.send(json.dumps({
                                "type": "screen_data",
                                "payload": screen_data,
                                "timestamp": datetime.now().isoformat()
                            }))
                            
                            logger.info(f"Sent screen data: {screen_data['screen_size']}, hash: {screen_data['image_hash'][:8]}")
                        
                        # Wait before next capture
                        await asyncio.sleep(capture_interval)
                        
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error in capture loop: {e}")
                        await asyncio.sleep(5)
                        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server failed: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket connection: {e}")
            await asyncio.sleep(5)
            
    # Clean up
    screen_capture.close()
    logger.info("WebSocket client stopped")

def capture_loop():
    """Backup thread for capturing screen data without WebSocket"""
    screen_capture = ScreenCapture()
    last_capture_time = 0
    
    logger.info("Starting backup capture loop")
    
    while running:
        try:
            current_time = time.time()
            
            # Only capture at the specified interval
            if current_time - last_capture_time >= capture_interval:
                # Capture screen
                screen_data = screen_capture.capture()
                
                if screen_data:
                    # Save to cache file
                    try:
                        with open(cache_file, 'w') as f:
                            json.dump({
                                'timestamp': screen_data["timestamp"],
                                'image_hash': screen_data["image_hash"],
                                'screen_size': screen_data["screen_size"]
                            }, f)
                            
                        # Also save comprehensive data
                        cache_file_full = f"{cache_dir}/screen_cache.json"
                        with open(cache_file_full, 'w') as f:
                            json.dump({
                                'timestamp': datetime.now().isoformat(),
                                'data': screen_data
                            }, f)
                            
                        logger.info(f"Backup capture saved: {screen_data['screen_size']}, hash: {screen_data['image_hash'][:8]}")
                    except Exception as cache_e:
                        logger.warning(f"Error writing to cache: {cache_e}")
                
                last_capture_time = current_time
            
            # Sleep a short time to prevent CPU hogging
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in backup capture loop: {e}")
            time.sleep(5)
    
    # Clean up
    screen_capture.close()
    logger.info("Backup capture loop stopped")

def handle_exit(signum, frame):
    """Handle exit signals gracefully"""
    global running
    logger.info("Received exit signal, shutting down...")
    running = False

def main():
    """Main function"""
    global running
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/screen_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info("Starting robust screen sensor...")
    
    # Start WebSocket thread
    ws_thread = threading.Thread(target=websocket_thread, daemon=True)
    ws_thread.start()
    
    # Start backup capture thread
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    
    # Keep the main thread alive
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
    
    logger.info("Waiting for threads to exit...")
    time.sleep(2)  # Give threads time to clean up
    
    logger.info("Screen sensor stopped")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error in screen sensor: {e}")
    finally:
        logger.info("Screen sensor stopped")