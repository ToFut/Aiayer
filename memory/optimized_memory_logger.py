"""
Optimized Memory Logger Module

This module provides logging functionality for the memory system with reduced log volume.
It only logs meaningful memory operations and state changes.
"""
import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

class OptimizedMemoryLogger:
    """Logger for memory system operations with reduced logging volume."""
    
    def __init__(self, log_dir: str = "logs/memory", log_level: int = logging.WARNING):
        """
        Initialize the memory logger with optimized logging.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (default: WARNING to reduce logs)
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create separate loggers for each memory type, with reduced logging levels
        self.conscious_logger = self._setup_logger("conscious", log_level)
        self.short_term_logger = self._setup_logger("short_term", log_level)
        self.long_term_logger = self._setup_logger("long_term", log_level)
        self.context_logger = self._setup_logger("context", log_level)
        
        # Main logger for general memory operations
        self.logger = self._setup_logger("memory", log_level)
        self.logger.info("Optimized memory logger initialized")
        
        # Track last logged data to avoid redundant logging
        self._last_logged = {
            "conscious": None,
            "short_term": None, 
            "long_term": None,
            "context": None
        }
        self._log_throttle = {
            "conscious": 0,
            "short_term": 0, 
            "long_term": 0,
            "context": 0
        }
        self._throttle_interval = 300  # Only log empty state changes every 5 minutes
    
    def _setup_logger(self, memory_type: str, log_level: int) -> logging.Logger:
        """Set up a logger for a specific memory type with reduced log volume."""
        logger = logging.getLogger(f"memory.{memory_type}")
        logger.setLevel(log_level)
        
        # Create file handler with larger max size and more backups
        log_file = os.path.join(self.log_dir, f"{memory_type}.log")
        file_handler = logging.FileHandler(log_file)
        
        # Set up formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers if they don't exist already
        if not logger.handlers:
            logger.addHandler(file_handler)
            
            # Console handler only for errors and above
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.ERROR)  # Only ERROR and above go to console
            logger.addHandler(console_handler)
        
        return logger
    
    def _should_log(self, memory_type: str, data: Dict[str, Any]) -> bool:
        """
        Determine if this entry should be logged based on content and time.
        Reduces redundant empty logs, only logging them periodically.
        """
        current_time = time.time()
        
        # If it's an empty list/dict or None, throttle the logging
        is_empty = data == [] or data == {} or data is None or data == ""
        
        if is_empty:
            # Only log empty states periodically
            if current_time - self._log_throttle[memory_type] > self._throttle_interval:
                self._log_throttle[memory_type] = current_time
                return True
            return False
            
        # If data changed from last log, always log it
        if data != self._last_logged[memory_type]:
            self._last_logged[memory_type] = data
            return True
            
        # Otherwise, don't log repeat data
        return False
    
    def log_conscious_memory(self, data: Dict[str, Any], operation: str = "conscious_memory_update") -> None:
        """Log conscious memory updates with reduced volume."""
        try:
            if self._should_log("conscious", data):
                self.conscious_logger.info(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging conscious memory: {e}")
    
    def log_short_term_memory(self, data: Dict[str, Any], operation: str = "short_term_memory_update") -> None:
        """Log short-term memory updates with reduced volume."""
        try:
            if self._should_log("short_term", data):
                self.short_term_logger.info(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging short-term memory: {e}")
    
    def log_long_term_memory(self, data: Dict[str, Any], operation: str = "long_term_memory_update") -> None:
        """Log long-term memory updates with reduced volume."""
        try:
            if self._should_log("long_term", data):
                self.long_term_logger.info(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging long-term memory: {e}")
    
    def log_context_memory(self, data: Dict[str, Any], operation: str = "context_memory_update") -> None:
        """Log contextual memory updates with reduced volume."""
        try:
            if self._should_log("context", data):
                self.context_logger.info(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging context memory: {e}")
    
    def log_memory_state(self, state: Dict[str, Any], operation: str = "memory_state_snapshot") -> None:
        """Log the current state of the memory system with reduced volume."""
        try:
            # Only log non-empty state changes for each memory type
            if 'conscious' in state and self._should_log("conscious", state['conscious']):
                self.log_conscious_memory(state['conscious'], f"{operation}_conscious")
            if 'short_term' in state and self._should_log("short_term", state['short_term']):
                self.log_short_term_memory(state['short_term'], f"{operation}_short_term")
            if 'long_term' in state and self._should_log("long_term", state['long_term']):
                self.log_long_term_memory(state['long_term'], f"{operation}_long_term")
            if 'context' in state and self._should_log("context", state['context']):
                self.log_context_memory(state['context'], f"{operation}_context")
            
            # Log overall state changes only when significant
            has_changed = False
            for memory_type in ["conscious", "short_term", "long_term", "context"]:
                if memory_type in state and state[memory_type] != self._last_logged[memory_type]:
                    has_changed = True
                    break
                    
            if has_changed:
                self.logger.info(f"{operation}: {json.dumps(state, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging memory state: {e}")
    
    def get_recent_logs(self, memory_type: str, limit: int = 100, operation: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries for a specific memory type."""
        log_entries = []
        log_file = os.path.join(self.log_dir, f"{memory_type}.log")
        
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Process lines in reverse order (most recent first)
                for line in reversed(lines):
                    if operation and operation not in line:
                        continue
                    
                    parts = line.split(' - ')
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        level = parts[2]
                        message = ' - '.join(parts[3:])
                        
                        log_entries.append({
                            "timestamp": timestamp,
                            "level": level,
                            "message": message.strip()
                        })
                        
                        if len(log_entries) >= limit:
                            break
            
            return log_entries
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return []