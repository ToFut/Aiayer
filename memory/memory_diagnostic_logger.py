"""
Memory Diagnostic Logger
Helps with memory diagnostics and logging.
"""
import logging
import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemoryDiagnosticLogger:
    """Diagnostic logger for memory system."""
    
    def __init__(self, log_file='logs/memory/diagnostic.log'):
        self.log_file = log_file
        self.start_time = time.time()
        self.events = []
        self.errors = []
        self.metrics = []
        
        # Make sure logs directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger("memory_diagnostics")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Add formatter to handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log initialization
        self.logger.info("Memory diagnostic logger initialized")
        self.log_memory_event("logger_initialized", {
            "timestamp": datetime.now().isoformat()
        })
    
    def log_memory_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a memory event."""
        try:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "elapsed": time.time() - self.start_time
            }
            self.events.append(event)
            self.logger.info(f"MEMORY EVENT: {event_type} - {json.dumps(data)}")
        except Exception as e:
            self.logger.error(f"Error logging memory event: {e}")
    
    def log_memory_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log a memory error."""
        try:
            error_data = {
                "type": type(error).__name__,
                "message": str(error),
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "elapsed": time.time() - self.start_time
            }
            self.errors.append(error_data)
            self.logger.error(f"MEMORY ERROR: {type(error).__name__} - {str(error)} - {json.dumps(context)}")
        except Exception as e:
            self.logger.error(f"Error logging memory error: {e}")
    
    def log_memory_metrics(self, memory_system) -> None:
        """Log memory metrics."""
        try:
            import psutil
            import sys
            import gc
            
            # Force garbage collection
            gc.collect()
            
            # Get process metrics
            process = psutil.Process()
            memory_info = process.memory_info()
            
            metrics = {
                "process_memory_mb": memory_info.rss / (1024 * 1024),
                "total_system_memory_mb": psutil.virtual_memory().total / (1024 * 1024),
                "available_system_memory_mb": psutil.virtual_memory().available / (1024 * 1024),
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(),
                "process_cpu_percent": process.cpu_percent(),
                "system_objects": len(gc.get_objects()),
                "python_version": sys.version,
                "timestamp": datetime.now().isoformat(),
                "elapsed": time.time() - self.start_time
            }
            
            # Add memory system data size estimates
            if memory_system:
                metrics.update({
                    "short_term_memory_size": self._estimate_size(memory_system.short_term_memory) if hasattr(memory_system, 'short_term_memory') else 0,
                    "long_term_memory_size": self._estimate_size(memory_system.long_term_memory) if hasattr(memory_system, 'long_term_memory') else 0,
                    "context_memory_size": self._estimate_size(memory_system.context_memory) if hasattr(memory_system, 'context_memory') else 0,
                    "total_memory_entries": (
                        len(memory_system.short_term_memory) if hasattr(memory_system, 'short_term_memory') else 0
                    ) + (
                        len(memory_system.long_term_memory) if hasattr(memory_system, 'long_term_memory') else 0
                    )
                })
            
            self.metrics.append(metrics)
            self.logger.info(f"MEMORY METRICS: {json.dumps(metrics)}")
        except Exception as e:
            self.logger.error(f"Error logging memory metrics: {e}")
    
    def _estimate_size(self, obj) -> int:
        """Estimate memory size of an object in bytes."""
        try:
            import sys
            
            if isinstance(obj, (str, bytes, bytearray)):
                return len(obj)
            elif isinstance(obj, (int, float, bool, type(None))):
                return sys.getsizeof(obj)
            elif isinstance(obj, (list, tuple)):
                return sys.getsizeof(obj) + sum(self._estimate_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sys.getsizeof(obj) + sum(
                    self._estimate_size(k) + self._estimate_size(v) for k, v in obj.items()
                )
            else:
                return sys.getsizeof(obj)
        except Exception:
            return 0
    
    def save_diagnostics(self, file_path: Optional[str] = None) -> None:
        """Save diagnostics to a file."""
        try:
            if file_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"logs/memory/diagnostics_{timestamp}.json"
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            diagnostics = {
                "events": self.events,
                "errors": self.errors,
                "metrics": self.metrics,
                "start_time": self.start_time,
                "end_time": time.time(),
                "duration": time.time() - self.start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(diagnostics, f, indent=2)
            
            self.logger.info(f"Diagnostics saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving diagnostics: {e}")
    
    def reset(self) -> None:
        """Reset diagnostics."""
        try:
            self.events = []
            self.errors = []
            self.metrics = []
            self.start_time = time.time()
            self.logger.info("Diagnostics reset")
        except Exception as e:
            self.logger.error(f"Error resetting diagnostics: {e}")