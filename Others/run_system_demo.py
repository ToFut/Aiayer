#!/usr/bin/env python3
"""
Demo runner for the Aiayer system with fixed overlay bridge
"""
import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/system_demo.log')
    ]
)
logger = logging.getLogger('system_demo')

# Import the fixed OverlayBridge
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.overlay_bridge import OverlayBridge

class SystemDemo:
    """Demo runner for the Aiayer system"""
    
    def __init__(self):
        self.bridge = OverlayBridge(port=8765)
        self.is_running = False
        self.loop = None
        
    def start(self):
        """Start the demo"""
        logger.info("Starting Aiayer system demo")
        
        # Start the bridge
        self.bridge.start()
        logger.info("OverlayBridge started on port 8765")
        
        # Start the demo loop
        self.loop = asyncio.new_event_loop()
        self.is_running = True
        
        def run_loop():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.demo_loop())
            except Exception as e:
                logger.error(f"Error in demo loop: {e}")
                
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        
        # Save PID
        with open('pids/system_demo.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info("Demo started successfully")
        
    async def demo_loop(self):
        """Main demo loop - send periodic updates to clients"""
        while self.is_running:
            try:
                # Generate process data
                processes = self.generate_process_data()
                
                # Generate screen data
                screen_data = self.generate_screen_data()
                
                # Send sensor data
                sensor_data = {
                    "processes": processes,
                    "screen": screen_data,
                    "files": [],
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.bridge.send_sensor_data(sensor_data)
                
                # Every 30 seconds, send a suggestion
                if int(time.time()) % 30 == 0:
                    suggestions = self.generate_suggestions()
                    await self.bridge.send_proactive_suggestions(suggestions)
                
                # Wait before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in demo loop: {e}")
                await asyncio.sleep(5)
    
    def generate_process_data(self):
        """Generate simulated process data"""
        processes = [
            {"name": "Visual Studio Code", "pid": 12345, "cpu": 15.3, "memory": 234.5},
            {"name": "Chrome", "pid": 12346, "cpu": 8.7, "memory": 412.8},
            {"name": "Terminal", "pid": 12347, "cpu": 2.2, "memory": 78.3},
            {"name": "Finder", "pid": 12348, "cpu": 1.4, "memory": 56.2},
            {"name": "Python", "pid": 12349, "cpu": 4.8, "memory": 123.6}
        ]
        
        # Add some randomness to CPU usage
        import random
        for proc in processes:
            proc["cpu"] = max(0.1, min(100, proc["cpu"] + random.uniform(-2, 2)))
            
        return processes
    
    def generate_screen_data(self):
        """Generate simulated screen data"""
        import random
        
        app_windows = [
            {"app": "Visual Studio Code", "title": "overlay_bridge.py - Aiayer - VS Code"},
            {"app": "Terminal", "title": "bash - /Users/user/Aiayer"},
            {"app": "Chrome", "title": "WebSocket API - Web APIs | MDN"},
            {"app": "Finder", "title": "Aiayer"}
        ]
        
        # Select a random window as active
        active_window = random.choice(app_windows)
        
        return {
            "active_app": active_window["app"],
            "window_title": active_window["title"],
            "resolution": {"width": 1920, "height": 1080},
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_suggestions(self):
        """Generate simulated suggestions"""
        suggestions = [
            {
                "suggestion_id": "suggest_" + str(int(time.time())),
                "title": "Optimize system performance",
                "content": "Your system is running multiple resource-intensive applications. Consider closing unused applications to improve performance.",
                "action_data": {},
                "urgency": 3,
                "category": "performance"
            }
        ]
        
        return suggestions
    
    def stop(self):
        """Stop the demo"""
        logger.info("Stopping demo")
        self.is_running = False
        
        # Stop the bridge
        self.bridge.stop()
        
        logger.info("Demo stopped")

if __name__ == "__main__":
    demo = SystemDemo()
    
    try:
        demo.start()
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        demo.stop()
