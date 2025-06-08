#!/usr/bin/env python3
"""
Suggestion Memory Module

Manages a persistent, high-performance suggestion memory store for autonomous epiphany system.
Provides structured storage and retrieval of actionable suggestions with context and action items.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Union
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/suggestion_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/memory', exist_ok=True)

class SuggestionMemory:
    """
    Global suggestion memory store for the autonomous epiphany system.
    Maintains suggestions with action items, confidence scores, and context.
    """
    
    def __init__(self):
        """Initialize the suggestion memory system."""
        self.suggestions: Dict[str, Dict[str, Any]] = {}
        self.pending_suggestions: Dict[str, Dict[str, Any]] = {}
        self.accepted_suggestions: Dict[str, Dict[str, Any]] = {}
        self.rejected_suggestions: Dict[str, Dict[str, Any]] = {}
        self.suggestion_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            "total_suggestions": 0,
            "accepted_suggestions": 0,
            "rejected_suggestions": 0,
            "executed_suggestions": 0,
            "avg_confidence": 0.0,
        }
        
        # User preferences (for learning)
        self.user_preferences = {
            "accepted_apps": set(),
            "rejected_apps": set(),
            "preferred_times": {},
            "suggestion_types": {}
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Maximum number of suggestions to keep in memory
        self.max_active_suggestions = 10
        self.max_history_size = 100
        
        # Minimum confidence threshold
        self.min_confidence_threshold = 0.65
        
        # Initialize storage file path
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'memory', 
            'suggestion_memory_state.json'
        )
        
        # Load existing state if available
        self._load_state()
        
        logger.info("✅ SuggestionMemory initialized successfully")
    
    async def add_suggestion(self, suggestion: Dict[str, Any]) -> Optional[str]:
        """
        Add a new suggestion to the memory.
        
        Args:
            suggestion: Dictionary containing suggestion data
                Required fields:
                - title: Short title for the suggestion
                - description: Detailed description
                - confidence: Float between 0-1
                - action_items: List of action steps
                - context: Dict with contextual information
                
        Returns:
            suggestion_id: ID of the added suggestion or None if rejected
        """
        async with self._lock:
            try:
                # Validate suggestion format
                if not self._validate_suggestion(suggestion):
                    logger.warning("❌ Invalid suggestion format")
                    return None
                
                # Check confidence threshold
                confidence = suggestion.get('confidence', 0.0)
                if confidence < self.min_confidence_threshold:
                    logger.info(f"⚠️ Suggestion below confidence threshold: {confidence}")
                    return None
                
                # Generate suggestion ID if not provided
                suggestion_id = suggestion.get('id', f"sugg_{str(uuid.uuid4())[:8]}")
                
                # Add metadata
                suggestion['id'] = suggestion_id
                suggestion['timestamp'] = suggestion.get('timestamp', datetime.now().isoformat())
                suggestion['status'] = 'pending'
                
                # Store in pending suggestions
                self.pending_suggestions[suggestion_id] = suggestion
                
                # Update metrics
                self.metrics["total_suggestions"] += 1
                total_conf = self.metrics["avg_confidence"] * (self.metrics["total_suggestions"] - 1)
                self.metrics["avg_confidence"] = (total_conf + confidence) / self.metrics["total_suggestions"]
                
                logger.info(f"✅ Added suggestion '{suggestion['title']}' (ID: {suggestion_id}, confidence: {confidence:.2f})")
                
                # Save state asynchronously
                asyncio.create_task(self._save_state())
                
                return suggestion_id
                
            except Exception as e:
                logger.error(f"❌ Error adding suggestion: {e}")
                logger.error(traceback.format_exc())
                return None
    
    async def get_suggestion(self, suggestion_id: str) -> Optional[Dict[str, Any]]:
        """Get a suggestion by its ID."""
        async with self._lock:
            # Check active suggestions first
            if suggestion_id in self.pending_suggestions:
                return self.pending_suggestions[suggestion_id]
            elif suggestion_id in self.accepted_suggestions:
                return self.accepted_suggestions[suggestion_id]
            elif suggestion_id in self.rejected_suggestions:
                return self.rejected_suggestions[suggestion_id]
                
            # Check history if not found in active suggestions
            for suggestion in self.suggestion_history:
                if suggestion.get('id') == suggestion_id:
                    return suggestion
                    
            return None
    
    async def get_all_pending_suggestions(self) -> List[Dict[str, Any]]:
        """Get all pending suggestions sorted by confidence (highest first)."""
        async with self._lock:
            return sorted(
                self.pending_suggestions.values(),
                key=lambda x: x.get('confidence', 0.0),
                reverse=True
            )
    
    async def get_top_suggestion(self) -> Optional[Dict[str, Any]]:
        """Get the highest confidence pending suggestion."""
        async with self._lock:
            pending = await self.get_all_pending_suggestions()
            return pending[0] if pending else None
    
    async def mark_suggestion_accepted(self, suggestion_id: str) -> bool:
        """Mark a suggestion as accepted by the user."""
        async with self._lock:
            try:
                if suggestion_id not in self.pending_suggestions:
                    logger.warning(f"⚠️ Cannot accept non-pending suggestion: {suggestion_id}")
                    return False
                
                # Move from pending to accepted
                suggestion = self.pending_suggestions.pop(suggestion_id)
                suggestion['status'] = 'accepted'
                suggestion['accepted_at'] = datetime.now().isoformat()
                self.accepted_suggestions[suggestion_id] = suggestion
                
                # Update metrics
                self.metrics["accepted_suggestions"] += 1
                
                # Update user preferences
                if 'context' in suggestion and 'app' in suggestion['context']:
                    app = suggestion['context']['app']
                    self.user_preferences["accepted_apps"].add(app)
                
                # Save state asynchronously
                asyncio.create_task(self._save_state())
                
                logger.info(f"✅ Marked suggestion {suggestion_id} as accepted")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error marking suggestion as accepted: {e}")
                return False
    
    async def mark_suggestion_rejected(self, suggestion_id: str, reason: Optional[str] = None) -> bool:
        """Mark a suggestion as rejected by the user."""
        async with self._lock:
            try:
                if suggestion_id not in self.pending_suggestions:
                    logger.warning(f"⚠️ Cannot reject non-pending suggestion: {suggestion_id}")
                    return False
                
                # Move from pending to rejected
                suggestion = self.pending_suggestions.pop(suggestion_id)
                suggestion['status'] = 'rejected'
                suggestion['rejected_at'] = datetime.now().isoformat()
                if reason:
                    suggestion['rejection_reason'] = reason
                self.rejected_suggestions[suggestion_id] = suggestion
                
                # Update metrics
                self.metrics["rejected_suggestions"] += 1
                
                # Update user preferences
                if 'context' in suggestion and 'app' in suggestion['context']:
                    app = suggestion['context']['app']
                    self.user_preferences["rejected_apps"].add(app)
                
                # Save state asynchronously
                asyncio.create_task(self._save_state())
                
                logger.info(f"✅ Marked suggestion {suggestion_id} as rejected")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error marking suggestion as rejected: {e}")
                return False
    
    async def mark_suggestion_executed(self, suggestion_id: str, success: bool = True) -> bool:
        """Mark a suggestion as executed successfully or with failure."""
        async with self._lock:
            try:
                # Find the suggestion
                if suggestion_id in self.accepted_suggestions:
                    suggestion = self.accepted_suggestions.pop(suggestion_id)
                elif suggestion_id in self.pending_suggestions:
                    suggestion = self.pending_suggestions.pop(suggestion_id)
                else:
                    logger.warning(f"⚠️ Cannot find suggestion to mark as executed: {suggestion_id}")
                    return False
                
                # Update suggestion status
                suggestion['status'] = 'executed' if success else 'execution_failed'
                suggestion['executed_at'] = datetime.now().isoformat()
                suggestion['execution_success'] = success
                
                # Add to history
                self.suggestion_history.append(suggestion)
                
                # Trim history if needed
                if len(self.suggestion_history) > self.max_history_size:
                    self.suggestion_history = self.suggestion_history[-self.max_history_size:]
                
                # Update metrics
                if success:
                    self.metrics["executed_suggestions"] += 1
                
                # Save state asynchronously
                asyncio.create_task(self._save_state())
                
                logger.info(f"✅ Marked suggestion {suggestion_id} as executed (success: {success})")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error marking suggestion as executed: {e}")
                return False
    
    async def clear_old_suggestions(self, max_age_hours: int = 24) -> int:
        """Clear suggestions older than specified hours."""
        async with self._lock:
            try:
                now = datetime.now()
                count = 0
                
                # Helper to check age
                def is_old(timestamp_str: str) -> bool:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        age_hours = (now - timestamp).total_seconds() / 3600
                        return age_hours > max_age_hours
                    except:
                        return True  # If can't parse, consider it old
                
                # Clear old pending suggestions
                old_ids = [
                    sugg_id for sugg_id, sugg in self.pending_suggestions.items()
                    if is_old(sugg.get('timestamp', ''))
                ]
                for sugg_id in old_ids:
                    suggestion = self.pending_suggestions.pop(sugg_id)
                    suggestion['status'] = 'expired'
                    self.suggestion_history.append(suggestion)
                    count += 1
                
                # Clear old accepted/rejected suggestions
                for collection in [self.accepted_suggestions, self.rejected_suggestions]:
                    old_ids = [
                        sugg_id for sugg_id, sugg in collection.items()
                        if is_old(sugg.get('timestamp', ''))
                    ]
                    for sugg_id in old_ids:
                        suggestion = collection.pop(sugg_id)
                        self.suggestion_history.append(suggestion)
                        count += 1
                
                # Trim history if needed
                if len(self.suggestion_history) > self.max_history_size:
                    self.suggestion_history = self.suggestion_history[-self.max_history_size:]
                
                # Save state asynchronously
                if count > 0:
                    asyncio.create_task(self._save_state())
                    logger.info(f"✅ Cleared {count} old suggestions")
                
                return count
                
            except Exception as e:
                logger.error(f"❌ Error clearing old suggestions: {e}")
                return 0
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        async with self._lock:
            metrics = self.metrics.copy()
            
            # Add derived metrics
            if metrics["total_suggestions"] > 0:
                metrics["acceptance_rate"] = metrics["accepted_suggestions"] / metrics["total_suggestions"]
                metrics["execution_rate"] = metrics["executed_suggestions"] / metrics["total_suggestions"]
            else:
                metrics["acceptance_rate"] = 0.0
                metrics["execution_rate"] = 0.0
                
            # Add counts
            metrics["pending_count"] = len(self.pending_suggestions)
            metrics["accepted_count"] = len(self.accepted_suggestions)
            metrics["rejected_count"] = len(self.rejected_suggestions)
            metrics["history_count"] = len(self.suggestion_history)
            
            return metrics
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """Get learned user preferences."""
        async with self._lock:
            return {
                "accepted_apps": list(self.user_preferences["accepted_apps"]),
                "rejected_apps": list(self.user_preferences["rejected_apps"]),
                "preferred_times": self.user_preferences["preferred_times"],
                "suggestion_types": self.user_preferences["suggestion_types"]
            }
    
    def _validate_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """Validate suggestion format."""
        required_fields = ['title', 'description', 'confidence', 'action_items']
        
        # Check required fields
        for field in required_fields:
            if field not in suggestion:
                logger.warning(f"❌ Missing required field in suggestion: {field}")
                return False
        
        # Validate confidence score
        confidence = suggestion.get('confidence', 0.0)
        if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            logger.warning(f"❌ Invalid confidence score: {confidence}")
            return False
        
        # Validate action items
        action_items = suggestion.get('action_items', [])
        if not isinstance(action_items, list) or len(action_items) == 0:
            logger.warning("❌ Missing or invalid action_items list")
            return False
        
        return True
    
    def _load_state(self) -> None:
        """Load suggestion memory state from file."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    state = json.load(f)
                
                # Restore state
                self.pending_suggestions = state.get('pending_suggestions', {})
                self.accepted_suggestions = state.get('accepted_suggestions', {})
                self.rejected_suggestions = state.get('rejected_suggestions', {})
                self.suggestion_history = state.get('suggestion_history', [])
                self.metrics = state.get('metrics', self.metrics)
                
                # Convert sets from lists
                user_prefs = state.get('user_preferences', {})
                self.user_preferences = {
                    "accepted_apps": set(user_prefs.get('accepted_apps', [])),
                    "rejected_apps": set(user_prefs.get('rejected_apps', [])),
                    "preferred_times": user_prefs.get('preferred_times', {}),
                    "suggestion_types": user_prefs.get('suggestion_types', {})
                }
                
                logger.info(f"✅ Loaded suggestion memory state: {len(self.pending_suggestions)} pending, "
                           f"{len(self.accepted_suggestions)} accepted, {len(self.rejected_suggestions)} rejected")
            else:
                logger.info("🆕 No existing suggestion memory state found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading suggestion memory state: {e}")
            logger.error(traceback.format_exc())
    
    async def _save_state(self) -> None:
        """Save suggestion memory state to file."""
        try:
            # Convert sets to lists for JSON serialization
            user_prefs = {
                "accepted_apps": list(self.user_preferences["accepted_apps"]),
                "rejected_apps": list(self.user_preferences["rejected_apps"]),
                "preferred_times": self.user_preferences["preferred_times"],
                "suggestion_types": self.user_preferences["suggestion_types"]
            }
            
            # Build state object
            state = {
                'pending_suggestions': self.pending_suggestions,
                'accepted_suggestions': self.accepted_suggestions,
                'rejected_suggestions': self.rejected_suggestions,
                'suggestion_history': self.suggestion_history,
                'metrics': self.metrics,
                'user_preferences': user_prefs,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to temporary file first, then rename for atomicity
            temp_path = f"{self.storage_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Atomic replacement
            os.replace(temp_path, self.storage_path)
            
            logger.debug(f"✅ Saved suggestion memory state")
        except Exception as e:
            logger.error(f"❌ Error saving suggestion memory state: {e}")
            logger.error(traceback.format_exc())

# Singleton instance for global access
_suggestion_memory_instance = None

async def get_suggestion_memory() -> SuggestionMemory:
    """Get or create the global suggestion memory instance."""
    global _suggestion_memory_instance
    if _suggestion_memory_instance is None:
        _suggestion_memory_instance = SuggestionMemory()
    return _suggestion_memory_instance

# Example usage
if __name__ == "__main__":
    async def test_suggestion_memory():
        """Test the suggestion memory system."""
        # Get suggestion memory instance
        memory = await get_suggestion_memory()
        
        # Create a test suggestion
        test_suggestion = {
            "title": "Create calendar event",
            "description": "I noticed you're reading an email about a meeting on Thursday",
            "confidence": 0.85,
            "action_items": [
                {"type": "open_app", "target": "Calendar"},
                {"type": "input_text", "target": "event_title", "value": "Team Meeting"},
                {"type": "input_text", "target": "date", "value": "Thursday 3pm"}
            ],
            "context": {
                "source": "email",
                "app": "Mail",
                "timestamp": "2025-06-06T15:30:00Z"
            }
        }
        
        # Add suggestion
        suggestion_id = await memory.add_suggestion(test_suggestion)
        print(f"Added suggestion with ID: {suggestion_id}")
        
        # Get suggestion
        suggestion = await memory.get_suggestion(suggestion_id)
        print(f"Retrieved suggestion: {suggestion['title']}")
        
        # Mark as accepted
        await memory.mark_suggestion_accepted(suggestion_id)
        
        # Get metrics
        metrics = await memory.get_metrics()
        print(f"Metrics: {metrics}")
        
        # Clean up
        count = await memory.clear_old_suggestions(max_age_hours=0)
        print(f"Cleared {count} suggestions")
    
    # Run the test
    asyncio.run(test_suggestion_memory())