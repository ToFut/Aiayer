#!/usr/bin/env python3
"""
Screen Sensor
Captures screen-related data such as active window, window title, and screen dimensions.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('screen_sensor')

class ScreenSensor:
    """Sensor for capturing screen-related data."""
    
    def __init__(self):
        """Initialize the screen sensor."""
        self.last_data = None
        logger.info("Screen sensor initialized")
    
    async def get_data(self) -> Dict[str, Any]:
        """Get current screen data."""
        try:
            # Get screen data
            data = {
                'timestamp': datetime.now().isoformat(),
                'active_window': self._get_active_window(),
                'window_title': self._get_window_title(),
                'screen_dimensions': self._get_screen_dimensions(),
                'mouse_position': self._get_mouse_position()
            }
            
            # Update last data
            self.last_data = data
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting screen data: {e}")
            logger.error(traceback.format_exc())
            return self.last_data or {
                'timestamp': datetime.now().isoformat(),
                'active_window': None,
                'window_title': None,
                'screen_dimensions': None,
                'mouse_position': None
            }
    
    def _get_active_window(self) -> Optional[str]:
        """Get the active window name."""
        try:
            # For macOS
            if sys.platform == 'darwin':
                import subprocess
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first process whose frontmost is true'], capture_output=True, text=True)
                return result.stdout.strip()
            # For Linux
            elif sys.platform == 'linux':
                import subprocess
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], capture_output=True, text=True)
                return result.stdout.strip()
            # For Windows
            elif sys.platform == 'win32':
                import win32gui
                return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return None
    
    def _get_window_title(self) -> Optional[str]:
        """Get the current window title."""
        try:
            # For macOS
            if sys.platform == 'darwin':
                import subprocess
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first process whose frontmost is true'], capture_output=True, text=True)
                return result.stdout.strip()
            # For Linux
            elif sys.platform == 'linux':
                import subprocess
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], capture_output=True, text=True)
                return result.stdout.strip()
            # For Windows
            elif sys.platform == 'win32':
                import win32gui
                return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting window title: {e}")
            return None
    
    def _get_screen_dimensions(self) -> Optional[Dict[str, int]]:
        """Get the screen dimensions."""
        try:
            # For macOS
            if sys.platform == 'darwin':
                import subprocess
                result = subprocess.run(['osascript', '-e', 'tell application "Finder" to get bounds of window of desktop'], capture_output=True, text=True)
                bounds = result.stdout.strip().split(', ')
                return {
                    'width': int(bounds[2]) - int(bounds[0]),
                    'height': int(bounds[3]) - int(bounds[1])
                }
            # For Linux
            elif sys.platform == 'linux':
                import subprocess
                result = subprocess.run(['xrandr', '--current'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if '*' in line:
                        dimensions = line.split()[0].split('x')
                        return {
                            'width': int(dimensions[0]),
                            'height': int(dimensions[1])
                        }
            # For Windows
            elif sys.platform == 'win32':
                import win32api
                width = win32api.GetSystemMetrics(0)
                height = win32api.GetSystemMetrics(1)
                return {
                    'width': width,
                    'height': height
                }
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting screen dimensions: {e}")
            return None
    
    def _get_mouse_position(self) -> Optional[Dict[str, int]]:
        """Get the current mouse position."""
        try:
            # For macOS
            if sys.platform == 'darwin':
                try:
                    from Quartz import CGEventCreate, CGEventGetLocation
                    event = CGEventCreate(None)
                    loc = CGEventGetLocation(event)
                    return {'x': int(loc.x), 'y': int(loc.y)}
                except Exception as e:
                    logger.error(f"Error using Quartz for mouse position: {e}")
                    return None
            # For Linux
            elif sys.platform == 'linux':
                import subprocess
                result = subprocess.run(['xdotool', 'getmouselocation'], capture_output=True, text=True)
                x = int(result.stdout.split()[0].split(':')[1])
                y = int(result.stdout.split()[1].split(':')[1])
                return {'x': x, 'y': y}
            # For Windows
            elif sys.platform == 'win32':
                import win32api
                x, y = win32api.GetCursorPos()
                return {'x': x, 'y': y}
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting mouse position: {e}")
            return None