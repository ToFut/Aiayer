"""
Sensors module for Memory System
Contains sensor implementations for screen and process monitoring.
"""
import logging
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
import psutil
from PIL import ImageGrab
import hashlib
from io import BytesIO
import os

# Configure logging
logger = logging.getLogger(__name__)

class ScreenSensor:
    """Sensor for monitoring screen content."""
    
    def __init__(self, config=None):
        """Initialize screen sensor with optional config."""
        self.config = config or {}
        self.current_state = {
            "timestamp": time.time(),
            "text": "",
            "image": None,
            "has_images": False,
            "has_videos": False,
            "image_hash": None
        }
        logger.info("Screen sensor initialized")
    
    async def initialize(self):
        """Initialize the sensor with proper error handling and retries"""
        try:
            logger.info("Screen sensor initialization started")
            return True
        except Exception as e:
            logger.error(f"Error initializing screen sensor: {e}")
            return False
    
    def get_active_apps(self) -> List[str]:
        """Get list of currently active applications."""
        try:
            active_apps = []
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    if proc.info['name']:
                        active_apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return active_apps
        except Exception as e:
            logger.error(f"Error getting active apps: {e}")
            return []
    
    async def get_current_state(self) -> Dict[str, Any]:
        """Get current screen state."""
        try:
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Convert to bytes for hashing
            img_byte_arr = BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Generate hash of the image
            image_hash = hashlib.md5(img_byte_arr).hexdigest()
            
            # Get active apps
            active_apps = self.get_active_apps()
            
            # Update state
            self.current_state.update({
                "timestamp": time.time(),
                "image": screenshot,
                "image_hash": image_hash,
                "image_size": len(img_byte_arr),
                "active_apps": active_apps
            })
            
            logger.info(f"Screen captured: {len(img_byte_arr)} bytes, hash: {image_hash[:8]}")
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error getting screen state: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _get_window_info(self) -> Dict[str, Any]:
        """Get information about current window."""
        try:
            # Get active window info using psutil
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    if proc.info['name']:
                        return {
                            "title": proc.info['name'],
                            "app": proc.info['name'],
                            "pid": proc.info['pid'],
                            "timestamp": time.time()
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return {
                "title": "Unknown",
                "app": "Unknown",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return {
                "title": "Error",
                "app": "Error",
                "timestamp": time.time()
            }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up screen sensor")
        self.current_state = None

class ProcessSensor:
    """Sensor for monitoring system processes."""
    
    def __init__(self, config=None):
        """Initialize process sensor with optional config."""
        self.config = config or {}
        self.current_state = {
            "timestamp": time.time(),
            "active_processes": [],
            "cpu_usage": 0,
            "memory_usage": 0
        }
        logger.info("Process sensor initialized")
    
    async def initialize(self):
        """Initialize the sensor with proper error handling and retries"""
        try:
            logger.info("Process sensor initialization started")
            return True
        except Exception as e:
            logger.error(f"Error initializing process sensor: {e}")
            return False
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get current process state."""
        try:
            # Get list of active processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Update state
            self.current_state.update({
                "timestamp": time.time(),
                "active_processes": processes[:10],  # Keep only top 10 processes
                "cpu_usage": sum(p['cpu_percent'] for p in processes),
                "memory_usage": sum(p['memory_percent'] for p in processes)
            })
            
            logger.info(f"Process state updated: {len(processes)} processes found")
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error getting process state: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up process sensor")
        self.current_state = None

class FileSensor:
    """Sensor for monitoring file system activity."""
    
    def __init__(self, config=None):
        """Initialize file sensor with optional config."""
        self.config = config or {}
        self.current_state = {
            "timestamp": time.time(),
            "recent_files": [],
            "active_files": [],
            "file_changes": []
        }
        logger.info("File sensor initialized")
    
    async def initialize(self):
        """Initialize the sensor with proper error handling and retries"""
        try:
            logger.info("File sensor initialization started")
            return True
        except Exception as e:
            logger.error(f"Error initializing file sensor: {e}")
            return False
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get current file system state."""
        try:
            # Get list of recently modified files
            recent_files = []
            for root, dirs, files in os.walk(os.path.expanduser("~")):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        stat = os.stat(file_path)
                        recent_files.append({
                            "path": file_path,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "accessed": stat.st_atime
                        })
                    except (OSError, PermissionError):
                        continue
                # Limit the number of files to check
                if len(recent_files) >= 100:
                    break
            
            # Sort by modification time
            recent_files.sort(key=lambda x: x["modified"], reverse=True)
            
            # Update state
            self.current_state.update({
                "timestamp": time.time(),
                "recent_files": recent_files[:10],  # Keep only 10 most recent
                "active_files": [f for f in recent_files if time.time() - f["accessed"] < 300]  # Files accessed in last 5 minutes
            })
            
            logger.info(f"File state updated: {len(recent_files)} files found")
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error getting file state: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up file sensor")
        self.current_state = None