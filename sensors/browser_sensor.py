"""
Browser Sensor Module
Monitors browser activity and tab information.
"""
import psutil
import time
import logging
from datetime import datetime
import threading
import platform
import subprocess
from collections import deque

class BrowserSensor:
    """
    Monitors browser activity and tab information.
    Runs in a background thread at specified intervals.
    """
    
    def __init__(self, interval_sec=5):
        """
        Initialize the browser sensor.
        
        Args:
            interval_sec (int): Seconds between browser checks
        """
        self.interval = interval_sec
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self.sensor_type = "browser"
        self._last_update = time.time()
        self._current_url = None
        self._current_title = None
        self._tab_count = 0
        self.url_history = deque(maxlen=100)
        self.selected_text = None
        
        # Platform-specific setup
        self.platform = platform.system().lower()
        if self.platform == "darwin":  # macOS
            self._setup_macos()
        elif self.platform == "windows":
            self._setup_windows()
        elif self.platform == "linux":
            self._setup_linux()

    def _setup_macos(self):
        """Setup macOS-specific components."""
        try:
            # Check if osascript is available
            subprocess.check_output(["which", "osascript"])
            self.logger.info("macOS setup completed successfully")
        except subprocess.CalledProcessError:
            self.logger.error("osascript not found. Some features may not work.")
        except Exception as e:
            self.logger.error(f"Error during macOS setup: {e}")

    def _setup_windows(self):
        """Setup Windows-specific components."""
        try:
            # Check if PowerShell is available
            subprocess.check_output(["powershell", "-Command", "Get-Process"])
            self.logger.info("Windows setup completed successfully")
        except subprocess.CalledProcessError:
            self.logger.error("PowerShell not found. Some features may not work.")
        except Exception as e:
            self.logger.error(f"Error during Windows setup: {e}")

    def _setup_linux(self):
        """Setup Linux-specific components."""
        try:
            # Check if xdotool is available
            subprocess.check_output(["which", "xdotool"])
            self.logger.info("Linux setup completed successfully")
        except subprocess.CalledProcessError:
            self.logger.error("xdotool not found. Some features may not work.")
        except Exception as e:
            self.logger.error(f"Error during Linux setup: {e}")

    def has_updates(self):
        """Check if there are new updates since last check."""
        current_time = time.time()
        if current_time - self._last_update >= self.interval:
            self._last_update = current_time
            return True
        return False

    def get_data(self):
        """Get the current sensor data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "type": "browser_info",
            "data": {
                "url": self.get_current_url(),
                "title": self.get_current_title(),
                "tab_count": self.get_tab_count()
            }
        }

    def get_current_url(self):
        """Get the current browser URL."""
        if self.platform == "darwin":
            return self._get_url_macos()
        elif self.platform == "windows":
            return self._get_url_windows()
        elif self.platform == "linux":
            return self._get_url_linux()
        return None

    def get_current_title(self):
        """Get the current browser tab title."""
        if self.platform == "darwin":
            return self._get_title_macos()
        elif self.platform == "windows":
            return self._get_title_windows()
        elif self.platform == "linux":
            return self._get_title_linux()
        return None

    def get_tab_count(self):
        """Get the number of open browser tabs."""
        if self.platform == "darwin":
            return self._get_tab_count_macos()
        elif self.platform == "windows":
            return self._get_tab_count_windows()
        elif self.platform == "linux":
            return self._get_tab_count_linux()
        return 0

    def _get_url_macos(self):
        """Get URL on macOS."""
        browsers = ["Safari", "Google Chrome"]
        for browser in browsers:
            try:
                if browser == "Safari":
                    cmd = 'tell application "Safari" to get URL of current tab of front window'
                else:
                    cmd = 'tell application "Google Chrome" to get URL of active tab of front window'
                return subprocess.check_output(["osascript", "-e", cmd], text=True).strip()
            except subprocess.CalledProcessError:
                continue
        return None

    def _get_title_macos(self):
        """Get title on macOS."""
        browsers = ["Safari", "Google Chrome"]
        for browser in browsers:
            try:
                if browser == "Safari":
                    cmd = 'tell application "Safari" to get name of current tab of front window'
                else:
                    cmd = 'tell application "Google Chrome" to get title of active tab of front window'
                return subprocess.check_output(["osascript", "-e", cmd], text=True).strip()
            except subprocess.CalledProcessError:
                continue
        return None

    def _get_tab_count_macos(self):
        """Get tab count on macOS."""
        browsers = ["Safari", "Google Chrome"]
        for browser in browsers:
            try:
                if browser == "Safari":
                    cmd = 'tell application "Safari" to count tabs of front window'
                else:
                    cmd = 'tell application "Google Chrome" to count tabs of front window'
                return int(subprocess.check_output(["osascript", "-e", cmd], text=True).strip())
            except subprocess.CalledProcessError:
                continue
        return 0

    def _get_url_windows(self):
        """Get URL on Windows."""
        # Placeholder for Windows implementation
        return None

    def _get_title_windows(self):
        """Get title on Windows."""
        # Placeholder for Windows implementation
        return None

    def _get_tab_count_windows(self):
        """Get tab count on Windows."""
        # Placeholder for Windows implementation
        return 0

    def _get_url_linux(self):
        """Get URL on Linux."""
        # Placeholder for Linux implementation
        return None

    def _get_title_linux(self):
        """Get title on Linux."""
        # Placeholder for Linux implementation
        return None

    def _get_tab_count_linux(self):
        """Get tab count on Linux."""
        # Placeholder for Linux implementation
        return 0
    
    def update_from_browser(self, url, title=None, text=None):
        """
        Update browser data (for browser extension push method).
        
        Args:
            url (str): Current browser URL
            title (str): Current page title
            text (str): Selected text on page (if any)
        """
        timestamp = time.time()
        self._current_url = url
        self._current_title = title
        
        if text:
            self.selected_text = text
        
        # Record URL in history
        if url and (not self.url_history or self.url_history[-1][1] != url):
            self.url_history.append((timestamp, url, title))
            self.logger.info(f"Browser navigated to: {url}")
        
        return True
    
    def poll_browser_info(self):
        """
        Poll for browser information using OS-specific methods.
        Only works with Safari/Chrome on macOS or Edge/Chrome on Windows.
        """
        try:
            if self.platform == "darwin":  # macOS
                self._poll_browser_macos()
            elif self.platform == "windows":
                self._poll_browser_windows()
            else:
                self.logger.warning("Browser polling not implemented for this platform")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error polling browser info: {e}")
            return False
    
    def _poll_browser_macos(self):
        """Poll browser info on macOS using AppleScript."""
        browsers = ["Safari", "Google Chrome"]
        
        for browser in browsers:
            try:
                # Check if browser is running
                check_cmd = f'tell application "System Events" to count processes whose name is "{browser}"'
                result = subprocess.check_output(["osascript", "-e", check_cmd], text=True).strip()
                
                if result == "0":
                    continue  # Browser not running
                
                # Get URL and title from browser
                if browser == "Safari":
                    get_url_cmd = 'tell application "Safari" to get URL of current tab of front window'
                    get_title_cmd = 'tell application "Safari" to get name of current tab of front window'
                else:  # Chrome
                    get_url_cmd = 'tell application "Google Chrome" to get URL of active tab of front window'
                    get_title_cmd = 'tell application "Google Chrome" to get title of active tab of front window'
                
                url = subprocess.check_output(["osascript", "-e", get_url_cmd], text=True).strip()
                title = subprocess.check_output(["osascript", "-e", get_title_cmd], text=True).strip()
                
                if url:
                    self.update_from_browser(url, title)
                    return
            except subprocess.CalledProcessError:
                pass  # Try next browser
    
    def _poll_browser_windows(self):
        """
        Poll browser info on Windows.
        Note: This is a placeholder. Actual implementation would require more complex
        Windows-specific code using UI Automation or browser automation.
        """
        self.logger.info("Windows browser polling not yet implemented")
        # In a real implementation, we might:
        # 1. Check if Chrome/Edge is the foreground window
        # 2. Use UI Automation or a browser automation library to extract URL/title
        # 3. Update self.current_url and self.current_title
    
    def _run_polling_loop(self):
        """Background thread function for periodic polling."""
        self.logger.info("Browser sensor polling started")
        self.running = True
        
        while self.running:
            try:
                self.poll_browser_info()
            except Exception as e:
                self.logger.error(f"Error in browser polling loop: {e}")
            
            time.sleep(self.interval)
    
    def start(self):
        """Start the browser sensor polling thread (if using pull method)."""
        if self.thread is not None and self.thread.is_alive():
            self.logger.warning("Browser sensor already running")
            return
        
        self.thread = threading.Thread(target=self._run_polling_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"Browser sensor thread started with {self.interval}s interval")
    
    def stop(self):
        """Stop the polling thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.logger.info("Browser sensor stopped")
    
    def get_recent_urls(self, count=5):
        """
        Get recently visited URLs.
        
        Args:
            count (int): Number of URL history items to return
            
        Returns:
            list: Recent URL history as formatted strings
        """
        recent = list(self.url_history)[-count:]
        formatted = []
        
        for timestamp, url, title in recent:
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            display_title = title if title else url
            formatted.append(f"{time_str}: {display_title}")
        
        return formatted

# For testing if run directly