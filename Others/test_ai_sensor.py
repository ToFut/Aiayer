"""
Test script for AI Sensor
Demonstrates the capabilities of the AI sensor and monitors its performance.
"""
import time
import logging
import random
from sensors.ai_sensor import AISensor, AISensorEvent
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_event() -> AISensorEvent:
    """Create a test event with random resource data."""
    return AISensorEvent(
        timestamp=time.time(),
        event_type=random.choice(['cpu_usage', 'memory_usage', 'disk_usage', 'network_usage']),
        source='test',
        data={
            'resource': random.choice(['cpu', 'memory', 'disk', 'network']),
            'value': random.uniform(0, 100),
            'change': random.uniform(-10, 10)
        },
        confidence=random.uniform(0.7, 1.0),
        insights=[],
        recommendations=[],
        metadata={'test': True}
    )

def main():
    """Main function to test the AI sensor."""
    # Initialize sensor with test configuration
    config = {
        'event_queue_size': 100,
        'insight_queue_size': 50,
        'alert_queue_size': 20,
        'history_size': 50,
        'performance_metrics_size': 50,
        'monitor_interval_sec': 120,
        'analysis_interval_sec': 600,
        'prediction_interval_sec': 1200,
        'max_memory_mb': 100,
        'max_cpu_percent': 30,
        'max_disk_usage': 80,
        'max_network_usage': 1000
    }
    
    sensor = AISensor(config)
    logger.info("AI Sensor initialized with configuration")
    
    try:
        # Run for 5 minutes
        end_time = time.time() + 300
        event_count = 0
        
        while time.time() < end_time:
            # Generate and process test events
            event = create_test_event()
            sensor._process_event_async(event)
            event_count += 1
            
            # Log stats every 30 seconds
            if event_count % 30 == 0:
                stats = sensor.get_stats()
                logger.info(f"Processed {event_count} events")
                logger.info(f"Current stats: {stats}")
                
                # Check sensor health
                if not sensor.is_healthy():
                    logger.warning("Sensor health check failed")
                
            time.sleep(1)  # Simulate real-time events
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        logger.info("Test completed")
        logger.info(f"Total events processed: {event_count}")

if __name__ == "__main__":
    main() 