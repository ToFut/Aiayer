import os
import json
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('file_sensor')

# Import the FileSensor class
sys.path.append('.')
from sensors.file_sensor import FileSensor

if __name__ == "__main__":
    # Create cache directory if it doesn't exist
    os.makedirs('cache/file_sensor', exist_ok=True)
    
    # Paths to monitor
    paths = ["/Users/segevbin/Desktop", "/Users/segevbin/Desktop/SensAI/Aiayer"]
    
    # Create file sensor instance
    sensor = FileSensor(paths=paths, interval_sec=5)
    
    # Define a function to periodically save events to cache
    def save_to_cache():
        while True:
            try:
                events = sensor.get_recent_events(count=20, format_str=False)
                
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
                    
                logger.debug(f"Saved {len(serializable_events)} events to cache")
            except Exception as e:
                logger.error(f"Error saving to cache: {e}")
                
            # Sleep before next save
            time.sleep(10)
    
    # Start the sensor
    sensor.start()
    
    # Start cache saving thread
    cache_thread = threading.Thread(target=save_to_cache, daemon=True)
    cache_thread.start()
    
    logger.info(f"Monitoring paths: {paths}")
    logger.info("File sensor started")
    
    try:
        # Keep the script running
        while True:
            time.sleep(5)
            
            # Print heartbeat every 30 seconds
            if int(time.time()) % 30 == 0:
                logger.info("HEARTBEAT: File sensor is alive")
                
    except KeyboardInterrupt:
        logger.info("Stopping file sensor...")
    finally:
        sensor.stop()
        logger.info("File sensor stopped")
