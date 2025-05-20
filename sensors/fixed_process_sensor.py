#!/usr/bin/env python3
"""
Fixed Process Sensor Module
Monitors system processes and active applications.
"""
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json
import psutil
import re

# Configure logging
os.makedirs('logs/sensors/sensor_process', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/sensor_process/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedProcessSensor:
    """Monitors system processes and active applications."""
    
    def __init__(self):
        """Initialize process sensor."""
        self.running = False
        self.cache_file = 'cache/process_sensor/process_cache.json'
        self.cache = self._load_cache()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Process sensor initialized")
        
        # Initialize process tracking
        self.last_process_list = set()
        self.last_active_apps = []
        self.last_update_time = 0
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
    def _load_cache(self) -> Dict[str, Any]:
        """Load cached data from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            return {
                'timestamp': time.time(),
                'active_window': '',
                'active_app': '',
                'active_apps': [],
                'window_history': []
            }
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            return {
                'timestamp': time.time(),
                'active_window': '',
                'active_app': '',
                'active_apps': [],
                'window_history': []
            }
    
    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save current state to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    async def start(self) -> bool:
        """Start process monitoring."""
        try:
            self.logger.info("Starting process monitoring...")
            self.running = True
            self.logger.info("Process monitoring started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start process monitoring: {e}")
            return False
    
    def _get_active_processes(self) -> List[Dict[str, Any]]:
        """Get list of active processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    process_info = {
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'username': proc.info['username'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    }
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return processes
        except Exception as e:
            self.logger.error(f"Error getting active processes: {e}")
            return []
    
    def _get_active_apps(self) -> List[str]:
        """Get list of active applications."""
        try:
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] not in apps:
                        apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return apps
        except Exception as e:
            self.logger.error(f"Error getting active applications: {e}")
            return []
    
    def _get_active_window(self) -> Optional[str]:
        """Get active window title."""
        try:
            script = 'tell application "System Events" to get name of first window of first process whose frontmost is true'
            result = os.popen(f'osascript -e \'{script}\'').read().strip()
            return result
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
            return None
    
    async def get_current_state(self) -> Dict[str, Any]:
        """Get current process state."""
        try:
            # Get process information
            processes = self._get_active_processes()
            apps = self._get_active_apps()
            active_window = self._get_active_window()
            
            # Create state dictionary
            state = {
                'timestamp': time.time(),
                'active_processes': processes,
                'active_apps': apps,
                'active_window': active_window,
                'process_count': len(processes),
                'app_count': len(apps)
            }
            
            # Save to cache
            self._save_cache(state)
            
            return state
        except Exception as e:
            self.logger.error(f"Error getting current state: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e)
            }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.logger.info("Cleaning up process sensor...")
            self.running = False
            self.logger.info("Process sensor cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error cleaning up process sensor: {e}")

async def main():
    """Main function."""
    sensor = FixedProcessSensor()
    if not await sensor.start():
        logger.error("Failed to start process sensor")
        return
    
    logger.info("Process sensor started")
    
    try:
        while True:
            try:
                # Get current state
                state = await sensor.get_current_state()
                
                # Log heartbeat occasionally
                if int(time.time()) % 60 == 0:  # Log every minute
                    logger.info("Process sensor heartbeat")
                
                # Sleep
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Stopping process sensor...")
    finally:
        await sensor.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 