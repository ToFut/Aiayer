"""
Simple software monitoring sensor with basic system stats tracking
"""
import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from queue import Queue

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


@dataclass
class AISensorEvent:
    """Data class for AI sensor events."""
    timestamp: float
    event_type: str
    source: str
    data: Dict[str, Any]
    confidence: float
    insights: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class AISensor:
    """AI sensor for system monitoring and analysis."""
    
    def __init__(self, config=None):
        """Initialize AI sensor with configuration.
        
        Args:
            config (dict): Configuration dictionary with sensor settings and resource limits
        """
        self.config = config or {}
        
        # Set monitoring intervals
        self.monitor_interval_sec = self.config.get('monitor_interval_sec', 60)
        self.analysis_interval_sec = self.config.get('analysis_interval_sec', 300)
        self.prediction_interval_sec = self.config.get('prediction_interval_sec', 600)
        
        # Set resource limits
        self.max_memory_mb = self.config.get('max_memory_mb', 2048)
        self.max_cpu_percent = self.config.get('max_cpu_percent', 80)
        self.max_disk_usage = self.config.get('max_disk_usage', 10240)  # MB
        self.max_network_usage = self.config.get('max_network_usage', 40)  # Mbps
        
        # Set queue sizes
        self.event_queue_size = self.config.get('event_queue_size', 1000)
        self.insight_queue_size = self.config.get('insight_queue_size', 100)
        self.alert_queue_size = self.config.get('alert_queue_size', 50)
        
        # Set analysis parameters
        self.anomaly_threshold = self.config.get('anomaly_threshold', 0.8)
        self.pattern_window = self.config.get('pattern_window', 24)  # hours
        self.prediction_window = self.config.get('prediction_window', 6)  # hours
        self.sequence_length = self.config.get('sequence_length', 128)
        self.batch_size = self.config.get('batch_size', 32)
        
        # Initialize queues
        self.event_queue = Queue(maxsize=self.event_queue_size)
        self.insight_queue = Queue(maxsize=self.insight_queue_size)
        self.alert_queue = Queue(maxsize=self.alert_queue_size)
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI sensor initialized with config: %s", self.config)
        
        self.running = False
        self.last_stats = None
        self.error_count = 0
        self.max_errors = 3
        self.events = []
        self.insights = []
        self.alerts = []
    
    def start(self) -> bool:
        """Start monitoring."""
        try:
            self.running = True
            self.last_stats = self.get_stats()
            self.logger.info("AI sensor initialized successfully")
            self.error_count = 0
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AI sensor: {str(e)}")
            self.running = False
            return False

    def stop(self) -> bool:
        """Stop monitoring."""
        try:
            self.running = False
            self.last_stats = None
            self.logger.info("AI sensor stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping AI sensor: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get basic system stats with error handling."""
        if not self.running:
            self.logger.warning("Attempted to get stats while sensor is not running")
            return {}
            
        try:
            stats = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'is_running': self.running,
                'error_count': self.error_count,
                'events_count': len(self.events),
                'insights_count': len(self.insights),
                'alerts_count': len(self.alerts)
            }
            self.last_stats = stats
            return stats
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error getting system stats: {str(e)}")
            if self.error_count >= self.max_errors:
                self.logger.critical("Too many errors, marking sensor as unhealthy")
            return self.last_stats or {}

    def is_healthy(self) -> bool:
        """Enhanced health check."""
        if not self.running:
            return False
        
        try:
            stats = self.get_stats()
            return (self.running and 
                   self.error_count < self.max_errors and
                   isinstance(stats, dict) and
                   len(stats) > 0)
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
            
    def process_event(self, event: AISensorEvent) -> bool:
        """Process an event synchronously."""
        try:
            # Add event to history
            self.events.append(event)
            
            # Trim events if needed
            while len(self.events) > self.event_queue_size:
                self.events.pop(0)
            
            # Generate insights if needed
            if event.confidence > 0.9:
                self.insights.append({
                    'timestamp': event.timestamp,
                    'source': event.source,
                    'insights': event.insights,
                    'recommendations': event.recommendations
                })
                
                # Trim insights if needed
                while len(self.insights) > self.insight_queue_size:
                    self.insights.pop(0)
            
            # Generate alerts if needed
            if self._should_generate_alert(event):
                self.alerts.append({
                    'timestamp': event.timestamp,
                    'source': event.source,
                    'event_type': event.event_type,
                    'data': event.data
                })
                
                # Trim alerts if needed
                while len(self.alerts) > self.alert_queue_size:
                    self.alerts.pop(0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}")
            return False
            
    async def _process_event_async(self, event: AISensorEvent) -> bool:
        """Process an event asynchronously."""
        return self.process_event(event)
            
    def _should_generate_alert(self, event: AISensorEvent) -> bool:
        """Check if an event should generate an alert."""
        try:
            if event.event_type == 'cpu_usage':
                return event.data.get('value', 0) > self.max_cpu_percent
            elif event.event_type == 'memory_usage':
                return event.data.get('value', 0) > self.max_memory_mb
            elif event.event_type == 'disk_usage':
                return event.data.get('value', 0) > self.max_disk_usage
            elif event.event_type == 'network_usage':
                return event.data.get('value', 0) > self.max_network_usage
            return False
        except Exception as e:
            self.logger.error(f"Error checking alert condition: {str(e)}")
            return False