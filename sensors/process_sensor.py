"""
Process Sensor Module
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessSensor:
    """Monitors system processes and active applications."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize process sensor with configuration."""
        self.config = config
        self.running = False
        self.cache_file = 'process_sensor_cache.json'
        self.cache = self._load_cache()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Process sensor initialized with config: %s", config)
        
        # Initialize process tracking
        self.last_process_list = set()
        self.last_active_apps = []
        self.last_update_time = 0
        
    def _load_cache(self) -> Dict[str, Any]:
        """Load cached data from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            return {}
    
    def _save_cache(self) -> None:
        """Save current state to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
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
        """Get list of active processes with detailed logging."""
        try:
            self.logger.info("Getting active processes...")
            start_time = time.time()
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    # Skip excluded processes
                    if any(pattern in proc.info['name'].lower() for pattern in self.config.get('exclude_patterns', [])):
                        continue
                    
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
            
            self.logger.info(f"Found {len(processes)} active processes in {time.time() - start_time:.2f} seconds")
            self.logger.debug(f"Process list: {json.dumps(processes, indent=2)}")
            
            return processes
            
        except Exception as e:
            self.logger.error(f"Error getting active processes: {e}")
            return []
    
    def _get_active_apps(self) -> List[str]:
        """Get list of active applications with detailed logging."""
        try:
            self.logger.info("Getting active applications...")
            start_time = time.time()
            
            # Get list of running applications
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    # Skip system processes
                    if proc.info['name'] in ['kernel_task', 'launchd', 'WindowServer']:
                        continue
                    
                    # Skip excluded patterns
                    if any(pattern in proc.info['name'].lower() for pattern in self.config.get('exclude_patterns', [])):
                        continue
                    
                    if proc.info['name'] not in apps:
                        apps.append(proc.info['name'])
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.logger.info(f"Found {len(apps)} active applications in {time.time() - start_time:.2f} seconds")
            self.logger.debug(f"Application list: {apps}")
            
            return apps
            
        except Exception as e:
            self.logger.error(f"Error getting active applications: {e}")
            return []
    
    def _get_active_window(self) -> Optional[str]:
        """Get active window title with enhanced detection and detailed logging."""
        try:
            self.logger.info("Getting active window...")
            start_time = time.time()
            
            # Enhanced AppleScript with multiple fallback methods
            try:
                # Method 1: Try to get window title
                script = '''
                tell application "System Events"
                    try
                        set frontWindow to title of front window of first application process whose frontmost is true
                        return frontWindow
                    on error
                        try
                            set frontWindow to name of front window of first application process whose frontmost is true
                            return frontWindow
                        on error
                            set frontApp to name of first application process whose frontmost is true
                            return frontApp & " - Main Window"
                        end try
                    end try
                end tell
                '''
                
                import subprocess
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=3)
                
                if result.returncode == 0 and result.stdout.strip():
                    window_title = result.stdout.strip()
                    self.logger.info(f"Active window retrieved in {time.time() - start_time:.2f} seconds")
                    self.logger.debug(f"Active window: {window_title}")
                    return window_title
                    
            except subprocess.TimeoutExpired:
                self.logger.warning("AppleScript timeout - using fallback")
            except Exception as e:
                self.logger.debug(f"AppleScript method failed: {e}")
            
            # Method 2: Fallback to just application name
            try:
                simple_script = 'tell application "System Events" to get name of first process whose frontmost is true'
                result = subprocess.run(['osascript', '-e', simple_script], 
                                      capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0 and result.stdout.strip():
                    app_name = result.stdout.strip()
                    # Clean up helper process names
                    if " (" in app_name:
                        app_name = app_name.split(" (")[0]
                    window_title = f"{app_name} - Active Window"
                    self.logger.info(f"Fallback window retrieved in {time.time() - start_time:.2f} seconds")
                    self.logger.debug(f"Fallback window: {window_title}")
                    return window_title
                    
            except Exception as e:
                self.logger.debug(f"Fallback method failed: {e}")
            
            # Method 3: Use psutil as last resort
            try:
                import psutil
                processes = []
                for proc in psutil.process_iter(['name', 'cpu_percent']):
                    try:
                        if proc.info['name'] not in ['kernel_task', 'WindowServer', 'loginwindow']:
                            processes.append((proc.info['name'], proc.info['cpu_percent'] or 0))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if processes:
                    # Sort by CPU and take the most active
                    processes.sort(key=lambda x: x[1], reverse=True)
                    app_name = processes[0][0]
                    window_title = f"{app_name} - Process Window"
                    self.logger.info(f"Process-based window retrieved in {time.time() - start_time:.2f} seconds")
                    self.logger.debug(f"Process window: {window_title}")
                    return window_title
                    
            except Exception as e:
                self.logger.debug(f"Process method failed: {e}")
            
            # Final fallback
            self.logger.warning("All window detection methods failed")
            return "Unknown - Active Window"
            
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
            return None
    
    async def get_current_state(self) -> Dict[str, Any]:
        """Get current process state with detailed logging."""
        try:
            self.logger.info("Getting current process state...")
            start_time = time.time()
            
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
            
            # Log state details
            self.logger.info(f"Process state captured in {time.time() - start_time:.2f} seconds")
            self.logger.debug(f"State details: {json.dumps(state, indent=2)}")
            
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