#!/usr/bin/env python3
"""
Minimal File Sensor
Monitors file system changes without using watchdog
"""
import os
import time
import json
import logging
import sys
from datetime import datetime
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('file_sensor')

class SimpleFileSensor:
    """A simple file sensor that polls directories for changes"""
    
    def __init__(self, paths, interval_sec=5):
        """Initialize with directories to monitor"""
        self.paths = paths
        self.interval_sec = interval_sec
        self.file_states = {}  # Last known file state
        self.running = False
        self.recent_events = []
        self.max_events = 100
        
    def start(self):
        """Start monitoring"""
        self.running = True
        self.scan_thread = threading.Thread(target=self._monitor_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        logger.info(f"Started monitoring paths: {self.paths}")
        
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if hasattr(self, 'scan_thread'):
            self.scan_thread.join(timeout=2)
        logger.info("File sensor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
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
    
    def _scan_path(self, base_path, record_events=True):
        """Scan a directory for changes"""
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
            logger.error(f"Error scanning path {base_path}: {e}")
    
    def _add_event(self, event_type, path):
        """Add a file event to recent events"""
        timestamp = time.time()
        event = (timestamp, event_type, path)
        self.recent_events.append(event)
        
        # Keep only the most recent events
        if len(self.recent_events) > self.max_events:
            self.recent_events = self.recent_events[-self.max_events:]
        
        logger.info(f"File {event_type}: {path}")
    
    def get_recent_events(self, count=10, format_str=False):
        """Get recent file events"""
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
    """Main function"""
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
    sensor = SimpleFileSensor(paths=paths, interval_sec=5)
    sensor.start()
    
    logger.info("File sensor started")
    logger.info(f"Monitoring paths: {paths}")
    
    # Cache writing function
    def save_to_cache():
        while sensor.running:
            try:
                events = sensor.get_recent_events(count=20)
                
                # Convert events to serializable format
                serializable_events = []
                for timestamp, event_type, path in events:
                    serializable_events.append({
                        "timestamp": timestamp,
                        "type": event_type,
                        "path": path
                    })
                
                # Save to cache
                cache_data = {
                    "timestamp": time.time(),
                    "events": serializable_events
                }
                
                with open('cache/file_sensor/last_file.json', 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
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