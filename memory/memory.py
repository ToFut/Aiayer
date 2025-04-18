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
    Enhanced context memory for storing longer-term context beyond conversation.
    Provides a persistent compass that remembers user preferences, frequently used commands,
    recent activities, and other contextual information.
    """
    
    def __init__(self, storage_path=None):
        """
        Initialize the enhanced context memory with persistent storage.
        
        Args:
            storage_path: Optional path to store context data persistently
        """
        self.context = {}
        self.activity_log = []
        self.preferences = {}
        self.frequent_patterns = {}
        self.logger = logging.getLogger(__name__)
        
        # Set up storage path for persistence
        if storage_path is None:
            home_dir = os.path.expanduser("~")
            self.storage_path = os.path.join(home_dir, ".local_assistant", "context")
        else:
            self.storage_path = storage_path
            
        # Create directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing context if available
        self._load()
    
    def _load(self):
        """Load context from persistent storage."""
        context_file = os.path.join(self.storage_path, "context.json")
        activity_file = os.path.join(self.storage_path, "activity_log.json")
        preferences_file = os.path.join(self.storage_path, "preferences.json")
        patterns_file = os.path.join(self.storage_path, "patterns.json")
        
        try:
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    self.context = json.load(f)
                self.logger.info(f"Loaded context with {len(self.context)} entries")
                
            if os.path.exists(activity_file):
                with open(activity_file, 'r') as f:
                    self.activity_log = json.load(f)
                self.logger.info(f"Loaded activity log with {len(self.activity_log)} entries")
                
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r') as f:
                    self.preferences = json.load(f)
                    
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    self.frequent_patterns = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading context memory: {e}")
    
    def _save(self):
        """Save context to persistent storage."""
        try:
            with open(os.path.join(self.storage_path, "context.json"), 'w') as f:
                json.dump(self.context, f, indent=2)
                
            with open(os.path.join(self.storage_path, "activity_log.json"), 'w') as f:
                json.dump(self.activity_log[-1000:], f, indent=2)  # Keep last 1000 activities
                
            with open(os.path.join(self.storage_path, "preferences.json"), 'w') as f:
                json.dump(self.preferences, f, indent=2)
                
            with open(os.path.join(self.storage_path, "patterns.json"), 'w') as f:
                json.dump(self.frequent_patterns, f, indent=2)
                
            self.logger.debug("Context memory saved to disk")
        except Exception as e:
            self.logger.error(f"Error saving context memory: {e}")
    
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
        self._save()  # Persist changes
    
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
    
    def log_activity(self, activity_type, details, source=None):
        """
        Log user activity to build a comprehensive activity history.
        
        Args:
            activity_type (str): Type of activity (e.g., 'app_usage', 'file_access', 'query')
            details (dict): Activity details
            source (str): Source of the activity information
        """
        activity = {
            'type': activity_type,
            'details': details,
            'timestamp': time.time(),
            'source': source
        }
        
        self.activity_log.append(activity)
        
        # Update patterns based on this activity
        self._update_patterns(activity)
        
        # Periodically save to disk (every 10 activities)
        if len(self.activity_log) % 10 == 0:
            self._save()
            
        return True
    
    def _update_patterns(self, activity):
        """Update pattern recognition based on new activity."""
        activity_type = activity['type']
        
        # Initialize pattern tracking for this activity type if needed
        if activity_type not in self.frequent_patterns:
            self.frequent_patterns[activity_type] = {
                'count': 0,
                'details': {}
            }
            
        # Update count
        self.frequent_patterns[activity_type]['count'] += 1
        
        # Update detail frequency
        if 'details' in activity and isinstance(activity['details'], dict):
            for key, value in activity['details'].items():
                # Only track string or numeric values
                if isinstance(value, (str, int, float)):
                    detail_key = f"{key}:{value}"
                    if detail_key not in self.frequent_patterns[activity_type]['details']:
                        self.frequent_patterns[activity_type]['details'][detail_key] = 0
                    self.frequent_patterns[activity_type]['details'][detail_key] += 1
    
    def get_recent_activities(self, activity_type=None, count=10):
        """
        Get recent user activities, optionally filtered by type.
        
        Args:
            activity_type (str): Optional filter for activity type
            count (int): Number of activities to return
            
        Returns:
            list: Recent activities
        """
        if activity_type:
            filtered = [a for a in self.activity_log if a['type'] == activity_type]
            return filtered[-count:]
        else:
            return self.activity_log[-count:]
    
    def get_common_patterns(self, min_count=3):
        """
        Get common patterns from user activities.
        
        Args:
            min_count (int): Minimum occurrence count to consider a pattern
            
        Returns:
            dict: Common patterns by activity type
        """
        patterns = {}
        
        for activity_type, data in self.frequent_patterns.items():
            if data['count'] >= min_count:
                # Find common details (details that appear in >20% of this activity type)
                common_details = {}
                for detail, count in data['details'].items():
                    if count >= min_count and (count / data['count'] >= 0.2):
                        common_details[detail] = count
                
                if common_details:
                    patterns[activity_type] = {
                        'count': data['count'],
                        'common_details': common_details
                    }
                    
        return patterns
    
    def set_preference(self, category, key, value):
        """
        Store user preference.
        
        Args:
            category (str): Preference category (e.g., 'ui', 'notifications')
            key (str): Preference key
            value: Preference value
        """
        if category not in self.preferences:
            self.preferences[category] = {}
            
        self.preferences[category][key] = {
            'value': value,
            'updated_at': time.time()
        }
        
        self._save()  # Persist changes
    
    def get_preference(self, category, key, default=None):
        """
        Get user preference.
        
        Args:
            category (str): Preference category
            key (str): Preference key
            default: Default value if preference not found
            
        Returns:
            Preference value or default
        """
        if category not in self.preferences or key not in self.preferences[category]:
            return default
            
        return self.preferences[category][key]['value']
    
    def clear(self):
        """Clear all context data."""
        self.context = {}
        # Don't clear activity log and patterns by default
        self.logger.info("Context memory cleared")
        self._save()


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