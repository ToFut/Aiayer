#!/usr/bin/env python3
"""
Minimal Screen Sensor

Captures screenshots and extracts basic information without dependencies on other modules.
"""
import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime
import socket
import websockets
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("minimal_screen_sensor")

# Try to import PIL for screen capture
try:
    from PIL import ImageGrab
    SCREENSHOT_AVAILABLE = True
except ImportError:
    logger.warning("PIL.ImageGrab not available. Screenshot functionality will be limited.")
    SCREENSHOT_AVAILABLE = False

class MinimalScreenSensor:
    """A minimal screen sensor that captures screenshots and basic information."""
    
    def __init__(self, websocket_url="ws://localhost:8768"):
        self.websocket_url = websocket_url
        self.capture_interval = 10  # Capture every 10 seconds
        self.running = False
        self.ws = None
        self.reconnect_delay = 5
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # Cache directory setup
        self.cache_dir = "cache/screen_sensor"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Memory file setup
        self.memory_dir = "memory"
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Last context file
        self.last_context_file = os.path.join(self.memory_dir, "last_context.json")
    
    async def start(self):
        """Start the screen sensor."""
        self.running = True
        
        # Start the websocket connection
        asyncio.create_task(self._connect_websocket())
        
        # Start capturing
        await self._capture_loop()
    
    async def stop(self):
        """Stop the screen sensor."""
        self.running = False
        if self.ws:
            await self.ws.close()
    
    async def _connect_websocket(self):
        """Connect to the WebSocket server."""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to WebSocket server at {self.websocket_url}")
                async with websockets.connect(self.websocket_url) as websocket:
                    self.ws = websocket
                    self.reconnect_attempts = 0
                    
                    # Send connection message
                    await self._send_connection_message()
                    
                    # Wait for messages (not used for anything but keeping connection alive)
                    async for message in websocket:
                        pass
            
            except (websockets.exceptions.ConnectionClosed, socket.gaierror):
                logger.warning("WebSocket connection closed or failed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                logger.error(traceback.format_exc())
            
            if self.running:
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay)
                self.ws = None
    
    async def _send_connection_message(self):
        """Send initial connection message to server."""
        try:
            if self.ws:
                await self.ws.send(json.dumps({
                    "type": "sensor_connected",
                    "payload": {
                        "sensor_type": "screen",
                        "timestamp": time.time(),
                        "hostname": socket.gethostname()
                    }
                }))
                logger.info("Sent connection message to WebSocket server")
        except Exception as e:
            logger.error(f"Error sending connection message: {e}")
    
    async def _capture_loop(self):
        """Main loop for capturing screenshots."""
        while self.running:
            try:
                # Capture screen data
                screen_data = await self._capture_screen()
                
                # Send data to WebSocket server
                if screen_data and self.ws:
                    await self._send_screen_data(screen_data)
                
                # Update last context file
                await self._update_last_context(screen_data)
                
                # Sleep until next capture
                await asyncio.sleep(self.capture_interval)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(self.capture_interval)
    
    async def _capture_screen(self):
        """Capture a screenshot and extract information."""
        try:
            timestamp = datetime.now().isoformat()
            logger.info(f"Capturing screen at {timestamp}")
            
            # Basic screen data
            screen_data = {
                "timestamp": timestamp,
                "hostname": socket.gethostname()
            }
            
            # Try to get active window using platform-specific methods
            try:
                import platform
                if platform.system() == "Darwin":  # macOS
                    from AppKit import NSWorkspace
                    active_app = NSWorkspace.sharedWorkspace().activeApplication()
                    if active_app:
                        screen_data["active_app"] = active_app["NSApplicationName"]
                        screen_data["active_window"] = active_app["NSApplicationName"]
                elif platform.system() == "Windows":
                    import win32gui
                    window = win32gui.GetForegroundWindow()
                    screen_data["active_window"] = win32gui.GetWindowText(window)
                    screen_data["active_app"] = screen_data["active_window"].split(" - ")[0] if " - " in screen_data["active_window"] else screen_data["active_window"]
            except Exception as e:
                logger.warning(f"Could not get active window: {e}")
                screen_data["active_window"] = "Unknown"
                screen_data["active_app"] = "Unknown"
            
            # Take screenshot if available
            if SCREENSHOT_AVAILABLE:
                screenshot = ImageGrab.grab()
                screen_data["screen_size"] = screenshot.size
                
                # Save screenshot to cache file
                cache_path = os.path.join(self.cache_dir, f"screen_{timestamp}.png")
                screenshot.save(cache_path)
                screen_data["image_path"] = cache_path
                
                # For simplicity, we won't do OCR or complex image analysis
                # Just note that a screenshot was captured
                screen_data["screen_text"] = f"Screenshot captured at {timestamp}"
                screen_data["visual_context"] = f"Screen showing {screen_data['active_app']} application"
            
            logger.info(f"Successfully captured screen data: {screen_data['active_window']}")
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def _send_screen_data(self, screen_data):
        """Send screen data to WebSocket server."""
        try:
            if self.ws:
                await self.ws.send(json.dumps({
                    "type": "sensor_data",
                    "payload": {
                        "sensor_type": "screen",
                        "data": screen_data,
                        "timestamp": time.time()
                    }
                }))
                logger.info("Sent screen data to WebSocket server")
        except Exception as e:
            logger.error(f"Error sending screen data: {e}")
    
    async def _update_last_context(self, screen_data):
        """Update the last_context.json file with screen data."""
        try:
            if not screen_data:
                return
                
            # Check if last_context.json exists
            if os.path.exists(self.last_context_file):
                with open(self.last_context_file, 'r') as f:
                    try:
                        context = json.load(f)
                    except json.JSONDecodeError:
                        context = {}
            else:
                context = {}
            
            # Update context with screen data
            context.update({
                "timestamp": int(time.time()),
                "active_window": screen_data.get("active_window", ""),
                "active_app": screen_data.get("active_app", ""),
                "screen_text": screen_data.get("screen_text", ""),
                "visual_context": screen_data.get("visual_context", "")
            })
            
            # Make sure active_apps is a list
            if "active_apps" not in context:
                context["active_apps"] = []
            
            # Add current app to active_apps if not already there
            active_app = screen_data.get("active_app")
            if active_app and active_app not in context["active_apps"]:
                context["active_apps"].insert(0, active_app)
                # Keep only the last 5 apps
                context["active_apps"] = context["active_apps"][:5]
            
            # Make sure window_history is a list
            if "window_history" not in context:
                context["window_history"] = []
            
            # Add current window to history if not already the most recent
            active_window = screen_data.get("active_window")
            if active_window:
                if not context["window_history"] or context["window_history"][0] != active_window:
                    context["window_history"].insert(0, active_window)
                    # Keep only the last 5 windows
                    context["window_history"] = context["window_history"][:5]
            
            # Write updated context to file
            with open(self.last_context_file, 'w') as f:
                json.dump(context, f, indent=2)
                
            logger.info(f"Updated last_context.json with active app: {active_app}")
            
        except Exception as e:
            logger.error(f"Error updating last_context.json: {e}")
            logger.error(traceback.format_exc())

# Main function to run the sensor
async def main():
    """Main function to run the screen sensor."""
    try:
        sensor = MinimalScreenSensor()
        await sensor.start()
    except KeyboardInterrupt:
        logger.info("Screen sensor stopped by user")
    except Exception as e:
        logger.error(f"Error in screen sensor: {e}")
        logger.error(traceback.format_exc())
        return 1
    return 0

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())