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
    """
    Monitors active processes and window titles.
    Runs in a background thread at specified intervals.
    """
    
    def __init__(self, interval_sec=5):
        """
        Initialize the process sensor.
        
        Args:
            interval_sec (int): Seconds between process checks
        """
        self.interval = interval_sec
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self.sensor_type = "process"
        self._last_update = time.time()
        self._active_process = None
        self._window_title = None
        self.running_apps = set()
        self.active_app = None
        self.active_window_title = None
        self.window_history = deque(maxlen=100)
        self._current_app_start_time = time.time()
        
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
        if WINDOWS_SUPPORT:
            self.logger.info("Windows setup completed successfully")
        else:
            self.logger.error("Windows API support not available")

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
            "type": "process_info",
            "data": {
                "active_process": self.get_active_process(),
                "window_title": self.get_window_title()
            }
        }

    def get_active_process(self):
        """Get the currently active process."""
        if self.platform == "darwin":
            return self._get_active_process_macos()
        elif self.platform == "windows":
            return self._get_active_process_windows()
        elif self.platform == "linux":
            return self._get_active_process_linux()
        return None

    def get_window_title(self):
        """Get the current window title."""
        if self.platform == "darwin":
            return self._get_window_title_macos()
        elif self.platform == "windows":
            return self._get_window_title_windows()
        elif self.platform == "linux":
            return self._get_window_title_linux()
        return None

    def _get_active_process_macos(self):
        """Get active process on macOS."""
        try:
            return subprocess.check_output(
                ["osascript", "-e",
                'tell application "System Events" to get name of first process whose frontmost is true'],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            return None

    def _get_window_title_macos(self):
        """Get window title on macOS."""
        try:
            app_name = self._get_active_process_macos()
            if app_name:
                return subprocess.check_output(
                    ["osascript", "-e",
                    f'tell application "System Events" to tell process "{app_name}" to get value of attribute "AXTitle" of front window'],
                    text=True
                ).strip()
        except subprocess.CalledProcessError:
            return None
        return None

    def _get_active_process_windows(self):
        """Get active process on Windows."""
        if not WINDOWS_SUPPORT:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
        except:
            return None

    def _get_window_title_windows(self):
        """Get window title on Windows."""
        if not WINDOWS_SUPPORT:
            return None
        try:
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except:
            return None

    def _get_active_process_linux(self):
        """Get active process on Linux."""
        try:
            return subprocess.check_output(
                ["xdotool", "getwindowfocus", "getwindowpid"],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            return None

    def _get_window_title_linux(self):
        """Get window title on Linux."""
        try:
            return subprocess.check_output(
                ["xdotool", "getwindowfocus", "getwindowname"],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            return None
    
    def update_process_list(self):
        """Update list of running applications."""
        try:
            current_apps = set()
            system_processes = {
                'ReportMemoryExce', 'MailCacheDelete', 'IMDPersistenceAgent', 'tesseract',
                'com.apple.iCloudHelper', 'tipsd', 'donotdisturbd', 'siriknowledged',
                'peopled', 'sociallayerd', 'appstoreagent', 'dataaccessd', 'imklaunchagent',
                'biomesyncd', 'TelemetryDiskChecker', 'ps', 'networkserviceproxy',
                'sysmond', 'CategoriesService', 'UsageTrackingAgent', 'AddressBookSourceSync',
                'MusicCacheExtension', 'CacheDeleteExtension', 'TVCacheExtension',
                'com.apple.AMPArtworkAgent', 'com.apple.AMPDeviceDiscoveryAgent',
                'com.apple.AMPLibraryAgent', 'com.apple.AMPArtworkAgent',
                'com.apple.AMPDeviceDiscoveryAgent', 'com.apple.AMPLibraryAgent',
                'com.apple.AMPArtworkAgent', 'com.apple.AMPDeviceDiscoveryAgent',
                'com.apple.AMPLibraryAgent', 'com.apple.AMPArtworkAgent',
                'com.apple.AMPDeviceDiscoveryAgent', 'com.apple.AMPLibraryAgent',
                'com.apple.AMPArtworkAgent', 'com.apple.AMPDeviceDiscoveryAgent',
                'com.apple.AMPLibraryAgent', 'com.apple.AMPArtworkAgent',
                'com.apple.AMPDeviceDiscoveryAgent', 'com.apple.AMPLibraryAgent'
            }
            
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                try:
                    name = proc.info.get('name')
                    if name and name not in system_processes and not name.startswith('com.apple.'):
                        current_apps.add(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Detect newly launched or closed apps
            opened = current_apps - self.running_apps
            closed = self.running_apps - current_apps
            
            for app in opened:
                self.logger.info(f"App opened: {app}")
            
            for app in closed:
                self.logger.info(f"App closed: {app}")
            
            self.running_apps = current_apps
            return True
        except Exception as e:
            self.logger.error(f"Error updating process list: {e}")
            return False
    
    def update_active_window(self):
        """
        Update the currently active (focused) application and window title.
        Uses platform-specific methods (AppleScript on macOS, Win32API on Windows).
        """
        try:
            prev_app = self.active_app
            prev_title = self.active_window_title
            
            if self.platform == "darwin":  # macOS
                self._update_active_window_macos()
            elif self.platform == "windows" and WINDOWS_SUPPORT:
                self._update_active_window_windows()
            else:
                # Fallback for Linux or unsupported platforms
                self._update_active_window_fallback()
            
            # Record change in window focus if it changed
            if (self.active_app != prev_app or self.active_window_title != prev_title) and self.active_app:
                timestamp = time.time()
                self.window_history.append((
                    timestamp, 
                    self.active_app, 
                    self.active_window_title
                ))
                
                # Update app start time when focus changes
                if self.active_app != prev_app:
                    self._current_app_start_time = timestamp
                
                self.logger.info(f"Focus changed: {self.active_app} - {self.active_window_title}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating active window: {e}")
            return False
    
    def _update_active_window_macos(self):
        """Get active window info using AppleScript on macOS."""
        try:
            # Get active app name via AppleScript
            app_name = subprocess.check_output(
                ["osascript", "-e",
                'tell application "System Events" to get name of first process whose frontmost is true'],
                text=True
            ).strip()
            self.active_app = app_name
            
            # Get window title of frontmost window
            try:
                window_title = subprocess.check_output(
                    ["osascript", "-e",
                    f'tell application "System Events" to tell process "{app_name}" to get value of attribute "AXTitle" of front window'],
                    text=True
                ).strip()
                self.active_window_title = window_title
            except subprocess.CalledProcessError:
                # Some apps don't have window title accessible
                self.active_window_title = f"{app_name} window"
        except subprocess.CalledProcessError:
            # In case of an error (no GUI apps, etc.)
            self.active_app = None
            self.active_window_title = None
    
    def _update_active_window_windows(self):
        """Get active window info using Win32 API on Windows."""
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            # Get process ID of foreground window
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Find process name by PID
            try:
                process = psutil.Process(pid)
                self.active_app = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.active_app = "Unknown"
            
            # Get window title
            self.active_window_title = win32gui.GetWindowText(hwnd)
        else:
            self.active_app = None
            self.active_window_title = None
    
    def _update_active_window_fallback(self):
        """Fallback method for platforms without specific implementations."""
        # For Linux, we could use xdotool or other X11 utilities
        # For now, just use the first GUI process as a placeholder
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'DISPLAY' in os.environ:  # Check if X11 is running
                    # This is a very simplistic approach
                    self.active_app = proc.info['name']
                    self.active_window_title = f"Window of {self.active_app}"
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def _run_update_loop(self):
        """Background thread function for periodic updates."""
        self.logger.info("Process sensor started")
        self.running = True
        
        while self.running:
            try:
                self.update_process_list()
                self.update_active_window()
            except Exception as e:
                self.logger.error(f"Error in process monitoring loop: {e}")
            
            time.sleep(self.interval)
    
    def start(self):
        """Start monitoring processes in background."""
        if self.thread is not None and self.thread.is_alive():
            self.logger.warning("Process sensor already running")
            return
        
        self.thread = threading.Thread(target=self._run_update_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"Process sensor thread started with {self.interval}s interval")
    
    def stop(self):
        """Stop the background thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.logger.info("Process sensor stopped")
    
    def get_recent_windows(self, count=5):
        """
        Get recently active windows.
        
        Args:
            count (int): Number of window history items to return
            
        Returns:
            list: Recent window activity as formatted strings
        """
        recent = list(self.window_history)[-count:]
        formatted = []
        
        for timestamp, app, title in recent:
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            formatted.append(f"{time_str}: {app} - {title}")
        
        return formatted
    
    def get_usage_duration(self) -> float:
        """Get the duration of the current app usage in seconds."""
        if self._current_app_start_time is not None:
            return time.time() - self._current_app_start_time
        return 0.0
            
    def _monitor_processes(self):
        """Monitor processes in a background thread."""
        while not self._stop_event.is_set():
            try:
                # Get current active window
                active_window = get_active_window()
                if active_window:
                    app_name = active_window.get('app_name', '')
                    window_title = active_window.get('title', '')
                    
                    # Update active app and window title
                    if app_name != self.active_app:
                        self.active_app = app_name
                        self._app_start_times[app_name] = time.time()
                        self.logger.info(f"App opened: {app_name}")
                        
                    if window_title != self.active_window_title:
                        self.active_window_title = window_title
                        self.logger.info(f"Focus changed: {app_name} - {window_title}")
                        
                    # Update running apps
                    self.running_apps.add(app_name)
                    
                # Clean up old app start times
                current_time = time.time()
                for app in list(self._app_start_times.keys()):
                    if app not in self.running_apps and current_time - self._app_start_times[app] > 3600:  # 1 hour
                        del self._app_start_times[app]
                        
            except Exception as e:
                self.logger.error(f"Error monitoring processes: {e}")
                
            time.sleep(self.interval)

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    sensor = ProcessSensor(interval_sec=2)
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