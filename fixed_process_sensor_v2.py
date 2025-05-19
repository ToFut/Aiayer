#!/usr/bin/env python3
"""
Fixed Process Sensor Script v2
"""
import os
import time
import logging
import json
import platform
import psutil
from datetime import datetime
from collections import deque
import asyncio
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/sensor_process/sensor_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define cache path
CACHE_PATH = 'cache/process_sensor/process_cache.json'

class SimpleProcessSensor:
    """Simple process sensor that doesn't require complex imports"""
    
    def __init__(self):
        self.running = False
        self.last_update = time.time()
        self.process_history = deque(maxlen=100)
        self.window_history = deque(maxlen=100)
        self.logger = logger
        
    async def start(self):
        """Start the process sensor."""
        self.running = True
        self.logger.info("Process sensor started")
        return True
    
    async def stop(self):
        """Stop the process sensor."""
        self.running = False
        self.logger.info("Process sensor stopped")
        return True
        
    async def get_data(self):
        """Get current process data."""
        try:
            current_time = time.time()
            
            # Get process data
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        process_info = proc.info
                        # Initialize CPU percent if None
                        if process_info['cpu_percent'] is None:
                            process_info['cpu_percent'] = 0.0
                        # Initialize memory percent if None
                        if process_info['memory_percent'] is None:
                            process_info['memory_percent'] = 0.0
                            
                        processes.append({
                            'pid': process_info['pid'],
                            'name': process_info['name'],
                            'username': process_info['username'],
                            'cpu_percent': process_info['cpu_percent'],
                            'memory_percent': process_info['memory_percent']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except Exception as e:
                self.logger.error(f"Error getting process data: {e}")
                processes = []
            
            # Get window data (simplified for cross-platform)
            windows = []
            try:
                if platform.system() == "Darwin":  # macOS
                    active_app = os.popen("osascript -e 'tell application \"System Events\" to name of first application process whose frontmost is true'").read().strip()
                    if active_app:
                        windows.append({
                            'name': active_app,
                            'owner': active_app,
                            'layer': 0
                        })
                else:
                    # Simplified version for other platforms
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            cpu_percent = proc.cpu_percent(interval=0.1)
                            if cpu_percent is None:
                                cpu_percent = 0.0
                            if cpu_percent > 5.0:  # Assume higher CPU usage might be foreground app
                                windows.append({
                                    'name': proc.info['name'],
                                    'owner': proc.info['name'],
                                    'layer': 0
                                })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
            except Exception as e:
                self.logger.error(f"Error getting window data: {e}")
                
            # Create data object
            data = {
                'timestamp': current_time,
                'type': 'process_sensor',
                'processes': processes,
                'windows': windows,
                'last_update': self.last_update
            }
            
            # Update histories
            self.process_history.append(processes)
            if windows:
                self.window_history.append(windows)
            
            # Update last update time
            self.last_update = current_time
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting process sensor data: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }

def write_cache(data):
    """Write data to cache file."""
    try:
        # Create simple data structure for cache
        active_window = None
        active_app = None
        active_apps = []
        window_history = []
        
        if 'windows' in data and data['windows']:
            active_window = data['windows'][0].get('name', '')
            active_app = data['windows'][0].get('owner', '')
        
        if 'processes' in data and data['processes']:
            active_apps = []
            for p in data['processes'][:10]:
                # Get CPU percent with safety check
                cpu_percent = p.get('cpu_percent', 0)
                if cpu_percent is None:
                    cpu_percent = 0.0
                
                # Only include processes with some CPU activity
                if cpu_percent > 0.1:
                    active_apps.append(p['name'])
        
        cache_data = {
            'timestamp': time.time(),
            'active_window': active_window,
            'active_app': active_app,
            'active_apps': active_apps,
            'window_history': window_history
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        
        # Write to cache
        with open(CACHE_PATH, 'w') as f:
            json.dump(cache_data, f, indent=2)
            
        logger.debug(f"Wrote to cache: {CACHE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error writing cache: {e}")
        logger.error(traceback.format_exc())
        return False

# Main function
async def main():
    """Main function"""
    sensor = SimpleProcessSensor()
    await sensor.start()
    
    print("Process sensor started. Press Ctrl+C to exit.")
    try:
        while True:
            try:
                # Get data
                data = await sensor.get_data()
                # Write to cache
                write_cache(data)
                # Log heartbeat occasionally
                if int(time.time()) % 60 == 0:  # Log every minute
                    logger.info("Process sensor heartbeat")
                # Sleep
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("Stopping process sensor...")
    finally:
        await sensor.stop()

if __name__ == "__main__":
    asyncio.run(main())