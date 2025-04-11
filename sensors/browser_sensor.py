"""
Browser Integration Sensor Module
Optional component that can receive data from browser extensions or local API integrations.
"""
import logging
import threading
import time
from collections import deque
import platform
import subprocess

class BrowserSensor:
    """
    Handles integration with browser data (URLs, page content, etc.).
    Can either receive data via push from extensions or pull via OS scripting.
    """
    
    def __init__(self, poll_interval=10, history_size=50):
        """
        Initialize the browser sensor.
        
        Args:
            poll_interval (int): Seconds between polling for browser info (if using pull method)
            history_size (int): Number of URL history items to keep
        """
        self.current_url = None
        self.current_title = None
        self.selected_text = None
        self.url_history = deque(maxlen=history_size)
        self.interval = poll_interval
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
    
    def update_from_browser(self, url, title=None, text=None):
        """
        Update browser data (for browser extension push method).
        
        Args:
            url (str): Current browser URL
            title (str): Current page title
            text (str): Selected text on page (if any)
        """
        timestamp = time.time()
        self.current_url = url
        self.current_title = title
        
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
            if self.system == "Darwin":  # macOS
                self._poll_browser_macos()
            elif self.system == "Windows":
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