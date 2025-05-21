#!/usr/bin/env python3
"""
Enhanced Screen Sensor Module

Captures screenshots at regular intervals and sends them to the bridge server.
Features:
- Error handling and recovery
- Connection management with retries
- Continuous operation with background threading
- 10-second interval captures
- Comprehensive logging
"""
import asyncio
import websockets
import json
import logging
import os
import time
import threading
import mss
import mss.tools
import base64
import io
import hashlib
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
import sys

# Create necessary directories
os.makedirs('logs/sensors', exist_ok=True)
os.makedirs('cache/screen_sensor', exist_ok=True)
os.makedirs('pids', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/enhanced_screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScreenData:
    """Container for screen capture data"""
    def __init__(self, timestamp: float, image_data: bytes, image_hash: str, 
                 screen_size: tuple, is_unchanged: bool = False):
        self.timestamp = timestamp
        self.image_data = image_data
        self.image_hash = image_hash
        self.screen_size = screen_size
        self.is_unchanged = is_unchanged

class EnhancedScreenSensor:
    """
    Enhanced screen sensor that captures screenshots at regular intervals
    and sends them to the bridge server.
    
    Features:
    - Robust error handling and recovery
    - Connection management with retries
    - Continuous operation with background threading
    - Configurable capture interval (default: 10 seconds)
    """
    
    def __init__(self, interval_sec: int = 10, bridge_url: str = "ws://localhost:8765"):
        self.interval = interval_sec
        self.bridge_url = bridge_url
        self.cache_dir = "cache/screen_sensor"
        self.cache_file = f"{self.cache_dir}/screen_cache.json"
        self.last_screen_file = f"{self.cache_dir}/last_screen.json"
        self.running = False
        self.connected = False
        self.last_data = None
        self.last_hash = None
        self.unchanged_count = 0
        self.max_unchanged = 5  # Skip processing after 5 unchanged frames
        
        # Initialize screen capture
        self.sct = None
        
        # Threading controls
        self._stop_event = threading.Event()
        self._websocket_lock = threading.Lock()
        self._websocket = None
        self._capture_thread = None
        self._connection_thread = None
        
        # Save PID for system management
        with open('pids/screen_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"Enhanced Screen Sensor initialized with interval: {interval_sec}s")
    
    async def initialize_screen_capture(self) -> bool:
        """Initialize the screen capture system with proper error handling"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing screen capture (attempt {attempt + 1}/{max_retries})")
                
                # Close previous instance if exists
                if self.sct:
                    try:
                        self.sct.close()
                    except:
                        pass
                
                # Initialize new screen capture instance
                self.sct = mss.mss()
                if not self.sct:
                    raise Exception("Failed to initialize screen capture")
                
                # Get monitor information
                monitors = self.sct.monitors
                if not monitors:
                    raise Exception("No monitors found")
                
                # Use primary monitor (usually index 1)
                primary_monitor = monitors[1]
                logger.info(f"Using primary monitor: {primary_monitor}")
                
                # Test capture to ensure it works
                test_screenshot = self.sct.grab(primary_monitor)
                if not test_screenshot:
                    raise Exception("Failed to capture test screenshot")
                
                logger.info("Screen capture initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Screen capture initialization failed (attempt {attempt + 1}): {str(e)}")
                if self.sct:
                    try:
                        self.sct.close()
                    except:
                        pass
                    self.sct = None
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Screen capture initialization failed after all retries")
                    return False
    
    def _calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate a hash of the image for change detection"""
        return hashlib.md5(image_data).hexdigest()
    
    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save the current screen data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            
            # Also update the last screen file
            with open(self.last_screen_file, 'w') as f:
                json.dump(data, f)
                
            logger.debug("Screen data saved to cache")
        except Exception as e:
            logger.warning(f"Failed to save screen cache: {e}")
    
    async def capture_screen(self) -> Optional[ScreenData]:
        """Capture the current screen with error handling"""
        try:
            current_time = time.time()
            
            # Ensure screen capture is initialized
            if not self.sct:
                logger.warning("Screen capture not initialized, attempting to initialize...")
                if not await self.initialize_screen_capture():
                    raise Exception("Failed to initialize screen capture")
            
            # Get primary monitor
            primary_monitor = self.sct.monitors[1]
            
            # Capture screen
            screenshot = self.sct.grab(primary_monitor)
            
            # Convert to PIL Image for processing
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Resize to reduce size while maintaining quality
            max_width = 1200
            if image.width > max_width:
                ratio = max_width / image.width
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.LANCZOS)
            
            # Convert to bytes for storage and transmission
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)  # Use JPEG with good quality
            img_bytes = img_byte_arr.getvalue()
            
            # Calculate image hash
            image_hash = self._calculate_image_hash(img_bytes)
            
            # Check if the image has changed
            is_unchanged = False
            if self.last_hash == image_hash:
                self.unchanged_count += 1
                if self.unchanged_count >= self.max_unchanged:
                    is_unchanged = True
                    logger.debug(f"Screen unchanged for {self.unchanged_count} captures, marking as unchanged")
            else:
                self.unchanged_count = 0
                self.last_hash = image_hash
            
            # Create and return screen data
            return ScreenData(
                timestamp=current_time,
                image_data=img_bytes,
                image_hash=image_hash,
                screen_size=image.size,
                is_unchanged=is_unchanged
            )
            
        except Exception as e:
            logger.error(f"Error capturing screen: {str(e)}")
            if "'NoneType' object has no attribute" in str(e):
                logger.info("Attempting to reinitialize screen capture...")
                self.sct = None
                await self.initialize_screen_capture()
            return None
    
    async def get_screen_data(self) -> Dict[str, Any]:
        """Get the current screen data formatted for transmission"""
        try:
            # Capture screen
            screen_data = await self.capture_screen()
            if not screen_data:
                raise Exception("Failed to capture screen")
            
            # Calculate metadata about the system
            try:
                battery = psutil.sensors_battery()
                battery_percent = battery.percent if battery else None
            except:
                battery_percent = None
                
            # Get active window information
            try:
                active_window = ""
                active_app = ""
                if sys.platform == 'darwin':  # macOS
                    try:
                        import AppKit
                        active_app = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
                    except:
                        active_app = "Unknown"
                        pass
            except:
                active_window = "Unknown"
                active_app = "Unknown"
            
            # Format data for transmission
            data = {
                "timestamp": datetime.now().isoformat(),
                "type": "screen_data",
                "image_hash": screen_data.image_hash,
                "image_data": base64.b64encode(screen_data.image_data).decode('utf-8'),
                "screen_size": list(screen_data.screen_size),
                "is_unchanged": screen_data.is_unchanged,
                "active_window": active_window,
                "active_app": active_app,
                "system_info": {
                    "cpu": psutil.cpu_percent(),
                    "memory": psutil.virtual_memory().percent,
                    "battery": battery_percent
                }
            }
            
            # Save to cache
            self._save_cache(data)
            self.last_data = data
            
            return data
        except Exception as e:
            logger.error(f"Error getting screen data: {str(e)}")
            
            # Return error data
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "type": "screen_data",
                "error": str(e),
                "image_data": "",
                "is_unchanged": True
            }
            
            # Return last known data if available
            if self.last_data:
                return self.last_data
            return error_data
    
    async def connect_websocket(self) -> None:
        """Connect to the WebSocket server with retry logic"""
        retry_delay = 2
        max_retries = 10
        retries = 0
        
        while not self._stop_event.is_set() and retries < max_retries:
            try:
                async with websockets.connect(
                    self.bridge_url,
                    ping_interval=30,
                    ping_timeout=90,
                    close_timeout=30,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                    max_queue=32,  # Maximum number of messages in queue
                    compression=None  # Disable compression for better performance
                ) as ws:
                    logger.info(f"Connected to bridge server at {self.bridge_url}")
                    self.connected = True
                    
                    # Process initial welcome message
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=10)
                        data = json.loads(response)
                        logger.info(f"Received from server: {data.get('type', 'unknown')}")
                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                        logger.warning(f"Error receiving welcome message: {e}")
                        continue
                    
                    # Send identification
                    try:
                        await ws.send(json.dumps({
                            "type": "register",
                            "client_type": "sensor",
                            "version": "1.0.0",
                            "capabilities": ["screen_capture"]
                        }))
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("Connection closed during registration")
                        continue
                    
                    with self._websocket_lock:
                        self._websocket = ws
                    
                    # Keep connection alive and handle incoming messages
                    last_ping_time = time.time()
                    while not self._stop_event.is_set():
                        try:
                            current_time = time.time()
                            
                            # Send periodic ping if needed
                            if current_time - last_ping_time >= 25:  # Send ping slightly before server's ping
                                try:
                                    await ws.send(json.dumps({
                                        "type": "ping",
                                        "timestamp": current_time
                                    }))
                                    last_ping_time = current_time
                                except websockets.exceptions.ConnectionClosed:
                                    logger.warning("Connection closed while sending ping")
                                    break
                            
                            # Check for any messages from the server (non-blocking)
                            try:
                                message = await asyncio.wait_for(ws.recv(), timeout=5)  # Short timeout for responsiveness
                                data = json.loads(message)
                                
                                if data.get("type") == "ping":
                                    await ws.send(json.dumps({
                                        "type": "pong",
                                        "timestamp": time.time()
                                    }))
                                elif data.get("type") == "pong":
                                    last_ping_time = current_time
                                elif data.get("type") == "registration_confirmed":
                                    logger.info("Registration confirmed by server")
                                elif data.get("type") == "error":
                                    logger.error(f"Server error: {data.get('message', 'Unknown error')}")
                                
                            except asyncio.TimeoutError:
                                # No messages, continue
                                continue
                            except websockets.exceptions.ConnectionClosed:
                                logger.warning("Connection closed while receiving message")
                                break
                            except Exception as e:
                                logger.error(f"Error processing message: {e}")
                                continue
                            
                            # Small delay to prevent CPU spinning
                            await asyncio.sleep(0.1)
                            
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error in message loop: {e}")
                            break
                    
                    # If we're here, either stop was requested or connection broke
                    logger.info("WebSocket connection closed")
                    self.connected = False
                    with self._websocket_lock:
                        self._websocket = None
                    
                    if self._stop_event.is_set():
                        return
                        
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                self.connected = False
                with self._websocket_lock:
                    self._websocket = None
                
                retries += 1
                logger.info(f"Retrying connection in {retry_delay} seconds (attempt {retries}/{max_retries})")
                
                # Wait before retrying, but check for stop event
                for _ in range(retry_delay):
                    if self._stop_event.is_set():
                        return
                    time.sleep(1)
                
                # Increase retry delay with backoff, max 30 seconds
                retry_delay = min(retry_delay * 1.5, 30)
            except Exception as e:
                logger.error(f"Unexpected WebSocket error: {e}")
                self.connected = False
                with self._websocket_lock:
                    self._websocket = None
                
                retries += 1
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30)
        
        if retries >= max_retries:
            logger.error(f"Failed to connect after {max_retries} attempts. Will try again later.")
            # Wait longer before trying connection series again
            time.sleep(60)
    
    async def send_screen_data(self) -> None:
        """Send screen data to the bridge server"""
        try:
            # Get the current screen data
            screen_data = await self.get_screen_data()
            
            # Send to server if connected
            with self._websocket_lock:
                if self._websocket and self.connected:
                    message = json.dumps({
                        "type": "sensor_data",
                        "payload": screen_data,
                        "source": "screen_sensor",
                        "timestamp": datetime.now().isoformat()
                    })
                    await self._websocket.send(message)
                    logger.debug(f"Sent screen data: {screen_data.get('image_hash', '')[:8]}, size: {len(message) // 1024}KB")
                else:
                    logger.debug("Not connected to server, data cached for later transmission")
        except Exception as e:
            logger.error(f"Error sending screen data: {e}")
    
    def _capture_and_send_loop(self) -> None:
        """Background thread function for capturing and sending screen data"""
        logger.info("Starting capture and send loop")
        
        while not self._stop_event.is_set():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Send screen data
                if self.connected:
                    loop.run_until_complete(self.send_screen_data())
                else:
                    # Just capture and cache if not connected
                    loop.run_until_complete(self.get_screen_data())
            except Exception as e:
                logger.error(f"Error in capture and send loop: {e}")
            
            # Close the event loop
            loop.close()
            
            # Wait for the specified interval, checking for stop event
            wait_start = time.time()
            while time.time() - wait_start < self.interval:
                if self._stop_event.is_set():
                    break
                time.sleep(0.2)
    
    def _connection_loop(self) -> None:
        """Background thread function for managing the WebSocket connection"""
        logger.info("Starting connection manager loop")
        
        while not self._stop_event.is_set():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Connect to WebSocket if not connected
                if not self.connected:
                    loop.run_until_complete(self.connect_websocket())
            except Exception as e:
                logger.error(f"Error in connection loop: {e}")
            
            # Close the event loop
            loop.close()
            
            # Small delay before checking connection again
            for _ in range(5):  # Check every second for 5 seconds
                if self._stop_event.is_set():
                    break
                time.sleep(1)
    
    def start(self) -> None:
        """Start the screen sensor threads"""
        if self.running:
            logger.warning("Screen sensor already running")
            return
        
        logger.info("Starting enhanced screen sensor")
        self.running = True
        self._stop_event.clear()
        
        # Initialize the screen capture in the main thread
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Initialize screen capture
            loop.run_until_complete(self.initialize_screen_capture())
            
            # Start connection thread
            self._connection_thread = threading.Thread(
                target=self._connection_loop,
                daemon=True,
                name="ScreenSensor-Connection"
            )
            self._connection_thread.start()
            
            # Start capture thread
            self._capture_thread = threading.Thread(
                target=self._capture_and_send_loop,
                daemon=True,
                name="ScreenSensor-Capture"
            )
            self._capture_thread.start()
            
            logger.info("Enhanced screen sensor started")
        except Exception as e:
            logger.error(f"Error starting screen sensor: {e}")
            self.running = False
            self._stop_event.set()
    
    def stop(self) -> None:
        """Stop the screen sensor"""
        if not self.running:
            return
        
        logger.info("Stopping enhanced screen sensor")
        self.running = False
        self._stop_event.set()
        
        # Wait for threads to finish
        if self._connection_thread and self._connection_thread.is_alive():
            self._connection_thread.join(timeout=5.0)
        
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=5.0)
        
        # Close screen capture resource
        if self.sct:
            try:
                self.sct.close()
            except:
                pass
            self.sct = None
        
        logger.info("Enhanced screen sensor stopped")

def main():
    """Main function to run the screen sensor"""
    try:
        # Create and start sensor
        sensor = EnhancedScreenSensor(interval_sec=10)
        sensor.start()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            sensor.stop()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()