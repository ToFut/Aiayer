"""
Minimal file monitoring
"""
import time
import logging
import os

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/file_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class FileSensor:
    """Minimal file monitoring."""
    
    def __init__(self):
        self.running = False
        self.last_check = 0
        
    def start(self):
        """Start monitoring."""
        self.running = True
        self.last_check = time.time()
        logger.info("file sensor initialized")
        return True
        
    def stop(self):
        """Stop monitoring."""
        self.running = False
        return True
        
    def is_healthy(self):
        """Basic health check."""
        return self.running

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test directory - use a temporary directory or specify your own
    test_dir = os.path.expanduser("~/Desktop")
    
    sensor = FileSensor()
    sensor.start()
    
    print(f"Monitoring {test_dir} for file events. Create/modify/delete files to test.")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
            events = sensor.get_updates()
            if events:
                print("\nRecent events:")
                for e in events:
                    print(f"  {e}")
    except KeyboardInterrupt:
        print("\nStopping file sensor...")
    finally:
        sensor.stop() 