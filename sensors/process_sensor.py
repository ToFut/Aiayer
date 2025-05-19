"""
Process Sensor Module
Monitors active processes and window titles.
"""
import os
import time
import logging
import platform
import subprocess
import threading
import psutil
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import asyncio
import sys
import traceback
from pathlib import Path

# Conditionally import Windows-specific modules
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        WINDOWS_SUPPORT = True
    except ImportError:
        WINDOWS_SUPPORT = False
else:
    WINDOWS_SUPPORT = False

logger = logging.getLogger(__name__)

@dataclass
class ProcessData:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    create_time: float
    last_seen: float

class ProcessSensor:
    """Monitors system processes and active windows."""
    
    def __init__(self, config=None):
        """Initialize the process sensor."""
        self.config = config or {}
        self.interval_sec = self.config.get('interval_sec', 2.0)
        self.log_dir = self.config.get('log_dir', 'logs/sensors')
        self.logger = logging.getLogger('sensors.process_sensor')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler(os.path.join(self.log_dir, 'process_sensor.log')))
        
        # Initialize state
        self.running = False
        self.last_update = time.time()
        self.process_data = {}
        self.window_data = {}
        self.sensor_type = "process"
        
        # Initialize stats
        self.stats = {
            'total_processes': 0,
            'active_windows': 0,
            'last_scan_time': None,
            'is_running': False
        }
        
        # Initialize process tracking
        self.process_history = deque(maxlen=100)
        self.window_history = deque(maxlen=100)
        
        self.logger.info("Process sensor initialized")
        
    async def start(self):
        """Start the process sensor."""
        try:
            self.running = True
            self.stats['is_running'] = True
            self.logger.info("Process sensor started")
            return True
        except Exception as e:
            self.logger.error(f"Error starting process sensor: {e}")
            return False

    async def stop(self):
        """Stop the process sensor."""
        try:
            self.running = False
            self.stats['is_running'] = False
            self.logger.info("Process sensor stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping process sensor: {e}")
            return False

    async def get_data(self) -> Dict[str, Any]:
        """Get current process and window data."""
        try:
            current_time = time.time()
            self.logger.info("Starting process data collection...")
            
            # Get process data with improved error handling
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                    try:
                        process_info = proc.info
                        processes.append({
                            'pid': process_info['pid'],
                            'name': process_info['name'],
                            'username': process_info['username'],
                            'cpu_percent': process_info['cpu_percent'],
                            'memory_percent': process_info['memory_percent']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                self.logger.info(f"Collected data for {len(processes)} processes")
            except Exception as e:
                self.logger.error(f"Error getting process data: {e}")
                processes = []
            
            # Get window data with improved error handling
            windows = []
            try:
                import Quartz
                window_list = Quartz.CGWindowListCopyWindowInfo(
                    Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                    Quartz.kCGNullWindowID
                )
                
                for window in window_list:
                    if window.get(Quartz.kCGWindowName):
                        # Convert NSDictionary and other Objective-C types to Python native types
                        window_bounds = window.get(Quartz.kCGWindowBounds)
                        if window_bounds:
                            # Convert NSDict bounds to a regular Python dict
                            bounds_dict = {
                                'x': window_bounds.get('X', 0),
                                'y': window_bounds.get('Y', 0),
                                'width': window_bounds.get('Width', 0),
                                'height': window_bounds.get('Height', 0)
                            }
                        else:
                            bounds_dict = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
                            
                        windows.append({
                            'name': str(window.get(Quartz.kCGWindowName, '')),
                            'owner': str(window.get(Quartz.kCGWindowOwnerName, '')),
                            'bounds': bounds_dict,
                            'layer': int(window.get(Quartz.kCGWindowLayer, 0))
                        })
                self.logger.info(f"Collected data for {len(windows)} windows")
            except Exception as e:
                self.logger.error(f"Error getting window data: {e}")
                self.logger.error(traceback.format_exc())
                windows = []
            
            # Update stats
            self.stats.update({
                'total_processes': len(processes),
                'active_windows': len(windows),
                'last_scan_time': current_time
            })
            
            # Create data object
            data = {
                'timestamp': current_time,
                'type': 'process_sensor',
                'processes': processes,
                'windows': windows,
                'stats': self.stats,
                'last_update': self.last_update
            }
            
            # Update history
            self.process_history.append(processes)
            self.window_history.append(windows)
            
            # Update last update time
            self.last_update = current_time
            
            # Write to cache file
            try:
                cache_dir = "cache/process_sensor"
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = f"{cache_dir}/process_cache.json"
                
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'data': data
                    }, f, indent=2)
                
                self.logger.info(f"Process data written to cache: {len(processes)} processes, {len(windows)} windows")
            except Exception as e:
                self.logger.error(f"Error writing process data to cache: {e}")
            
            self.logger.info("Process data collection completed successfully")
            return data
            
        except Exception as e:
            self.logger.error(f"Error in process sensor get_data: {e}")
            self.logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'timestamp': current_time
            }

    async def get_stats(self) -> Dict[str, Any]:
        """Get process sensor statistics."""
        try:
            return {
                'total_processes': self.stats['total_processes'],
                'active_windows': self.stats['active_windows'],
                'last_scan_time': self.stats['last_scan_time'],
                'is_running': self.running,
                'interval_sec': self.interval_sec,
                'process_history_size': len(self.process_history),
                'window_history_size': len(self.window_history)
            }
        except Exception as e:
            self.logger.error(f"Error getting process sensor stats: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get process sensor metrics (alias for get_stats for consistency)."""
        return await self.get_stats()

    def load_from_cache(self):
        """Load process data from cache file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    if isinstance(cache_data, dict):
                        return cache_data.get("processes", [])
                    elif isinstance(cache_data, list):
                        return cache_data
                    else:
                        return []
            return []
        except Exception as e:
            self.logger.error(f"Error loading from cache: {e}")
            return []

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Define cache path
    CACHE_PATH = 'cache/process_sensor/process_cache.json'
    
    sensor = ProcessSensor(config={})
    asyncio.run(sensor.start())
    
    print("Monitoring active windows and processes. Switch windows to test.")
    print("Press Ctrl+C to stop")
    
    try:
        last_heartbeat = time.time()
        while True:
            data = asyncio.run(sensor.get_data())
            # Write to cache file
            try:
                # Custom JSON serialization to handle Objective-C types
                def clean_dict(obj):
                    """Recursively convert an object to a serializable dict"""
                    if isinstance(obj, dict):
                        return {str(k): clean_dict(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_dict(item) for item in obj]
                    elif isinstance(obj, (str, int, float, bool, type(None))):
                        return obj
                    else:
                        # Convert any other type to string
                        return str(obj)
                
                # Clean the data before serializing
                clean_data = clean_dict(data)
                
                os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
                with open(CACHE_PATH, 'w') as f:
                    json.dump(clean_data, f, indent=2)
                    
                # Validate after writing
                with open(CACHE_PATH, 'r') as f:
                    loaded = json.load(f)
                    assert 'processes' in loaded and isinstance(loaded['processes'], list)
            except Exception as e:
                print(f"[ERROR] Failed to write/validate process cache: {e}")
                print(traceback.format_exc())
            time.sleep(2)
            # Optionally print a summary
            print(f"Wrote {len(data.get('processes', []))} processes and {len(data.get('windows', []))} windows to cache.")
            # Heartbeat log
            if time.time() - last_heartbeat > 10:
                print("[HEARTBEAT] Process sensor is alive.")
                last_heartbeat = time.time()
    except KeyboardInterrupt:
        print("\nStopping process sensor...")
    finally:
        asyncio.run(sensor.stop())