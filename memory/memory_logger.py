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

class MemoryLogger:
    """Logger for memory system operations and state changes."""
    
    def __init__(self, log_dir: str = "logs/memory", log_level: int = logging.INFO):
        """
        Initialize the memory logger.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger("memory")
        self.logger.setLevel(log_level)
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up file handler
        log_file = os.path.join(log_dir, f"memory_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        
        # Set up formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers if they don't exist already
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            
            # Add console handler for immediate feedback
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.log_dir = log_dir
        self.logger.info("Memory logger initialized")
    
    def log_operation(self, operation: str, data: Any = None, status: str = "success", details: Optional[Dict[str, Any]] = None):
        """
        Log a memory operation.
        
        Args:
            operation: The name of the operation being performed
            data: The data associated with the operation (optional)
            status: The status of the operation (success/error/warning)
            details: Additional details about the operation
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "status": status
        }
        
        if data is not None:
            # Truncate large data for logging
            if isinstance(data, str) and len(data) > 500:
                log_entry["data"] = data[:500] + "... [truncated]"
            elif isinstance(data, dict):
                log_entry["data"] = {k: v for k, v in data.items()}
            else:
                log_entry["data"] = str(data)
        
        if details:
            log_entry["details"] = details
            
        # Log with appropriate level based on status
        message = f"{operation}: {status}"
        if data is not None:
            if isinstance(data, dict):
                truncated_data = {k: (str(v)[:100] + "..." if isinstance(v, str) and len(str(v)) > 100 else v) 
                                  for k, v in data.items()}
                message += f" - {json.dumps(truncated_data)}"
            else:
                data_str = str(data)
                if len(data_str) > 100:
                    message += f" - {data_str[:100]}..."
                else:
                    message += f" - {data_str}"
                    
        if status == "error":
            self.logger.error(message)
        elif status == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
            
        # Write detailed log to separate file for complex operations
        if details and "write_to_file" in details and details["write_to_file"]:
            self._write_detail_log(operation, log_entry)
    
    def _write_detail_log(self, operation: str, log_entry: Dict[str, Any]):
        """Write detailed log to a separate file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detail_log_file = os.path.join(self.log_dir, f"{operation}_{timestamp}.json")
        
        try:
            with open(detail_log_file, 'w') as f:
                json.dump(log_entry, f, indent=2)
            self.logger.info(f"Detailed log written to {detail_log_file}")
        except Exception as e:
            self.logger.error(f"Failed to write detailed log: {e}")
    
    def log_error(self, operation: str, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log an error that occurred during a memory operation.
        
        Args:
            operation: The operation where the error occurred
            error: The exception that was raised
            context: Additional context about when the error occurred
        """
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        if context:
            details["context"] = context
            
        self.log_operation(operation, None, "error", details)
    
    def log_memory_state(self, state: Dict[str, Any], operation: str = "memory_state_snapshot"):
        """
        Log the current state of the memory system.
        
        Args:
            state: A dictionary representing the memory state
            operation: The operation name for this state snapshot
        """
        # Simplify state for logging by removing large values
        simplified_state = {}
        for key, value in state.items():
            if isinstance(value, dict):
                simplified_state[key] = {k: f"<{type(v).__name__} of size {len(str(v)) if hasattr(v, '__len__') else 'unknown'}>" 
                                       if isinstance(v, (dict, list)) and len(str(v)) > 200 
                                       else v 
                                       for k, v in value.items()}
            elif isinstance(value, list):
                simplified_state[key] = f"<list of {len(value)} items>"
            else:
                simplified_state[key] = value
                
        self.log_operation(operation, simplified_state)
        
    def get_recent_logs(self, limit: int = 100, operation: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent log entries.
        
        Args:
            limit: Maximum number of log entries to return
            operation: Filter logs by operation (optional)
            
        Returns:
            A list of log entries
        """
        # This is a simplified implementation that reads the log file
        # In a real system, you might want to use a database or other storage
        log_entries = []
        log_file = os.path.join(self.log_dir, f"memory_{datetime.now().strftime('%Y%m%d')}.log")
        
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