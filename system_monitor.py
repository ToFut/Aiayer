"""
System Monitor Module
Manages and monitors all system components (sensors, LLM, etc.)
"""
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from sensors.file_sensor import FileSensor
from sensors.process_sensor import ProcessSensor
from sensors.ai_sensor import AISensor
from llm.model import LocalLLM
from llm.debug import LLMDebugger

class SystemMonitor:
    """Monitors and manages all system components."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the system monitor.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.running = False
        self.monitor_thread = None
        self.monitor_interval = 60  # 1 minute
        
        # Initialize sensors
        self.file_sensor = FileSensor(
            monitor_paths=config['sensors']['file']['monitor_paths'],
            exclude_patterns=config['sensors']['file']['exclude_patterns'],
            max_file_size_mb=config['sensors']['file']['max_file_size_mb'],
            max_files_monitored=config['sensors']['file']['max_files_monitored'],
            max_memory_mb=config['sensors']['file']['max_memory_mb'],
            cleanup_threshold_mb=config['sensors']['file']['cleanup_threshold_mb'],
            monitor_interval_sec=config['sensors']['file']['monitor_interval_sec'],
            max_errors=config['sensors']['file']['max_errors'],
            max_file_descriptors=config['sensors']['file']['max_file_descriptors']
        )
        
        self.process_sensor = ProcessSensor(
            interval_sec=config['sensors']['process']['interval_sec'],
            max_processes=config['sensors']['process']['max_processes'],
            exclude_patterns=config['sensors']['process']['exclude_patterns'],
            cache_timeout_sec=config['sensors']['process']['cache_timeout_sec'],
            max_memory_mb=config['sensors']['process']['max_memory_mb'],
            cleanup_threshold_mb=config['sensors']['process']['cleanup_threshold_mb'],
            max_errors=config['sensors']['process']['max_errors'],
            history_size=config['sensors']['process']['history_size']
        )
        
        self.ai_sensor = AISensor(
            monitor_interval_sec=config['sensors']['ai']['monitor_interval_sec'],
            analysis_interval_sec=config['sensors']['ai']['analysis_interval_sec'],
            prediction_interval_sec=config['sensors']['ai']['prediction_interval_sec'],
            max_memory_mb=config['sensors']['ai']['max_memory_mb'],
            max_cpu_percent=config['sensors']['ai']['max_cpu_percent'],
            max_disk_usage=config['sensors']['ai']['max_disk_usage'],
            max_network_usage=config['sensors']['ai']['max_network_usage'],
            event_queue_size=config['sensors']['ai']['event_queue_size'],
            insight_queue_size=config['sensors']['ai']['insight_queue_size'],
            alert_queue_size=config['sensors']['ai']['alert_queue_size'],
            anomaly_threshold=config['sensors']['ai']['anomaly_threshold'],
            pattern_window=config['sensors']['ai']['pattern_window'],
            prediction_window=config['sensors']['ai']['prediction_window'],
            sequence_length=config['sensors']['ai']['sequence_length'],
            batch_size=config['sensors']['ai']['batch_size']
        )
        
        # Initialize LLM
        self.llm = LocalLLM(
            model_name=config['llm']['model_name'],
            host=config['llm']['host'],
            port=config['llm']['port']
        )
        
        # Enable debug mode if configured
        if config.get('system', {}).get('debug', False):
            self.enable_debug_mode()
            
        # Initialize health status
        self.health_status = True
        self.health_reasons = []
        self.last_health_check = time.time()
        self.health_check_interval = 300  # 5 minutes
        
        self.logger.info("System monitor initialized")
        
    def start(self) -> bool:
        """Start all system components."""
        try:
            self.logger.info("Starting system monitor...")
            
            # Start sensors
            if self.config['sensors']['file']['enabled']:
                self.file_sensor.start()
                self.logger.info("File sensor started")
            
            if self.config['sensors']['process']['enabled']:
                self.process_sensor.start()
                self.logger.info("Process sensor started")
            
            if self.config['sensors']['ai']['enabled']:
                self.ai_sensor.start()
                self.logger.info("AI sensor started")
            
            # Start monitoring thread
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            self.logger.info("System monitor started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system monitor: {str(e)}")
            return False
            
    def stop(self) -> bool:
        """Stop all system components."""
        try:
            self.logger.info("Stopping system monitor...")
            
            # Stop monitoring thread
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
                
            # Stop sensors
            if self.config['sensors']['file']['enabled']:
                self.file_sensor.stop()
            
            if self.config['sensors']['process']['enabled']:
                self.process_sensor.stop()
            
            if self.config['sensors']['ai']['enabled']:
                self.ai_sensor.stop()
            
            self.logger.info("System monitor stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping system monitor: {str(e)}")
            return False
            
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Check component health
                self._check_health()
                
                # Get component statistics
                file_stats = self.file_sensor.get_stats()
                process_stats = self.process_sensor.get_stats()
                ai_stats = self.ai_sensor.get_stats()
                llm_stats = self.llm.get_stats()
                
                # Log statistics if in debug mode
                if self.config.get('system', {}).get('debug', False):
                    self._log_statistics(file_stats, process_stats, ai_stats, llm_stats)
                    
                # Sleep until next check
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)  # Wait before retrying
                
    def _check_health(self) -> None:
        """Check health of all components."""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return
            
        self.health_status = True
        self.health_reasons = []
        
        # Check file sensor
        if not self.file_sensor.is_healthy():
            self.health_status = False
            self.health_reasons.append("File sensor is unhealthy")
            
        # Check process sensor
        if not self.process_sensor.is_healthy():
            self.health_status = False
            self.health_reasons.append("Process sensor is unhealthy")
            
        # Check AI sensor
        if not self.ai_sensor.is_healthy():
            self.health_status = False
            self.health_reasons.append("AI sensor is unhealthy")
            
        # Check LLM
        if not self.llm.is_connected():
            self.health_status = False
            self.health_reasons.append("LLM is disconnected")
            
        self.last_health_check = current_time
        
    def _log_statistics(self, file_stats: Dict[str, Any], 
                       process_stats: Dict[str, Any],
                       ai_stats: Dict[str, Any],
                       llm_stats: Dict[str, Any]) -> None:
        """Log component statistics."""
        self.logger.info("System Statistics:")
        self.logger.info("File Sensor:")
        self.logger.info(f"  Total Events: {file_stats['total_events']}")
        self.logger.info(f"  Processed Events: {file_stats['processed_events']}")
        self.logger.info(f"  Resource Usage: {file_stats['resource_usage']}")
        
        self.logger.info("Process Sensor:")
        self.logger.info(f"  Active Apps: {process_stats['process_stats']}")
        self.logger.info(f"  Performance: {process_stats['performance_stats']}")
        
        self.logger.info("AI Sensor:")
        self.logger.info(f"  Total Events: {ai_stats['total_events']}")
        self.logger.info(f"  Resource Usage: {ai_stats['resource_usage']}")
        
        self.logger.info("LLM:")
        self.logger.info(f"  Total Requests: {llm_stats['total_requests']}")
        self.logger.info(f"  Success Rate: {llm_stats['successful_requests'] / max(1, llm_stats['total_requests']):.2%}")
        self.logger.info(f"  Average Response Time: {llm_stats['average_response_time']:.2f}s")
        self.logger.info(f"  Resource Usage: {llm_stats['resource_usage']}")
        
    def enable_debug_mode(self) -> None:
        """Enable debug mode for all components."""
        self.file_sensor.enable_debug_mode()
        self.process_sensor.enable_debug_mode()
        self.ai_sensor.enable_debug_mode()
        self.llm.enable_debug_mode()
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("Debug mode enabled for all components")
        
    def disable_debug_mode(self) -> None:
        """Disable debug mode for all components."""
        self.file_sensor.disable_debug_mode()
        self.process_sensor.disable_debug_mode()
        self.ai_sensor.disable_debug_mode()
        self.llm.disable_debug_mode()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Debug mode disabled for all components")
        
    def is_healthy(self) -> bool:
        """Check if the system is healthy."""
        return self.health_status
        
    def get_health_reasons(self) -> list:
        """Get reasons for unhealthy status."""
        return self.health_reasons
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        return {
            'file_sensor': self.file_sensor.get_stats(),
            'process_sensor': self.process_sensor.get_stats(),
            'ai_sensor': self.ai_sensor.get_stats(),
            'llm': self.llm.get_stats(),
            'health': {
                'status': self.health_status,
                'reasons': self.health_reasons
            }
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current status of all components"""
        status = {
            'file_sensor': {
                'enabled': self.config['sensors']['file']['enabled'],
                'status': 'running' if self.config['sensors']['file']['enabled'] else 'disabled'
            },
            'process_sensor': {
                'enabled': self.config['sensors']['process']['enabled'],
                'status': 'running' if self.config['sensors']['process']['enabled'] else 'disabled'
            },
            'ai_sensor': {
                'enabled': self.config['sensors']['ai']['enabled'],
                'status': 'running' if self.config['sensors']['ai']['enabled'] else 'disabled'
            },
            'llm': {
                'status': 'connected' if self.llm.is_connected() else 'disconnected'
            }
        }
        return status 