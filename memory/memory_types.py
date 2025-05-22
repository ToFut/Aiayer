"""
Memory Types Module
Contains base memory type classes for the memory system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

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