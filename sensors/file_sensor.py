#!/usr/bin/env python3
"""
File Sensor Module
Monitors file system changes in specified directories.
"""
import os
import time
import json
import logging
import sys
from datetime import datetime
import threading
from typing import Dict, Any, List, Optional

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)

# Create a custom filter to prevent duplicate logs
class DuplicateFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_log = None
        self.last_time = None
        self.min_interval = 5  # Minimum seconds between similar logs

    def filter(self, record):
        current_log = (record.levelno, record.getMessage())
        current_time = time.time()
        
        # Allow if it's a different message
        if current_log != self.last_log:
            self.last_log = current_log
            self.last_time = current_time
            return True
            
        # Allow if enough time has passed since last similar log
        if current_time - self.last_time >= self.min_interval:
            self.last_time = current_time
            return True
            
        return False

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/sensors/file_sensor.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('file_sensor')
logger.addFilter(DuplicateFilter())

# Reduce logging level for all modules
logging.getLogger('watchdog').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

class FileSensor:
    """Monitors file system changes in specified directories."""
    
    def __init__(self, paths: List[str], interval_sec: int = 5):
        """Initialize file sensor with paths to monitor."""
        self.paths = paths
        self.interval_sec = interval_sec
        self.file_states = {}  # Last known file state
        self.running = False
        self.recent_events = []
        self.max_events = 100
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"File sensor initialized with paths: {paths}")
        
    def start(self) -> bool:
        """Start monitoring files."""
        try:
            self.running = True
            self.scan_thread = threading.Thread(target=self._monitor_loop)
            self.scan_thread.daemon = True
            self.scan_thread.start()
            self.logger.info("File sensor started")
            return True
        except Exception as e:
            self.logger.error(f"Error starting file sensor: {e}")
            return False
    
    def stop(self) -> None:
        """Stop monitoring files."""
        self.running = False
        if hasattr(self, 'scan_thread'):
            self.scan_thread.join(timeout=2)
        self.logger.info("File sensor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        # Initial scan to establish baseline
        for path in self.paths:
            if os.path.exists(path):
                self._scan_path(path, record_events=False)
        
        # Monitoring loop
        while self.running:
            for path in self.paths:
                if os.path.exists(path):
                    self._scan_path(path)
            time.sleep(self.interval_sec)
    
    def _scan_path(self, base_path: str, record_events: bool = True) -> None:
        """Scan a directory for changes."""
        try:
            current_files = {}
            
            # If it's a file, just check that file
            if os.path.isfile(base_path):
                stat = os.stat(base_path)
                current_files[base_path] = {
                    'mtime': stat.st_mtime,
                    'size': stat.st_size
                }
            # Otherwise scan the directory
            elif os.path.isdir(base_path):
                for root, _, files in os.walk(base_path):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            stat = os.stat(file_path)
                            current_files[file_path] = {
                                'mtime': stat.st_mtime,
                                'size': stat.st_size
                            }
                        except (FileNotFoundError, PermissionError):
                            pass  # Skip files we can't access
            
            # Don't record events on first scan
            if not record_events:
                self.file_states = current_files
                return
                
            # Check for new or modified files
            for file_path, state in current_files.items():
                if file_path not in self.file_states:
                    # New file
                    self._add_event("created", file_path)
                elif state['mtime'] > self.file_states[file_path]['mtime']:
                    # Modified file
                    self._add_event("modified", file_path)
            
            # Check for deleted files
            for file_path in list(self.file_states.keys()):
                if file_path not in current_files:
                    self._add_event("deleted", file_path)
            
            # Update file states
            self.file_states = current_files
            
        except Exception as e:
            self.logger.error(f"Error scanning path {base_path}: {e}")
    
    def _add_event(self, event_type: str, path: str) -> None:
        """Add a file event to recent events."""
        timestamp = time.time()
        event = (timestamp, event_type, path)
        self.recent_events.append(event)
        
        # Keep only the most recent events
        if len(self.recent_events) > self.max_events:
            self.recent_events = self.recent_events[-self.max_events:]
        
        self.logger.info(f"File {event_type}: {path}")
    
    def get_recent_events(self, count: int = 10, format_str: bool = False) -> List[Any]:
        """Get recent file events."""
        events = self.recent_events[-count:] if count < len(self.recent_events) else self.recent_events
        
        if format_str:
            formatted_events = []
            for timestamp, event_type, path in events:
                time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
                filename = os.path.basename(path)
                formatted_events.append(f"{time_str}: {event_type} {filename}")
            return formatted_events
        
        return events

def main():
    """Main function."""
    # Get paths to monitor
    home_dir = os.path.expanduser('~')
    current_dir = os.getcwd()
    paths = [
        os.path.join(home_dir, 'Desktop'),
        current_dir
    ]
    
    # Create cache directory
    os.makedirs('cache/file_sensor', exist_ok=True)
    
    # Create and start sensor
    sensor = FileSensor(paths=paths, interval_sec=5)
    if not sensor.start():
        logger.error("Failed to start file sensor")
        return
    
    logger.info("File sensor started")
    logger.info(f"Monitoring paths: {paths}")
    
    # Cache writing function with memory optimization
    def save_to_cache():
        while sensor.running:
            try:
                # Get only the most recent, limited number of events
                events = sensor.get_recent_events(count=10)  # Reduced from 20 to 10
                
                # Convert events to serializable format with minimal data
                serializable_events = []
                for timestamp, event_type, path in events:
                    # Store only filename, not full path to save memory
                    filename = os.path.basename(path)
                    serializable_events.append({
                        "timestamp": timestamp,
                        "type": event_type,
                        "filename": filename  # Store just filename instead of full path
                    })
                
                # Save to cache (minimal data)
                cache_data = {
                    "timestamp": time.time(),
                    "event_count": len(serializable_events),
                    "events": serializable_events
                }
                
                # Write to cache file (overwriting previous data)
                with open('cache/file_sensor/last_file.json', 'w') as f:
                    json.dump(cache_data, f)  # No indent to save space
                
                # Remove any backup files older than 1 hour
                try:
                    cache_dir = 'cache/file_sensor'
                    current_time = time.time()
                    for filename in os.listdir(cache_dir):
                        if filename.startswith('last_file.json.bak_'):
                            file_path = os.path.join(cache_dir, filename)
                            file_age = current_time - os.path.getmtime(file_path)
                            if file_age > 3600:  # 1 hour in seconds
                                os.remove(file_path)
                                logger.debug(f"Removed old backup file: {filename}")
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up old backups: {cleanup_error}")
                
            except Exception as e:
                logger.error(f"Error saving to cache: {e}")
            
            time.sleep(10)
    
    # Start cache writer thread
    cache_thread = threading.Thread(target=save_to_cache)
    cache_thread.daemon = True
    cache_thread.start()
    
    try:
        # Main thread heartbeat
        while True:
            time.sleep(30)
            logger.info("HEARTBEAT: File sensor is alive")
    except KeyboardInterrupt:
        logger.info("Stopping file sensor...")
    finally:
        sensor.stop()

if __name__ == "__main__":
    main()