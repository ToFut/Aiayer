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
from typing import Dict, List, Optional
import asyncio

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

class ProcessSensor:
    """Sensor for monitoring active processes and window information."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        self.logger.info(f"{self.platform} setup completed successfully")
        self._last_active_app = ""
        self._last_window_title = ""
        
    async def get_data(self) -> Dict:
        """Get current process data with proper error handling."""
        try:
            # Get process data based on platform
            if self.platform == "darwin":
                data = await asyncio.get_event_loop().run_in_executor(
                    None, self._get_macos_data
                )
                return data
            else:
                return {
                    'status': 'error',
                    'error': 'Unsupported platform',
                    'active_app': '',
                    'window_title': '',
                    'app_category': 'unknown',
                    'running_apps': [],
                    'usage_duration': 0
                }

        except Exception as e:
            self.logger.error(f"Error in process monitoring: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'active_app': '',
                'window_title': '',
                'app_category': 'unknown',
                'running_apps': [],
                'usage_duration': 0
            }
            
    def _get_running_apps(self) -> List[str]:
        """Get list of running applications."""
        try:
            if self.platform == "darwin":
                ps_cmd = "ps -ax -o comm="
                ps_result = subprocess.run(ps_cmd.split(), 
                                        capture_output=True, text=True, timeout=1.0)
                if ps_result.returncode == 0:
                    return [line.strip() for line in ps_result.stdout.splitlines() 
                            if line.strip() and not line.startswith('/')][:10]  # Limit to 10 apps
            return []
        except Exception as e:
            self.logger.error(f"Error getting running apps: {e}")
            return []
            
    def _get_usage_duration(self, app_name: str) -> int:
        """Get the duration an app has been in use."""
        try:
            if not app_name:
                return 0
                
            for proc in psutil.process_iter(['name', 'create_time']):
                try:
                    if proc.info['name'].lower() == app_name.lower():
                        return int(time.time() - proc.info['create_time'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return 0
        except Exception as e:
            self.logger.error(f"Error getting usage duration: {e}")
            return 0

    def _get_macos_data(self) -> Dict:
        """Get process data on macOS."""
        try:
            # Get active app using AppleScript
            as_cmd = """
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontWindow to ""
                try
                    tell process frontApp
                        set frontWindow to name of front window
                    end tell
                end try
                return {frontApp & ":::" & frontWindow}
            end tell
            """
            
            result = subprocess.run(['osascript', '-e', as_cmd], 
                                  capture_output=True, text=True, timeout=1.0)
            
            if result.returncode == 0 and result.stdout.strip():
                app_info = result.stdout.strip().split(":::")
                active_app = app_info[0] if len(app_info) > 0 else ""
                window_title = app_info[1] if len(app_info) > 1 else ""
                
                # Update last known values if we got valid data
                if active_app:
                    self._last_active_app = active_app
                if window_title:
                    self._last_window_title = window_title
                    
                # Get running apps
                ps_cmd = "ps -ax -o comm="
                ps_result = subprocess.run(ps_cmd.split(), 
                                        capture_output=True, text=True, timeout=1.0)
                running_apps = []
                if ps_result.returncode == 0:
                    running_apps = [line.strip() for line in ps_result.stdout.splitlines() 
                                  if line.strip() and not line.startswith('/')]
                
                return {
                    "active_app": self._last_active_app,
                    "window_title": self._last_window_title,
                    "app_category": self._determine_app_category(self._last_active_app),
                    "running_apps": running_apps[:10],  # Limit to 10 apps
                    "usage_duration": 0  # TODO: Implement usage tracking
                }
            else:
                # Return last known values if current query failed
                return {
                    "active_app": self._last_active_app,
                    "window_title": self._last_window_title,
                    "app_category": self._determine_app_category(self._last_active_app),
                    "running_apps": [],
                    "usage_duration": 0
                }
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Process query timed out")
            return {
                "active_app": self._last_active_app,
                "window_title": self._last_window_title,
                "app_category": self._determine_app_category(self._last_active_app),
                "running_apps": [],
                "usage_duration": 0
            }
        except Exception as e:
            self.logger.error(f"Error in macOS process data collection: {e}")
            return {
                "active_app": self._last_active_app,
                "window_title": self._last_window_title,
                "app_category": "unknown",
                "running_apps": [],
                "usage_duration": 0
            }
            
    def _determine_app_category(self, app_name: str) -> str:
        """Determine the category of an application based on its name."""
        app_name = app_name.lower()
        
        categories = {
            'development': ['code', 'editor', 'ide', 'terminal', 'git', 'github'],
            'browser': ['chrome', 'firefox', 'safari', 'edge', 'brave'],
            'document': ['word', 'excel', 'powerpoint', 'pdf', 'document'],
            'communication': ['slack', 'discord', 'teams', 'zoom', 'mail', 'message'],
            'media': ['spotify', 'youtube', 'netflix', 'player', 'music'],
            'system': ['settings', 'finder', 'explorer', 'terminal', 'cmd']
        }
        
        for category, keywords in categories.items():
            if any(keyword in app_name for keyword in keywords):
                return category
                
        return 'other'

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sensor = ProcessSensor()
    sensor.start()
    
    print("Monitoring active windows and processes. Switch windows to test.")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(2)
            print(f"\nActive: {sensor.active_app} - {sensor.active_window_title}")
            print(f"Running apps: {', '.join(list(sensor.running_apps)[:5])}...")
    except KeyboardInterrupt:
        print("\nStopping process sensor...")
    finally:
        sensor.stop()