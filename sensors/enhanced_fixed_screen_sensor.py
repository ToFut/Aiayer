#!/usr/bin/env python3
"""
Enhanced Fixed Screen Sensor

This module captures screen information and sends it to the bridge server.
It includes application detection and direct memory integration.
"""
import os
import json
import time
import asyncio
import logging
import websockets
import tempfile
import hashlib
import base64
import traceback
from datetime import datetime
from PIL import ImageGrab

# Configure logging
os.makedirs('logs/sensors/screen_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('screen_sensor')

class ScreenSensor:
    """Captures screen information and sends to bridge server"""
    
    def __init__(self, bridge_uri="ws://localhost:8768", capture_interval=5):  # Using port 8768 to match bridge_server.py
        self.bridge_uri = bridge_uri
        self.capture_interval = capture_interval
        self.running = True
        self.cache_dir = "cache/screen_sensor"
        self.last_screen_hash = None
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Screen sensor initialized with interval {capture_interval}s")
    
    def _capture_screen(self):
        """Capture screen and extract information"""
        try:
            # Take screenshot
            screenshot = ImageGrab.grab()
            
            # Save screenshot to temporary file
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"screen_{int(time.time())}.png")
            screenshot.save(temp_file)
            
            # Get basic image info
            width, height = screenshot.size
            
            # Calculate image hash to detect changes
            img_hash = hashlib.md5(screenshot.tobytes()).hexdigest()
            
            # Convert image to base64 for transmission
            with open(temp_file, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Prepare screen data
            screen_data = {
                "timestamp": datetime.now().isoformat(),
                "resolution": f"{width}x{height}",
                "image_hash": img_hash,
                "image_base64": img_base64,
                "temp_file": temp_file,
                "window_title": self._get_window_title()
            }
            
            # Add application detection
            app_info = self._detect_application(screenshot)
            if app_info:
                screen_data["application"] = app_info
            
            # Check if screen has changed
            is_changed = self.last_screen_hash != img_hash
            screen_data["is_changed"] = is_changed
            
            if is_changed:
                self.last_screen_hash = img_hash
                logger.info(f"Captured screen with hash: {img_hash[:8]}... (changed)")
            else:
                logger.debug(f"Captured screen with hash: {img_hash[:8]}... (no change)")
            
            # Cache last screen data
            self._cache_screen_data(screen_data)
            
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _get_window_title(self):
        """Get active window title (simplified implementation)"""
        try:
            # This is a placeholder - in a real implementation we would use
            # platform-specific libraries to get the actual window title
            return "Unknown Window"
        except Exception as e:
            logger.error(f"Error getting window title: {e}")
            return "Unknown Window"
    
    def _detect_application(self, screenshot):
        """Detect application from screenshot (simplified implementation)"""
        try:
            # This is a placeholder - in a real implementation we would use
            # image recognition or other techniques to detect the application
            return {
                "name": "Unknown Application",
                "view": "Unknown View",
                "confidence": 0.5
            }
        except Exception as e:
            logger.error(f"Error detecting application: {e}")
            return None
    
    def _cache_screen_data(self, screen_data):
        """Cache screen data to file"""
        try:
            # Create simplified version without the large base64 image
            cache_data = {
                "timestamp": screen_data["timestamp"],
                "resolution": screen_data["resolution"],
                "image_hash": screen_data["image_hash"],
                "window_title": screen_data["window_title"],
                "is_changed": screen_data["is_changed"]
            }
            
            # Add application info if available
            if "application" in screen_data:
                cache_data["application"] = screen_data["application"]
            
            # Save to cache file
            cache_file = os.path.join(self.cache_dir, "last_screen.json")
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            # Create a backup before overwriting
            if os.path.exists(cache_file):
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{cache_file}.bak_{backup_timestamp}"
                os.rename(cache_file, backup_file)
            
            # Write new cache file
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached screen data to {cache_file}")
            
        except Exception as e:
            logger.error(f"Error caching screen data: {e}")
    
    async def _heartbeat_loop(self, websocket):
        """Send periodic heartbeats to keep the connection alive"""
        heartbeat_interval = 30  # seconds
        try:
            while self.running:
                try:
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": time.time()
                    }))
                    logger.debug("Sent heartbeat ping to bridge server")
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                    break
                
                await asyncio.sleep(heartbeat_interval)
        except asyncio.CancelledError:
            logger.info("Heartbeat task cancelled")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
            
    async def connect_to_bridge(self):
        """Connect to bridge server and send screen data"""
        while self.running:
            heartbeat_task = None
            try:
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Identify as screen sensor with proper registration format
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "sensor",
                        "sensor_type": "screen",  # Add specific sensor type
                        "version": "1.0.0",
                        "capabilities": ["screen_capture", "application_detection"]
                    }))
                    logger.info("Sent registration message to bridge server")
                    
                    # Wait for registration confirmation
                    registered = False
                    registration_timeout = 10  # seconds
                    registration_start = time.time()
                    
                    while not registered and time.time() - registration_start < registration_timeout:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            data = json.loads(response)
                            
                            if data.get('type') == 'registration_confirmed':
                                logger.info("Registration confirmed by bridge server")
                                registered = True
                                break
                            elif data.get('type') == 'error':
                                logger.error(f"Registration error: {data.get('message', 'Unknown error')}")
                                await asyncio.sleep(2)
                                # Retry registration
                                await websocket.send(json.dumps({
                                    "type": "register",
                                    "client_type": "sensor",
                                    "sensor_type": "screen",  # Add specific sensor type
                                    "version": "1.0.0",
                                    "capabilities": ["screen_capture", "application_detection"]
                                }))
                            else:
                                logger.warning(f"Unexpected message during registration: {data.get('type')}")
                        except asyncio.TimeoutError:
                            logger.warning("Waiting for registration confirmation...")
                        except Exception as e:
                            logger.error(f"Error during registration confirmation: {e}")
                            await asyncio.sleep(1)
                    
                    if not registered:
                        logger.error("Failed to confirm registration, retrying connection")
                        continue  # Retry the connection
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket))
                    logger.debug("Started heartbeat task")
                    
                    # Main loop for sending screen updates
                    while self.running:
                        try:
                            # Capture screen
                            screen_data = self._capture_screen()
                            if screen_data:
                                # Clean up screen data for transmission (remove large fields)
                                transmission_data = {k: v for k, v in screen_data.items() if k != 'image_base64'}
                                
                                # Send to bridge
                                await websocket.send(json.dumps({
                                    "type": "sensor_data",
                                    "sensor_type": "screen",
                                    "payload": transmission_data
                                }))
                                
                                logger.info(f"Sent screen data to bridge server")
                            
                            # Process incoming messages (pongs, etc.)
                            while True:
                                try:
                                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                                    data = json.loads(response)
                                    logger.debug(f"Received message: {data.get('type')}")
                                    
                                    # Handle pong responses
                                    if data.get('type') == 'pong':
                                        logger.debug("Received pong from bridge server")
                                except asyncio.TimeoutError:
                                    # No more messages to process
                                    break
                                except Exception as msg_e:
                                    logger.error(f"Error processing message: {msg_e}")
                                    break
                            
                            # Wait for next capture
                            await asyncio.sleep(self.capture_interval)
                            
                        except (websockets.exceptions.ConnectionClosed, ConnectionError) as conn_e:
                            logger.warning(f"Connection lost: {conn_e}")
                            break
                        except Exception as loop_e:
                            logger.error(f"Error in main processing loop: {loop_e}")
                            logger.error(traceback.format_exc())
                            await asyncio.sleep(1)  # Brief pause before retrying
            
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)  # Wait before reconnecting
            finally:
                # Clean up heartbeat task if it exists
                if heartbeat_task and not heartbeat_task.done():
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass
    
    async def run(self):
        """Run the screen sensor"""
        logger.info("Starting screen sensor")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/screen_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to bridge and start sending data
        await self.connect_to_bridge()

# Run the screen sensor
async def run_screen_sensor():
    sensor = ScreenSensor()
    await sensor.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_screen_sensor())
    except KeyboardInterrupt:
        logger.info("Screen sensor stopped by user")
    except Exception as e:
        logger.error(f"Error running screen sensor: {e}")
        logger.error(traceback.format_exc())
