"""
Conversation Memory Module
Manages conversation history and contextual memory.
"""
import time
import logging
import os
import json
from collections import deque


class ConversationMemory:
    """
    Manages the conversation history between user and assistant.
    Allows retrieving recent history for context window, and provides
    memory management to prevent context overflow.
    """
    
    def __init__(self, max_length=50, compression_enabled=False, memory_ttl=None, encrypt_sensitive=False):
        """
        Initialize the conversation memory.
        
        Args:
            max_length (int): Maximum number of messages to store
            compression_enabled (bool): Whether to enable memory compression (ignored in this implementation)
            memory_ttl (int): Time-to-live in seconds for old messages (ignored in this implementation)
            encrypt_sensitive (bool): Whether to encrypt sensitive information (ignored in this implementation)
        """
        self.messages = deque(maxlen=max_length)
        self.max_length = max_length
        self.logger = logging.getLogger(__name__)
        # Store these parameters for future compatibility
        self.compression_enabled = compression_enabled
        self.memory_ttl = memory_ttl
        self.encrypt_sensitive = encrypt_sensitive
    
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
    recent activities, and other contextual information with semantic understanding.
    """
    
    def __init__(self, storage_path=None, enable_semantic_indexing=True, 
                 pattern_learning=True, enable_embedding=True):
        """
        Initialize the enhanced context memory with persistent storage and semantic capabilities.
        
        Args:
            storage_path: Optional path to store context data persistently
            enable_semantic_indexing: Whether to enable semantic indexing of activities
            pattern_learning: Whether to enable pattern learning from user activities
            enable_embedding: Whether to enable embedding-based retrieval for related items
        """
        self.context = {}
        self.activity_log = []
        self.preferences = {}
        self.frequent_patterns = {}
        self.semantic_index = {}
        self.topic_clusters = {}
        self.temporal_patterns = {}
        self.sequence_patterns = []
        self.logger = logging.getLogger(__name__)
        
        # Advanced memory capabilities
        self.enable_semantic_indexing = enable_semantic_indexing
        self.pattern_learning = pattern_learning
        self.enable_embedding = enable_embedding
        
        # Configure memory management
        self.max_activities = 5000  # Increased from 1000
        self.memory_decay_factor = 0.85  # Memory decay for older items
        self.persistence_threshold = 0.3  # Importance threshold for long-term storage
        
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
        
        # Initialize any derived data structures
        self._initialize_derived_structures()
    
    def _initialize_derived_structures(self):
        """Initialize derived data structures from loaded data."""
        # Build semantic index if enabled and not already built
        if self.enable_semantic_indexing and not self.semantic_index and len(self.activity_log) > 10:
            self._build_semantic_index()
            
        # Extract temporal patterns if enabled
        if self.pattern_learning and not self.temporal_patterns and len(self.activity_log) > 20:
            self._extract_temporal_patterns()
    
    def _load(self):
        """Load context from persistent storage with enhanced error recovery."""
        context_file = os.path.join(self.storage_path, "context.json")
        activity_file = os.path.join(self.storage_path, "activity_log.json")
        preferences_file = os.path.join(self.storage_path, "preferences.json")
        patterns_file = os.path.join(self.storage_path, "patterns.json")
        semantic_file = os.path.join(self.storage_path, "semantic_index.json")
        temporal_file = os.path.join(self.storage_path, "temporal_patterns.json")
        
        try:
            # Load core data files
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
                    
            # Load enhanced data structures if available
            if os.path.exists(semantic_file) and self.enable_semantic_indexing:
                with open(semantic_file, 'r') as f:
                    self.semantic_index = json.load(f)
                self.logger.info(f"Loaded semantic index with {len(self.semantic_index)} entries")
                
            if os.path.exists(temporal_file) and self.pattern_learning:
                with open(temporal_file, 'r') as f:
                    self.temporal_patterns = json.load(f)
                self.logger.info(f"Loaded temporal patterns")
                
        except Exception as e:
            self.logger.error(f"Error loading context memory: {e}")
            # Attempt recovery - if main files failed, try loading backup files
            try:
                backup_path = os.path.join(self.storage_path, "backup")
                if os.path.exists(backup_path):
                    self.logger.info("Attempting to load from backup files")
                    for filename in ["context.json", "activity_log.json", "preferences.json", "patterns.json"]:
                        backup_file = os.path.join(backup_path, filename)
                        if os.path.exists(backup_file):
                            with open(backup_file, 'r') as f:
                                if filename == "context.json":
                                    self.context = json.load(f)
                                elif filename == "activity_log.json":
                                    self.activity_log = json.load(f)
                                elif filename == "preferences.json":
                                    self.preferences = json.load(f)
                                elif filename == "patterns.json":
                                    self.frequent_patterns = json.load(f)
                            self.logger.info(f"Recovered {filename} from backup")
            except Exception as backup_err:
                self.logger.error(f"Error loading from backup: {backup_err}")
    
    def _save(self):
        """Save context to persistent storage with backups."""
        # Create backup directory if it doesn't exist
        backup_path = os.path.join(self.storage_path, "backup")
        os.makedirs(backup_path, exist_ok=True)
        
        # First, backup the existing files
        try:
            for filename in ["context.json", "activity_log.json", "preferences.json", "patterns.json"]:
                src_file = os.path.join(self.storage_path, filename)
                if os.path.exists(src_file):
                    with open(src_file, 'r') as src:
                        with open(os.path.join(backup_path, filename), 'w') as dest:
                            dest.write(src.read())
        except Exception as e:
            self.logger.error(f"Error creating backups: {e}")
        
        # Now save the current state
        try:
            with open(os.path.join(self.storage_path, "context.json"), 'w') as f:
                json.dump(self.context, f, indent=2)
                
            with open(os.path.join(self.storage_path, "activity_log.json"), 'w') as f:
                # Keep last N activities, sorted by recency and importance
                sorted_activities = self._sort_activities_by_importance(self.activity_log)
                json.dump(sorted_activities[-self.max_activities:], f, indent=2)
                
            with open(os.path.join(self.storage_path, "preferences.json"), 'w') as f:
                json.dump(self.preferences, f, indent=2)
                
            with open(os.path.join(self.storage_path, "patterns.json"), 'w') as f:
                json.dump(self.frequent_patterns, f, indent=2)
                
            # Save enhanced data structures
            if self.enable_semantic_indexing and self.semantic_index:
                with open(os.path.join(self.storage_path, "semantic_index.json"), 'w') as f:
                    json.dump(self.semantic_index, f, indent=2)
                    
            if self.temporal_patterns:
                with open(os.path.join(self.storage_path, "temporal_patterns.json"), 'w') as f:
                    json.dump(self.temporal_patterns, f, indent=2)
                    
            self.logger.debug("Context memory saved to disk")
        except Exception as e:
            self.logger.error(f"Error saving context memory: {e}")
    
    def _sort_activities_by_importance(self, activities):
        """Sort activities by importance combining recency, frequency, and semantic relevance."""
        if not activities:
            return []
            
        # Define importance scoring function
        def score_activity(activity):
            # Base score starts with recency (0-1 range, 1 being most recent)
            current_time = time.time()
            max_age = 60 * 60 * 24 * 30  # 30 days in seconds
            age = current_time - activity.get('timestamp', current_time)
            recency_score = max(0, 1 - (age / max_age))
            
            # Frequency score based on activity type
            activity_type = activity.get('type', '')
            type_frequency = self.frequent_patterns.get(activity_type, {}).get('count', 0)
            frequency_score = min(1, type_frequency / 100)  # Cap at 1
            
            # Calculate importance using recency and frequency
            importance = (recency_score * 0.7) + (frequency_score * 0.3)
            
            # Apply memory decay for older items
            if age > (60 * 60 * 24):  # Older than a day
                importance *= self.memory_decay_factor
                
            return importance
            
        # Add importance score to each activity
        scored_activities = []
        for activity in activities:
            activity_copy = activity.copy()
            activity_copy['importance'] = score_activity(activity)
            scored_activities.append(activity_copy)
            
        # Sort by importance score (descending)
        return sorted(scored_activities, key=lambda x: x.get('importance', 0), reverse=True)
    
    def set(self, key, value, metadata=None):
        """
        Store a value in context memory with optional metadata.
        
        Args:
            key (str): Context identifier
            value: Value to store
            metadata (dict): Optional metadata about this context item
        """
        if metadata is None:
            metadata = {}
            
        self.context[key] = {
            'value': value,
            'updated_at': time.time(),
            'metadata': metadata
        }
        self.logger.debug(f"Stored context: {key}")
        
        # If semantic indexing is enabled and value is a string, add to semantic index
        if self.enable_semantic_indexing and isinstance(value, str):
            self._add_to_semantic_index(key, value)
            
        # Only save periodically to reduce disk I/O
        if len(self.context) % 10 == 0:
            self._save()
    
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
        # Update access time and frequency
        item['accessed_at'] = time.time()
        item['access_count'] = item.get('access_count', 0) + 1
        return item['value']
    
    def get_similar(self, query, top_n=5):
        """
        Retrieve values semantically similar to the query.
        
        Args:
            query (str): Query to match
            top_n (int): Maximum number of results to return
            
        Returns:
            list: Similar items as (key, value, score) tuples
        """
        if not self.enable_semantic_indexing or not self.semantic_index:
            return []
            
        # Find similar items using semantic index
        results = []
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        # Find matching items for each keyword
        candidates = {}
        for keyword in keywords:
            if keyword in self.semantic_index:
                # Get items containing this keyword
                for item_key in self.semantic_index[keyword]:
                    if item_key in self.context:
                        # Increment score for this item
                        candidates[item_key] = candidates.get(item_key, 0) + 1
        
        # Sort by match score
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N results
        for key, score in sorted_candidates[:top_n]:
            if key in self.context:
                item = self.context[key]
                # Normalize score to 0-1 range
                normalized_score = score / len(keywords)
                results.append((key, item['value'], normalized_score))
        
        return results
    
    def log_activity(self, activity_type, details, source=None, importance=None, semantic_tags=None):
        """
        Log user activity with enhanced metadata for better pattern recognition.
        
        Args:
            activity_type (str): Type of activity (e.g., 'app_usage', 'file_access', 'query')
            details (dict): Activity details
            source (str): Source of the activity information
            importance (float): Optional explicit importance score (0-1)
            semantic_tags (list): Optional list of semantic tags for this activity
        """
        # Create activity with enhanced metadata
        activity = {
            'type': activity_type,
            'details': details,
            'timestamp': time.time(),
            'source': source
        }
        
        if importance is not None:
            activity['importance'] = min(1.0, max(0.0, importance))
            
        if semantic_tags and isinstance(semantic_tags, list):
            activity['semantic_tags'] = semantic_tags
            
        # Add time of day and day of week for temporal pattern analysis
        current_time = time.localtime()
        activity['time_of_day'] = current_time.tm_hour
        activity['day_of_week'] = current_time.tm_wday
        
        self.activity_log.append(activity)
        
        # Update patterns based on this activity
        self._update_patterns(activity)
        
        # Update temporal patterns if enabled
        if self.pattern_learning:
            self._update_temporal_patterns(activity)
            
        # Add to semantic index if enabled
        if self.enable_semantic_indexing and 'semantic_tags' in activity:
            for tag in activity['semantic_tags']:
                self._add_to_semantic_index(f"activity_{len(self.activity_log)}", tag)
        
        # Periodically save to disk (every 10 activities)
        if len(self.activity_log) % 10 == 0:
            self._save()
            
        return True
    
    def _update_patterns(self, activity):
        """Update pattern recognition with enhanced sequence detection."""
        activity_type = activity['type']
        
        # Initialize pattern tracking for this activity type if needed
        if activity_type not in self.frequent_patterns:
            self.frequent_patterns[activity_type] = {
                'count': 0,
                'details': {},
                'sequences': {},  # Track common sequences
                'co_occurrences': {}  # Track co-occurring activities
            }
            
        # Update count
        self.frequent_patterns[activity_type]['count'] += 1
        
        # Update detail frequency with more comprehensive analysis
        if 'details' in activity and isinstance(activity['details'], dict):
            for key, value in activity['details'].items():
                # Process string, numeric, boolean, or list values
                if isinstance(value, (str, int, float, bool)):
                    detail_key = f"{key}:{value}"
                    if detail_key not in self.frequent_patterns[activity_type]['details']:
                        self.frequent_patterns[activity_type]['details'][detail_key] = 0
                    self.frequent_patterns[activity_type]['details'][detail_key] += 1
                elif isinstance(value, list) and all(isinstance(item, (str, int, float, bool)) for item in value):
                    # Handle list values by tracking individual items and combinations
                    for item in value:
                        detail_key = f"{key}:[{item}]"
                        if detail_key not in self.frequent_patterns[activity_type]['details']:
                            self.frequent_patterns[activity_type]['details'][detail_key] = 0
                        self.frequent_patterns[activity_type]['details'][detail_key] += 1
        
        # Update sequence patterns if we have previous activities
        if self.activity_log and len(self.activity_log) > 1:
            # Get previous activity
            prev_activity = self.activity_log[-2]
            prev_type = prev_activity.get('type')
            
            if prev_type:
                # Update sequence tracking
                sequence_key = f"{prev_type}->{activity_type}"
                if 'sequences' not in self.frequent_patterns:
                    self.frequent_patterns['sequences'] = {}
                    
                if sequence_key not in self.frequent_patterns['sequences']:
                    self.frequent_patterns['sequences'][sequence_key] = 0
                    
                self.frequent_patterns['sequences'][sequence_key] += 1
                
                # Track co-occurrences
                if 'co_occurrences' not in self.frequent_patterns[activity_type]:
                    self.frequent_patterns[activity_type]['co_occurrences'] = {}
                    
                if prev_type not in self.frequent_patterns[activity_type]['co_occurrences']:
                    self.frequent_patterns[activity_type]['co_occurrences'][prev_type] = 0
                    
                self.frequent_patterns[activity_type]['co_occurrences'][prev_type] += 1
    
    def _update_temporal_patterns(self, activity):
        """Update temporal patterns based on time of activity."""
        hour = activity.get('time_of_day')
        day = activity.get('day_of_week')
        activity_type = activity.get('type')
        
        if hour is not None and day is not None and activity_type:
            # Initialize if needed
            if 'hourly' not in self.temporal_patterns:
                self.temporal_patterns['hourly'] = {}
            if 'daily' not in self.temporal_patterns:
                self.temporal_patterns['daily'] = {}
                
            # Update hourly patterns
            if hour not in self.temporal_patterns['hourly']:
                self.temporal_patterns['hourly'][hour] = {}
                
            if activity_type not in self.temporal_patterns['hourly'][hour]:
                self.temporal_patterns['hourly'][hour][activity_type] = 0
                
            self.temporal_patterns['hourly'][hour][activity_type] += 1
            
            # Update daily patterns
            if day not in self.temporal_patterns['daily']:
                self.temporal_patterns['daily'][day] = {}
                
            if activity_type not in self.temporal_patterns['daily'][day]:
                self.temporal_patterns['daily'][day][activity_type] = 0
                
            self.temporal_patterns['daily'][day][activity_type] += 1
    
    def _add_to_semantic_index(self, key, text):
        """Add an item to the semantic index."""
        # Extract keywords from text
        keywords = self._extract_keywords(text)
        
        # Add item to index for each keyword
        for keyword in keywords:
            if keyword not in self.semantic_index:
                self.semantic_index[keyword] = []
                
            if key not in self.semantic_index[keyword]:
                self.semantic_index[keyword].append(key)
                
            # Limit number of items per keyword
            if len(self.semantic_index[keyword]) > 100:
                self.semantic_index[keyword] = self.semantic_index[keyword][-100:]
    
    def _extract_keywords(self, text):
        """Extract keywords from text for semantic indexing."""
        if not isinstance(text, str):
            return []
            
        # Convert to lowercase
        text = text.lower()
        
        # Basic stopwords
        stopwords = {"a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be", "been", 
                    "being", "in", "on", "at", "to", "for", "with", "by", "about", "against", "between",
                    "into", "through", "during", "before", "after", "above", "below", "from", "up", "down",
                    "of", "off", "over", "under", "again", "further", "then", "once", "here", "there",
                    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most",
                    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
                    "too", "very", "s", "t", "can", "will", "just", "now", "d", "ll", "m", "o", "re",
                    "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven",
                    "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won",
                    "wouldn", "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", 
                    "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
                    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
                    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", 
                    "am", "have", "has", "had", "do", "does", "did", "doing", "should", "would", 
                    "could", "ought", "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
                    "i've", "you've", "we've", "they've", "i'd", "you'd", "he'd", "she'd", "we'd",
                    "they'd", "i'll", "you'll", "he'll", "she'll", "we'll", "they'll", "let's"}
        
        # Simple tokenization by splitting on non-alphanumeric characters
        tokens = [token.strip() for token in ''.join(c if c.isalnum() else ' ' for c in text).split()]
        
        # Filter out stopwords and short tokens
        keywords = [token for token in tokens if token not in stopwords and len(token) > 2]
        
        return keywords
    
    def _build_semantic_index(self):
        """Build or rebuild the semantic index from existing activities."""
        self.semantic_index = {}
        
        # Process context items
        for key, item in self.context.items():
            if isinstance(item, dict) and 'value' in item:
                value = item['value']
                if isinstance(value, str):
                    self._add_to_semantic_index(key, value)
        
        # Process activities
        for i, activity in enumerate(self.activity_log):
            # Process semantic tags if available
            if 'semantic_tags' in activity and isinstance(activity['semantic_tags'], list):
                for tag in activity['semantic_tags']:
                    self._add_to_semantic_index(f"activity_{i}", tag)
            
            # Process details
            if 'details' in activity and isinstance(activity['details'], dict):
                for detail_key, detail_value in activity['details'].items():
                    if isinstance(detail_value, str):
                        self._add_to_semantic_index(f"activity_{i}_{detail_key}", detail_value)
    
    def _extract_temporal_patterns(self):
        """Extract temporal patterns from existing activities."""
        self.temporal_patterns = {'hourly': {}, 'daily': {}}
        
        for activity in self.activity_log:
            hour = activity.get('time_of_day')
            day = activity.get('day_of_week')
            activity_type = activity.get('type')
            
            if hour is not None and day is not None and activity_type:
                # Update hourly patterns
                if hour not in self.temporal_patterns['hourly']:
                    self.temporal_patterns['hourly'][hour] = {}
                    
                if activity_type not in self.temporal_patterns['hourly'][hour]:
                    self.temporal_patterns['hourly'][hour][activity_type] = 0
                    
                self.temporal_patterns['hourly'][hour][activity_type] += 1
                
                # Update daily patterns
                if day not in self.temporal_patterns['daily']:
                    self.temporal_patterns['daily'][day] = {}
                    
                if activity_type not in self.temporal_patterns['daily'][day]:
                    self.temporal_patterns['daily'][day][activity_type] = 0
                    
                self.temporal_patterns['daily'][day][activity_type] += 1
    
    def get_recent_activities(self, activity_type=None, count=10, include_metadata=False):
        """
        Get recent user activities with enhanced filtering options.
        
        Args:
            activity_type (str, list): Optional filter for activity type(s)
            count (int): Number of activities to return
            include_metadata (bool): Whether to include temporal metadata
            
        Returns:
            list: Recent activities
        """
        # Handle multiple activity types
        if isinstance(activity_type, list):
            filtered = [a for a in self.activity_log if a['type'] in activity_type]
        elif activity_type:
            filtered = [a for a in self.activity_log if a['type'] == activity_type]
        else:
            filtered = self.activity_log
        
        # Get recent activities
        recent = filtered[-count:]
        
        # Strip internal metadata if not requested
        if not include_metadata:
            return [self._strip_internal_metadata(a) for a in recent]
        
        return recent
    
    def _strip_internal_metadata(self, activity):
        """Strip internal metadata fields from activity."""
        if not isinstance(activity, dict):
            return activity
        
        result = {}
        internal_fields = {'importance', 'time_of_day', 'day_of_week'}
        
        for key, value in activity.items():
            if key not in internal_fields:
                result[key] = value
                
        return result
    
    def get_common_patterns(self, min_count=3, include_sequences=True):
        """
        Get common patterns from user activities with enhanced sequence recognition.
        
        Args:
            min_count (int): Minimum occurrence count to consider a pattern
            include_sequences (bool): Whether to include activity sequences
            
        Returns:
            dict: Common patterns by activity type
        """
        patterns = {}
        
        # Process activity type patterns
        for activity_type, data in self.frequent_patterns.items():
            if activity_type == 'sequences':
                continue  # Handle sequences separately
                
            if isinstance(data, dict) and data.get('count', 0) >= min_count:
                # Find common details (details that appear in >20% of this activity type)
                common_details = {}
                for detail, count in data.get('details', {}).items():
                    if count >= min_count and (count / data['count'] >= 0.2):
                        common_details[detail] = count
                
                # Find common co-occurrences
                common_co_occurrences = {}
                for co_type, count in data.get('co_occurrences', {}).items():
                    if count >= min_count and (count / data['count'] >= 0.1):
                        common_co_occurrences[co_type] = count
                
                if common_details or common_co_occurrences:
                    patterns[activity_type] = {
                        'count': data['count'],
                        'common_details': common_details
                    }
                    
                    if common_co_occurrences:
                        patterns[activity_type]['common_co_occurrences'] = common_co_occurrences
        
        # Add sequence patterns if requested
        if include_sequences and 'sequences' in self.frequent_patterns:
            common_sequences = {}
            for sequence, count in self.frequent_patterns['sequences'].items():
                if count >= min_count:
                    common_sequences[sequence] = count
                    
            if common_sequences:
                patterns['activity_sequences'] = common_sequences
                
        return patterns
    
    def get_temporal_patterns(self, time_of_day=None, day_of_week=None):
        """
        Get temporal patterns of activities.
        
        Args:
            time_of_day (int): Optional hour of day to filter (0-23)
            day_of_week (int): Optional day of week to filter (0-6, 0=Monday)
            
        Returns:
            dict: Temporal patterns
        """
        if not self.temporal_patterns:
            return {}
            
        # Filter by time of day if specified
        if time_of_day is not None:
            return self.temporal_patterns.get('hourly', {}).get(time_of_day, {})
            
        # Filter by day of week if specified
        if day_of_week is not None:
            return self.temporal_patterns.get('daily', {}).get(day_of_week, {})
            
        # Return all patterns
        return self.temporal_patterns
    
    def set_preference(self, category, key, value, metadata=None):
        """
        Store user preference with optional metadata.
        
        Args:
            category (str): Preference category (e.g., 'ui', 'notifications')
            key (str): Preference key
            value: Preference value
            metadata (dict): Optional metadata about this preference
        """
        if category not in self.preferences:
            self.preferences[category] = {}
            
        self.preferences[category][key] = {
            'value': value,
            'updated_at': time.time(),
            'metadata': metadata or {}
        }
        
        # Add to activity log for pattern recognition
        self.log_activity(
            activity_type='preference_change',
            details={
                'category': category,
                'key': key,
                'value': str(value)
            },
            source='preference_manager'
        )
        
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
            
        # Update access tracking
        self.preferences[category][key]['accessed_at'] = time.time()
        self.preferences[category][key]['access_count'] = self.preferences[category][key].get('access_count', 0) + 1
        
        return self.preferences[category][key]['value']
    
    def get_all_preferences(self, category=None):
        """
        Get all preferences, optionally filtered by category.
        
        Args:
            category (str): Optional category to filter by
            
        Returns:
            dict: All preferences in the given category or all categories
        """
        if category:
            return {k: v.get('value') for k, v in self.preferences.get(category, {}).items()}
        
        # Return all preferences organized by category
        result = {}
        for cat, prefs in self.preferences.items():
            result[cat] = {k: v.get('value') for k, v in prefs.items()}
            
        return result
    
    def clear(self, keep_preferences=True, keep_patterns=True):
        """
        Clear all or selected context data.
        
        Args:
            keep_preferences (bool): Whether to keep user preferences
            keep_patterns (bool): Whether to keep learned patterns
        """
        self.context = {}
        
        if not keep_preferences:
            self.preferences = {}
            
        if not keep_patterns:
            self.frequent_patterns = {}
            self.semantic_index = {}
            self.temporal_patterns = {}
            self.sequence_patterns = []
            # Keep activity log but reset
            self.activity_log = []
            
        self.logger.info(f"Context memory cleared (keep_preferences={keep_preferences}, keep_patterns={keep_patterns})")
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