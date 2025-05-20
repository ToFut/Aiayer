#!/usr/bin/env python3
"""
Enhanced Screen Sensor
Captures screenshots every 10 seconds and stores them in cache.
With improved error handling and continuous operation.
"""
import asyncio
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
last_image_hash = None
capture_interval = 10  # seconds
cache_dir = "cache/screen_sensor"
memory_dir = "memory/screen_data"
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(memory_dir, exist_ok=True)
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
                "changed": img_hash != last_image_hash
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


async def capture_loop():
    """Continuously capture and store screen data"""
    global last_image_hash
    screen_capture = ScreenCapture()
    
    try:
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
                    
                    # Save to memory if screen changed
                    if screen_data["changed"]:
                        memory_file = f"{memory_dir}/screen_{screen_data['timestamp'].replace(':', '-')}.json"
                        try:
                            with open(memory_file, 'w') as f:
                                json.dump(screen_data, f)
                            logger.info(f"Saved screen data to memory: {memory_file}")
                        except Exception as mem_e:
                            logger.warning(f"Error writing to memory: {mem_e}")
                    
                    logger.info(f"Captured screen: {screen_data['screen_size']}, hash: {screen_data['image_hash'][:8]}")
                
                # Wait before next capture
                await asyncio.sleep(capture_interval)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                await asyncio.sleep(5)
    finally:
        # Clean up resources
        screen_capture.close()


async def main():
    """Main function to run the screen sensor"""
    logger.info("Starting enhanced screen sensor...")
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        global running
        logger.info("Received shutdown signal")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await capture_loop()
    except Exception as e:
        logger.error(f"Fatal error in screen sensor: {e}")
    finally:
        logger.info("Screen sensor stopped")


if __name__ == "__main__":
    asyncio.run(main())