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

# Configure logging
logger = logging.getLogger(__name__)

class ScreenSensor:
    """Sensor for monitoring screen content."""
    
    def __init__(self):
        self.current_state = {
            "timestamp": time.time(),
            "text": "",
            "image": None,
            "has_images": False,
            "has_videos": False,
            "image_hash": None
        }
        logger.info("Screen sensor initialized")
    
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
            
            # Update state
            self.current_state.update({
                "timestamp": time.time(),
                "image": screenshot,
                "image_hash": image_hash,
                "image_size": len(img_byte_arr)
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
    """Sensor for monitoring active processes."""
    
    def __init__(self):
        self.current_state = {
            "timestamp": time.time(),
            "active_window": "Unknown",
            "active_app": "Unknown",
            "active_apps": [],
            "window_history": []
        }
        logger.info("Process sensor initialized")
    
    async def get_current_state(self) -> Dict[str, Any]:
        """Get current process state."""
        try:
            # Get active processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['name']:
                        processes.append({
                            "pid": proc_info['pid'],
                            "name": proc_info['name'],
                            "cpu_percent": proc_info['cpu_percent'],
                            "memory_percent": proc_info['memory_percent'],
                            "create_time": proc_info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Update state
            self.current_state.update({
                "timestamp": time.time(),
                "active_apps": processes,
                "active_window": processes[0]['name'] if processes else "Unknown",
                "active_app": processes[0]['name'] if processes else "Unknown"
            })
            
            # Update window history
            if processes:
                self.current_state['window_history'].append({
                    "window": processes[0]['name'],
                    "timestamp": time.time()
                })
                # Keep only last 10 entries
                self.current_state['window_history'] = self.current_state['window_history'][-10:]
            
            logger.info(f"Process state updated: {len(processes)} active processes")
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error getting process state: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def get_active_processes(self) -> List[Dict[str, Any]]:
        """Get list of active processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['name']:
                        processes.append({
                            "pid": proc_info['pid'],
                            "name": proc_info['name'],
                            "cpu_percent": proc_info['cpu_percent'],
                            "memory_percent": proc_info['memory_percent'],
                            "create_time": proc_info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            logger.error(f"Error getting active processes: {e}")
            return []
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up process sensor")
        self.current_state = None