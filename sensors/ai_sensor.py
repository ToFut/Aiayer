"""
Simple software monitoring sensor
"""
import logging
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AISensor:
    """Minimal software monitoring sensor."""
    
    def __init__(self):
        self.running = False
        self.logger = logger
    
    def start(self):
        """Start monitoring."""
        try:
            self.running = True
            stats = self.get_stats()
            self.logger.info("ai sensor initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False

    def stop(self):
        """Stop monitoring."""
        self.running = False
        self.logger.info("Monitoring stopped")
        return True

    def get_stats(self):
        """Get basic system stats."""
        stats = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'is_running': self.running
        }
        self.logger.info(f"System stats: {stats}")
        return stats

    def is_healthy(self):
        """Basic health check."""
        return self.running 