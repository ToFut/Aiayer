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
    Monitors file system events in specified directories.
    Uses watchdog to track file creation, modification, deletion, and moves.
    """
    
    def __init__(self, paths, max_events=100):
        """
        Initialize the file system sensor.
        
        Args:
            paths (list): List of directory paths to monitor
            max_events (int): Maximum number of recent events to retain
        """
        self.paths = [os.path.expanduser(p) for p in paths]  # Expand ~ to home dir
        self.max_events = max_events
        self.observer = Observer()
        self.event_handler = FileEventHandler(self)
        self.recent_events = deque(maxlen=max_events)  # Thread-safe, fixed-size queue
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start monitoring file system events."""
        for path in self.paths:
            if os.path.exists(path):
                self.observer.schedule(self.event_handler, path, recursive=True)
                self.logger.info(f"Watching directory: {path}")
            else:
                self.logger.warning(f"Path does not exist, skipping: {path}")
        
        self.observer.start()
        self.logger.info("File system sensor started")
    
    def stop(self):
        """Stop monitoring file system events."""
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
    
    sensor = FileSensor(paths=[test_dir])
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