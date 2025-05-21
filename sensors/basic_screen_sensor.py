#!/usr/bin/env python3
"""
Basic Screen Sensor

A simplified screen sensor that captures screenshots and updates context.
"""
import os
import json
import time
import logging
import asyncio
import websockets
from datetime import datetime
from PIL import ImageGrab
import hashlib
import traceback

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

class BasicScreenSensor:
    """Captures screen information and updates context."""
    
    def __init__(self, bridge_uri="ws://localhost:8768", capture_interval=5):
        self.bridge_uri = bridge_uri
        self.capture_interval = capture_interval
        self.running = False
        self.cache_dir = "cache/screen_sensor"
        self.memory_dir = "memory"
        self.last_screen_hash = None
        
        # Create required directories
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)
        
        logger.info(f"Screen sensor initialized with interval {capture_interval}s")
    
    def _capture_screen(self):
        """Capture screen and extract information"""
        try:
            # Take screenshot
            screenshot = ImageGrab.grab()
            
            # Get basic image info
            width, height = screenshot.size
            
            # Calculate image hash for change detection
            img_hash = hashlib.md5(screenshot.tobytes()).hexdigest()
            
            # Get window title and app info
            window_title = self._get_window_title()
            app_name = window_title.split(" - ")[0] if " - " in window_title else window_title
            
            # Prepare screen data
            screen_data = {
                "timestamp": datetime.now().isoformat(),
                "image_hash": img_hash,
                "screen_size": [width, height],
                "active_window": window_title,
                "active_app": app_name,
                "window_title": window_title
            }
            
            # Add basic visual context (simplified)
            screen_data["visual_context"] = f"Screen showing {app_name} application with resolution {width}x{height}"
            
            # Add basic screen text (simplified)
            screen_data["screen_text"] = f"Screenshot captured at {datetime.now().isoformat()} showing {window_title}"
            
            # Check if screen has changed
            is_changed = self.last_screen_hash != img_hash
            screen_data["is_changed"] = is_changed
            
            if is_changed:
                self.last_screen_hash = img_hash
                logger.info(f"Captured screen with hash: {img_hash[:8]}... (changed)")
            else:
                logger.debug(f"Captured screen with hash: {img_hash[:8]}... (no change)")
            
            # Cache screen data and update context
            self._cache_screen_data(screen_data)
            self._update_last_context(screen_data)
            
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _get_window_title(self):
        """Get active window title using platform-specific methods"""
        try:
            # Get platform-specific information
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                try:
                    from AppKit import NSWorkspace
                    active_app = NSWorkspace.sharedWorkspace().activeApplication()
                    if active_app:
                        return active_app["NSApplicationName"]
                except ImportError:
                    pass
            elif system == "Windows":
                try:
                    import win32gui
                    window = win32gui.GetForegroundWindow()
                    return win32gui.GetWindowText(window)
                except ImportError:
                    pass
            
            # Fallback: Return system name and Python version
            return f"{system} - Python {platform.python_version()}"
            
        except Exception as e:
            logger.error(f"Error getting window title: {e}")
            return "Unknown Window"
    
    def _cache_screen_data(self, screen_data):
        """Cache screen data to file"""
        try:
            # Create a backup before overwriting
            cache_file = os.path.join(self.cache_dir, "last_screen.json")
            if os.path.exists(cache_file):
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{cache_file}.bak_{backup_timestamp}"
                os.rename(cache_file, backup_file)
            
            # Write new cache file
            with open(cache_file, 'w') as f:
                json.dump(screen_data, f, indent=2)
            
            logger.debug(f"Cached screen data to {cache_file}")
            
        except Exception as e:
            logger.error(f"Error caching screen data: {e}")
    
    def _update_last_context(self, screen_data):
        """Update the last_context.json file with screen data."""
        try:
            # File path
            context_file = os.path.join(self.memory_dir, "last_context.json")
            
            # Load existing context if available
            if os.path.exists(context_file):
                try:
                    with open(context_file, 'r') as f:
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
            with open(context_file, 'w') as f:
                json.dump(context, f, indent=2)
                
            logger.info(f"Updated last_context.json with active app: {active_app}")
            
        except Exception as e:
            logger.error(f"Error updating last_context.json: {e}")
            logger.error(traceback.format_exc())
    
    async def _heartbeat_loop(self, websocket):
        """Send periodic heartbeats to keep the connection alive"""
        heartbeat_interval = 30  # seconds
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
    
    async def connect_to_bridge(self):
        """Connect to bridge server and send screen data"""
        self.running = True
        
        while self.running:
            try:
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Identify as screen sensor
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "sensor",
                        "sensor_type": "screen",
                        "version": "1.0.0"
                    }))
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket))
                    
                    # Main capture loop
                    while self.running:
                        try:
                            # Capture screen data
                            screen_data = self._capture_screen()
                            if screen_data:
                                # Send to bridge server
                                await websocket.send(json.dumps({
                                    "type": "sensor_data",
                                    "sensor_type": "screen",
                                    "data": screen_data
                                }))
                                logger.info("Sent screen data to bridge server")
                            
                            # Wait for next capture
                            await asyncio.sleep(self.capture_interval)
                            
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Connection to bridge server closed")
                            break
                        except Exception as e:
                            logger.error(f"Error in capture loop: {e}")
                            await asyncio.sleep(5)
                    
                    # Cancel heartbeat task
                    heartbeat_task.cancel()
                    
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run the screen sensor"""
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/screen_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to bridge and start sending data
        await self.connect_to_bridge()
    
    async def stop(self):
        """Stop the screen sensor"""
        self.running = False

# Run the screen sensor
async def main():
    try:
        sensor = BasicScreenSensor()
        await sensor.run()
    except KeyboardInterrupt:
        logger.info("Screen sensor stopped by user")
    except Exception as e:
        logger.error(f"Error running screen sensor: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())