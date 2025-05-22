#!/usr/bin/env python3
"""
Fix Memory Module Path Issues

This script checks and fixes Python module path issues for the memory system.
It updates the necessary files to ensure proper imports and module resolution.
"""
import os
import sys
import shutil
import glob

def main():
    print("Fixing memory module path issues...")
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    memory_dir = os.path.join(base_dir, 'memory')
    
    # Create __init__.py files where needed
    init_paths = [
        os.path.join(memory_dir, 'memory', '__init__.py'),
        os.path.join(memory_dir, '__init__.py')
    ]
    
    for init_path in init_paths:
        directory = os.path.dirname(init_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Create __init__.py file if it doesn't exist
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write('# Memory system module\n')
            print(f"Created {init_path}")
    
    # Create memory.py file with ConversationMemory and ContextMemory classes if it doesn't exist
    memory_py_path = os.path.join(memory_dir, 'memory.py')
    if not os.path.exists(memory_py_path):
        with open(memory_py_path, 'w') as f:
            f.write('''"""
Memory Module with essential classes for conversation and context management.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional


class ConversationMemory:
    """Manages conversation history."""
    
    def __init__(self):
        self.messages = []
        
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to conversation history."""
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        self.messages.append(message)
        
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent messages."""
        return self.messages[-count:] if self.messages else []
        
    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []


class ContextMemory:
    """Manages contextual information."""
    
    def __init__(self):
        self.contexts = {}
        
    def add_context(self, key: str, value: Any) -> None:
        """Add context information."""
        self.contexts[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
    def get_context(self, key: str) -> Optional[Any]:
        """Get context by key."""
        if key in self.contexts:
            return self.contexts[key]['value']
        return None
        
    def clear(self) -> None:
        """Clear all contexts."""
        self.contexts = {}
''')
        print(f"Created {memory_py_path}")
    
    # Check for log directories and create if needed
    log_dirs = [
        os.path.join(base_dir, 'logs'),
        os.path.join(base_dir, 'logs', 'sensors'),
        os.path.join(base_dir, 'logs', 'sensors', 'screen_sensor'),
        os.path.join(base_dir, 'logs', 'memory'),
        os.path.join(base_dir, 'logs', 'llm')
    ]
    
    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"Created log directory: {log_dir}")
    
    print("Path issues fixed. Now restarting the system should work correctly.")


if __name__ == "__main__":
    main()