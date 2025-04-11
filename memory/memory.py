"""
Conversation Memory Module
Manages conversation history and contextual memory.
"""
import time
import logging
from collections import deque


class ConversationMemory:
    """
    Manages the conversation history between user and assistant.
    Allows retrieving recent history for context window, and provides
    memory management to prevent context overflow.
    """
    
    def __init__(self, max_length=50):
        """
        Initialize the conversation memory.
        
        Args:
            max_length (int): Maximum number of messages to store
        """
        self.messages = deque(maxlen=max_length)
        self.max_length = max_length
        self.logger = logging.getLogger(__name__)
    
    def add_message(self, message):
        """
        Add a message to the conversation history.
        
        Args:
            message (dict): Message object with 'role' and 'content' keys
        """
        if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
            self.logger.error(f"Invalid message format: {message}")
            return False
        
        # Add timestamp for tracking purposes
        message_with_meta = message.copy()
        message_with_meta['timestamp'] = time.time()
        
        self.messages.append(message_with_meta)
        self.logger.debug(f"Added {message['role']} message: {message['content'][:30]}...")
        return True
    
    def get_all(self):
        """
        Get all messages in the conversation history.
        
        Returns:
            list: All messages in conversation history
        """
        # Return messages without metadata
        return [self._strip_metadata(msg) for msg in self.messages]
    
    def get_recent(self, count=None, max_tokens=3000):
        """
        Get recent messages within token budget.
        
        Args:
            count (int): Maximum number of messages to retrieve
            max_tokens (int): Approximate token budget
            
        Returns:
            list: Recent messages that fit within budget
        """
        if count is None:
            count = self.max_length
        
        # Get the most recent 'count' messages
        recent_msgs = list(self.messages)[-count:]
        
        # Estimate token count and trim if needed
        # Note: This is a very rough estimate (4 chars ≈ 1 token)
        total_chars = sum(len(msg.get('content', '')) for msg in recent_msgs)
        estimated_tokens = total_chars / 4
        
        if estimated_tokens <= max_tokens:
            return [self._strip_metadata(msg) for msg in recent_msgs]
        
        # If we exceed token budget, keep removing oldest messages until we fit
        # Always keep the most recent user message
        while estimated_tokens > max_tokens and len(recent_msgs) > 1:
            # Remove the oldest message (but not if it's the only one left)
            removed = recent_msgs.pop(0)
            chars = len(removed.get('content', ''))
            estimated_tokens -= chars / 4
            self.logger.debug(f"Trimmed message to fit token budget: {removed['role']}")
        
        return [self._strip_metadata(msg) for msg in recent_msgs]
    
    def clear(self):
        """Clear the conversation history."""
        self.messages.clear()
        self.logger.info("Conversation memory cleared")
    
    def _strip_metadata(self, message):
        """Remove metadata fields from message."""
        if not isinstance(message, dict):
            return message
        
        result = {}
        for key, value in message.items():
            if key not in ['timestamp']:  # Fields to exclude
                result[key] = value
        return result
    
    def get_summary(self):
        """
        Get a summary of the conversation state.
        
        Returns:
            dict: Summary stats about the conversation
        """
        if not self.messages:
            return {"count": 0, "empty": True}
        
        # Count message types
        role_counts = {}
        for msg in self.messages:
            role = msg.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Get timestamps for first and last message
        first_ts = self.messages[0].get('timestamp', 0)
        last_ts = self.messages[-1].get('timestamp', 0)
        duration = last_ts - first_ts if first_ts and last_ts else 0
        
        return {
            "count": len(self.messages),
            "roles": role_counts,
            "duration_seconds": round(duration, 1),
            "usage_percent": (len(self.messages) / self.max_length) * 100
        }


class ContextMemory:
    """
    Optional extension for storing longer-term context beyond conversation.
    Can be used to remember user preferences, frequently used commands, etc.
    """
    
    def __init__(self):
        """Initialize the context memory."""
        self.context = {}
        self.logger = logging.getLogger(__name__)
    
    def set(self, key, value):
        """
        Store a value in context memory.
        
        Args:
            key (str): Context identifier
            value: Value to store
        """
        self.context[key] = {
            'value': value,
            'updated_at': time.time()
        }
        self.logger.debug(f"Stored context: {key}")
    
    def get(self, key, default=None):
        """
        Retrieve a value from context memory.
        
        Args:
            key (str): Context identifier
            default: Value to return if key not found
            
        Returns:
            Value stored for key or default
        """
        if key not in self.context:
            return default
        
        item = self.context[key]
        # Update access time
        item['accessed_at'] = time.time()
        return item['value']
    
    def clear(self):
        """Clear all context data."""
        self.context = {}
        self.logger.info("Context memory cleared")


# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test conversation memory
    memory = ConversationMemory(max_length=5)
    
    # Add some test messages
    memory.add_message({"role": "system", "content": "You are a helpful AI assistant."})
    memory.add_message({"role": "user", "content": "Hello, who are you?"})
    memory.add_message({"role": "assistant", "content": "I'm a local AI assistant that runs entirely on your machine. How can I help you today?"})
    memory.add_message({"role": "user", "content": "What time is it?"})
    
    # Print all messages
    print("All messages:")
    for msg in memory.get_all():
        print(f"{msg['role']}: {msg['content']}")
    
    # Print summary
    print("\nMemory summary:")
    print(memory.get_summary())
    
    # Test max length
    print("\nTesting max length (adding more messages)...")
    memory.add_message({"role": "assistant", "content": "I can tell you the current time based on your system clock."})
    memory.add_message({"role": "user", "content": "Thanks! Can you also tell me the weather?"})  # Should push out oldest message
    
    # Print all messages after overflow
    print("\nMessages after overflow:")
    for msg in memory.get_all():
        print(f"{msg['role']}: {msg['content']}")