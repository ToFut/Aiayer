#!/usr/bin/env python3
"""
Script to start the overlay bridge and WebSocket server with integrated sensors
"""
import logging
import asyncio
import signal
import sys
import os
import time
from agent.overlay_bridge import OverlayBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize the overlay bridge
overlay_bridge = OverlayBridge(port=8765)
bridge_thread = None
sensor_loop = None

# Global sensor references
screen_sensor = None
process_sensor = None

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal...")
    # Stop sensors if running
    try:
        if 'screen_sensor' in globals() and screen_sensor:
            screen_sensor.stop()
        if 'process_sensor' in globals() and process_sensor:
            process_sensor.stop()
    except Exception as e:
        logger.error(f"Error stopping sensors: {e}")
        
    # Stop bridge
    if bridge_thread:
        overlay_bridge.stop()
    sys.exit(0)

async def forward_sensor_data():
    """Forward sensor data to overlay"""
    global screen_sensor, process_sensor
    
    # Import sensors here to avoid issues if not available
    try:
        from sensors.screen_sensor import ScreenSensor
        from sensors.process_sensor import ProcessSensor
        
        # Initialize sensors
        screen_sensor = ScreenSensor()
        process_sensor = ProcessSensor()
        
        # Start sensors
        screen_sensor.start()
        logger.info("Screen sensor started")
        process_sensor.start()
        logger.info("Process sensor started")
    except ImportError as e:
        logger.warning(f"Sensors not available: {e}")
        screen_sensor = None
        process_sensor = None
    
    while True:
        try:
            # Skip if no sensors available
            if not screen_sensor or not process_sensor:
                await asyncio.sleep(5)
                continue
                
            # Get data from sensors
            try:
                screen_data = screen_sensor.get_latest()
                screen_text = screen_data.get('text', '') if screen_data else "No screen data"
                screen_timestamp = screen_data.get('timestamp', time.time()) if screen_data else time.time()
            except Exception as e:
                logger.error(f"Error getting screen data: {e}")
                screen_text = "Error getting screen data"
                screen_timestamp = time.time()
                
            try:
                process_data = process_sensor.get_active_app_info()
                app_name = process_data.get('app_name', 'Unknown') if process_data else "Unknown"
                window_title = process_data.get('window_title', '') if process_data else ""
                process_timestamp = process_data.get('timestamp', time.time()) if process_data else time.time()
            except Exception as e:
                logger.error(f"Error getting process data: {e}")
                app_name = "Error getting app info"
                window_title = ""
                process_timestamp = time.time()
            
            # Create payload
            sensor_payload = {
                'screen': {
                    'text': screen_text[:1000],  # Limit text size
                    'timestamp': screen_timestamp
                },
                'process': {
                    'app': app_name,
                    'title': window_title,
                    'timestamp': process_timestamp
                },
                'system_time': time.time()
            }
            
            # Send to overlay
            await overlay_bridge.send_sensor_data(sensor_payload)
            
            # Generate system activity summary
            summary = f"Working in {app_name}: {window_title}"
            
            await overlay_bridge.add_system_activity("system_summary", {
                "summary": summary,
                "app": app_name,
                "window_title": window_title,
                "suggestion": f"I can help with your work in {app_name}. Click to ask a question."
            })
            
            # Wait before next update
            await asyncio.sleep(15)  # Update every 15 seconds
        except Exception as e:
            logger.error(f"Error in sensor forwarding loop: {e}")
            await asyncio.sleep(5)

async def main_async():
    """Async main function"""
    global bridge_thread, sensor_loop
    
    # Start the overlay bridge
    bridge_thread = overlay_bridge.start()
    logger.info("Overlay bridge started on port 8765")
    
    # Start sensor data forwarding in background
    sensor_loop = asyncio.create_task(forward_sensor_data())
    
    # Keep running until terminated
    while True:
        try:
            print("Overlay server running. Type 'exit' to stop: ", end='', flush=True)
            await asyncio.sleep(0.1)  # Small delay to allow input
            
            # Check for console input without blocking
            if sys.stdin in asyncio.get_event_loop()._ready:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if line.strip().lower() == 'exit':
                    break
                    
            await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            logger.info("Main task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

def main():
    """Start the overlay bridge and sensors"""
    global bridge_thread, screen_sensor, process_sensor
    
    logger.info("Starting overlay bridge on port 8765...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bridge
    bridge_thread = overlay_bridge.start()
    logger.info("Overlay bridge started")
    
    # Try to import sensors
    try:
        from sensors.screen_sensor import ScreenSensor
        from sensors.process_sensor import ProcessSensor
        
        # Create and start sensors
        screen_sensor = ScreenSensor()
        process_sensor = ProcessSensor()
        
        screen_sensor.start()
        logger.info("Screen sensor started")
        process_sensor.start()
        logger.info("Process sensor started")
    except ImportError as e:
        logger.warning(f"Sensor import failed: {e}")
    except Exception as e:
        logger.error(f"Error starting sensors: {e}")
    
    # Set up async event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create and run coroutine
    async def run_async():
        # Start sensor forwarding if available
        if 'screen_sensor' in globals() and screen_sensor and 'process_sensor' in globals() and process_sensor:
            asyncio.create_task(forward_sensor_data())
            logger.info("Started sensor data forwarding")
        
        # Send test activity periodically even without sensors
        asyncio.create_task(send_test_activities())
        logger.info("Started test activity generator")
        
        # Loop to check for input
        while True:
            print("Overlay server running. Type 'exit' to stop: ", end='', flush=True)
            await asyncio.sleep(0.1)
            
            # Non-blocking input check
            if sys.stdin in asyncio.get_event_loop()._ready:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if line.strip().lower() == 'exit':
                    break
                elif line.strip().lower() == 'test':
                    # Send a test message
                    await overlay_bridge.add_system_activity("manual_test", {
                        "summary": "Manual test activity",
                        "app": "Terminal",
                        "window_title": "Testing overlay bridge",
                        "suggestion": "This is a manually triggered test notification. Click to expand."
                    })
                    logger.info("Sent manual test activity")
            
            await asyncio.sleep(1)
            
    # Function to send periodic test activities
    async def send_test_activities():
        """Send test activity messages periodically"""
        count = 0
        apps = ["Terminal", "Browser", "Editor", "Mail", "Calendar"]
        actions = ["opened", "active", "working in", "typing in", "viewing"]
        
        while True:
            count += 1
            app = apps[count % len(apps)]
            action = actions[count % len(actions)]
            
            activity = {
                "summary": f"You are {action} {app}",
                "app": app,
                "window_title": f"Test Window {count}",
                "suggestion": f"I notice you're using {app}. Can I help you with anything?"
            }
            
            await overlay_bridge.add_system_activity("test_activity", activity)
            logger.info(f"Sent test activity {count}: {app}")
            
            # Wait between 20-30 seconds before next activity
            await asyncio.sleep(20)
    
    try:
        # Run the async code
        loop.run_until_complete(run_async())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down...")
        
        # Stop sensors
        try:
            if 'screen_sensor' in globals() and screen_sensor:
                screen_sensor.stop()
                logger.info("Stopped screen sensor")
            if 'process_sensor' in globals() and process_sensor:
                process_sensor.stop()
                logger.info("Stopped process sensor")
        except Exception as e:
            logger.error(f"Error stopping sensors: {e}")
        
        # Stop bridge
        if bridge_thread:
            overlay_bridge.stop()
            logger.info("Stopped overlay bridge")
        
if __name__ == "__main__":
    main()
