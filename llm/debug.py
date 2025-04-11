"""
LLM Debugging and Monitoring Module
Provides tools for monitoring LLM performance and debugging issues.
"""
import time
import logging
import threading
import gc
import psutil
from collections import deque
from typing import Dict, Any, Optional

class LLMDebugger:
    """Monitors and debugs LLM performance and responses."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.debug_mode = False
        self.response_times = deque(maxlen=100)
        self.error_count = 0
        self.last_error_time = None
        self.error_types = {}
        self.response_cache = {}
        self.cache_timeout = 3600  # 1 hour
        self.last_cache_cleanup = time.time()
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'max_response_time': 0,
            'min_response_time': float('inf'),
            'last_request_time': None,
            'consecutive_errors': 0,
            'error_types': {},
            'response_lengths': [],
            'token_counts': [],
            'resource_usage': {
                'memory_usage': 0,
                'cpu_usage': 0,
                'thread_count': 0
            }
        }
        self.stats_lock = threading.Lock()
        self.debug_interval = 300  # 5 minutes
        self.last_debug_update = time.time()
        self.resource_check_interval = 60  # 1 minute
        self.last_resource_check = time.time()
        self.max_memory_usage = 200 * 1024 * 1024  # 200MB
        self.max_thread_count = 100
        self.cleanup_threshold = 0.8  # 80% of max resources
        self.resource_lock = threading.Lock()
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = time.time()
        self.health_status = True
        self.health_reasons = []
        
    def log_request(self, start_time: float, end_time: float, success: bool,
                   error: Optional[Exception] = None, response_length: int = 0,
                   token_count: int = 0) -> None:
        """Log an LLM request and its outcome."""
        try:
            # Check resources before processing
            if not self._check_resources():
                self.logger.warning("Resource limits exceeded, skipping request logging")
                return
                
            with self.stats_lock:
                response_time = end_time - start_time
                self.response_times.append(response_time)
                self.performance_stats['total_requests'] += 1
                self.performance_stats['last_request_time'] = end_time
                
                if success:
                    self.performance_stats['successful_requests'] += 1
                    self.performance_stats['consecutive_errors'] = 0
                    self.performance_stats['response_lengths'].append(response_length)
                    self.performance_stats['token_counts'].append(token_count)
                    
                    # Update response time statistics
                    self.performance_stats['average_response_time'] = (
                        sum(self.response_times) / len(self.response_times)
                    )
                    self.performance_stats['max_response_time'] = max(
                        self.performance_stats['max_response_time'],
                        response_time
                    )
                    self.performance_stats['min_response_time'] = min(
                        self.performance_stats['min_response_time'],
                        response_time
                    )
                else:
                    self.performance_stats['failed_requests'] += 1
                    self.performance_stats['consecutive_errors'] += 1
                    self.error_count += 1
                    self.last_error_time = end_time
                    
                    if error:
                        error_type = type(error).__name__
                        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
                        self.performance_stats['error_types'][error_type] = (
                            self.performance_stats['error_types'].get(error_type, 0) + 1
                        )
                        
                # Clean up old cache entries
                current_time = time.time()
                if current_time - self.last_cache_cleanup > self.cache_timeout:
                    self._cleanup_cache(current_time)
                    self.last_cache_cleanup = current_time
                    
                # Update debug information periodically
                if current_time - self.last_debug_update > self.debug_interval:
                    self._update_debug_info()
                    self.last_debug_update = current_time
                    
                # Check health periodically
                if current_time - self.last_health_check > self.health_check_interval:
                    self._check_health()
                    self.last_health_check = current_time
                    
        except Exception as e:
            self.logger.error(f"Error logging request: {e}")
            self._update_error_stats(e)
            
    def _check_resources(self) -> bool:
        """Check if system resources are within limits."""
        current_time = time.time()
        if current_time - self.last_resource_check < self.resource_check_interval:
            return True
            
        try:
            with self.resource_lock:
                process = psutil.Process()
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                thread_count = process.num_threads()
                
                # Update resource usage stats
                self.performance_stats['resource_usage'].update({
                    'memory_usage': memory_info.rss,
                    'cpu_usage': cpu_percent,
                    'thread_count': thread_count
                })
                
                # Check if resources are within limits
                if memory_info.rss > self.max_memory_usage * self.cleanup_threshold:
                    self.logger.warning("Memory usage high, performing cleanup")
                    self._cleanup_resources()
                    
                if thread_count > self.max_thread_count * self.cleanup_threshold:
                    self.logger.warning("Thread count high, performing cleanup")
                    self._cleanup_resources()
                    
                self.last_resource_check = current_time
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking resources: {e}")
            self._update_error_stats(e)
            return False
            
    def _cleanup_resources(self) -> None:
        """Clean up resources to stay within limits."""
        try:
            with self.stats_lock:
                # Clear old cache entries
                current_time = time.time()
                old_entries = [key for key, (_, time) in self.response_cache.items() 
                              if current_time - time > self.cache_timeout]
                for key in old_entries:
                    del self.response_cache[key]
                    
                # Clear old statistics
                if len(self.performance_stats['response_lengths']) > 100:
                    self.performance_stats['response_lengths'] = self.performance_stats['response_lengths'][-100:]
                if len(self.performance_stats['token_counts']) > 100:
                    self.performance_stats['token_counts'] = self.performance_stats['token_counts'][-100:]
                    
                # Force garbage collection
                gc.collect()
                
        except Exception as e:
            self.logger.error(f"Error cleaning up resources: {e}")
            self._update_error_stats(e)
            
    def _cleanup_cache(self, current_time: float) -> None:
        """Clean up old cache entries."""
        old_entries = [key for key, (_, time) in self.response_cache.items() 
                      if current_time - time > self.cache_timeout]
        for key in old_entries:
            del self.response_cache[key]
            
    def _update_debug_info(self) -> None:
        """Update and log debug information."""
        if self.debug_mode:
            self.logger.info("LLM Debug Information:")
            self.logger.info(f"Total Requests: {self.performance_stats['total_requests']}")
            self.logger.info(f"Successful Requests: {self.performance_stats['successful_requests']}")
            self.logger.info(f"Failed Requests: {self.performance_stats['failed_requests']}")
            self.logger.info(f"Average Response Time: {self.performance_stats['average_response_time']:.2f}s")
            self.logger.info(f"Max Response Time: {self.performance_stats['max_response_time']:.2f}s")
            self.logger.info(f"Min Response Time: {self.performance_stats['min_response_time']:.2f}s")
            self.logger.info(f"Consecutive Errors: {self.performance_stats['consecutive_errors']}")
            self.logger.info(f"Error Types: {self.performance_stats['error_types']}")
            self.logger.info(f"Average Response Length: {sum(self.performance_stats['response_lengths']) / max(1, len(self.performance_stats['response_lengths'])):.0f}")
            self.logger.info(f"Average Token Count: {sum(self.performance_stats['token_counts']) / max(1, len(self.performance_stats['token_counts'])):.0f}")
            self.logger.info(f"Resource Usage: {self.performance_stats['resource_usage']}")
            
    def _check_health(self) -> None:
        """Check the health of the LLM system."""
        self.health_status = True
        self.health_reasons = []
        
        # Check error rate
        if self.performance_stats['total_requests'] > 0:
            error_rate = (
                self.performance_stats['failed_requests'] /
                self.performance_stats['total_requests']
            )
            if error_rate > 0.2:  # More than 20% error rate
                self.health_status = False
                self.health_reasons.append(f"High error rate: {error_rate:.2%}")
                
        # Check consecutive errors
        if self.performance_stats['consecutive_errors'] > 5:
            self.health_status = False
            self.health_reasons.append(f"Too many consecutive errors: {self.performance_stats['consecutive_errors']}")
            
        # Check resource usage
        if self.performance_stats['resource_usage']['memory_usage'] > self.max_memory_usage:
            self.health_status = False
            self.health_reasons.append("Memory usage exceeded")
            
        if self.performance_stats['resource_usage']['thread_count'] > self.max_thread_count:
            self.health_status = False
            self.health_reasons.append("Thread count exceeded")
            
        # Check response times
        if self.performance_stats['average_response_time'] > 10.0:  # More than 10 seconds
            self.health_status = False
            self.health_reasons.append(f"Slow average response time: {self.performance_stats['average_response_time']:.2f}s")
            
    def _update_error_stats(self, error: Exception) -> None:
        """Update error statistics."""
        self.error_count += 1
        self.last_error_time = time.time()
        error_type = type(error).__name__
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        self.performance_stats['error_types'][error_type] = (
            self.performance_stats['error_types'].get(error_type, 0) + 1
        )
            
    def enable_debug_mode(self) -> None:
        """Enable debug mode for detailed logging."""
        self.debug_mode = True
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("LLM Debug mode enabled")
        
    def disable_debug_mode(self) -> None:
        """Disable debug mode."""
        self.debug_mode = False
        self.logger.setLevel(logging.INFO)
        self.logger.info("LLM Debug mode disabled")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current LLM statistics."""
        return self.performance_stats
        
    def is_healthy(self) -> bool:
        """Check if the LLM is healthy based on recent performance."""
        return self.health_status
        
    def get_health_reasons(self) -> list:
        """Get reasons for unhealthy status."""
        return self.health_reasons 