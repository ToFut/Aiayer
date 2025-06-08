#!/usr/bin/env python3
"""
Enhanced Suggestion Detector with ML-based Pattern Recognition

This module enhances the system's ability to detect potential automation opportunities
by using machine learning techniques to identify patterns in user behavior and screen content
without relying on explicit markers.

It integrates with the existing memory system architecture to provide a seamless experience.
"""

import asyncio
import json
import logging
import os
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
import traceback
import numpy as np
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/suggestion_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/memory', exist_ok=True)

# Import memory system components (dynamic imports to avoid circular references)
try:
    from memory.memory_system import MemorySystem
except ImportError:
    logger.warning("⚠️ Memory system module not available directly, will access through methods")

class PatternFeatures:
    """Feature extraction for pattern recognition."""
    
    @staticmethod
    def extract_features_from_screen(screen_content: str) -> Dict[str, Any]:
        """Extract features from screen content."""
        features = {}
        
        # Content length
        features["content_length"] = len(screen_content)
        
        # Keyword presence
        features["has_email"] = "email" in screen_content.lower() or "@" in screen_content
        features["has_date"] = bool(re.search(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b', screen_content.lower()))
        features["has_time"] = bool(re.search(r'\b\d{1,2}:\d{2}\b', screen_content))
        features["has_url"] = bool(re.search(r'https?://\S+', screen_content))
        features["has_phone"] = bool(re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', screen_content))
        features["has_address"] = bool(re.search(r'\b\d+\s+[a-zA-Z]+\s+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|place|pl|court|ct)\b', screen_content.lower()))
        
        # Action indicators
        features["has_action_words"] = bool(re.search(r'\b(?:schedule|book|reserve|create|add|send|review|complete|submit|buy|purchase|order|register|sign up|login)\b', screen_content.lower()))
        features["has_list_markers"] = bool(re.search(r'(?:\d+\.\s|\*\s|-\s|\[\s?\]|\☐|\☑|\✓)', screen_content))
        
        # Form elements
        features["has_form_elements"] = bool(re.search(r'\b(?:form|field|input|button|submit|select|option|checkbox|radio)\b', screen_content.lower()))
        
        # Interface components
        features["has_search"] = bool(re.search(r'\b(?:search|find|query|lookup)\b', screen_content.lower()))
        features["has_menu"] = bool(re.search(r'\b(?:menu|navigation|dropdown|list|options)\b', screen_content.lower()))
        
        return features
    
    @staticmethod
    def extract_features_from_app(app_name: str, app_history: List[str]) -> Dict[str, Any]:
        """Extract features from application context."""
        features = {}
        
        # Categorize app
        productivity_apps = {"word", "excel", "powerpoint", "docs", "sheets", "slides", "notion", "evernote", "onenote"}
        communication_apps = {"mail", "outlook", "gmail", "messages", "slack", "teams", "zoom", "meet", "whatsapp"}
        browser_apps = {"chrome", "safari", "firefox", "edge", "opera", "brave"}
        media_apps = {"spotify", "netflix", "youtube", "vlc", "itunes", "photos", "gallery"}
        
        app_lower = app_name.lower()
        features["is_productivity_app"] = any(app in app_lower for app in productivity_apps)
        features["is_communication_app"] = any(app in app_lower for app in communication_apps)
        features["is_browser_app"] = any(app in app_lower for app in browser_apps)
        features["is_media_app"] = any(app in app_lower for app in media_apps)
        
        # App switching patterns
        if app_history:
            features["app_switch_count"] = len(app_history)
            features["unique_apps"] = len(set(app_history))
            features["repeated_app"] = any(app_history.count(app) > 2 for app in set(app_history))
        else:
            features["app_switch_count"] = 0
            features["unique_apps"] = 0
            features["repeated_app"] = False
        
        return features
    
    @staticmethod
    def extract_features_from_activity(activity_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from user activity history."""
        features = {}
        
        if not activity_history:
            return {
                "action_count": 0,
                "repetitive_actions": False,
                "has_scroll": False,
                "has_click": False,
                "has_type": False,
                "has_navigation": False
            }
        
        # Action counts
        actions = [activity.get("action", "") for activity in activity_history if isinstance(activity, dict)]
        action_counter = Counter(actions)
        
        features["action_count"] = len(actions)
        features["repetitive_actions"] = any(count > 2 for count in action_counter.values())
        
        # Action types
        features["has_scroll"] = any("scroll" in action.lower() for action in actions)
        features["has_click"] = any("click" in action.lower() for action in actions)
        features["has_type"] = any(word in " ".join(actions).lower() for word in ["type", "input", "enter", "write"])
        features["has_navigation"] = any(word in " ".join(actions).lower() for word in ["navigate", "open", "go to", "browse"])
        
        # Time patterns
        if len(activity_history) > 1:
            try:
                timestamps = []
                for activity in activity_history:
                    if isinstance(activity, dict) and "timestamp" in activity:
                        try:
                            if isinstance(activity["timestamp"], str):
                                timestamps.append(datetime.fromisoformat(activity["timestamp"]))
                            elif isinstance(activity["timestamp"], (int, float)):
                                timestamps.append(datetime.fromtimestamp(activity["timestamp"]))
                        except (ValueError, TypeError):
                            pass
                
                if len(timestamps) > 1:
                    # Calculate time intervals between activities
                    intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() 
                                for i in range(1, len(timestamps))]
                    
                    features["avg_interval"] = sum(intervals) / len(intervals)
                    features["rapid_actions"] = any(interval < 2.0 for interval in intervals)
                    features["consistent_tempo"] = (max(intervals) - min(intervals)) < 5.0
            except Exception as e:
                logger.error(f"Error calculating time patterns: {e}")
        
        return features

class MLSuggestionDetector:
    """
    ML-based suggestion detector that identifies potential automation opportunities
    by recognizing patterns in screen content and user behavior.
    """
    
    def __init__(self, memory_system=None):
        """
        Initialize the ML suggestion detector.
        
        Args:
            memory_system: Reference to the memory system for context access
        """
        self.memory_system = memory_system
        self.logger = logger
        
        # Pattern recognition parameters
        self.min_confidence_threshold = 0.65
        self.high_confidence_threshold = 0.85
        
        # Pattern definitions (can be updated/learned over time)
        self.pattern_weights = {
            # Screen content patterns
            "has_action_words": 0.15,
            "has_list_markers": 0.12,
            "has_form_elements": 0.14,
            "has_date": 0.10,
            "has_time": 0.08,
            "has_email": 0.07,
            
            # App context patterns
            "is_productivity_app": 0.08,
            "is_communication_app": 0.10,
            "is_browser_app": 0.06,
            
            # Activity patterns
            "repetitive_actions": 0.25,
            "rapid_actions": 0.20,
            "consistent_tempo": 0.15,
            "has_scroll": 0.05,
            "has_click": 0.08,
            "has_type": 0.10,
            "has_navigation": 0.07
        }
        
        # Pattern categories for suggestion types
        self.suggestion_categories = {
            "calendar_event": {
                "patterns": ["has_date", "has_time", "is_communication_app", "has_action_words"],
                "threshold": 0.7,
                "title_template": "Schedule event on {date} at {time}",
                "description_template": "I noticed a potential event in your {app_name}"
            },
            "form_completion": {
                "patterns": ["has_form_elements", "is_browser_app", "has_type"],
                "threshold": 0.7,
                "title_template": "Complete form in {app_name}",
                "description_template": "I can help you complete this form automatically"
            },
            "repeated_task": {
                "patterns": ["repetitive_actions", "consistent_tempo", "has_click"],
                "threshold": 0.75,
                "title_template": "Automate repetitive task",
                "description_template": "I noticed you're performing the same actions repeatedly"
            },
            "data_extraction": {
                "patterns": ["has_list_markers", "is_productivity_app", "has_scroll"],
                "threshold": 0.7,
                "title_template": "Extract data from {app_name}",
                "description_template": "I can help you extract this data into a structured format"
            }
        }
        
        # Learning parameters
        self.feature_importance = {}
        self.successful_patterns = Counter()
        self.rejected_patterns = Counter()
        
        # Detection history for learning
        self.detection_history = []
        self.max_history_size = 100
        
        self.logger.info("✅ Enhanced ML Suggestion Detector initialized")
    
    async def detect_suggestion_opportunities(
        self, 
        screen_content: str, 
        active_app: str,
        app_history: Optional[List[str]] = None,
        activity_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Detect suggestion opportunities using ML-based pattern recognition.
        
        Args:
            screen_content: Current screen content text
            active_app: Current active application
            app_history: History of recently used applications
            activity_history: History of user activities
            
        Returns:
            Dict containing detection results
        """
        try:
            start_time = time.time()
            
            # Initialize histories if not provided
            app_history = app_history or []
            activity_history = activity_history or []
            
            # Extract features
            screen_features = PatternFeatures.extract_features_from_screen(screen_content)
            app_features = PatternFeatures.extract_features_from_app(active_app, app_history)
            activity_features = PatternFeatures.extract_features_from_activity(activity_history)
            
            # Combine all features
            all_features = {**screen_features, **app_features, **activity_features}
            
            # Calculate pattern match scores
            pattern_scores = self._calculate_pattern_scores(all_features)
            
            # Determine overall confidence and best category
            overall_confidence, best_category = self._evaluate_pattern_confidence(pattern_scores)
            
            # Create detection result
            detection_result = {
                "has_suggestion_opportunity": overall_confidence >= self.min_confidence_threshold,
                "confidence": overall_confidence,
                "category": best_category,
                "features": all_features,
                "pattern_scores": pattern_scores,
                "processing_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # If we have a valid suggestion opportunity, enhance it with details
            if detection_result["has_suggestion_opportunity"] and best_category:
                detection_result.update(
                    self._create_enhanced_suggestion(
                        best_category, 
                        overall_confidence,
                        screen_content,
                        active_app,
                        all_features
                    )
                )
            
            # Store detection for learning
            self._store_detection_result(detection_result)
            
            return detection_result
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting suggestion opportunities: {e}")
            self.logger.error(traceback.format_exc())
            
            return {
                "has_suggestion_opportunity": False,
                "error": str(e),
                "confidence": 0.0,
                "processing_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_pattern_scores(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scores for each pattern category based on features."""
        category_scores = {}
        
        for category, config in self.suggestion_categories.items():
            # Get relevant patterns for this category
            relevant_patterns = config["patterns"]
            
            # Calculate match score based on presence of relevant features
            score = 0.0
            matched_patterns = []
            
            for pattern in relevant_patterns:
                if pattern in features and features[pattern]:
                    pattern_weight = self.pattern_weights.get(pattern, 0.1)
                    score += pattern_weight
                    matched_patterns.append(pattern)
            
            # Normalize score based on number of patterns
            if relevant_patterns:
                normalized_score = score / sum(self.pattern_weights.get(p, 0.1) for p in relevant_patterns)
                category_scores[category] = min(1.0, normalized_score)
            else:
                category_scores[category] = 0.0
        
        return category_scores
    
    def _evaluate_pattern_confidence(self, pattern_scores: Dict[str, float]) -> Tuple[float, Optional[str]]:
        """Evaluate overall confidence and determine best suggestion category."""
        if not pattern_scores:
            return 0.0, None
        
        # Find category with highest score
        best_category = max(pattern_scores.items(), key=lambda x: x[1])
        category_name = best_category[0]
        category_score = best_category[1]
        
        # Check if score exceeds category threshold
        category_threshold = self.suggestion_categories[category_name]["threshold"]
        if category_score < category_threshold:
            return category_score, None
        
        return category_score, category_name
    
    def _create_enhanced_suggestion(
        self, 
        category: str, 
        confidence: float,
        screen_content: str,
        active_app: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an enhanced suggestion based on the detected category."""
        category_config = self.suggestion_categories[category]
        
        # Extract potential relevant information from screen content
        extracted_info = self._extract_relevant_info(category, screen_content)
        
        # Create title and description using templates
        title_template = category_config["title_template"]
        description_template = category_config["description_template"]
        
        # Fill in template variables
        title = title_template.format(
            app_name=active_app,
            date=extracted_info.get("date", "the specified date"),
            time=extracted_info.get("time", "the specified time")
        )
        
        description = description_template.format(
            app_name=active_app
        )
        
        # Generate action items based on category
        action_items = self._generate_action_items(category, extracted_info, active_app)
        
        # Create suggestion
        suggestion = {
            "title": title,
            "description": description,
            "confidence": confidence,
            "category": category,
            "action_items": action_items,
            "context": {
                "source": "ml_detector",
                "app": active_app,
                "extracted_info": extracted_info,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return suggestion
    
    def _extract_relevant_info(self, category: str, screen_content: str) -> Dict[str, Any]:
        """Extract relevant information from screen content based on category."""
        info = {}
        
        if category == "calendar_event":
            # Extract date
            date_match = re.search(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b', screen_content.lower())
            if date_match:
                info["date"] = date_match.group(0).capitalize()
            else:
                date_match = re.search(r'\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b', screen_content)
                if date_match:
                    info["date"] = date_match.group(0)
            
            # Extract time
            time_match = re.search(r'\b(\d{1,2}):(\d{2})(?:\s*(am|pm))?\b', screen_content.lower())
            if time_match:
                info["time"] = time_match.group(0)
        
        elif category == "form_completion":
            # Extract form fields
            field_matches = re.finditer(r'\b(?:name|email|phone|address|username|password)\b', screen_content.lower())
            fields = [match.group(0) for match in field_matches]
            if fields:
                info["fields"] = fields
        
        elif category == "data_extraction":
            # Extract data structure type
            if "table" in screen_content.lower():
                info["data_type"] = "table"
            elif any(marker in screen_content for marker in ["* ", "- ", "1. "]):
                info["data_type"] = "list"
            else:
                info["data_type"] = "text"
        
        return info
    
    def _generate_action_items(
        self, 
        category: str, 
        extracted_info: Dict[str, Any],
        active_app: str
    ) -> List[Dict[str, Any]]:
        """Generate action items based on category and extracted information."""
        action_items = []
        
        if category == "calendar_event":
            # Calendar event action items
            action_items = [
                {"type": "open_app", "target": "Calendar"},
                {"type": "click", "target": "New Event"}
            ]
            
            # Add title if available
            if "title" in extracted_info:
                action_items.append(
                    {"type": "input_text", "target": "Title", "value": extracted_info["title"]}
                )
            
            # Add date if available
            if "date" in extracted_info:
                action_items.append(
                    {"type": "input_text", "target": "Date", "value": extracted_info["date"]}
                )
            
            # Add time if available
            if "time" in extracted_info:
                action_items.append(
                    {"type": "input_text", "target": "Time", "value": extracted_info["time"]}
                )
        
        elif category == "form_completion":
            # Form completion action items
            if "fields" in extracted_info:
                for field in extracted_info["fields"]:
                    action_items.append(
                        {"type": "input_text", "target": field.capitalize()}
                    )
            else:
                # Generic form action items
                action_items = [
                    {"type": "click", "target": "Form Field"},
                    {"type": "input_text", "target": "Selected Field"}
                ]
        
        elif category == "repeated_task":
            # Repeated task action items (generic)
            action_items = [
                {"type": "click", "target": "Target Element"},
                {"type": "wait", "duration": "0.5"},
                {"type": "click", "target": "Next Element"}
            ]
        
        elif category == "data_extraction":
            # Data extraction action items
            data_type = extracted_info.get("data_type", "text")
            
            if data_type == "table":
                action_items = [
                    {"type": "select_all", "target": "Table"},
                    {"type": "copy", "target": "Selected Content"},
                    {"type": "open_app", "target": "Excel"},
                    {"type": "paste", "target": "Spreadsheet"}
                ]
            else:
                action_items = [
                    {"type": "select_all", "target": "Content"},
                    {"type": "copy", "target": "Selected Content"},
                    {"type": "extract_info", "from": "clipboard"}
                ]
        
        return action_items
    
    def _store_detection_result(self, detection_result: Dict[str, Any]) -> None:
        """Store detection result for learning."""
        try:
            # Add to history
            self.detection_history.append(detection_result)
            
            # Trim history if needed
            if len(self.detection_history) > self.max_history_size:
                self.detection_history = self.detection_history[-self.max_history_size:]
        except Exception as e:
            self.logger.error(f"Error storing detection result: {e}")
    
    async def update_from_feedback(
        self, 
        suggestion_id: str, 
        accepted: bool, 
        success: Optional[bool] = None
    ) -> bool:
        """
        Update pattern weights based on user feedback.
        
        Args:
            suggestion_id: ID of the suggestion
            accepted: Whether the suggestion was accepted by the user
            success: Whether the execution was successful (if applicable)
            
        Returns:
            success: Whether the update was successful
        """
        try:
            # Get suggestion memory to retrieve the suggestion
            try:
                from memory.suggestion_memory import get_suggestion_memory
                memory = await get_suggestion_memory()
            except ImportError:
                self.logger.error("❌ Could not import suggestion memory")
                return False
            
            # Get the suggestion
            suggestion = await memory.get_suggestion(suggestion_id)
            if not suggestion:
                self.logger.warning(f"⚠️ Could not find suggestion {suggestion_id} for feedback")
                return False
            
            # Extract pattern information
            category = suggestion.get("category")
            features = suggestion.get("features", {})
            
            if not category or not features:
                self.logger.warning(f"⚠️ Suggestion {suggestion_id} missing category or features")
                return False
            
            # Update pattern statistics
            patterns = self.suggestion_categories.get(category, {}).get("patterns", [])
            
            if accepted:
                # Increase weights for successful patterns
                for pattern in patterns:
                    if pattern in features and features[pattern]:
                        self.successful_patterns[pattern] += 1
                        # Gradually increase weight
                        self.pattern_weights[pattern] *= 1.05
                        self.pattern_weights[pattern] = min(0.5, self.pattern_weights[pattern])
            else:
                # Decrease weights for rejected patterns
                for pattern in patterns:
                    if pattern in features and features[pattern]:
                        self.rejected_patterns[pattern] += 1
                        # Gradually decrease weight
                        self.pattern_weights[pattern] *= 0.95
                        self.pattern_weights[pattern] = max(0.01, self.pattern_weights[pattern])
            
            # If execution feedback is provided, adjust category threshold
            if success is not None:
                if success:
                    # Lower threshold slightly for successful categories
                    current_threshold = self.suggestion_categories[category]["threshold"]
                    self.suggestion_categories[category]["threshold"] = max(
                        0.5, current_threshold * 0.98
                    )
                else:
                    # Raise threshold slightly for unsuccessful categories
                    current_threshold = self.suggestion_categories[category]["threshold"]
                    self.suggestion_categories[category]["threshold"] = min(
                        0.95, current_threshold * 1.02
                    )
            
            self.logger.info(f"✅ Updated pattern weights based on feedback for {suggestion_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating from feedback: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get current pattern statistics."""
        stats = {
            "pattern_weights": self.pattern_weights,
            "successful_patterns": dict(self.successful_patterns),
            "rejected_patterns": dict(self.rejected_patterns),
            "category_thresholds": {
                category: config["threshold"]
                for category, config in self.suggestion_categories.items()
            }
        }
        
        return stats

# Singleton instance
_detector_instance = None

async def get_ml_suggestion_detector(memory_system=None) -> MLSuggestionDetector:
    """Get or create the global ML suggestion detector instance."""
    global _detector_instance
    
    if _detector_instance is None:
        _detector_instance = MLSuggestionDetector(memory_system)
    
    return _detector_instance

# Example usage
if __name__ == "__main__":
    async def test_detector():
        # Create test screen content
        screen_content = """
        Inbox - user@example.com - Mail
        
        From: manager@example.com
        Subject: Team Meeting Thursday
        
        Hi team,
        
        Let's schedule a team meeting for Thursday at 3pm to discuss the new project timeline.
        
        Please come prepared with your status updates and any questions you may have.
        
        Best regards,
        Manager
        """
        
        active_app = "Mail"
        
        # Sample app history
        app_history = ["Chrome", "Slack", "Mail", "Calendar", "Mail"]
        
        # Sample activity history
        activity_history = [
            {"action": "open_app", "app": "Mail", "timestamp": "2025-06-06T14:30:00"},
            {"action": "click", "target": "Inbox", "timestamp": "2025-06-06T14:30:05"},
            {"action": "click", "target": "Email", "timestamp": "2025-06-06T14:30:10"},
            {"action": "scroll", "direction": "down", "timestamp": "2025-06-06T14:30:15"}
        ]
        
        # Get detector
        detector = await get_ml_suggestion_detector()
        
        # Detect suggestions
        result = await detector.detect_suggestion_opportunities(
            screen_content=screen_content,
            active_app=active_app,
            app_history=app_history,
            activity_history=activity_history
        )
        
        # Print results
        print(json.dumps(result, indent=2))
    
    # Run the test
    asyncio.run(test_detector())