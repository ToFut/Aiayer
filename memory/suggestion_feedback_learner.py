#!/usr/bin/env python3
"""
Suggestion Feedback Learner

Implements a feedback loop system for improving suggestions based on user responses.
Learns from acceptance/rejection patterns to enhance future suggestion quality.
"""

import asyncio
import json
import logging
import os
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
import traceback
import uuid
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/suggestion_feedback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/memory', exist_ok=True)

# Import related modules
try:
    from memory.suggestion_memory import get_suggestion_memory
    SUGGESTION_MEMORY_AVAILABLE = True
except ImportError:
    SUGGESTION_MEMORY_AVAILABLE = False
    logger.warning("⚠️ Suggestion memory module not available")

class SuggestionFeature:
    """Represents a feature extracted from a suggestion for learning."""
    
    def __init__(self, name: str, value: Any, weight: float = 1.0):
        self.name = name
        self.value = value
        self.weight = weight
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SuggestionFeature':
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            value=data.get("value"),
            weight=data.get("weight", 1.0)
        )

class FeedbackRecord:
    """Record of user feedback on a suggestion."""
    
    def __init__(
        self, 
        suggestion_id: str,
        features: List[SuggestionFeature],
        outcome: str,  # 'accepted', 'rejected', 'executed', 'failed'
        timestamp: Optional[str] = None,
        execution_success: Optional[bool] = None,
        rejection_reason: Optional[str] = None
    ):
        self.suggestion_id = suggestion_id
        self.features = features
        self.outcome = outcome
        self.timestamp = timestamp or datetime.now().isoformat()
        self.execution_success = execution_success
        self.rejection_reason = rejection_reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suggestion_id": self.suggestion_id,
            "features": [f.to_dict() for f in self.features],
            "outcome": self.outcome,
            "timestamp": self.timestamp,
            "execution_success": self.execution_success,
            "rejection_reason": self.rejection_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackRecord':
        """Create from dictionary."""
        return cls(
            suggestion_id=data.get("suggestion_id", ""),
            features=[SuggestionFeature.from_dict(f) for f in data.get("features", [])],
            outcome=data.get("outcome", "unknown"),
            timestamp=data.get("timestamp"),
            execution_success=data.get("execution_success"),
            rejection_reason=data.get("rejection_reason")
        )

class SuggestionFeedbackLearner:
    """
    Learns from user feedback on suggestions to improve future suggestions.
    Implements a feedback loop for continuous improvement of the autonomous epiphany system.
    """
    
    def __init__(self):
        """Initialize the feedback learner."""
        # Feedback records
        self.feedback_records: List[FeedbackRecord] = []
        
        # Feature importance weights
        self.feature_weights = {
            "app": 1.5,            # App context is important
            "action_type": 1.2,    # Type of action matters
            "time_of_day": 1.0,    # Time patterns matter
            "day_of_week": 0.8,    # Day patterns
            "complexity": 0.7,     # Complexity of suggestion
            "content_type": 1.1,   # Type of content being analyzed
            "suggestion_type": 1.3 # Category of suggestion
        }
        
        # Success metrics by feature
        self.feature_success_rates: Dict[str, Dict[Any, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(
                lambda: {"count": 0, "successes": 0, "rate": 0.0}
            )
        )
        
        # Time patterns
        self.time_patterns: Dict[str, Dict[str, int]] = {
            "hour": defaultdict(int),
            "day": defaultdict(int),
            "app_hour": defaultdict(int)
        }
        
        # Rejection reasons analysis
        self.rejection_reasons: Counter = Counter()
        
        # Metadata
        self.last_updated = datetime.now().isoformat()
        self.version = "1.0.0"
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Storage path
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'memory', 
            'suggestion_feedback_state.json'
        )
        
        # Load existing state if available
        self._load_state()
        
        logger.info("✅ SuggestionFeedbackLearner initialized successfully")
    
    async def process_suggestion_feedback(self, suggestion_id: str, outcome: str) -> bool:
        """
        Process feedback for a suggestion and learn from it.
        
        Args:
            suggestion_id: ID of the suggestion
            outcome: Feedback outcome ('accepted', 'rejected', 'executed', 'failed')
            
        Returns:
            bool: Success status
        """
        async with self._lock:
            try:
                # Get suggestion from memory
                if not SUGGESTION_MEMORY_AVAILABLE:
                    logger.error("❌ Suggestion memory not available")
                    return False
                
                memory = await get_suggestion_memory()
                suggestion = await memory.get_suggestion(suggestion_id)
                
                if not suggestion:
                    logger.warning(f"⚠️ Suggestion not found: {suggestion_id}")
                    return False
                
                # Extract features from suggestion
                features = self._extract_features(suggestion)
                
                # Get additional metadata based on outcome
                execution_success = None
                rejection_reason = None
                
                if outcome == 'executed':
                    execution_success = suggestion.get('execution_success', True)
                elif outcome == 'rejected':
                    rejection_reason = suggestion.get('rejection_reason')
                    if rejection_reason:
                        self.rejection_reasons[rejection_reason] += 1
                
                # Create feedback record
                feedback_record = FeedbackRecord(
                    suggestion_id=suggestion_id,
                    features=features,
                    outcome=outcome,
                    timestamp=datetime.now().isoformat(),
                    execution_success=execution_success,
                    rejection_reason=rejection_reason
                )
                
                # Add to records
                self.feedback_records.append(feedback_record)
                
                # Update feature success rates
                self._update_feature_success_rates(feedback_record)
                
                # Update time patterns
                self._update_time_patterns(feedback_record)
                
                # Save state asynchronously
                asyncio.create_task(self._save_state())
                
                logger.info(f"✅ Processed feedback for suggestion {suggestion_id}: {outcome}")
                
                # Apply learning to update suggestion memory preferences
                await self._update_suggestion_memory_preferences()
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Error processing suggestion feedback: {e}")
                logger.error(traceback.format_exc())
                return False
    
    async def get_suggestion_quality_score(self, suggestion: Dict[str, Any]) -> float:
        """
        Calculate quality score for a suggestion based on learned patterns.
        
        Args:
            suggestion: Suggestion data
            
        Returns:
            float: Quality score between 0.0 and 1.0
        """
        async with self._lock:
            try:
                # Extract features from suggestion
                features = self._extract_features(suggestion)
                
                # Base score (from suggestion confidence)
                base_score = suggestion.get('confidence', 0.7)
                
                # Feature-based adjustments
                feature_adjustment = 0.0
                total_weight = 0.0
                
                for feature in features:
                    feature_name = feature.name
                    feature_value = feature.value
                    feature_weight = feature.weight
                    
                    # Get success rate for this feature value
                    if feature_name in self.feature_success_rates and feature_value in self.feature_success_rates[feature_name]:
                        success_data = self.feature_success_rates[feature_name][feature_value]
                        if success_data["count"] >= 3:  # Minimum threshold for confidence
                            # Apply success rate as adjustment
                            adjustment = (success_data["rate"] - 0.5) * 2  # Scale from [-1, 1]
                            feature_adjustment += adjustment * feature_weight
                            total_weight += feature_weight
                
                # Apply adjustment
                if total_weight > 0:
                    normalized_adjustment = feature_adjustment / total_weight
                    adjusted_score = base_score + (normalized_adjustment * 0.3)  # Max 30% adjustment
                    final_score = max(0.0, min(1.0, adjusted_score))  # Clamp to [0, 1]
                else:
                    final_score = base_score
                
                # Apply time-based patterns
                time_adjustment = self._calculate_time_adjustment(suggestion)
                final_score = max(0.0, min(1.0, final_score + time_adjustment))
                
                logger.debug(f"Quality score for suggestion: {final_score:.2f} (base: {base_score:.2f})")
                return final_score
                
            except Exception as e:
                logger.error(f"❌ Error calculating suggestion quality: {e}")
                logger.error(traceback.format_exc())
                return suggestion.get('confidence', 0.5)  # Fallback to original confidence
    
    async def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get suggestions for improving the suggestion system based on feedback analysis.
        
        Returns:
            List of improvement suggestions
        """
        async with self._lock:
            improvements = []
            
            try:
                # Analyze rejection reasons
                if self.rejection_reasons:
                    top_reasons = self.rejection_reasons.most_common(3)
                    for reason, count in top_reasons:
                        if count >= 3:  # Threshold for significance
                            improvements.append({
                                "type": "rejection_pattern",
                                "reason": reason,
                                "count": count,
                                "suggestion": f"Address common rejection reason: '{reason}'"
                            })
                
                # Analyze time patterns
                hour_data = sorted(
                    [(hour, count) for hour, count in self.time_patterns["hour"].items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if hour_data and hour_data[0][1] >= 5:  # Threshold for significance
                    peak_hour = hour_data[0][0]
                    improvements.append({
                        "type": "time_pattern",
                        "hour": peak_hour,
                        "count": hour_data[0][1],
                        "suggestion": f"Optimize suggestion timing for peak hour {peak_hour}"
                    })
                
                # Analyze feature success rates
                for feature_name, feature_values in self.feature_success_rates.items():
                    high_success = []
                    low_success = []
                    
                    for value, metrics in feature_values.items():
                        if metrics["count"] >= 5:  # Threshold for significance
                            if metrics["rate"] >= 0.8:
                                high_success.append((value, metrics["rate"]))
                            elif metrics["rate"] <= 0.3:
                                low_success.append((value, metrics["rate"]))
                    
                    if high_success:
                        top_value, rate = max(high_success, key=lambda x: x[1])
                        improvements.append({
                            "type": "high_success_feature",
                            "feature": feature_name,
                            "value": top_value,
                            "rate": rate,
                            "suggestion": f"Prioritize suggestions with {feature_name}={top_value} (success rate: {rate:.0%})"
                        })
                    
                    if low_success:
                        bottom_value, rate = min(low_success, key=lambda x: x[1])
                        improvements.append({
                            "type": "low_success_feature",
                            "feature": feature_name,
                            "value": bottom_value,
                            "rate": rate,
                            "suggestion": f"Reduce suggestions with {feature_name}={bottom_value} (success rate: {rate:.0%})"
                        })
                
                return improvements
                
            except Exception as e:
                logger.error(f"❌ Error generating improvement suggestions: {e}")
                logger.error(traceback.format_exc())
                return []
    
    async def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        async with self._lock:
            total_records = len(self.feedback_records)
            if total_records == 0:
                return {
                    "total_records": 0,
                    "acceptance_rate": 0.0,
                    "execution_rate": 0.0,
                    "success_rate": 0.0
                }
            
            # Count by outcome
            outcomes = Counter(record.outcome for record in self.feedback_records)
            
            # Calculate rates
            acceptance_rate = (outcomes.get('accepted', 0) + outcomes.get('executed', 0)) / total_records
            execution_rate = outcomes.get('executed', 0) / total_records if total_records > 0 else 0.0
            
            # Success rate (among executed)
            success_count = sum(1 for record in self.feedback_records 
                              if record.outcome == 'executed' and record.execution_success)
            executed_count = outcomes.get('executed', 0)
            success_rate = success_count / executed_count if executed_count > 0 else 0.0
            
            # Get top features
            top_features = {}
            for feature_name, feature_values in self.feature_success_rates.items():
                if not feature_values:
                    continue
                
                top_features[feature_name] = sorted(
                    [(value, metrics["rate"]) for value, metrics in feature_values.items() 
                     if metrics["count"] >= 3],
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
            
            return {
                "total_records": total_records,
                "outcomes": dict(outcomes),
                "acceptance_rate": acceptance_rate,
                "execution_rate": execution_rate,
                "success_rate": success_rate,
                "top_features": top_features,
                "last_updated": self.last_updated
            }
    
    def _extract_features(self, suggestion: Dict[str, Any]) -> List[SuggestionFeature]:
        """Extract learning features from a suggestion."""
        features = []
        
        try:
            # App context
            if 'context' in suggestion and 'app' in suggestion['context']:
                app = suggestion['context']['app']
                features.append(SuggestionFeature("app", app, self.feature_weights.get("app", 1.0)))
            
            # Action types
            if 'action_items' in suggestion and suggestion['action_items']:
                action_types = [item.get('type') for item in suggestion['action_items'] if 'type' in item]
                if action_types:
                    primary_action = action_types[0]
                    features.append(SuggestionFeature(
                        "action_type", primary_action, self.feature_weights.get("action_type", 1.0)
                    ))
                    
                    # Complexity (number of actions)
                    complexity = "simple" if len(action_types) <= 2 else "complex"
                    features.append(SuggestionFeature(
                        "complexity", complexity, self.feature_weights.get("complexity", 0.7)
                    ))
            
            # Time features
            if 'timestamp' in suggestion:
                try:
                    timestamp = datetime.fromisoformat(suggestion['timestamp'])
                    hour = timestamp.hour
                    day = timestamp.strftime('%A')  # Day name
                    
                    time_of_day = "morning" if 5 <= hour < 12 else \
                                  "afternoon" if 12 <= hour < 17 else \
                                  "evening" if 17 <= hour < 22 else "night"
                    
                    features.append(SuggestionFeature(
                        "time_of_day", time_of_day, self.feature_weights.get("time_of_day", 1.0)
                    ))
                    features.append(SuggestionFeature(
                        "day_of_week", day, self.feature_weights.get("day_of_week", 0.8)
                    ))
                    
                    # App-time combination
                    if 'context' in suggestion and 'app' in suggestion['context']:
                        app_hour = f"{suggestion['context']['app']}_{time_of_day}"
                        features.append(SuggestionFeature("app_time", app_hour, 1.4))
                except:
                    pass
            
            # Content type
            if 'context' in suggestion and 'content_type' in suggestion['context']:
                content_type = suggestion['context']['content_type']
                features.append(SuggestionFeature(
                    "content_type", content_type, self.feature_weights.get("content_type", 1.1)
                ))
            
            # Suggestion type/category
            if 'title' in suggestion:
                title = suggestion['title'].lower()
                
                # Detect suggestion type from title
                suggestion_type = "unknown"
                if any(word in title for word in ["create", "add", "new"]):
                    suggestion_type = "creation"
                elif any(word in title for word in ["open", "launch", "start"]):
                    suggestion_type = "launch"
                elif any(word in title for word in ["search", "find", "lookup"]):
                    suggestion_type = "search"
                elif any(word in title for word in ["schedule", "calendar", "meeting"]):
                    suggestion_type = "calendar"
                elif any(word in title for word in ["email", "send", "message"]):
                    suggestion_type = "communication"
                
                features.append(SuggestionFeature(
                    "suggestion_type", suggestion_type, self.feature_weights.get("suggestion_type", 1.3)
                ))
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error extracting features: {e}")
            return features
    
    def _update_feature_success_rates(self, feedback: FeedbackRecord) -> None:
        """Update feature success rates based on feedback."""
        try:
            # Determine if this feedback is a success
            is_success = feedback.outcome in ['accepted', 'executed']
            
            # Update success rates for each feature
            for feature in feedback.features:
                feature_name = feature.name
                feature_value = feature.value
                
                # Get current stats
                stats = self.feature_success_rates[feature_name][feature_value]
                
                # Update stats
                stats["count"] += 1
                if is_success:
                    stats["successes"] += 1
                
                # Update success rate
                stats["rate"] = stats["successes"] / stats["count"]
                
                # Store updated stats
                self.feature_success_rates[feature_name][feature_value] = stats
                
        except Exception as e:
            logger.error(f"❌ Error updating feature success rates: {e}")
    
    def _update_time_patterns(self, feedback: FeedbackRecord) -> None:
        """Update time pattern statistics."""
        try:
            # Only track successful suggestions
            if feedback.outcome not in ['accepted', 'executed']:
                return
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(feedback.timestamp)
            hour = timestamp.hour
            day = timestamp.strftime('%A')  # Day name
            
            # Update hour and day counters
            self.time_patterns["hour"][str(hour)] += 1
            self.time_patterns["day"][day] += 1
            
            # Update app-specific hour patterns
            for feature in feedback.features:
                if feature.name == "app":
                    app = feature.value
                    self.time_patterns["app_hour"][f"{app}_{hour}"] += 1
                    break
                
        except Exception as e:
            logger.error(f"❌ Error updating time patterns: {e}")
    
    def _calculate_time_adjustment(self, suggestion: Dict[str, Any]) -> float:
        """Calculate time-based adjustment for a suggestion."""
        try:
            # Default adjustment
            adjustment = 0.0
            
            # Get current time
            now = datetime.now()
            current_hour = now.hour
            current_day = now.strftime('%A')
            
            # Check if this hour is a preferred hour
            hour_counts = self.time_patterns["hour"]
            total_hour_suggestions = sum(hour_counts.values())
            
            if total_hour_suggestions >= 10:  # Enough data to be significant
                if str(current_hour) in hour_counts:
                    hour_ratio = hour_counts[str(current_hour)] / total_hour_suggestions
                    if hour_ratio > 0.2:  # Significantly preferred hour
                        adjustment += 0.1
                    elif hour_ratio < 0.05:  # Significantly non-preferred hour
                        adjustment -= 0.1
            
            # Check app-time pattern
            if 'context' in suggestion and 'app' in suggestion['context']:
                app = suggestion['context']['app']
                app_hour_key = f"{app}_{current_hour}"
                
                if app_hour_key in self.time_patterns["app_hour"] and self.time_patterns["app_hour"][app_hour_key] >= 3:
                    adjustment += 0.15
            
            return adjustment
            
        except Exception as e:
            logger.error(f"❌ Error calculating time adjustment: {e}")
            return 0.0
    
    async def _update_suggestion_memory_preferences(self) -> None:
        """Update suggestion memory preferences based on learned patterns."""
        try:
            if not SUGGESTION_MEMORY_AVAILABLE:
                return
            
            memory = await get_suggestion_memory()
            
            # Get current user preferences
            current_prefs = await memory.get_user_preferences()
            
            # Apply learned preferences
            updates = {}
            
            # Process app preferences
            accepted_apps = set()
            rejected_apps = set()
            
            # Find apps with strong acceptance patterns
            for app, metrics in self.feature_success_rates.get("app", {}).items():
                if metrics["count"] >= 3:  # Minimum threshold
                    if metrics["rate"] >= 0.7:
                        accepted_apps.add(app)
                    elif metrics["rate"] <= 0.3:
                        rejected_apps.add(app)
            
            # Process time preferences
            preferred_times = {}
            hour_data = sorted(
                [(hour, count) for hour, count in self.time_patterns["hour"].items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            if hour_data:
                for hour, count in hour_data[:3]:  # Top 3 hours
                    if count >= 3:  # Minimum threshold
                        preferred_times[hour] = count
            
            # Process suggestion type preferences
            suggestion_types = {}
            for stype, metrics in self.feature_success_rates.get("suggestion_type", {}).items():
                if metrics["count"] >= 3:
                    suggestion_types[stype] = metrics["rate"]
            
            # Apply updates to memory
            # This would typically involve some internal API call to the memory system
            # For now, we'll log the updates
            logger.info(f"✅ Would update memory preferences with: {len(accepted_apps)} accepted apps, "
                      f"{len(rejected_apps)} rejected apps, {len(preferred_times)} preferred times")
            
        except Exception as e:
            logger.error(f"❌ Error updating suggestion memory preferences: {e}")
    
    def _load_state(self) -> None:
        """Load feedback learner state from file."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    state = json.load(f)
                
                # Load version and metadata
                self.version = state.get('version', '1.0.0')
                self.last_updated = state.get('last_updated', datetime.now().isoformat())
                
                # Load feedback records
                self.feedback_records = [
                    FeedbackRecord.from_dict(record) 
                    for record in state.get('feedback_records', [])
                ]
                
                # Load feature weights
                self.feature_weights = state.get('feature_weights', self.feature_weights)
                
                # Load feature success rates (with defaultdict conversion)
                raw_rates = state.get('feature_success_rates', {})
                for feature_name, values in raw_rates.items():
                    for value, metrics in values.items():
                        self.feature_success_rates[feature_name][value] = metrics
                
                # Load time patterns (with defaultdict conversion)
                raw_patterns = state.get('time_patterns', {})
                for pattern_type, values in raw_patterns.items():
                    for key, count in values.items():
                        self.time_patterns[pattern_type][key] = count
                
                # Load rejection reasons
                self.rejection_reasons = Counter(state.get('rejection_reasons', {}))
                
                logger.info(f"✅ Loaded feedback learner state: {len(self.feedback_records)} records")
            else:
                logger.info("🆕 No existing feedback learner state found, starting fresh")
                
        except Exception as e:
            logger.error(f"❌ Error loading feedback learner state: {e}")
            logger.error(traceback.format_exc())
    
    async def _save_state(self) -> None:
        """Save feedback learner state to file."""
        try:
            # Update timestamp
            self.last_updated = datetime.now().isoformat()
            
            # Convert defaultdict to regular dict for JSON serialization
            serialized_rates = {}
            for feature_name, values in self.feature_success_rates.items():
                serialized_rates[feature_name] = {str(k): v for k, v in values.items()}
            
            serialized_patterns = {}
            for pattern_type, values in self.time_patterns.items():
                serialized_patterns[pattern_type] = {str(k): v for k, v in values.items()}
            
            # Build state object
            state = {
                'version': self.version,
                'last_updated': self.last_updated,
                'feedback_records': [record.to_dict() for record in self.feedback_records],
                'feature_weights': self.feature_weights,
                'feature_success_rates': serialized_rates,
                'time_patterns': serialized_patterns,
                'rejection_reasons': dict(self.rejection_reasons)
            }
            
            # Save to temporary file first, then rename for atomicity
            temp_path = f"{self.storage_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Atomic replacement
            os.replace(temp_path, self.storage_path)
            
            logger.debug(f"✅ Saved feedback learner state")
            
        except Exception as e:
            logger.error(f"❌ Error saving feedback learner state: {e}")
            logger.error(traceback.format_exc())

# Singleton instance
_feedback_learner_instance = None

async def get_feedback_learner() -> SuggestionFeedbackLearner:
    """Get or create the global feedback learner instance."""
    global _feedback_learner_instance
    
    if _feedback_learner_instance is None:
        _feedback_learner_instance = SuggestionFeedbackLearner()
    
    return _feedback_learner_instance

# Example usage
if __name__ == "__main__":
    async def test_feedback_learner():
        """Test the feedback learner system."""
        # Get feedback learner instance
        learner = await get_feedback_learner()
        
        # Check if suggestion memory is available
        if SUGGESTION_MEMORY_AVAILABLE:
            # Get suggestion memory
            memory = await get_suggestion_memory()
            
            # Create test suggestion
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
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Add suggestion to memory
            suggestion_id = await memory.add_suggestion(test_suggestion)
            print(f"Added test suggestion with ID: {suggestion_id}")
            
            # Process feedback for the suggestion
            await learner.process_suggestion_feedback(suggestion_id, "accepted")
            print("Processed feedback")
            
            # Get feedback stats
            stats = await learner.get_feedback_stats()
            print(f"Feedback stats: {stats}")
            
            # Get improvement suggestions
            improvements = await learner.get_improvement_suggestions()
            print(f"Improvement suggestions: {improvements}")
            
        else:
            print("Suggestion memory not available for testing")
    
    # Run the test
    asyncio.run(test_feedback_learner())