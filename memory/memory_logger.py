"""
Memory Logger Module

This module provides logging functionality for the memory system.
It captures and formats memory operations for debugging and monitoring.
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from logging.handlers import RotatingFileHandler
import time

class MemoryLogger:
    """Logger for memory system operations and state changes."""
    
    def __init__(self, log_dir: str = "logs/memory", log_level: int = logging.WARNING):
        """
        Initialize the memory logger.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (default: WARNING to reduce logs)
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create separate loggers for each memory type with rotation
        self.conscious_logger = self._setup_logger("conscious", log_level)
        self.short_term_logger = self._setup_logger("short_term", log_level)
        self.long_term_logger = self._setup_logger("long_term", log_level)
        self.context_logger = self._setup_logger("context", log_level)
        
        # Main logger for general memory operations
        self.logger = self._setup_logger("memory", log_level)
        self.logger.info("Memory logger initialized")
        
        # Track last logged data to avoid duplicate logging
        self._last_logged = {}
        self._log_throttle = 300  # Only log similar events every 5 minutes
    
    def _setup_logger(self, memory_type: str, log_level: int) -> logging.Logger:
        """Set up a logger for a specific memory type with rotation."""
        logger = logging.getLogger(f"memory.{memory_type}")
        logger.setLevel(log_level)
        
        # Create rotating file handler
        log_file = os.path.join(self.log_dir, f"{memory_type}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        
        # Set up formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers if they don't exist already
        if not logger.handlers:
            logger.addHandler(file_handler)
            
            # Add console handler for immediate feedback (errors only)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _should_log(self, data: Dict[str, Any]) -> bool:
        """Determine if this entry should be logged based on content and time."""
        current_time = time.time()
        data_hash = hash(json.dumps(data, sort_keys=True))
        
        # Get last logged time for this data hash
        last_time = self._last_logged.get(data_hash, 0)
        
        # Only log if enough time has passed since the same data was logged
        if current_time - last_time > self._log_throttle:
            self._last_logged[data_hash] = current_time
            return True
            
        return False
    
    def log_conscious_memory(self, data: Dict[str, Any], operation: str = "conscious_memory_update") -> None:
        """Log conscious memory updates."""
        try:
            if self._should_log(data):
                self.conscious_logger.warning(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging conscious memory: {e}")
    
    def log_short_term_memory(self, data: Dict[str, Any], operation: str = "short_term_memory_update") -> None:
        """Log short-term memory updates."""
        try:
            if self._should_log(data):
                self.short_term_logger.warning(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging short-term memory: {e}")
    
    def log_long_term_memory(self, data: Dict[str, Any], operation: str = "long_term_memory_update") -> None:
        """Log long-term memory updates."""
        try:
            if self._should_log(data):
                self.long_term_logger.warning(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging long-term memory: {e}")
    
    def log_context_memory(self, data: Dict[str, Any], operation: str = "context_memory_update") -> None:
        """Log contextual memory updates."""
        try:
            if self._should_log(data):
                self.context_logger.warning(f"{operation}: {json.dumps(data, indent=2)}")
        except Exception as e:
            self.logger.error(f"Error logging context memory: {e}")
    
    def log_memory_state(self, state: Dict[str, Any], operation: str = "memory_state_snapshot") -> None:
        """Log the current state of the memory system."""
        try:
            if self._should_log(state):
                # Log each memory type separately
                if 'conscious' in state:
                    self.log_conscious_memory(state['conscious'], f"{operation}_conscious")
                if 'short_term' in state:
                    self.log_short_term_memory(state['short_term'], f"{operation}_short_term")
                if 'long_term' in state:
                    self.log_long_term_memory(state['long_term'], f"{operation}_long_term")
                if 'context' in state:
                    self.log_context_memory(state['context'], f"{operation}_context")
                
                # Log overall state
                self.logger.warning(f"{operation}: {json.dumps(state, indent=2)}")
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