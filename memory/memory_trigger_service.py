"""
Memory Trigger Service - Proactive Suggestion and Action Execution System

This module provides a service that monitors memory for patterns and opportunities
to provide proactive suggestions to the user, with the ability to execute actions
in agent mode upon user approval.

Features:
- Memory pattern monitoring and detection
- Rule-based trigger system for suggestions
- Push notification to chat interface
- Action execution in agent mode upon approval
- Performance tracking and metrics

Integration points:
- Semantic search for pattern detection
- Task memory for context and history
- Suggest mode for generating suggestions
- Brain router for chat interface integration and execution
"""

import asyncio
import json
import time
import logging
import threading
import re
import uuid
import os
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import weakref


# Chat mode enum for brain router compatibility
class ChatMode(Enum):
    """Chat mode enum to match what's used in the brain router"""
    ASK = "ASK"
    SUGGEST = "SUGGEST"
    AGENT = "AGENT"
    GENERAL = "GENERAL"

# Try to import the necessary components
try:
    from memory.semantic_search_agent import semantic_search_agent, search_memories
    from memory.task_memory_manager import task_memory_manager
    from brain.handlers.suggest_mode_handler import suggest_mode_handler, SuggestModeAnalyzer
    from brain.core.brain_router import BrainRouter, BrainResponse, ChatRequest, ChatMode, Priority
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: Memory Trigger Service dependencies not fully available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_trigger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_trigger")

class TriggerType(Enum):
    """Types of triggers that can generate suggestions"""
    APPLICATION_PATTERN = "application_pattern"
    ACTIVITY_SEQUENCE = "activity_sequence"
    TIME_BASED = "time_based"
    SEMANTIC_PATTERN = "semantic_pattern"
    TASK_COMPLETION = "task_completion"
    CONTENT_BASED = "content_based"
    USER_BEHAVIOR = "user_behavior"

class TriggerPriority(Enum):
    """Priority levels for trigger notifications"""
    HIGH = "high"       # Urgent, should be shown immediately
    MEDIUM = "medium"   # Important but not urgent
    LOW = "low"         # Informational only

class TriggerStatus(Enum):
    """Status of a trigger notification"""
    PENDING = "pending"       # Created but not yet shown
    DELIVERED = "delivered"   # Shown to user
    ACCEPTED = "accepted"     # User accepted suggestion
    EXECUTING = "executing"   # Action being executed
    COMPLETED = "completed"   # Action completed
    DISMISSED = "dismissed"   # User dismissed suggestion
    EXPIRED = "expired"       # Suggestion expired without action
    FAILED = "failed"         # Action execution failed

@dataclass
class TriggerRule:
    """Rule for when to trigger a suggestion"""
    id: str
    name: str
    description: str
    trigger_type: TriggerType
    priority: TriggerPriority
    pattern: Union[str, Dict[str, Any]]  # Regex pattern or complex pattern definition
    confidence_threshold: float = 0.7
    cooldown_seconds: int = 3600  # Prevent repeated triggers
    enabled: bool = True
    action_template: Optional[Dict[str, Any]] = None
    contexts: List[str] = field(default_factory=list)  # Contexts where this rule applies
    max_triggers_per_day: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "pattern": self.pattern,
            "confidence_threshold": self.confidence_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "enabled": self.enabled,
            "action_template": self.action_template,
            "contexts": self.contexts,
            "max_triggers_per_day": self.max_triggers_per_day
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerRule':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            trigger_type=TriggerType(data["trigger_type"]),
            priority=TriggerPriority(data["priority"]),
            pattern=data["pattern"],
            confidence_threshold=data["confidence_threshold"],
            cooldown_seconds=data["cooldown_seconds"],
            enabled=data["enabled"],
            action_template=data.get("action_template"),
            contexts=data.get("contexts", []),
            max_triggers_per_day=data.get("max_triggers_per_day", 5)
        )

@dataclass
class TriggerEvent:
    """An event that triggered a suggestion"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: TriggerStatus = TriggerStatus.PENDING
    priority: TriggerPriority = TriggerPriority.MEDIUM
    confidence: float = 0.0
    title: str = ""
    description: str = ""
    suggestion: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    memory_references: List[str] = field(default_factory=list)
    action_plan: Optional[Dict[str, Any]] = None
    expiration_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "context": self.context,
            "memory_references": self.memory_references,
            "action_plan": self.action_plan,
            "expiration_time": self.expiration_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerEvent':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            rule_id=data["rule_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=TriggerStatus(data["status"]),
            priority=TriggerPriority(data["priority"]),
            confidence=data["confidence"],
            title=data["title"],
            description=data["description"],
            suggestion=data["suggestion"],
            context=data.get("context", {}),
            memory_references=data.get("memory_references", []),
            action_plan=data.get("action_plan"),
            expiration_time=data.get("expiration_time")
        )

class MemoryPatternDetector:
    """Detects patterns in memory that could trigger suggestions"""
    
    def __init__(self):
        """Initialize pattern detector"""
        self.suggestion_analyzer = SuggestModeAnalyzer() if DEPENDENCIES_AVAILABLE else None
        self.last_check_time = time.time()
        self.recent_applications = set()
        self.recent_activities = []
        
    async def detect_patterns(self, memory_items: List[Dict[str, Any]], rules: List[TriggerRule]) -> List[Dict[str, Any]]:
        """Detect patterns in memory items that match trigger rules"""
        try:
            current_time = time.time()
            detected_patterns = []
            
            # Process memory items
            await self._process_memory_items(memory_items)
            
            # Check each rule against memory
            for rule in rules:
                if not rule.enabled:
                    continue
                    
                # Skip if rule is in cooldown
                if self._is_rule_in_cooldown(rule.id):
                    continue
                
                # Apply pattern detection based on rule type
                match rule.trigger_type:
                    case TriggerType.APPLICATION_PATTERN:
                        patterns = await self._detect_application_patterns(rule)
                    case TriggerType.ACTIVITY_SEQUENCE:
                        patterns = await self._detect_activity_sequences(rule)
                    case TriggerType.TIME_BASED:
                        patterns = await self._detect_time_based_patterns(rule)
                    case TriggerType.SEMANTIC_PATTERN:
                        patterns = await self._detect_semantic_patterns(rule, memory_items)
                    case TriggerType.TASK_COMPLETION:
                        patterns = await self._detect_task_completion_patterns(rule)
                    case TriggerType.CONTENT_BASED:
                        patterns = await self._detect_content_patterns(rule, memory_items)
                    case TriggerType.USER_BEHAVIOR:
                        patterns = await self._detect_user_behavior_patterns(rule)
                    case _:
                        patterns = []
                
                # Add detected patterns with rule information
                for pattern in patterns:
                    if pattern["confidence"] >= rule.confidence_threshold:
                        pattern["rule"] = rule
                        detected_patterns.append(pattern)
            
            self.last_check_time = current_time
            return detected_patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    async def _process_memory_items(self, memory_items: List[Dict[str, Any]]) -> None:
        """Process memory items to update state for pattern detection"""
        try:
            # Extract applications from memory
            for item in memory_items:
                if "current_application" in item:
                    self.recent_applications.add(item["current_application"])
                
                # Extract activities from memory
                if "searchable_text" in item and len(item["searchable_text"]) > 10:
                    self.recent_activities.append({
                        "timestamp": item.get("timestamp", time.time()),
                        "activity": item["searchable_text"]
                    })
            
            # Keep only the last 20 activities
            self.recent_activities = sorted(self.recent_activities, 
                                           key=lambda x: x["timestamp"], 
                                           reverse=True)[:20]
                
        except Exception as e:
            logger.error(f"Error processing memory items: {e}")
    
    def _is_rule_in_cooldown(self, rule_id: str) -> bool:
        """Check if a rule is in cooldown period"""
        # This would check a persistent store of recently triggered rules
        # For now, just return False as placeholder
        return False
    
    async def _detect_application_patterns(self, rule: TriggerRule) -> List[Dict[str, Any]]:
        """Detect patterns based on application usage"""
        try:
            patterns = []
            
            if isinstance(rule.pattern, str):
                # Simple regex pattern
                for app in self.recent_applications:
                    if re.search(rule.pattern, app, re.IGNORECASE):
                        patterns.append({
                            "type": TriggerType.APPLICATION_PATTERN.value,
                            "confidence": 0.85,
                            "context": {"application": app},
                            "description": f"Detected application pattern: {app}"
                        })
            elif isinstance(rule.pattern, dict) and "applications" in rule.pattern:
                # List of applications
                for app in self.recent_applications:
                    if app.lower() in [a.lower() for a in rule.pattern["applications"]]:
                        patterns.append({
                            "type": TriggerType.APPLICATION_PATTERN.value,
                            "confidence": 0.9,
                            "context": {"application": app},
                            "description": f"Detected application pattern: {app}"
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting application patterns: {e}")
            return []
    
    async def _detect_activity_sequences(self, rule: TriggerRule) -> List[Dict[str, Any]]:
        """Detect patterns in sequences of activities"""
        try:
            patterns = []
            
            if len(self.recent_activities) < 2:
                return patterns
                
            # Extract sequence from rule pattern
            if isinstance(rule.pattern, dict) and "sequence" in rule.pattern:
                sequence = rule.pattern["sequence"]
                min_sequence_length = rule.pattern.get("min_length", 2)
                
                # Check for sequence pattern in recent activities
                activities_text = " ".join([a["activity"] for a in self.recent_activities])
                
                if all(step.lower() in activities_text.lower() for step in sequence):
                    confidence = min(0.7 + (0.1 * len(sequence)), 0.95)
                    patterns.append({
                        "type": TriggerType.ACTIVITY_SEQUENCE.value,
                        "confidence": confidence,
                        "context": {
                            "sequence": sequence,
                            "activities": [a["activity"] for a in self.recent_activities[:3]]
                        },
                        "description": f"Detected activity sequence pattern"
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting activity sequences: {e}")
            return []
    
    async def _detect_time_based_patterns(self, rule: TriggerRule) -> List[Dict[str, Any]]:
        """Detect patterns based on time"""
        try:
            patterns = []
            
            if isinstance(rule.pattern, dict):
                now = datetime.now()
                
                # Time of day trigger
                if "time_of_day" in rule.pattern:
                    target_time = rule.pattern["time_of_day"]
                    current_hour = now.hour
                    
                    # Check if current hour matches target time
                    if isinstance(target_time, list) and current_hour in target_time:
                        patterns.append({
                            "type": TriggerType.TIME_BASED.value,
                            "confidence": 0.8,
                            "context": {"time_of_day": current_hour},
                            "description": f"Time-based trigger: {current_hour}:00"
                        })
                    elif isinstance(target_time, dict) and "start" in target_time and "end" in target_time:
                        if target_time["start"] <= current_hour < target_time["end"]:
                            patterns.append({
                                "type": TriggerType.TIME_BASED.value,
                                "confidence": 0.85,
                                "context": {"time_range": f"{target_time['start']}:00-{target_time['end']}:00"},
                                "description": f"Time-based trigger: Time range {target_time['start']}:00-{target_time['end']}:00"
                            })
                
                # Duration-based trigger
                if "duration" in rule.pattern and self.recent_activities:
                    duration_minutes = rule.pattern["duration"]
                    first_activity_time = self.recent_activities[-1].get("timestamp", 0)
                    last_activity_time = self.recent_activities[0].get("timestamp", 0)
                    
                    # Check if duration exceeds threshold
                    if last_activity_time - first_activity_time >= (duration_minutes * 60):
                        patterns.append({
                            "type": TriggerType.TIME_BASED.value,
                            "confidence": 0.75,
                            "context": {"duration_minutes": duration_minutes},
                            "description": f"Duration-based trigger: {duration_minutes} minutes"
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting time-based patterns: {e}")
            return []
    
    async def _detect_semantic_patterns(self, rule: TriggerRule, memory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns using semantic search"""
        try:
            patterns = []
            
            if not DEPENDENCIES_AVAILABLE or not semantic_search_agent:
                logger.warning("Semantic search not available for pattern detection")
                return patterns
            
            if isinstance(rule.pattern, dict) and "query" in rule.pattern:
                query = rule.pattern["query"]
                
                # Perform semantic search
                search_results = await search_memories(
                    query=query,
                    top_k=5,
                    min_similarity=0.3
                )
                
                # Check for strong matches
                strong_matches = [r for r in search_results if r.similarity_score >= rule.confidence_threshold]
                
                if strong_matches:
                    # Create pattern with the highest similarity match
                    best_match = max(strong_matches, key=lambda x: x.similarity_score)
                    patterns.append({
                        "type": TriggerType.SEMANTIC_PATTERN.value,
                        "confidence": best_match.similarity_score,
                        "context": {
                            "query": query,
                            "match_content": best_match.content,
                            "match_source": best_match.source,
                            "memory_references": [best_match.context.get("document_id", "")]
                        },
                        "description": f"Semantic pattern match: {query}"
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting semantic patterns: {e}")
            return []
    
    async def _detect_task_completion_patterns(self, rule: TriggerRule) -> List[Dict[str, Any]]:
        """Detect patterns related to task completion"""
        try:
            patterns = []
            
            if not DEPENDENCIES_AVAILABLE or not task_memory_manager:
                logger.warning("Task memory manager not available for pattern detection")
                return patterns
            
            if isinstance(rule.pattern, dict) and "task_status" in rule.pattern:
                target_status = rule.pattern["task_status"]
                
                # Search for tasks with the target status
                try:
                    task_query = f"task {target_status}"
                    matching_tasks = await task_memory_manager.search_task_records(task_query, limit=3)
                    
                    # Create patterns for matching tasks
                    for task in matching_tasks:
                        if task.get("status", "").lower() == target_status.lower():
                            patterns.append({
                                "type": TriggerType.TASK_COMPLETION.value,
                                "confidence": 0.9,
                                "context": {
                                    "task_id": task.get("task_id", ""),
                                    "task_description": task.get("description", ""),
                                    "task_status": task.get("status", "")
                                },
                                "description": f"Task completion pattern: {task.get('status', '')}"
                            })
                except:
                    # If search_task_records doesn't exist or fails
                    pass
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting task completion patterns: {e}")
            return []
    
    async def _detect_content_patterns(self, rule: TriggerRule, memory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns in content"""
        try:
            patterns = []
            
            if isinstance(rule.pattern, str):
                # Regex pattern for content
                pattern = re.compile(rule.pattern, re.IGNORECASE)
                
                # Check memory items for content matches
                for item in memory_items:
                    content = item.get("searchable_text", "")
                    if not content:
                        continue
                    
                    match = pattern.search(content)
                    if match:
                        matched_text = match.group(0)
                        context = {
                            "matched_text": matched_text,
                            "content_type": item.get("type", "unknown"),
                            "memory_id": item.get("memory_id", "")
                        }
                        
                        patterns.append({
                            "type": TriggerType.CONTENT_BASED.value,
                            "confidence": 0.8,
                            "context": context,
                            "description": f"Content pattern match: {matched_text[:30]}..."
                        })
            elif isinstance(rule.pattern, dict) and "keywords" in rule.pattern:
                # Keywords pattern
                keywords = rule.pattern["keywords"]
                min_matches = rule.pattern.get("min_matches", 1)
                
                # Check memory items for keyword matches
                for item in memory_items:
                    content = item.get("searchable_text", "").lower()
                    if not content:
                        continue
                    
                    matches = [kw for kw in keywords if kw.lower() in content]
                    if len(matches) >= min_matches:
                        context = {
                            "matched_keywords": matches,
                            "content_type": item.get("type", "unknown"),
                            "memory_id": item.get("memory_id", "")
                        }
                        
                        # Confidence increases with more matches
                        confidence = min(0.7 + (0.1 * len(matches)), 0.95)
                        
                        patterns.append({
                            "type": TriggerType.CONTENT_BASED.value,
                            "confidence": confidence,
                            "context": context,
                            "description": f"Keyword pattern match: {', '.join(matches[:3])}"
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting content patterns: {e}")
            return []
    
    async def _detect_user_behavior_patterns(self, rule: TriggerRule) -> List[Dict[str, Any]]:
        """Detect patterns in user behavior"""
        try:
            patterns = []
            
            if isinstance(rule.pattern, dict):
                # Repetitive action pattern
                if "repetitive_action" in rule.pattern and len(self.recent_activities) >= 3:
                    min_repetitions = rule.pattern.get("min_repetitions", 3)
                    
                    # Look for repeated similar activities
                    activity_texts = [a["activity"].lower() for a in self.recent_activities[:5]]
                    
                    # Simple detection of repetitive activities based on similarity
                    similar_activities = 0
                    for i in range(1, len(activity_texts)):
                        # Check for similar text (very simple implementation)
                        prev = activity_texts[i-1]
                        curr = activity_texts[i]
                        
                        # If activities are similar enough
                        if (len(prev) > 10 and len(curr) > 10 and 
                            (prev[:10] == curr[:10] or prev[-10:] == curr[-10:])):
                            similar_activities += 1
                    
                    if similar_activities >= min_repetitions - 1:
                        patterns.append({
                            "type": TriggerType.USER_BEHAVIOR.value,
                            "confidence": 0.7 + (0.05 * similar_activities),
                            "context": {
                                "repetitions": similar_activities + 1,
                                "recent_activity": activity_texts[0]
                            },
                            "description": f"Repetitive action pattern detected"
                        })
                
                # Switching context pattern
                if "context_switching" in rule.pattern and len(self.recent_applications) >= 3:
                    timeframe_minutes = rule.pattern.get("timeframe_minutes", 15)
                    min_switches = rule.pattern.get("min_switches", 4)
                    
                    # If we have enough recent distinct applications
                    if len(self.recent_applications) >= min_switches:
                        patterns.append({
                            "type": TriggerType.USER_BEHAVIOR.value,
                            "confidence": 0.75,
                            "context": {
                                "applications": list(self.recent_applications)[:5],
                                "switch_count": len(self.recent_applications)
                            },
                            "description": f"Context switching pattern detected"
                        })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting user behavior patterns: {e}")
            return []

class TriggerRuleManager:
    """Manages trigger rules"""
    
    def __init__(self, rules_file: str = "config/trigger_rules.json"):
        """Initialize with default rules or from file"""
        self.rules_file = rules_file
        self.rules: Dict[str, TriggerRule] = {}
        self.rule_stats: Dict[str, Dict[str, Any]] = {}  # Statistics for each rule
        
        # Create default rules
        self._create_default_rules()
        
        # Try to load rules from file
        self.load_rules()
        
    def _create_default_rules(self) -> None:
        """Create default trigger rules"""
        default_rules = [
            TriggerRule(
                id="app_browser_search",
                name="Browser Search Detection",
                description="Detects when user is searching in a browser",
                trigger_type=TriggerType.APPLICATION_PATTERN,
                priority=TriggerPriority.MEDIUM,
                pattern={"applications": ["Chrome", "Safari", "Firefox", "Edge"]},
                action_template={
                    "type": "search_assistance",
                    "description": "Help with search optimization"
                }
            ),
            TriggerRule(
                id="repetitive_action",
                name="Repetitive Action Detection",
                description="Detects when user is performing repetitive actions",
                trigger_type=TriggerType.USER_BEHAVIOR,
                priority=TriggerPriority.HIGH,
                pattern={"repetitive_action": True, "min_repetitions": 3},
                action_template={
                    "type": "automation_suggestion",
                    "description": "Suggest automation for repetitive task"
                }
            ),
            TriggerRule(
                id="code_review_suggestion",
                name="Code Review Suggestion",
                description="Suggests code review after coding session",
                trigger_type=TriggerType.CONTENT_BASED,
                priority=TriggerPriority.MEDIUM,
                pattern={"keywords": ["function", "class", "def", "var", "const", "if", "for", "while"], "min_matches": 3},
                action_template={
                    "type": "code_review",
                    "description": "Offer to review code changes"
                }
            ),
            TriggerRule(
                id="long_session_break",
                name="Long Session Break Reminder",
                description="Reminds user to take a break after long session",
                trigger_type=TriggerType.TIME_BASED,
                priority=TriggerPriority.MEDIUM,
                pattern={"duration": 60},  # 60 minutes
                action_template={
                    "type": "wellness_suggestion",
                    "description": "Suggest taking a break"
                }
            ),
            TriggerRule(
                id="task_completed_summary",
                name="Task Completion Summary",
                description="Offers summary when task is completed",
                trigger_type=TriggerType.TASK_COMPLETION,
                priority=TriggerPriority.MEDIUM,
                pattern={"task_status": "completed"},
                action_template={
                    "type": "task_summary",
                    "description": "Generate summary of completed task"
                }
            ),
            TriggerRule(
                id="web_page_content_action",
                name="Web Page Content Action",
                description="Detects web page content and suggests relevant actions",
                trigger_type=TriggerType.CONTENT_BASED,
                priority=TriggerPriority.HIGH,
                pattern={
                    "keywords": [
                        "article", "blog", "tutorial", "documentation", "guide", 
                        "purchase", "sign up", "login", "register", "download",
                        "form", "checkout", "payment", "subscribe", "fill out"
                    ],
                    "min_matches": 2
                },
                action_template={
                    "type": "web_content_action",
                    "description": "Offer to perform action based on web content"
                }
            ),
            TriggerRule(
                id="shopping_detection",
                name="Shopping Detection",
                description="Detects when user is shopping online",
                trigger_type=TriggerType.CONTENT_BASED,
                priority=TriggerPriority.MEDIUM,
                pattern={
                    "keywords": [
                        "add to cart", "checkout", "purchase", "buy", "price", "sale",
                        "discount", "product", "item", "order", "shipping", "payment"
                    ],
                    "min_matches": 3
                },
                action_template={
                    "type": "shopping_assistance",
                    "description": "Offer to help with online shopping"
                }
            ),
            TriggerRule(
                id="form_filling_detection",
                name="Form Filling Detection",
                description="Detects when user is filling out forms",
                trigger_type=TriggerType.CONTENT_BASED,
                priority=TriggerPriority.HIGH,
                pattern={
                    "keywords": [
                        "form", "input", "field", "required", "submit", "name", "email",
                        "address", "phone", "registration", "sign up", "create account"
                    ],
                    "min_matches": 3
                },
                action_template={
                    "type": "form_automation",
                    "description": "Offer to help fill out the form"
                }
            )
        ]
        
        # Add default rules to dictionary
        for rule in default_rules:
            self.rules[rule.id] = rule
            
            # Initialize stats
            self.rule_stats[rule.id] = {
                "trigger_count": 0,
                "last_triggered": None,
                "success_rate": 0.0,
                "accepted_count": 0,
                "dismissed_count": 0
            }
    
    def load_rules(self) -> bool:
        """Load rules from file"""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)
                
                # Create rules from data
                loaded_rules = {}
                for rule_data in rules_data.get("rules", []):
                    try:
                        rule = TriggerRule.from_dict(rule_data)
                        loaded_rules[rule.id] = rule
                    except Exception as e:
                        logger.error(f"Error loading rule {rule_data.get('id', 'unknown')}: {e}")
                
                # Use loaded rules if any were successfully loaded
                if loaded_rules:
                    self.rules = loaded_rules
                    
                # Load stats if available
                if "stats" in rules_data:
                    self.rule_stats = rules_data["stats"]
                
                logger.info(f"Loaded {len(self.rules)} trigger rules from {self.rules_file}")
                return True
            else:
                logger.info(f"Rules file {self.rules_file} not found, using default rules")
                return False
                
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return False
    
    def save_rules(self) -> bool:
        """Save rules to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
            
            # Prepare data for saving
            rules_data = {
                "version": "1.0",
                "last_updated": time.time(),
                "rules": [rule.to_dict() for rule in self.rules.values()],
                "stats": self.rule_stats
            }
            
            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            logger.info(f"Saved {len(self.rules)} trigger rules to {self.rules_file}")
            return True
                
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
            return False
    
    def get_active_rules(self) -> List[TriggerRule]:
        """Get all active rules"""
        return [rule for rule in self.rules.values() if rule.enabled]
    
    def get_rule(self, rule_id: str) -> Optional[TriggerRule]:
        """Get a specific rule by ID"""
        return self.rules.get(rule_id)
    
    def add_rule(self, rule: TriggerRule) -> bool:
        """Add a new rule"""
        try:
            self.rules[rule.id] = rule
            
            # Initialize stats
            self.rule_stats[rule.id] = {
                "trigger_count": 0,
                "last_triggered": None,
                "success_rate": 0.0,
                "accepted_count": 0,
                "dismissed_count": 0
            }
            
            self.save_rules()
            return True
                
        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            return False
    
    def update_rule(self, rule: TriggerRule) -> bool:
        """Update an existing rule"""
        try:
            if rule.id in self.rules:
                self.rules[rule.id] = rule
                self.save_rules()
                return True
            else:
                logger.warning(f"Rule {rule.id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating rule: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                
                # Also delete stats
                if rule_id in self.rule_stats:
                    del self.rule_stats[rule_id]
                    
                self.save_rules()
                return True
            else:
                logger.warning(f"Rule {rule_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting rule: {e}")
            return False
    
    def update_rule_stats(self, rule_id: str, trigger_event: TriggerEvent) -> None:
        """Update statistics for a rule"""
        try:
            if rule_id not in self.rule_stats:
                self.rule_stats[rule_id] = {
                    "trigger_count": 0,
                    "last_triggered": None,
                    "success_rate": 0.0,
                    "accepted_count": 0,
                    "dismissed_count": 0
                }
            
            stats = self.rule_stats[rule_id]
            
            # Update trigger count and time
            stats["trigger_count"] += 1
            stats["last_triggered"] = time.time()
            
            # Update acceptance stats if applicable
            if trigger_event.status == TriggerStatus.ACCEPTED:
                stats["accepted_count"] += 1
            elif trigger_event.status == TriggerStatus.DISMISSED:
                stats["dismissed_count"] += 1
            
            # Calculate success rate
            total_responses = stats["accepted_count"] + stats["dismissed_count"]
            if total_responses > 0:
                stats["success_rate"] = stats["accepted_count"] / total_responses
                
        except Exception as e:
            logger.error(f"Error updating rule stats: {e}")

class NotificationManager:
    """Manages trigger notifications and their lifecycle"""
    
    def __init__(self, storage_file: str = "memory/trigger_notifications.json"):
        """Initialize notification manager"""
        self.storage_file = storage_file
        self.active_notifications: Dict[str, TriggerEvent] = {}
        self.completed_notifications: Dict[str, TriggerEvent] = {}
        self.notification_callbacks: List[Callable[[TriggerEvent], None]] = []
        
        # Load existing notifications
        self._load_notifications()
        
        # Start background task for cleanup
        self._start_cleanup_task()
    
    def _load_notifications(self) -> None:
        """Load notifications from storage"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                
                # Load active notifications
                for notification_data in data.get("active", []):
                    try:
                        notification = TriggerEvent.from_dict(notification_data)
                        self.active_notifications[notification.id] = notification
                    except Exception as e:
                        logger.error(f"Error loading notification: {e}")
                
                # Load limited set of completed notifications
                for notification_data in data.get("completed", [])[:100]:  # Limit to 100
                    try:
                        notification = TriggerEvent.from_dict(notification_data)
                        self.completed_notifications[notification.id] = notification
                    except Exception as e:
                        logger.error(f"Error loading completed notification: {e}")
                
                logger.info(f"Loaded {len(self.active_notifications)} active and {len(self.completed_notifications)} completed notifications")
                
        except Exception as e:
            logger.error(f"Error loading notifications: {e}")
    
    def _save_notifications(self) -> None:
        """Save notifications to storage"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            # Prepare data
            data = {
                "last_updated": time.time(),
                "active": [notification.to_dict() for notification in self.active_notifications.values()],
                "completed": [notification.to_dict() for notification in list(self.completed_notifications.values())[:100]]  # Limit to 100
            }
            
            # Save to file
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving notifications: {e}")
    
    def _start_cleanup_task(self) -> None:
        """Start background task for notification cleanup"""
        def cleanup_task():
            while True:
                try:
                    self._cleanup_expired_notifications()
                    time.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Error in notification cleanup: {e}")
                    time.sleep(600)  # 10 minutes on error
        
        # Start thread
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_notifications(self) -> None:
        """Clean up expired notifications"""
        try:
            current_time = time.time()
            expired_ids = []
            
            # Find expired notifications
            for notification_id, notification in self.active_notifications.items():
                # Check if expired
                if notification.expiration_time and current_time > notification.expiration_time:
                    expired_ids.append(notification_id)
                    
                    # Update status
                    notification.status = TriggerStatus.EXPIRED
                    notification.updated_at = current_time
                    
                    # Move to completed
                    self.completed_notifications[notification_id] = notification
            
            # Remove expired from active
            for notification_id in expired_ids:
                del self.active_notifications[notification_id]
            
            # Prune completed notifications if too many
            if len(self.completed_notifications) > 100:
                # Sort by updated_at
                sorted_notifications = sorted(
                    self.completed_notifications.items(),
                    key=lambda x: x[1].updated_at
                )
                
                # Keep only the 100 most recent
                self.completed_notifications = dict(sorted_notifications[-100:])
            
            # Save changes if any were made
            if expired_ids:
                self._save_notifications()
                logger.info(f"Cleaned up {len(expired_ids)} expired notifications")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {e}")
    
    def add_notification_callback(self, callback: Callable[[TriggerEvent], None]) -> None:
        """Add callback for new notifications"""
        self.notification_callbacks.append(callback)
    
    def create_notification(self, rule: TriggerRule, pattern: Dict[str, Any]) -> TriggerEvent:
        """Create a new notification from a rule and pattern"""
        try:
            # Generate title and description
            title = f"{rule.name}"
            description = pattern.get("description", rule.description)
            
            # Create notification
            notification = TriggerEvent(
                rule_id=rule.id,
                status=TriggerStatus.PENDING,
                priority=rule.priority,
                confidence=pattern.get("confidence", 0.7),
                title=title,
                description=description,
                context=pattern.get("context", {}),
                memory_references=pattern.get("context", {}).get("memory_references", []),
                action_plan=rule.action_template,
                expiration_time=time.time() + (3600 * 24)  # 24 hour expiration by default
            )
            
            # Store notification
            self.active_notifications[notification.id] = notification
            
            # Save notifications
            self._save_notifications()
            
            # Call notification callbacks
            for callback in self.notification_callbacks:
                try:
                    callback(notification)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
            
            logger.info(f"Created notification {notification.id} from rule {rule.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            # Return minimal notification
            return TriggerEvent(
                rule_id=rule.id,
                status=TriggerStatus.FAILED,
                title="Error creating notification",
                description=str(e)
            )
    
    def update_notification(self, notification_id: str, updates: Dict[str, Any]) -> Optional[TriggerEvent]:
        """Update a notification"""
        try:
            # Check if notification exists
            if notification_id not in self.active_notifications:
                logger.warning(f"Notification {notification_id} not found for update")
                return None
            
            notification = self.active_notifications[notification_id]
            
            # Apply updates
            if "status" in updates:
                notification.status = TriggerStatus(updates["status"])
            if "suggestion" in updates:
                notification.suggestion = updates["suggestion"]
            if "context" in updates:
                notification.context.update(updates["context"])
            if "action_plan" in updates:
                notification.action_plan = updates["action_plan"]
            
            # Update timestamp
            notification.updated_at = time.time()
            
            # If status is terminal, move to completed
            if notification.status in [TriggerStatus.COMPLETED, TriggerStatus.DISMISSED, TriggerStatus.FAILED]:
                self.completed_notifications[notification_id] = notification
                del self.active_notifications[notification_id]
            
            # Save notifications
            self._save_notifications()
            
            return notification
            
        except Exception as e:
            logger.error(f"Error updating notification: {e}")
            return None
    
    def get_notification(self, notification_id: str) -> Optional[TriggerEvent]:
        """Get a notification by ID"""
        # Check active notifications
        if notification_id in self.active_notifications:
            return self.active_notifications[notification_id]
        
        # Check completed notifications
        if notification_id in self.completed_notifications:
            return self.completed_notifications[notification_id]
        
        return None
    
    def get_active_notifications(self) -> List[TriggerEvent]:
        """Get all active notifications"""
        return list(self.active_notifications.values())
    
    def get_pending_notifications(self) -> List[TriggerEvent]:
        """Get pending notifications that should be delivered"""
        return [n for n in self.active_notifications.values() if n.status == TriggerStatus.PENDING]
    
    def mark_notification_delivered(self, notification_id: str) -> bool:
        """Mark a notification as delivered"""
        try:
            return self.update_notification(notification_id, {"status": TriggerStatus.DELIVERED.value}) is not None
        except Exception as e:
            logger.error(f"Error marking notification as delivered: {e}")
            return False
    
    def mark_notification_accepted(self, notification_id: str) -> bool:
        """Mark a notification as accepted"""
        try:
            return self.update_notification(notification_id, {"status": TriggerStatus.ACCEPTED.value}) is not None
        except Exception as e:
            logger.error(f"Error marking notification as accepted: {e}")
            return False
    
    def mark_notification_dismissed(self, notification_id: str) -> bool:
        """Mark a notification as dismissed"""
        try:
            return self.update_notification(notification_id, {"status": TriggerStatus.DISMISSED.value}) is not None
        except Exception as e:
            logger.error(f"Error marking notification as dismissed: {e}")
            return False

# Define ChatRequest class locally if import fails
if 'ChatRequest' not in globals():
    @dataclass
    class ChatRequest:
        """Incoming chat request with full context"""
        mode: str  # ChatMode
        query: str
        user_id: str
        session_id: str
        timestamp: float
        priority: str = "MEDIUM"  # Priority
        context: Dict[str, Any] = field(default_factory=dict)
        resources_needed: List[Any] = field(default_factory=list)

class MemoryTriggerService:
    """
    Service that monitors memory for patterns and triggers suggestions
    
    This service:
    1. Periodically checks memory for patterns
    2. Generates suggestions based on detected patterns
    3. Pushes notifications to the chat interface
    4. Handles action execution upon user approval
    """
    
    def __init__(self, 
                brain_router=None, 
                memory_system=None,
                config_path: str = "config/memory_trigger_config.json"):
        """Initialize memory trigger service"""
        self.brain_router = brain_router
        self.memory_system = memory_system
        self.config_path = config_path
        self.running = False
        self.check_interval = 60  # seconds
        self.last_check_time = 0
        self.trigger_count = 0
        self.execution_count = 0
        
        # Initialize components
        self.pattern_detector = MemoryPatternDetector()
        self.rule_manager = TriggerRuleManager()
        self.notification_manager = NotificationManager()
        
        # Load configuration
        self._load_config()
        
        # Add notification callback
        self.notification_manager.add_notification_callback(self._on_new_notification)
        
        logger.info("Memory Trigger Service initialized")
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Apply configuration
                self.check_interval = config.get("check_interval", 60)
                
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                # Create default configuration
                config = {
                    "check_interval": 60,
                    "max_notifications_per_hour": 5,
                    "enabled": True
                }
                
                # Save default configuration
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                logger.info(f"Created default configuration at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    async def start(self) -> None:
        """Start the memory trigger service"""
        if self.running:
            return
            
        self.running = True
        logger.info("Memory Trigger Service started")
        
        # Start memory monitoring in background
        asyncio.create_task(self._monitor_memory())
    
    async def stop(self) -> None:
        """Stop the memory trigger service"""
        self.running = False
        logger.info("Memory Trigger Service stopped")
    
    async def _monitor_memory(self) -> None:
        """Monitor memory for patterns"""
        while self.running:
            try:
                # Check if enough time has passed since last check
                current_time = time.time()
                if current_time - self.last_check_time < self.check_interval:
                    await asyncio.sleep(1)
                    continue
                
                # Update last check time
                self.last_check_time = current_time
                logger.info(f"Starting memory monitoring cycle at {datetime.fromtimestamp(current_time).isoformat()}")
                
                # Get memory items
                memory_items = await self._get_recent_memory_items()
                
                # No memory items to process
                if not memory_items:
                    logger.info("No memory items found for pattern detection, skipping this cycle")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                # Get active rules
                active_rules = self.rule_manager.get_active_rules()
                logger.info(f"Using {len(active_rules)} active trigger rules for pattern detection")
                
                # Detect patterns
                detected_patterns = await self.pattern_detector.detect_patterns(memory_items, active_rules)
                
                # Process detected patterns
                if detected_patterns:
                    logger.info(f"Detected {len(detected_patterns)} patterns matching trigger rules")
                    await self._process_detected_patterns(detected_patterns)
                else:
                    logger.info("No patterns matched trigger rules")
                
                # Look for web content patterns specifically
                web_items = [item for item in memory_items if "url" in item and item.get("url") and "http" in item.get("url", "")]
                if web_items:
                    logger.info(f"Found {len(web_items)} web content items, generating suggestions")
                    suggestions = self._generate_web_content_suggestions(web_items)
                    
                    # Create notifications for web suggestions
                    for suggestion in suggestions:
                        # Create a temporary rule for this suggestion
                        temp_rule_id = f"web_content_{int(time.time())}_{hash(suggestion.get('url', ''))}"
                        temp_rule = TriggerRule(
                            id=temp_rule_id,
                            name="Web Content Suggestion",
                            description=f"Suggestion based on web content: {suggestion.get('url', '')}",
                            trigger_type=TriggerType.CONTENT_BASED,
                            priority=TriggerPriority.MEDIUM,
                            pattern={"url": suggestion.get("url", "")},
                            action_template={
                                "type": "web_content_action",
                                "url": suggestion.get("url", ""),
                                "content_type": suggestion.get("content_type", "unknown")
                            }
                        )
                        
                        # Create notification
                        self.notification_manager.create_notification(temp_rule, suggestion)
                        self.trigger_count += 1
                        logger.info(f"Created web content suggestion for {suggestion.get('content_type')} at {suggestion.get('url')}")
                
                # Process pending notifications
                await self._process_pending_notifications()
                
                # Log completion
                logger.info(f"Memory monitoring cycle completed, next check in {self.check_interval} seconds")
                
                # Sleep for a while
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
                logger.error(f"Error details: {str(e)}")
                await asyncio.sleep(self.check_interval * 2)  # Sleep longer on error
                
    def _generate_web_content_suggestions(self, web_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate suggestions based on web content"""
        try:
            suggestions = []
            
            for item in web_items:
                url = item.get("url", "")
                title = item.get("title", "")
                content = item.get("searchable_text", "")
                
                if not url or not content:
                    continue
                
                # Extract keywords
                keywords = self._extract_keywords(content)
                keyword_text = ", ".join(keywords) if keywords else "unknown"
                
                # Determine content type
                content_type = "general"
                if any(kw in content.lower() for kw in ["article", "blog", "tutorial", "guide", "documentation"]):
                    content_type = "article"
                    description = f"I noticed you're reading an article about {keyword_text}. Would you like me to help you with this content?"
                elif any(kw in content.lower() for kw in ["product", "price", "buy", "purchase", "shipping", "checkout"]):
                    content_type = "shopping"
                    description = f"I noticed you're shopping for {keyword_text}. Would you like me to help you find the best deals or reviews?"
                elif any(kw in content.lower() for kw in ["form", "sign up", "register", "login", "account"]):
                    content_type = "form"
                    description = f"I noticed you're filling out a form. Would you like me to help you complete it?"
                elif any(kw in content.lower() for kw in ["video", "youtube", "watch", "stream"]):
                    content_type = "video"
                    description = f"I noticed you're watching a video about {keyword_text}. Would you like me to find related content?"
                else:
                    description = f"I noticed you're browsing content about {keyword_text}. Would you like assistance with this page?"
                
                # Create suggestion
                suggestion = {
                    "type": "web_content",
                    "confidence": 0.8,
                    "url": url,
                    "title": title,
                    "content_type": content_type,
                    "keywords": keywords,
                    "description": description,
                    "context": {
                        "url": url,
                        "title": title,
                        "content_type": content_type,
                        "matched_keywords": keywords
                    }
                }
                
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating web content suggestions: {e}")
            return []
    
    async def _get_recent_memory_items(self) -> List[Dict[str, Any]]:
        """Get recent memory items"""
        try:
            if not self.memory_system:
                logger.warning("Memory system not available")
                return []
            
            # Get recent items from memory
            recent_time = time.time() - (3600)  # Last hour
            
            try:
                logger.info(f"Retrieving recent memory items since {datetime.fromtimestamp(recent_time).isoformat()}")
                
                # Try to get short-term memory
                short_term_items = await self.memory_system.get_short_term_memory(
                    since=recent_time,
                    limit=50
                )
                
                logger.info(f"Successfully retrieved {len(short_term_items)} short-term memory items")
                
                # Try to get recent application memories
                app_memories = await self.memory_system.get_memories_by_type(
                    memory_type="application",
                    limit=10
                )
                
                logger.info(f"Successfully retrieved {len(app_memories)} application memory items")
                
                # Combine all items
                all_items = short_term_items + app_memories
                
                logger.info(f"Total memory items retrieved: {len(all_items)}")
                
                # Extract memory patterns from items
                patterns = self._extract_memory_patterns(all_items)
                if patterns:
                    logger.info(f"Detected {len(patterns)} patterns in memory items")
                
                return all_items
                
            except Exception as e:
                logger.error(f"Error getting memory items, falling back to semantic search: {e}")
                
                # Fallback to semantic search if available
                if DEPENDENCIES_AVAILABLE and semantic_search_agent:
                    results = await search_memories(
                        query="recent activity",
                        top_k=20
                    )
                    
                    # Convert to memory items
                    items = []
                    for result in results:
                        items.append({
                            "memory_id": result.context.get("document_id", ""),
                            "searchable_text": result.content,
                            "source": result.source,
                            "timestamp": time.time() - (3600 * 24 * 30),  # Placeholder timestamp
                            "similarity_score": result.similarity_score
                        })
                    
                    logger.info(f"Retrieved {len(items)} memory items via semantic search fallback")
                    return items
                    
                return []
                
        except Exception as e:
            logger.error(f"Error getting recent memory items: {e}")
            return []
            
    def _extract_memory_patterns(self, memory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns from memory items"""
        try:
            patterns = []
            
            # Skip if no items
            if not memory_items:
                return patterns
                
            # Extract applications
            applications = set()
            for item in memory_items:
                app = item.get("application", "")
                if app:
                    applications.add(app)
            
            # Extract web content
            web_patterns = []
            for item in memory_items:
                url = item.get("url", "")
                content = item.get("searchable_text", "")
                
                if url and "http" in url:
                    # Look for common web page patterns
                    if any(kw in content.lower() for kw in ["article", "blog", "news", "tutorial"]):
                        web_patterns.append({
                            "type": "web_content",
                            "subtype": "article",
                            "url": url,
                            "keywords": self._extract_keywords(content)
                        })
                    elif any(kw in content.lower() for kw in ["product", "price", "buy", "purchase"]):
                        web_patterns.append({
                            "type": "web_content",
                            "subtype": "shopping",
                            "url": url,
                            "keywords": self._extract_keywords(content)
                        })
            
            # Add application patterns
            if applications:
                patterns.append({
                    "type": "application_usage",
                    "applications": list(applications),
                    "confidence": 0.9
                })
            
            # Add web patterns
            patterns.extend(web_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error extracting memory patterns: {e}")
            return []
            
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text"""
        try:
            # Simple keyword extraction
            if not text:
                return []
                
            # Remove common stop words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "of"}
            
            # Tokenize and filter
            words = re.findall(r'\b\w+\b', text.lower())
            keywords = [w for w in words if len(w) > 3 and w not in stop_words]
            
            # Count occurrences
            keyword_counts = {}
            for keyword in keywords:
                if keyword in keyword_counts:
                    keyword_counts[keyword] += 1
                else:
                    keyword_counts[keyword] = 1
            
            # Sort by count and return top keywords
            sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            return [k for k, _ in sorted_keywords[:max_keywords]]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def _process_detected_patterns(self, detected_patterns: List[Dict[str, Any]]) -> None:
        """Process detected patterns"""
        try:
            for pattern in detected_patterns:
                rule = pattern.get("rule")
                if not rule:
                    continue
                
                # Create notification from pattern
                notification = self.notification_manager.create_notification(rule, pattern)
                
                # Generate suggestion if rule has a valid action template
                if rule.action_template:
                    suggestion = await self._generate_suggestion(notification, rule)
                    
                    # Update notification with suggestion
                    self.notification_manager.update_notification(
                        notification.id,
                        {"suggestion": suggestion}
                    )
                
                self.trigger_count += 1
                logger.info(f"Created trigger notification {notification.id} from rule {rule.id}")
                
                # Update rule statistics
                self.rule_manager.update_rule_stats(rule.id, notification)
                
        except Exception as e:
            logger.error(f"Error processing detected patterns: {e}")
    
    async def _generate_suggestion(self, notification: TriggerEvent, rule: TriggerRule) -> str:
        """Generate a suggestion for the notification"""
        try:
            # If suggest mode handler is available, use it
            if DEPENDENCIES_AVAILABLE and suggest_mode_handler:
                # Create request
                request = ChatRequest(
                    mode=ChatMode.SUGGEST,
                    query=f"Suggest actions for {notification.title}",
                    user_id="system",
                    session_id=f"trigger_{notification.id}",
                    timestamp=time.time(),
                    context={
                        "trigger_notification": notification.to_dict(),
                        "trigger_rule": rule.to_dict(),
                        "suggestion_type": rule.action_template.get("type", "general")
                    }
                )
                
                # Get response
                response = await suggest_mode_handler.handle_request(request)
                return response.response
            
            # Fallback to template-based suggestions
            action_type = rule.action_template.get("type", "general")
            
            # Get context-specific information for better suggestions
            context = notification.context
            app = context.get("application", "")
            keywords = context.get("matched_keywords", [])
            keywords_str = ", ".join(keywords[:3]) if keywords else ""
            
            # Generate suggestions based on action type with context
            if action_type == "search_assistance":
                return f"I noticed you're searching in {app}. Would you like me to help you find what you're looking for more efficiently?"
            
            elif action_type == "automation_suggestion":
                activity = context.get("recent_activity", "this")
                return f"You seem to be repeatedly doing {activity}. Would you like me to automate this task for you?"
            
            elif action_type == "code_review":
                return "I can review your code to help identify potential improvements or issues. Would you like me to do that?"
            
            elif action_type == "wellness_suggestion":
                duration = context.get("duration_minutes", 60)
                return f"You've been working for {duration} minutes. Would you like to take a short break to maintain productivity?"
            
            elif action_type == "task_summary":
                task_desc = context.get("task_description", "your task")
                return f"You've completed {task_desc}. Would you like me to summarize what you've accomplished?"
            
            elif action_type == "web_content_action":
                # Web page content-specific suggestions
                if any(kw in keywords for kw in ["article", "blog", "tutorial", "documentation", "guide"]):
                    return f"I see you're viewing content about {keywords_str}. Would you like me to summarize this information or find related resources?"
                
                elif any(kw in keywords for kw in ["purchase", "checkout", "payment"]):
                    return "I notice you're on a checkout page. Would you like me to help you complete this purchase or check for discount codes?"
                
                elif any(kw in keywords for kw in ["sign up", "login", "register"]):
                    return "I see you're on a registration page. Would you like me to help you create an account or log in?"
                
                elif any(kw in keywords for kw in ["download", "subscribe"]):
                    return f"I notice you're about to download or subscribe to something related to {keywords_str}. Would you like me to assist with this process?"
                
                else:
                    return f"I notice you're viewing a web page about {keywords_str}. Would you like me to help you with any actions on this page?"
            
            elif action_type == "shopping_assistance":
                return "I notice you're shopping online. Would you like me to help compare prices, find reviews, or check for discount codes?"
            
            elif action_type == "form_automation":
                return "I see you're filling out a form. Would you like me to help auto-fill this information for you?"
            
            else:
                return "I've noticed a pattern in your activity. Would you like assistance with your current task?"
                
        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return "I've noticed something in your recent activity that I might be able to help with. Would you like assistance?"
    
    async def _process_pending_notifications(self) -> None:
        """Process pending notifications"""
        try:
            # Get pending notifications
            pending_notifications = self.notification_manager.get_pending_notifications()
            
            # Limit number of notifications to process
            max_notifications = min(3, len(pending_notifications))
            notifications_to_process = pending_notifications[:max_notifications]
            
            # Process each notification
            for notification in notifications_to_process:
                # Push notification to chat interface
                await self._push_notification_to_chat(notification)
                
                # Mark as delivered
                self.notification_manager.mark_notification_delivered(notification.id)
                
        except Exception as e:
            logger.error(f"Error processing pending notifications: {e}")
    
    async def _push_notification_to_chat(self, notification: TriggerEvent) -> None:
        """Push notification to chat interface"""
        try:
            if not self.brain_router:
                logger.warning("Brain router not available, can't push notification")
                return
            
            # Create suggestion text with action buttons
            suggestion = notification.suggestion or notification.description
            
            # Create direct chat message in the EXACT format expected by EnterpriseChatWidget handleBackendMessage function
            # This is based on analysis of EnterpriseChatWidget.svelte component
            direct_context = {
                "success": True,
                "response": f"💡 {notification.title}: {suggestion}",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success",
                        "plan_id": notification.id
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True,
                "plan_id": notification.id
            }
            
            # If notification has an action plan, add it to context
            if notification.action_plan:
                direct_context["action_plan"] = notification.action_plan
            
            # Create request for suggest mode
            request = ChatRequest(
                mode=ChatMode.SUGGEST,
                query=json.dumps(direct_context),  # Pass the entire formatted message as the query
                user_id="system",
                session_id=f"trigger_{notification.id}",
                timestamp=time.time(),
                context={
                    "notification_id": notification.id,
                    "direct_message_format": True,  # Signal that this is a direct message
                    "rule_id": notification.rule_id,
                    "trigger_context": notification.context
                }
            )
            
            # Send notification
            try:
                logger.info(f"Sending notification to chat interface in direct format: {notification.title}")
                response = await self.brain_router.process_request(request)
                
                if response.success:
                    logger.info(f"✅ Successfully pushed notification {notification.id} to chat")
                    # Update notification status to delivered
                    self.notification_manager.mark_notification_delivered(notification.id)
            except Exception as e:
                logger.error(f"Error pushing notification to chat: {e}")
                # Try fallback format if direct format fails
                try:
                    # Create fallback format - simpler message
                    fallback_message = {
                        "type": "chat_message",
                        "mode": "SUGGEST",
                        "message": f"💡 {notification.title}: {notification.description or notification.suggestion}",
                        "user_id": "system",
                        "session_id": f"suggestion_{notification.id}",
                        "timestamp": time.time(),
                        "suggestion_type": "memory_trigger"
                    }
                    
                    await self.brain_router.process_request(
                        type('MockRequest', (), {
                            'mode': "SUGGEST",
                            'query': notification.title,
                            'user_id': "system",
                            'session_id': f"fallback_{notification.id}",
                            'timestamp': time.time(),
                            'context': {"direct_message": json.dumps(fallback_message)}
                        })
                    )
                    logger.info(f"✅ Successfully pushed notification via fallback format")
                    self.notification_manager.mark_notification_delivered(notification.id)
                except Exception as inner_e:
                    logger.error(f"Error with fallback notification format: {inner_e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Try again with standard format in case the previous format wasn't recognized
                    try:
                        # Create standard request
                        standard_request = ChatRequest(
                            mode=ChatMode.SUGGEST,
                            query=suggestion,
                            user_id="system",
                            session_id=f"standard_trigger_{notification.id}",
                            timestamp=time.time(),
                            context={
                                "notification_id": notification.id,
                                "notification_title": notification.title
                            }
                        )
                        logger.info(f"Retrying with standard format...")
                        standard_response = await self.brain_router.process_request(standard_request)
                        
                        if standard_response.success:
                            logger.info(f"✅ Successfully pushed notification with standard format")
                            self.notification_manager.mark_notification_delivered(notification.id)
                        else:
                            logger.error(f"❌ Still failed to push notification: {standard_response.response}")
                    except Exception as retry_error:
                        logger.error(f"Error in standard format retry: {retry_error}")
                else:
                    logger.info(f"✅ Used fallback format successfully")
                
        except Exception as e:
            logger.error(f"Error pushing notification to chat: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def handle_notification_action(self, notification_id: str, action: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Handle user action on a notification"""
        try:
            # Get notification
            notification = self.notification_manager.get_notification(notification_id)
            if not notification:
                return {
                    "success": False,
                    "message": f"Notification {notification_id} not found"
                }
            
            # Handle action
            if action == "execute":
                # Mark notification as accepted
                self.notification_manager.mark_notification_accepted(notification_id)
                
                # Execute action in agent mode
                result = await self._execute_action(notification, user_id, session_id)
                
                return {
                    "success": True,
                    "message": "Action execution started",
                    "execution_id": result.get("execution_id", ""),
                    "notification_id": notification_id
                }
                
            elif action == "dismiss":
                # Mark notification as dismissed
                self.notification_manager.mark_notification_dismissed(notification_id)
                
                return {
                    "success": True,
                    "message": "Notification dismissed",
                    "notification_id": notification_id
                }
                
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Error handling notification action: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def _execute_action(self, notification: TriggerEvent, user_id: str, session_id: str) -> Dict[str, Any]:
        """Execute action in agent mode"""
        try:
            if not self.brain_router:
                logger.warning("Brain router not available, can't execute action")
                return {"success": False, "message": "Brain router not available"}
            
            # Generate execution ID
            execution_id = f"exec_{notification.id}_{int(time.time())}"
            
            # Update notification status
            self.notification_manager.update_notification(
                notification.id,
                {
                    "status": TriggerStatus.EXECUTING.value,
                    "context": {"execution_id": execution_id}
                }
            )
            
            # Get context-specific information for better actions
            context = notification.context
            keywords = context.get("matched_keywords", [])
            
            # Generate query based on notification type
            action_type = notification.action_plan.get("type", "general") if notification.action_plan else "general"
            
            # Create appropriate query based on action type
            if action_type == "search_assistance":
                app = context.get("application", "browser")
                query = f"Help me optimize my search in {app} for better results"
                
            elif action_type == "automation_suggestion":
                activity = context.get("recent_activity", "current task")
                query = f"Automate the repetitive task I'm doing: {activity}"
                
            elif action_type == "code_review":
                query = "Review my code and suggest improvements"
                
            elif action_type == "wellness_suggestion":
                duration = context.get("duration_minutes", 60)
                query = f"After working for {duration} minutes, suggest a quick break activity to refresh my mind"
                
            elif action_type == "task_summary":
                task_desc = context.get("task_description", "this task")
                query = f"Summarize what I've accomplished in {task_desc}"
                
            elif action_type == "web_content_action":
                # Web content-specific actions
                if any(kw in keywords for kw in ["article", "blog", "tutorial", "documentation", "guide"]):
                    query = f"Summarize the content I'm viewing about {', '.join(keywords[:3]) if keywords else 'this topic'} and find related resources"
                    
                elif any(kw in keywords for kw in ["purchase", "checkout", "payment"]):
                    query = "Help me complete this purchase and check for available discount codes"
                    
                elif any(kw in keywords for kw in ["sign up", "login", "register"]):
                    query = "Help me create an account or log in to this service"
                    
                elif any(kw in keywords for kw in ["download", "subscribe"]):
                    query = f"Help me safely download or subscribe to this content related to {', '.join(keywords[:3]) if keywords else 'this topic'}"
                    
                else:
                    query = f"Help me interact with this web page about {', '.join(keywords[:3]) if keywords else 'this topic'}"
                    
            elif action_type == "shopping_assistance":
                query = "Help me with my online shopping by comparing prices, finding reviews, and checking for discount codes"
                
            elif action_type == "form_automation":
                query = "Help me auto-fill this form with appropriate information"
                
            else:
                query = f"Help me with: {notification.title}"
            
            # Create request for agent mode
            request = ChatRequest(
                mode=ChatMode.AGENT,
                query=query,
                user_id=user_id,
                session_id=session_id,
                timestamp=time.time(),
                context={
                    "notification_id": notification.id,
                    "execution_id": execution_id,
                    "action_type": action_type,
                    "trigger_context": notification.context,
                    "notification_title": notification.title,
                    "notification_description": notification.description
                }
            )
            
            # Send request to brain router
            asyncio.create_task(self._execute_action_async(request, notification, execution_id))
            
            self.execution_count += 1
            
            return {
                "success": True,
                "execution_id": execution_id,
                "message": "Action execution started"
            }
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            
            # Update notification status to failed
            self.notification_manager.update_notification(
                notification.id,
                {
                    "status": TriggerStatus.FAILED.value,
                    "context": {"error": str(e)}
                }
            )
            
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def _execute_action_async(self, request: ChatRequest, notification: TriggerEvent, execution_id: str) -> None:
        """Execute action asynchronously"""
        try:
            # Process request through brain router
            response = await self.brain_router.process_request(request)
            
            # Check if execution was successful
            if response.success:
                # Update notification status to completed
                self.notification_manager.update_notification(
                    notification.id,
                    {
                        "status": TriggerStatus.COMPLETED.value,
                        "context": {
                            "execution_id": execution_id,
                            "execution_result": "completed",
                            "execution_time": time.time()
                        }
                    }
                )
                
                logger.info(f"Successfully executed action for notification {notification.id}")
            else:
                # Update notification status to failed
                self.notification_manager.update_notification(
                    notification.id,
                    {
                        "status": TriggerStatus.FAILED.value,
                        "context": {
                            "execution_id": execution_id,
                            "execution_result": "failed",
                            "error": response.response,
                            "execution_time": time.time()
                        }
                    }
                )
                
                logger.warning(f"Failed to execute action for notification {notification.id}: {response.response}")
                
        except Exception as e:
            logger.error(f"Error executing action asynchronously: {e}")
            
            # Update notification status to failed
            self.notification_manager.update_notification(
                notification.id,
                {
                    "status": TriggerStatus.FAILED.value,
                    "context": {
                        "execution_id": execution_id,
                        "execution_result": "failed",
                        "error": str(e),
                        "execution_time": time.time()
                    }
                }
            )
    
    def _on_new_notification(self, notification: TriggerEvent) -> None:
        """Callback for new notifications"""
        logger.info(f"New notification created: {notification.id} - {notification.title}")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status and metrics"""
        try:
            active_notifications = self.notification_manager.get_active_notifications()
            active_rules = self.rule_manager.get_active_rules()
            
            return {
                "running": self.running,
                "trigger_count": self.trigger_count,
                "execution_count": self.execution_count,
                "last_check_time": self.last_check_time,
                "check_interval": self.check_interval,
                "active_notifications_count": len(active_notifications),
                "active_rules_count": len(active_rules),
                "memory_system_available": self.memory_system is not None,
                "brain_router_available": self.brain_router is not None,
                "service_start_time": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "running": self.running,
                "error": str(e)
            }

# Create singleton instance
memory_trigger_service = MemoryTriggerService()

# API functions
async def initialize(brain_router=None, memory_system=None) -> None:
    """Initialize memory trigger service"""
    memory_trigger_service.brain_router = brain_router
    memory_trigger_service.memory_system = memory_system
    await memory_trigger_service.start()

async def handle_notification_action(notification_id: str, action: str, user_id: str, session_id: str) -> Dict[str, Any]:
    """Handle user action on a notification"""
    return await memory_trigger_service.handle_notification_action(notification_id, action, user_id, session_id)

async def get_service_status() -> Dict[str, Any]:
    """Get service status and metrics"""
    return await memory_trigger_service.get_service_status()

async def add_trigger_rule(rule: Dict[str, Any]) -> bool:
    """Add a new trigger rule"""
    try:
        # Create rule from dict
        trigger_rule = TriggerRule(
            id=rule.get("id", f"rule_{int(time.time())}"),
            name=rule.get("name", "Custom Rule"),
            description=rule.get("description", "Custom trigger rule"),
            trigger_type=TriggerType(rule.get("trigger_type", "content_based")),
            priority=TriggerPriority(rule.get("priority", "medium")),
            pattern=rule.get("pattern", {}),
            confidence_threshold=rule.get("confidence_threshold", 0.7),
            cooldown_seconds=rule.get("cooldown_seconds", 3600),
            enabled=rule.get("enabled", True),
            action_template=rule.get("action_template", None)
        )
        
        return memory_trigger_service.rule_manager.add_rule(trigger_rule)
        
    except Exception as e:
        logger.error(f"Error adding trigger rule: {e}")
        return False