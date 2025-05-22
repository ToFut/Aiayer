"""
Test script for the process sensor.
"""
import time
import logging
from sensors.process_sensor import ProcessSensor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the process sensor test."""
    logger.info("Starting process sensor test...")
    
    # Create and start the sensor
    sensor = ProcessSensor()
    if not sensor.start():
        logger.error("Failed to start process sensor")
        return
        
    logger.info("Process sensor started successfully")
    print("\nMonitoring active processes. Switch applications to test.")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Get updates
            updates = sensor.get_updates()
            if updates:
                print(f"\rActive process: {updates['name']} (PID: {updates['pid']})", end='', flush=True)
            else:
                print("\rNo active process found", end='', flush=True)
                
            # Check health
            if not sensor.is_healthy():
                logger.warning("Process sensor is not healthy")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping process sensor...")
    finally:
        sensor.stop()
        logger.info("Process sensor stopped")

if __name__ == "__main__":
    main() 