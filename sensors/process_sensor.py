"""
Minimal process monitoring
"""
import time
import logging
import psutil

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class ProcessSensor:
    """Minimal process monitoring."""
    
    def __init__(self):
        self.running = False
        self.last_check = 0
        
    def start(self):
        """Start monitoring."""
        self.running = True
        self.last_check = time.time()
        logger.info("process sensor initialized")
        return True
        
    def stop(self):
        """Stop monitoring."""
        self.running = False
        return True
        
    def is_healthy(self):
        """Basic health check."""
        return self.running