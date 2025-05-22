#!/usr/bin/env python3
"""
Better Process Sensor Implementation
Monitors running processes and writes their info to cache
"""
import os
import time
import json
import logging
import subprocess
import platform
from datetime import datetime

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

# Cache file path
CACHE_PATH = 'cache/process_sensor/process_cache.json'

def get_active_window():
    """Get the currently active window."""
    try:
        if platform.system() == "Darwin":  # macOS
            cmd = "osascript -e 'tell application \"System Events\" to name of first application process whose frontmost is true'"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()
            window = stdout.decode('utf-8').strip()
            return window if window else "Unknown"
        elif platform.system() == "Windows":
            # Windows implementation here if needed
            return "Unknown - Windows"
        else:
            return "Unknown - " + platform.system()
    except Exception as e:
        logger.error(f"Error getting active window: {e}")
        return "Error"

def get_active_apps(limit=10):
    """Get a list of active applications."""
    try:
        if platform.system() == "Darwin":  # macOS
            cmd = "ps -eo comm | head -n 20"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()
            apps = [line.strip() for line in stdout.decode('utf-8').split('\n') if line.strip()]
            return apps[:limit]  # Limit the number of apps
        elif platform.system() == "Windows":
            # Windows implementation here if needed
            return ["Unknown - Windows"]
        else:
            return ["Unknown - " + platform.system()]
    except Exception as e:
        logger.error(f"Error getting active apps: {e}")
        return ["Error"]

def update_cache():
    """Update the process cache file."""
    try:
        # Get active window
        active_window = get_active_window()
        
        # Get active apps
        active_apps = get_active_apps()
        
        # Create data
        data = {
            "timestamp": time.time(),
            "active_window": active_window,
            "active_app": active_window,  # Use the active window as the active app
            "active_apps": active_apps,
            "window_history": []
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        
        # Write to cache file
        with open(CACHE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.debug(f"Updated process cache: {active_window}")
        return True
    except Exception as e:
        logger.error(f"Error updating cache: {e}")
        return False

def main():
    """Main function."""
    logger.info("Better process sensor started")
    
    # Create pid file
    with open('pids/process_sensor.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    last_heartbeat = time.time()
    
    try:
        while True:
            # Update cache
            update_cache()
            
            # Print heartbeat log every minute
            if time.time() - last_heartbeat > 60:
                logger.info("Process sensor heartbeat")
                last_heartbeat = time.time()
                
            # Sleep for 2 seconds
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Process sensor stopped by user")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        logger.info("Process sensor stopped")

if __name__ == "__main__":
    main()