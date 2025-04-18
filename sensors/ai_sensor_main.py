"""
AI Sensor Main Entry Point
Simple non-async implementation for system monitoring
"""
import time
import logging
from typing import Dict, Any
from ai_sensor import AISensor

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

def main():
    """Main function to run the AI sensor."""
    try:
        # Initialize sensor
        sensor = AISensor()
        
        # Start sensor
        if not sensor.start():
            logger.error("Failed to start AI sensor")
            return
            
        logger.info("AI sensor started successfully")
        
        # Main loop
        while True:
            try:
                # Get current stats
                stats = sensor.get_stats()
                
                # Check health
                if not sensor.is_healthy():
                    logger.warning("AI sensor health check failed")
                
                # Sleep for monitoring interval
                time.sleep(15)  # 15 second interval
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
                
    except KeyboardInterrupt:
        logger.info("Shutting down AI sensor...")
        sensor.stop()
    except Exception as e:
        logger.error(f"Fatal error in AI sensor: {str(e)}")
    finally:
        logger.info("AI sensor shutdown complete")

if __name__ == "__main__":
    main() 