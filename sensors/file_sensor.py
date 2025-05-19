"""
File System Sensor Module
Monitors file system events (creation, modification, deletion, etc.)
"""
import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import deque
from datetime import datetime
import threading
from typing import List, Optional, Dict
import fnmatch

class FileEventHandler(FileSystemEventHandler):
    """Custom handler for file system events."""
    
    def __init__(self, file_sensor):
        """
        Initialize the handler.
        
        Args:
            file_sensor: The parent FileSensor instance
        """
        self.file_sensor = file_sensor
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            path = event.src_path
            self.logger.info(f"File created: {path}")
            self._add_event("created", path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            path = event.src_path
            self.logger.info(f"File modified: {path}")
            self._add_event("modified", path)
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            path = event.src_path
            self.logger.info(f"File deleted: {path}")
            self._add_event("deleted", path)
    
    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory:
            src_path = event.src_path
            dest_path = event.dest_path
            self.logger.info(f"File moved: {src_path} -> {dest_path}")
            self._add_event("moved", f"{src_path} -> {dest_path}")
    
    def _add_event(self, event_type, path):
        """Add event to recent events with timestamp."""
        timestamp = time.time()
        self.file_sensor.recent_events.append((timestamp, event_type, path))
        
        # Trim events if needed
        while len(self.file_sensor.recent_events) > self.file_sensor.max_events:
            self.file_sensor.recent_events.popleft()

class FileSensor:
    """
    Monitors file system changes in specified paths.
    Uses watchdog to track file creation, modification, and deletion.
    """
    
    def __init__(self, paths: List[str], interval_sec: int, patterns: List[str] = None, max_size_mb: int = None):
        """
        Initialize the file sensor.
        
        Args:
            paths (list): List of paths to monitor
            interval_sec (int): Seconds between checks
            patterns (list): List of patterns to match
            max_size_mb (int): Maximum size in MB
        """
        self.paths = paths
        self.interval_sec = interval_sec
        self.patterns = patterns or ["*"]
        self.max_size_mb = max_size_mb
        self.running = False
        self._stop_event = threading.Event()
        self._thread = None
        self.logger = logging.getLogger(__name__)
        self._last_update = time.time()
        self._recent_events = []
        self.observer = None
        self.event_handler = None
        self.max_events = 100
        self.recent_events = deque(maxlen=self.max_events)  # Thread-safe, fixed-size queue
    
    def has_updates(self):
        """Check if there are new updates since last check."""
        current_time = time.time()
        if current_time - self._last_update >= self.interval_sec:
            self._last_update = current_time
            return True
        return False

    def get_data(self):
        """Get the current sensor data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "type": "file_events",
            "data": {
                "paths": self.paths,
                "recent_events": self._recent_events
            }
        }

    def _check_file(self, file_path: str) -> Optional[Dict]:
        try:
            if not any(fnmatch.fnmatch(file_path, pattern) for pattern in self.patterns):
                return None

            stats = os.stat(file_path)
            if self.max_size_mb and stats.st_size > self.max_size_mb * 1024 * 1024:
                return {
                    "path": file_path,
                    "size_mb": stats.st_size / (1024 * 1024),
                    "timestamp": datetime.now().isoformat(),
                    "type": "file_size_exceeded"
                }
            return None
        except Exception as e:
            logging.error(f"Error checking file {file_path}: {str(e)}")
            return None

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            for path in self.paths:
                if not os.path.exists(path):
                    logging.warning(f"Path does not exist: {path}")
                    continue
                
                if os.path.isfile(path):
                    result = self._check_file(path)
                    if result:
                        self._handle_event(result)
                else:
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            result = self._check_file(file_path)
                            if result:
                                self._handle_event(result)
            
            time.sleep(self.interval_sec)

    def _handle_event(self, event: Dict):
        # Override this method to handle events
        logging.info(f"File event detected: {event}")

    def start(self):
        """Start monitoring file system events."""
        if not self.paths:
            self.logger.warning("No paths provided for monitoring, skipping file system watcher")
            return

        self.observer = Observer()
        self.event_handler = FileEventHandler(self)
        
        valid_paths = False
        for path in self.paths:
            if os.path.exists(path):
                self.observer.schedule(self.event_handler, path, recursive=True)
                self.logger.info(f"Watching directory: {path}")
                valid_paths = True
            else:
                self.logger.warning(f"Path does not exist, skipping: {path}")
        
        if valid_paths:
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._monitor_loop)
            self._thread.daemon = True
            self._thread.start()
            self.observer.start()
            self.logger.info("File system sensor started")
        else:
            self.logger.warning("No valid paths found for monitoring, file system watcher disabled")
    
    def stop(self):
        """Stop monitoring file system events."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None
        
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()
            
        self.logger.info("File system sensor stopped")
    
    def get_recent_events(self, count=10, format_str=True):
        """
        Get recent file events.
        
        Args:
            count (int): Number of events to return (most recent first)
            format_str (bool): If True, return formatted strings; if False, return raw tuples
            
        Returns:
            list: Recent file events (most recent first)
        """
        events = list(self.recent_events)[-count:]  # Get last 'count' events
        
        if format_str:
            formatted_events = []
            for timestamp, event_type, path in events:
                time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
                filename = os.path.basename(path.split(' -> ')[0])  # Extract filename
                formatted_events.append(f"{time_str}: {event_type} {filename}")
            return formatted_events
        
        return events

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test directory - use a temporary directory or specify your own
    test_dir = os.path.expanduser("~/Desktop")
    
    sensor = FileSensor(paths=[test_dir], interval_sec=5)
    sensor.start()
    
    print(f"Monitoring {test_dir} for file events. Create/modify/delete files to test.")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
            events = sensor.get_recent_events()
            if events:
                print("\nRecent events:")
                for e in events:
                    print(f"  {e}")
    except KeyboardInterrupt:
        print("\nStopping file sensor...")
    finally:
        sensor.stop()