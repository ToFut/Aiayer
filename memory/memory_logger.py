#!/usr/bin/env python3
"""
Memory Logger Module
Handles logging of memory operations and state changes.
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_logger')

class MemoryLogger:
    """Handles logging of memory operations and state changes."""
    
    def __init__(self):
        self.log_dir = 'logs/memory'
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_memory_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a memory operation with details."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'operation': operation,
            'details': details
        }
        
        # Log to file
        log_file = os.path.join(self.log_dir, 'memory_operations.log')
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        # Log to console
        logger.info(f"Memory operation: {operation}")
        
    def log_state_change(self, state_type: str, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """Log a memory state change."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'state_type': state_type,
            'old_state': old_state,
            'new_state': new_state
        }
        
        # Log to file
        log_file = os.path.join(self.log_dir, 'state_changes.log')
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        # Log to console
        logger.info(f"State change in {state_type}")
        
    def get_recent_operations(self, limit: int = 100) -> list:
        """Get recent memory operations."""
        log_file = os.path.join(self.log_dir, 'memory_operations.log')
        if not os.path.exists(log_file):
            return []
            
        operations = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    operations.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        return operations[-limit:]
        
    def get_recent_state_changes(self, limit: int = 100) -> list:
        """Get recent state changes."""
        log_file = os.path.join(self.log_dir, 'state_changes.log')
        if not os.path.exists(log_file):
            return []
            
        changes = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    changes.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        return changes[-limit:]