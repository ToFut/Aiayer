"""
Minimal Memory Logger Module

Drastically reduced logging for memory operations with built-in throttling and deduplication.
Only logs meaningful changes and errors.
"""
import logging
import json
import os
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

class MinimalMemoryLogger:
    """
    Logger for memory system with minimal logging and built-in throttling.
    Reduces log volume by ~99% compared to original implementation.
    """
    
    def __init__(self, log_dir: str = "logs/memory", log_level: int = logging.ERROR):
        """
        Initialize the minimal memory logger.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (default: ERROR to reduce logs dramatically)
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a single unified logger
        self.logger = self._setup_logger("memory", log_level)
        
        # Use separate loggers only for ERROR level messages
        self.conscious_logger = self._setup_logger("conscious", logging.ERROR)
        self.short_term_logger = self._setup_logger("short_term", logging.ERROR)
        self.long_term_logger = self._setup_logger("long_term", logging.ERROR)
        self.context_logger = self._setup_logger("context", logging.ERROR)
        
        # Track last logged data to avoid duplicate logging
        self._last_logged_hash = {}
        self._last_logged_time = {}
        self._throttle_interval = 300  # Only log similar events every 5 minutes
        self._empty_throttle_interval = 1800  # Only log empty states every 30 minutes
    
    def _setup_logger(self, memory_type: str, log_level: int) -> logging.Logger:
        """Set up a minimalist logger for a memory type."""
        logger = logging.getLogger(f"memory.{memory_type}")
        logger.setLevel(log_level)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
            
        # Create file handler with larger max size
        log_file = os.path.join(self.log_dir, f"{memory_type}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Set up minimal formatter - only essentials
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler only for errors
        if log_level <= logging.ERROR:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _hash_data(self, data: Any) -> str:
        """Create a hash of data for comparison."""
        if data is None:
            return "none"
        try:
            if isinstance(data, (dict, list)) and not data:
                return "empty"
            serialized = json.dumps(data, sort_keys=True)
            return hashlib.md5(serialized.encode('utf-8')).hexdigest()
        except:
            return str(data)
    
    def _should_log(self, memory_type: str, data: Any, is_error: bool = False) -> bool:
        """
        Determine if this entry should be logged based on content and time.
        Uses aggressive throttling to reduce log volume.
        """
        if is_error:
            return True  # Always log errors
            
        current_time = time.time()
        data_hash = self._hash_data(data)
        
        # Get last logged time for this memory type and data hash
        last_time = self._last_logged_time.get((memory_type, data_hash), 0)
        
        # Use longer throttle interval for empty data
        throttle_interval = self._empty_throttle_interval if data_hash in ("empty", "none") else self._throttle_interval
        
        # Only log if enough time has passed since the same data was logged
        if current_time - last_time > throttle_interval:
            self._last_logged_time[(memory_type, data_hash)] = current_time
            return True
            
        return False
    
    def log_conscious_memory(self, data: Dict[str, Any], operation: str = "conscious_memory_update") -> None:
        """Log only significant conscious memory updates."""
        try:
            if self._should_log("conscious", data):
                # Truncate data for logging
                log_data = "empty" if not data else f"{len(data)} items"
                self.logger.debug(f"{operation}: {log_data}")
        except Exception as e:
            self.logger.error(f"Error logging conscious memory: {e}")
    
    def log_short_term_memory(self, data: Dict[str, Any], operation: str = "short_term_memory_update") -> None:
        """Log only significant short-term memory updates."""
        try:
            if self._should_log("short_term", data):
                # Truncate data for logging
                log_data = "empty" if not data else f"{len(data)} items"
                self.logger.debug(f"{operation}: {log_data}")
        except Exception as e:
            self.logger.error(f"Error logging short-term memory: {e}")
    
    def log_long_term_memory(self, data: Dict[str, Any], operation: str = "long_term_memory_update") -> None:
        """Log only significant long-term memory updates."""
        try:
            if self._should_log("long_term", data):
                # Truncate data for logging
                log_data = "empty" if not data else f"{len(data)} items"
                # Use WARNING level to ensure it's captured
                self.logger.debug(f"{operation}: {log_data}")
        except Exception as e:
            self.logger.error(f"Error logging long-term memory: {e}")
    
    def log_context_memory(self, data: Dict[str, Any], operation: str = "context_memory_update") -> None:
        """Log only significant contextual memory updates."""
        try:
            if self._should_log("context", data):
                # Truncate data for logging
                log_data = "empty" if not data else f"{len(data)} items"
                self.logger.debug(f"{operation}: {log_data}")
        except Exception as e:
            self.logger.error(f"Error logging context memory: {e}")
    
    def log_memory_state(self, state: Dict[str, Any], operation: str = "memory_state_snapshot") -> None:
        """Log only meaningful memory state changes."""
        try:
            # For complete state snapshot, just log a summary
            components = []
            for memory_type in ("conscious", "short_term", "long_term", "context"):
                if memory_type in state:
                    size = len(state[memory_type]) if state[memory_type] else 0
                    components.append(f"{memory_type}:{size}")
            
            # Only log if throttling allows
            state_summary = ", ".join(components)
            if self._should_log("memory", state_summary):
                self.logger.debug(f"{operation}: {state_summary}")
        except Exception as e:
            self.logger.error(f"Error logging memory state: {e}")
    
    def get_recent_logs(self, memory_type: str, limit: int = 100) -> List[Dict[str, Any]]:
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
            
    def log_error(self, memory_type: str, message: str) -> None:
        """Log error for a specific memory type."""
        logger = getattr(self, f"{memory_type}_logger", self.logger)
        logger.error(message)