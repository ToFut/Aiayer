#!/usr/bin/env python3
"""
Intelligent Context Memory System
Truly understands what the user is doing and creates meaningful memories

This system:
1. Analyzes user behavior patterns and intentions
2. Creates rich contextual memories with semantic understanding
3. Connects related activities across time
4. Predicts user needs based on context
5. Builds a comprehensive understanding of user workflows
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import os
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserAction:
    """Represents a single user action with rich context"""
    timestamp: datetime
    action_type: str  # "click", "type", "navigate", "open", "close", etc.
    target: str  # What was acted upon
    context: Dict[str, Any]  # Rich contextual information
    intent: Optional[str] = None  # Inferred user intent
    workflow_stage: Optional[str] = None  # Part of which workflow
    significance: float = 0.5  # How important this action is (0-1)
    relationships: List[str] = None  # Related actions/objects

    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []

@dataclass
class UserWorkflow:
    """Represents a sequence of related user actions forming a workflow"""
    workflow_id: str
    name: str
    description: str
    actions: List[UserAction]
    start_time: datetime
    end_time: Optional[datetime] = None
    goal: Optional[str] = None
    success: Optional[bool] = None
    patterns: List[str] = None
    frequency: int = 1  # How often this workflow occurs

    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []

@dataclass
class UserIntent:
    """Represents inferred user intention"""
    intent_id: str
    description: str
    confidence: float
    evidence: List[str]
    predicted_actions: List[str]
    context: Dict[str, Any]
    timestamp: datetime

@dataclass
class ContextualInsight:
    """Rich contextual understanding of user behavior"""
    insight_id: str
    category: str  # "workflow", "pattern", "preference", "goal"
    title: str
    description: str
    evidence: List[str]
    confidence: float
    impact: str  # "high", "medium", "low"
    actionable: bool
    recommendations: List[str]
    timestamp: datetime

class IntelligentContextMemory:
    """
    Advanced memory system that truly understands user context and behavior
    """
    
    def __init__(self):
        self.actions_history: deque = deque(maxlen=10000)  # Last 10k actions
        self.workflows: Dict[str, UserWorkflow] = {}
        self.active_workflows: Dict[str, UserWorkflow] = {}
        self.user_intents: Dict[str, UserIntent] = {}
        self.contextual_insights: Dict[str, ContextualInsight] = {}
        
        # Behavior patterns
        self.app_usage_patterns: Dict[str, Dict] = defaultdict(dict)
        self.time_patterns: Dict[str, List] = defaultdict(list)
        self.file_patterns: Dict[str, Dict] = defaultdict(dict)
        self.interaction_patterns: Dict[str, int] = defaultdict(int)
        
        # Context tracking
        self.current_context: Dict[str, Any] = {
            "active_app": None,
            "active_window": None,
            "current_task": None,
            "focus_area": None,
            "work_session": None
        }
        
        # Create cache directory
        self.cache_dir = Path("memory/intelligent_context")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing memory
        self._load_memory()
        
        logger.info("Intelligent Context Memory System initialized")
    
    def record_user_action(self, action_type: str, target: str, context: Dict[str, Any]) -> UserAction:
        """Record a user action with intelligent context analysis"""
        
        # Create rich action record
        action = UserAction(
            timestamp=datetime.now(),
            action_type=action_type,
            target=target,
            context=context
        )
        
        # Analyze and enrich the action
        self._analyze_action_intent(action)
        self._analyze_action_significance(action)
        self._detect_workflow_membership(action)
        self._find_action_relationships(action)
        
        # Update patterns
        self._update_behavioral_patterns(action)
        
        # Update current context
        self._update_current_context(action)
        
        # Store action
        self.actions_history.append(action)
        
        # Check for workflow completion or new workflow start
        self._analyze_workflow_transitions(action)
        
        # Generate insights if needed
        self._generate_contextual_insights()
        
        logger.info(f"Recorded action: {action_type} on {target} (intent: {action.intent}, significance: {action.significance:.2f})")
        
        return action
    
    def _analyze_action_intent(self, action: UserAction):
        """Analyze and infer user intent from action"""
        
        action_type = action.action_type.lower()
        target = action.target.lower()
        context = action.context
        
        # File operations
        if "documents" in target or "folder" in target:
            if action_type in ["click", "open"]:
                action.intent = "file_management"
            elif action_type == "navigate":
                action.intent = "file_exploration"
        
        # Application usage
        elif "app" in context.get("type", ""):
            if action_type == "open":
                action.intent = "start_work_session"
            elif action_type == "switch":
                action.intent = "multitasking"
        
        # Text editing
        elif action_type in ["type", "edit", "delete"]:
            if context.get("file_type") in ["txt", "doc", "md"]:
                action.intent = "content_creation"
            elif context.get("file_type") in ["py", "js", "html"]:
                action.intent = "code_development"
        
        # Web browsing
        elif "browser" in context.get("application", ""):
            if action_type == "navigate":
                action.intent = "research" if "search" in target else "web_browsing"
        
        # Communication
        elif any(comm in target for comm in ["mail", "message", "chat"]):
            action.intent = "communication"
        
        # Default intent based on patterns
        else:
            action.intent = self._infer_intent_from_patterns(action)
    
    def _analyze_action_significance(self, action: UserAction):
        """Determine how significant this action is"""
        
        significance = 0.5  # Base significance
        
        # High significance actions
        if action.action_type in ["open", "save", "create", "delete"]:
            significance += 0.3
        
        # Important targets
        if any(important in action.target.lower() for important in ["document", "project", "important", "work"]):
            significance += 0.2
        
        # Rare actions are more significant
        action_frequency = self.interaction_patterns.get(f"{action.action_type}:{action.target}", 0)
        if action_frequency < 5:
            significance += 0.1
        
        # Actions during focused work sessions
        if self.current_context.get("work_session"):
            significance += 0.1
        
        # Context-based significance
        if action.context.get("file_type") in ["py", "js", "html", "css"]:
            significance += 0.15  # Code files are important
        
        action.significance = min(1.0, significance)
    
    def _detect_workflow_membership(self, action: UserAction):
        """Detect which workflow this action belongs to"""
        
        # Check if action continues an active workflow
        for workflow_id, workflow in self.active_workflows.items():
            if self._action_fits_workflow(action, workflow):
                workflow.actions.append(action)
                action.workflow_stage = f"{workflow.name}_step_{len(workflow.actions)}"
                return
        
        # Check if action starts a new workflow
        workflow = self._detect_new_workflow(action)
        if workflow:
            self.active_workflows[workflow.workflow_id] = workflow
            action.workflow_stage = f"{workflow.name}_start"
    
    def _action_fits_workflow(self, action: UserAction, workflow: UserWorkflow) -> bool:
        """Check if action fits into existing workflow"""
        
        # Time-based: action should be within reasonable time of last action
        if workflow.actions:
            last_action = workflow.actions[-1]
            time_diff = (action.timestamp - last_action.timestamp).seconds
            if time_diff > 300:  # 5 minutes gap = workflow break
                return False
        
        # Context-based: should be related to workflow context
        workflow_apps = {a.context.get("application") for a in workflow.actions}
        if action.context.get("application") in workflow_apps:
            return True
        
        # Intent-based: similar intent
        workflow_intents = {a.intent for a in workflow.actions}
        if action.intent in workflow_intents:
            return True
        
        # Target-based: working with related files/objects
        workflow_targets = {a.target for a in workflow.actions}
        if any(target in action.target or action.target in target for target in workflow_targets):
            return True
        
        return False
    
    def _detect_new_workflow(self, action: UserAction) -> Optional[UserWorkflow]:
        """Detect if action starts a new workflow"""
        
        # High-significance actions often start workflows
        if action.significance > 0.7:
            workflow_id = f"workflow_{int(time.time())}"
            
            # Infer workflow name and goal based on action
            if action.intent == "file_management":
                name = "File Organization"
                description = f"Managing files starting with {action.target}"
                goal = "Organize and manage files"
            elif action.intent == "content_creation":
                name = "Content Creation"
                description = f"Creating content in {action.target}"
                goal = "Create or edit content"
            elif action.intent == "code_development":
                name = "Code Development"
                description = f"Developing code in {action.target}"
                goal = "Write or modify code"
            elif action.intent == "research":
                name = "Research Session"
                description = f"Researching topic related to {action.target}"
                goal = "Gather information"
            else:
                name = f"{action.intent.title()} Session"
                description = f"Working with {action.target}"
                goal = f"Complete {action.intent} task"
            
            workflow = UserWorkflow(
                workflow_id=workflow_id,
                name=name,
                description=description,
                actions=[action],
                start_time=action.timestamp,
                goal=goal
            )
            
            return workflow
        
        return None
    
    def _find_action_relationships(self, action: UserAction):
        """Find relationships between this action and previous actions"""
        
        relationships = []
        
        # Look at recent actions (last 50)
        recent_actions = list(self.actions_history)[-50:]
        
        for prev_action in recent_actions:
            # Same target relationship
            if action.target == prev_action.target:
                relationships.append(f"same_target:{prev_action.timestamp.isoformat()}")
            
            # Same application relationship
            if (action.context.get("application") == prev_action.context.get("application") and
                action.context.get("application")):
                relationships.append(f"same_app:{prev_action.timestamp.isoformat()}")
            
            # Sequential file operations
            if (action.intent == prev_action.intent and 
                action.intent in ["file_management", "content_creation"]):
                relationships.append(f"sequential_{action.intent}:{prev_action.timestamp.isoformat()}")
            
            # Rapid succession (within 30 seconds)
            time_diff = (action.timestamp - prev_action.timestamp).seconds
            if time_diff < 30:
                relationships.append(f"rapid_sequence:{prev_action.timestamp.isoformat()}")
        
        action.relationships = relationships[:10]  # Keep top 10 relationships
    
    def _update_behavioral_patterns(self, action: UserAction):
        """Update learned behavioral patterns"""
        
        # App usage patterns
        app = action.context.get("application")
        if app:
            hour = action.timestamp.hour
            day_of_week = action.timestamp.weekday()
            
            if app not in self.app_usage_patterns:
                self.app_usage_patterns[app] = {
                    "total_uses": 0,
                    "hourly_pattern": defaultdict(int),
                    "daily_pattern": defaultdict(int),
                    "common_actions": defaultdict(int)
                }
            
            self.app_usage_patterns[app]["total_uses"] += 1
            self.app_usage_patterns[app]["hourly_pattern"][hour] += 1
            self.app_usage_patterns[app]["daily_pattern"][day_of_week] += 1
            self.app_usage_patterns[app]["common_actions"][action.action_type] += 1
        
        # Time patterns
        time_key = f"{action.timestamp.hour}:{action.timestamp.minute//15*15}"  # 15-minute buckets
        self.time_patterns[time_key].append({
            "action": action.action_type,
            "target": action.target,
            "intent": action.intent
        })
        
        # File patterns
        if "file" in action.context:
            file_ext = action.context.get("file_type", "unknown")
            if file_ext not in self.file_patterns:
                self.file_patterns[file_ext] = {
                    "total_interactions": 0,
                    "common_actions": defaultdict(int),
                    "apps_used": defaultdict(int)
                }
            
            self.file_patterns[file_ext]["total_interactions"] += 1
            self.file_patterns[file_ext]["common_actions"][action.action_type] += 1
            if app:
                self.file_patterns[file_ext]["apps_used"][app] += 1
        
        # Interaction patterns
        pattern_key = f"{action.action_type}:{action.target}"
        self.interaction_patterns[pattern_key] += 1
    
    def _update_current_context(self, action: UserAction):
        """Update the current context based on action"""
        
        # Update active app
        if action.context.get("application"):
            self.current_context["active_app"] = action.context["application"]
        
        # Update active window
        if action.context.get("window_title"):
            self.current_context["active_window"] = action.context["window_title"]
        
        # Infer current task from recent actions and intent
        if action.intent:
            self.current_context["current_task"] = action.intent
        
        # Determine focus area
        if action.intent in ["code_development", "content_creation"]:
            self.current_context["focus_area"] = "creative_work"
        elif action.intent in ["file_management", "file_exploration"]:
            self.current_context["focus_area"] = "organization"
        elif action.intent in ["research", "web_browsing"]:
            self.current_context["focus_area"] = "information_gathering"
        elif action.intent == "communication":
            self.current_context["focus_area"] = "communication"
        
        # Track work sessions
        if action.significance > 0.6:
            session_key = f"session_{action.timestamp.date()}_{action.timestamp.hour}"
            self.current_context["work_session"] = session_key
    
    def _analyze_workflow_transitions(self, action: UserAction):
        """Analyze workflow completion and transitions"""
        
        # Check for workflow completion indicators
        completed_workflows = []
        
        for workflow_id, workflow in self.active_workflows.items():
            # Time-based completion (no activity for 10 minutes)
            if workflow.actions:
                last_action_time = workflow.actions[-1].timestamp
                if (action.timestamp - last_action_time).seconds > 600:
                    workflow.end_time = last_action_time
                    workflow.success = True  # Assume success if no explicit failure
                    completed_workflows.append(workflow_id)
            
            # Context-based completion (major context switch)
            if self._is_major_context_switch(action, workflow):
                workflow.end_time = action.timestamp
                workflow.success = True
                completed_workflows.append(workflow_id)
        
        # Move completed workflows to history
        for workflow_id in completed_workflows:
            workflow = self.active_workflows.pop(workflow_id)
            self.workflows[workflow_id] = workflow
            self._extract_workflow_patterns(workflow)
            logger.info(f"Completed workflow: {workflow.name} with {len(workflow.actions)} actions")
    
    def _is_major_context_switch(self, action: UserAction, workflow: UserWorkflow) -> bool:
        """Determine if action represents a major context switch from workflow"""
        
        # Different application and intent
        workflow_apps = {a.context.get("application") for a in workflow.actions}
        workflow_intents = {a.intent for a in workflow.actions}
        
        if (action.context.get("application") not in workflow_apps and 
            action.intent not in workflow_intents):
            return True
        
        # Explicit completion actions
        if action.action_type in ["close", "save", "exit"] and action.target in workflow.name.lower():
            return True
        
        return False
    
    def _extract_workflow_patterns(self, workflow: UserWorkflow):
        """Extract patterns from completed workflow"""
        
        # Common action sequences
        action_sequence = [a.action_type for a in workflow.actions]
        if len(action_sequence) >= 3:
            for i in range(len(action_sequence) - 2):
                pattern = "->".join(action_sequence[i:i+3])
                workflow.patterns.append(f"sequence:{pattern}")
        
        # Time patterns
        duration = (workflow.end_time - workflow.start_time).seconds if workflow.end_time else 0
        workflow.patterns.append(f"duration:{duration}s")
        
        # App transitions
        apps_used = [a.context.get("application") for a in workflow.actions if a.context.get("application")]
        unique_apps = list(dict.fromkeys(apps_used))  # Preserve order, remove duplicates
        if len(unique_apps) > 1:
            workflow.patterns.append(f"app_flow:{'->'.join(unique_apps)}")
    
    def _generate_contextual_insights(self):
        """Generate high-level insights about user behavior"""
        
        # Only generate insights periodically to avoid spam
        if len(self.actions_history) % 100 != 0:
            return
        
        insights = []
        
        # Workflow insights
        if self.workflows:
            insights.extend(self._analyze_workflow_insights())
        
        # App usage insights
        if self.app_usage_patterns:
            insights.extend(self._analyze_app_usage_insights())
        
        # Time pattern insights
        if self.time_patterns:
            insights.extend(self._analyze_time_pattern_insights())
        
        # Store new insights
        for insight in insights:
            self.contextual_insights[insight.insight_id] = insight
            logger.info(f"Generated insight: {insight.title}")
    
    def _analyze_workflow_insights(self) -> List[ContextualInsight]:
        """Analyze workflow patterns to generate insights"""
        
        insights = []
        
        # Most common workflow types
        workflow_types = defaultdict(int)
        for workflow in self.workflows.values():
            workflow_types[workflow.name] += 1
        
        if workflow_types:
            most_common = max(workflow_types.items(), key=lambda x: x[1])
            insight = ContextualInsight(
                insight_id=f"workflow_common_{int(time.time())}",
                category="workflow",
                title="Most Common Workflow",
                description=f"You frequently engage in '{most_common[0]}' workflows ({most_common[1]} times)",
                evidence=[f"Workflow '{most_common[0]}' occurred {most_common[1]} times"],
                confidence=0.9,
                impact="medium",
                actionable=True,
                recommendations=[
                    f"Consider creating shortcuts for '{most_common[0]}' tasks",
                    "Look for automation opportunities in this workflow"
                ],
                timestamp=datetime.now()
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_app_usage_insights(self) -> List[ContextualInsight]:
        """Analyze app usage patterns"""
        
        insights = []
        
        # Peak usage hours
        all_hourly_usage = defaultdict(int)
        for app_data in self.app_usage_patterns.values():
            for hour, count in app_data["hourly_pattern"].items():
                all_hourly_usage[hour] += count
        
        if all_hourly_usage:
            peak_hour = max(all_hourly_usage.items(), key=lambda x: x[1])
            insight = ContextualInsight(
                insight_id=f"usage_peak_{int(time.time())}",
                category="pattern",
                title="Peak Productivity Hours",
                description=f"You're most active around {peak_hour[0]}:00 with {peak_hour[1]} interactions",
                evidence=[f"Hour {peak_hour[0]} has {peak_hour[1]} total interactions"],
                confidence=0.8,
                impact="high",
                actionable=True,
                recommendations=[
                    f"Schedule important tasks around {peak_hour[0]}:00",
                    "Avoid scheduling meetings during peak productivity hours"
                ],
                timestamp=datetime.now()
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_time_pattern_insights(self) -> List[ContextualInsight]:
        """Analyze time-based behavior patterns"""
        
        insights = []
        
        # Most productive time slots
        productive_slots = []
        for time_slot, actions in self.time_patterns.items():
            if len(actions) > 5:  # Significant activity
                creative_actions = sum(1 for a in actions if a["intent"] in ["code_development", "content_creation"])
                if creative_actions > len(actions) * 0.5:  # More than 50% creative work
                    productive_slots.append((time_slot, creative_actions))
        
        if productive_slots:
            best_slot = max(productive_slots, key=lambda x: x[1])
            insight = ContextualInsight(
                insight_id=f"productive_time_{int(time.time())}",
                category="pattern",
                title="Prime Creative Hours",
                description=f"You do your best creative work around {best_slot[0]}",
                evidence=[f"Creative actions peak at {best_slot[0]} with {best_slot[1]} instances"],
                confidence=0.85,
                impact="high",
                actionable=True,
                recommendations=[
                    f"Block {best_slot[0]} for creative work",
                    "Avoid routine tasks during prime creative hours"
                ],
                timestamp=datetime.now()
            )
            insights.append(insight)
        
        return insights
    
    def _infer_intent_from_patterns(self, action: UserAction) -> str:
        """Infer intent based on learned patterns"""
        
        # Check interaction patterns
        pattern_key = f"{action.action_type}:{action.target}"
        if self.interaction_patterns.get(pattern_key, 0) > 10:
            # This is a common action, infer from context
            if self.current_context.get("current_task"):
                return self.current_context["current_task"]
        
        # Check recent actions for context
        if len(self.actions_history) > 0:
            recent_intents = [a.intent for a in list(self.actions_history)[-5:] if a.intent]
            if recent_intents:
                most_common_intent = max(set(recent_intents), key=recent_intents.count)
                return most_common_intent
        
        return "general_activity"
    
    def get_contextual_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of user context and behavior"""
        
        return {
            "current_context": self.current_context,
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.workflows),
            "total_actions": len(self.actions_history),
            "recent_insights": len([i for i in self.contextual_insights.values() 
                                 if (datetime.now() - i.timestamp).days < 1]),
            "top_apps": dict(sorted(
                [(app, data["total_uses"]) for app, data in self.app_usage_patterns.items()],
                key=lambda x: x[1], reverse=True
            )[:5]),
            "productivity_focus": self.current_context.get("focus_area", "unknown"),
            "session_summary": self._get_current_session_summary()
        }
    
    def _get_current_session_summary(self) -> Dict[str, Any]:
        """Get summary of current work session"""
        
        # Actions in last hour
        recent_actions = [a for a in self.actions_history 
                         if (datetime.now() - a.timestamp).seconds < 3600]
        
        if not recent_actions:
            return {"status": "inactive"}
        
        # Analyze recent activity
        intents = [a.intent for a in recent_actions if a.intent]
        apps = [a.context.get("application") for a in recent_actions if a.context.get("application")]
        
        return {
            "status": "active",
            "duration_minutes": int((datetime.now() - recent_actions[0].timestamp).seconds / 60),
            "actions_count": len(recent_actions),
            "primary_intent": max(set(intents), key=intents.count) if intents else "unknown",
            "apps_used": len(set(apps)),
            "productivity_score": sum(a.significance for a in recent_actions) / len(recent_actions)
        }
    
    def _save_memory(self):
        """Save memory state to disk"""
        
        try:
            # Save actions (last 1000 for performance)
            actions_data = []
            for action in list(self.actions_history)[-1000:]:
                actions_data.append({
                    "timestamp": action.timestamp.isoformat(),
                    "action_type": action.action_type,
                    "target": action.target,
                    "context": action.context,
                    "intent": action.intent,
                    "workflow_stage": action.workflow_stage,
                    "significance": action.significance,
                    "relationships": action.relationships
                })
            
            with open(self.cache_dir / "actions_history.json", "w") as f:
                json.dump(actions_data, f, indent=2)
            
            # Save workflows
            workflows_data = {}
            for wf_id, workflow in self.workflows.items():
                workflows_data[wf_id] = {
                    "workflow_id": workflow.workflow_id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "start_time": workflow.start_time.isoformat(),
                    "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
                    "goal": workflow.goal,
                    "success": workflow.success,
                    "patterns": workflow.patterns,
                    "frequency": workflow.frequency,
                    "action_count": len(workflow.actions)
                }
            
            with open(self.cache_dir / "workflows.json", "w") as f:
                json.dump(workflows_data, f, indent=2)
            
            # Save patterns
            patterns_data = {
                "app_usage_patterns": dict(self.app_usage_patterns),
                "time_patterns": {k: v[-50:] for k, v in self.time_patterns.items()},  # Keep last 50
                "file_patterns": dict(self.file_patterns),
                "interaction_patterns": dict(self.interaction_patterns)
            }
            
            with open(self.cache_dir / "patterns.json", "w") as f:
                json.dump(patterns_data, f, indent=2)
            
            # Save insights
            insights_data = {}
            for insight_id, insight in self.contextual_insights.items():
                insights_data[insight_id] = {
                    "insight_id": insight.insight_id,
                    "category": insight.category,
                    "title": insight.title,
                    "description": insight.description,
                    "evidence": insight.evidence,
                    "confidence": insight.confidence,
                    "impact": insight.impact,
                    "actionable": insight.actionable,
                    "recommendations": insight.recommendations,
                    "timestamp": insight.timestamp.isoformat()
                }
            
            with open(self.cache_dir / "insights.json", "w") as f:
                json.dump(insights_data, f, indent=2)
            
            logger.info("Intelligent context memory saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def _load_memory(self):
        """Load memory state from disk"""
        
        try:
            # Load patterns
            patterns_file = self.cache_dir / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file, "r") as f:
                    patterns_data = json.load(f)
                    self.app_usage_patterns = defaultdict(dict, patterns_data.get("app_usage_patterns", {}))
                    self.time_patterns = defaultdict(list, patterns_data.get("time_patterns", {}))
                    self.file_patterns = defaultdict(dict, patterns_data.get("file_patterns", {}))
                    self.interaction_patterns = defaultdict(int, patterns_data.get("interaction_patterns", {}))
            
            # Load workflows
            workflows_file = self.cache_dir / "workflows.json"
            if workflows_file.exists():
                with open(workflows_file, "r") as f:
                    workflows_data = json.load(f)
                    for wf_id, wf_data in workflows_data.items():
                        workflow = UserWorkflow(
                            workflow_id=wf_data["workflow_id"],
                            name=wf_data["name"],
                            description=wf_data["description"],
                            actions=[],  # Don't load all actions for performance
                            start_time=datetime.fromisoformat(wf_data["start_time"]),
                            end_time=datetime.fromisoformat(wf_data["end_time"]) if wf_data["end_time"] else None,
                            goal=wf_data["goal"],
                            success=wf_data["success"],
                            patterns=wf_data["patterns"],
                            frequency=wf_data["frequency"]
                        )
                        self.workflows[wf_id] = workflow
            
            logger.info("Intelligent context memory loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
    
    def __del__(self):
        """Save memory on destruction"""
        self._save_memory()

# Global instance
intelligent_memory = IntelligentContextMemory()

# Integration functions for the broader system
async def record_screen_change(screen_data: Dict[str, Any]):
    """Record screen change with intelligent analysis"""
    
    action = intelligent_memory.record_user_action(
        action_type="screen_change",
        target=screen_data.get("active_window", "unknown"),
        context={
            "application": screen_data.get("active_application", "unknown"),
            "window_title": screen_data.get("active_window", ""),
            "screen_content": screen_data.get("text_content", []),
            "ui_elements": screen_data.get("ui_elements", []),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    return action

async def record_process_change(process_data: Dict[str, Any]):
    """Record process change with intelligent analysis"""
    
    action = intelligent_memory.record_user_action(
        action_type="process_change",
        target=process_data.get("name", "unknown"),
        context={
            "process_name": process_data.get("name", ""),
            "pid": process_data.get("pid", 0),
            "cpu_percent": process_data.get("cpu_percent", 0),
            "memory_percent": process_data.get("memory_percent", 0),
            "status": process_data.get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    return action

async def record_user_interaction(interaction_type: str, target: str, context: Dict[str, Any]):
    """Record user interaction with intelligent analysis"""
    
    return intelligent_memory.record_user_action(interaction_type, target, context)

def get_intelligent_context() -> Dict[str, Any]:
    """Get current intelligent context for other systems"""
    
    return intelligent_memory.get_contextual_summary()

if __name__ == "__main__":
    # Test the intelligent memory system
    async def test_intelligent_memory():
        
        print("🧠 Testing Intelligent Context Memory System")
        
        # Simulate user actions
        test_actions = [
            ("click", "Documents folder", {"application": "Finder", "window_title": "Finder"}),
            ("open", "project.py", {"application": "VSCode", "file_type": "py"}),
            ("type", "code content", {"application": "VSCode", "file": "project.py"}),
            ("save", "project.py", {"application": "VSCode", "file_type": "py"}),
            ("click", "Terminal", {"application": "Terminal"}),
            ("type", "python project.py", {"application": "Terminal"}),
        ]
        
        for action_type, target, context in test_actions:
            action = intelligent_memory.record_user_action(action_type, target, context)
            print(f"Action: {action_type} -> {target} (Intent: {action.intent}, Significance: {action.significance:.2f})")
            await asyncio.sleep(1)  # Simulate time between actions
        
        # Get summary
        summary = intelligent_memory.get_contextual_summary()
        print("\n📊 Context Summary:")
        print(json.dumps(summary, indent=2, default=str))
    
    asyncio.run(test_intelligent_memory())