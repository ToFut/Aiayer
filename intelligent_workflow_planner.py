#!/usr/bin/env python3
"""
Intelligent Workflow Planner

Creates step-by-step workflows for complex UI automation tasks.
Understands current context and creates intelligent action sequences.

This addresses the critical case study: "Search in google 'SEGEV HALFON'"
- Understands current UI context (user already in Google website)
- Creates step-by-step workflow plan
- Determines where and what to click/type
- Executes complete goal achievement
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger('workflow_planner')

class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    ANALYZE = "analyze"
    SCROLL = "scroll"
    HOTKEY = "hotkey"

@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    step_number: int
    action_type: ActionType
    target: str
    value: str = ""
    description: str = ""
    expected_result: str = ""
    confidence: float = 0.0
    coordinates: Optional[Tuple[int, int]] = None
    fallback_strategies: List[str] = None

@dataclass
class WorkflowPlan:
    """Complete workflow plan for achieving a goal"""
    goal: str
    context_analysis: Dict[str, Any]
    steps: List[WorkflowStep]
    estimated_duration: int
    confidence: float
    fallback_plan: Optional['WorkflowPlan'] = None

class IntelligentWorkflowPlanner:
    """
    Creates intelligent, context-aware workflow plans for complex UI automation
    """
    
    def __init__(self):
        self.workflow_patterns = self._initialize_workflow_patterns()
        self.context_analyzers = self._initialize_context_analyzers()
        
    def _initialize_workflow_patterns(self) -> Dict[str, Dict]:
        """Initialize common workflow patterns"""
        return {
            "web_search": {
                "triggers": ["search", "find", "google", "look up", "search for"],
                "required_context": ["browser", "search_engine"],
                "pattern": [
                    ("analyze", "current_page", "Understand current page context"),
                    ("click", "search_box", "Click on search input field"),
                    ("type", "search_query", "Enter search terms"),
                    ("click", "search_button", "Execute search"),
                    ("wait", "results", "Wait for results to load")
                ]
            },
            "file_operation": {
                "triggers": ["open file", "save file", "create document", "folder"],
                "required_context": ["file_system", "application"],
                "pattern": [
                    ("analyze", "current_app", "Understand current application"),
                    ("hotkey", "cmd+o", "Open file dialog"),
                    ("wait", "dialog", "Wait for file dialog"),
                    ("navigate", "target_folder", "Navigate to target location"),
                    ("select", "target_file", "Select target file")
                ]
            },
            "application_workflow": {
                "triggers": ["open app", "launch", "start", "run"],
                "required_context": ["desktop", "launcher"],
                "pattern": [
                    ("hotkey", "cmd+space", "Open Spotlight search"),
                    ("wait", "spotlight", "Wait for Spotlight to appear"),
                    ("type", "app_name", "Type application name"),
                    ("wait", "suggestions", "Wait for search suggestions"),
                    ("click", "enter", "Launch application")
                ]
            },
            "navigation_workflow": {
                "triggers": ["go to", "navigate", "visit", "browse to"],
                "required_context": ["browser"],
                "pattern": [
                    ("click", "address_bar", "Click address bar"),
                    ("hotkey", "cmd+a", "Select all current text"),
                    ("type", "url", "Type new URL"),
                    ("click", "enter", "Navigate to URL")
                ]
            }
        }
    
    def _initialize_context_analyzers(self) -> Dict[str, callable]:
        """Initialize context analysis functions"""
        return {
            "browser_context": self._analyze_browser_context,
            "search_context": self._analyze_search_context,
            "application_context": self._analyze_application_context,
            "desktop_context": self._analyze_desktop_context
        }
    
    async def create_workflow_plan(self, goal: str, current_context: Dict[str, Any]) -> WorkflowPlan:
        """
        Create intelligent workflow plan based on goal and current context
        
        This is the main method that handles the case study:
        "Search in google 'SEGEV HALFON'"
        """
        logger.info(f"🧠 Creating workflow plan for goal: '{goal}'")
        
        # Analyze the goal and extract intent
        goal_analysis = await self._analyze_goal(goal)
        
        # Analyze current context
        context_analysis = await self._analyze_current_context(current_context)
        
        # Determine workflow pattern
        workflow_pattern = await self._determine_workflow_pattern(goal_analysis, context_analysis)
        
        # Create specific workflow steps
        workflow_steps = await self._create_workflow_steps(goal_analysis, context_analysis, workflow_pattern)
        
        # Calculate confidence and timing
        confidence = await self._calculate_workflow_confidence(workflow_steps, context_analysis)
        estimated_duration = self._estimate_workflow_duration(workflow_steps)
        
        # Create fallback plan if confidence is low
        fallback_plan = None
        if confidence < 0.7:
            fallback_plan = await self._create_fallback_plan(goal, context_analysis)
        
        workflow = WorkflowPlan(
            goal=goal,
            context_analysis=context_analysis,
            steps=workflow_steps,
            estimated_duration=estimated_duration,
            confidence=confidence,
            fallback_plan=fallback_plan
        )
        
        logger.info(f"✅ Created workflow plan with {len(workflow_steps)} steps, confidence: {confidence:.2f}")
        return workflow
    
    async def _analyze_goal(self, goal: str) -> Dict[str, Any]:
        """Analyze goal to extract intent, target, and action type"""
        goal_lower = goal.lower()
        
        analysis = {
            "raw_goal": goal,
            "intent": "unknown",
            "action_type": "unknown",
            "target": "",
            "parameters": {},
            "keywords": goal_lower.split()
        }
        
        # Search intent detection
        if any(keyword in goal_lower for keyword in ["search", "find", "look up", "google"]):
            analysis["intent"] = "search"
            analysis["action_type"] = "web_search"
            
            # Extract search query
            # Handle patterns like "search in google 'SEGEV HALFON'" or "google search SEGEV HALFON"
            if "'" in goal:
                # Extract quoted search terms
                import re
                quotes = re.findall(r"'([^']*)'", goal)
                if quotes:
                    analysis["target"] = quotes[0]
                    analysis["parameters"]["search_query"] = quotes[0]
            elif "search" in goal_lower:
                # Extract everything after "search" (or similar)
                for trigger in ["search for", "search in google", "google search", "search"]:
                    if trigger in goal_lower:
                        parts = goal_lower.split(trigger, 1)
                        if len(parts) > 1:
                            query = parts[1].strip().strip("'\"")
                            analysis["target"] = query
                            analysis["parameters"]["search_query"] = query
                            break
        
        # Navigation intent detection
        elif any(keyword in goal_lower for keyword in ["go to", "navigate", "visit", "open website"]):
            analysis["intent"] = "navigation"
            analysis["action_type"] = "navigation_workflow"
            
            # Extract URL or website name
            url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            urls = re.findall(url_pattern, goal)
            if urls:
                analysis["target"] = urls[0]
                analysis["parameters"]["url"] = urls[0]
        
        # Application opening intent
        elif any(keyword in goal_lower for keyword in ["open", "launch", "start", "run"]):
            analysis["intent"] = "application_launch"
            analysis["action_type"] = "application_workflow"
            
            # Extract application name
            for trigger in ["open", "launch", "start", "run"]:
                if trigger in goal_lower:
                    parts = goal_lower.split(trigger, 1)
                    if len(parts) > 1:
                        app_name = parts[1].strip()
                        analysis["target"] = app_name
                        analysis["parameters"]["app_name"] = app_name
                        break
        
        # File operation intent
        elif any(keyword in goal_lower for keyword in ["save", "create", "file", "document"]):
            analysis["intent"] = "file_operation"
            analysis["action_type"] = "file_operation"
        
        logger.info(f"Goal analysis: {analysis['intent']} - {analysis['target']}")
        return analysis
    
    async def _analyze_current_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current UI context to understand where user is"""
        analysis = {
            "detected_environment": "unknown",
            "current_application": "unknown",
            "ui_state": "unknown",
            "available_actions": [],
            "context_confidence": 0.0,
            "special_elements": []
        }
        
        if not context:
            return analysis
        
        # Extract context from screen analysis
        layers = context.get('layers', {})
        
        # Application context
        app_analysis = layers.get('application_analysis', {})
        if app_analysis:
            analysis["detected_environment"] = app_analysis.get('detected_app', 'unknown')
            analysis["context_confidence"] = app_analysis.get('confidence', 0.0)
        
        window_context = layers.get('window_context', {})
        if window_context:
            analysis["current_application"] = window_context.get('application_name', 'Unknown')
        
        # Text analysis for understanding page content
        text_analysis = layers.get('text_analysis', {})
        if text_analysis:
            all_text = text_analysis.get('all_text', '').lower()
            
            # Detect if we're on Google
            if any(indicator in all_text for indicator in ['google', 'search', 'google.com']):
                analysis["detected_environment"] = "google_search"
                analysis["ui_state"] = "search_page"
                
                # Check for search box
                if any(indicator in all_text for indicator in ['search', 'google search']):
                    analysis["available_actions"].append("search_input_available")
                    analysis["special_elements"].append({
                        "type": "search_box",
                        "context": "Google search input field detected"
                    })
        
        # UI element analysis
        ui_analysis = layers.get('ui_analysis', {})
        if ui_analysis:
            elements = ui_analysis.get('elements', [])
            
            for element in elements:
                element_type = element.get('type', '').lower()
                
                # Detect interactive elements
                if 'button' in element_type:
                    analysis["available_actions"].append("buttons_available")
                elif 'text_field' in element_type:
                    analysis["available_actions"].append("text_input_available")
                elif 'interactive' in element_type:
                    analysis["available_actions"].append("interactive_elements_available")
        
        logger.info(f"Context analysis: {analysis['detected_environment']} - {analysis['current_application']}")
        return analysis
    
    async def _determine_workflow_pattern(self, goal_analysis: Dict, context_analysis: Dict) -> str:
        """Determine which workflow pattern to use"""
        intent = goal_analysis.get('intent', 'unknown')
        action_type = goal_analysis.get('action_type', 'unknown')
        current_env = context_analysis.get('detected_environment', 'unknown')
        
        # Special case: Google search workflow
        if intent == "search" and "google" in current_env:
            return "google_search_optimized"
        elif intent == "search":
            return "web_search"
        elif action_type in self.workflow_patterns:
            return action_type
        else:
            return "generic_workflow"
    
    async def _create_workflow_steps(self, goal_analysis: Dict, context_analysis: Dict, pattern: str) -> List[WorkflowStep]:
        """Create specific workflow steps based on pattern and context"""
        steps = []
        
        # Handle Google search case study specifically
        if pattern == "google_search_optimized":
            steps = await self._create_google_search_steps(goal_analysis, context_analysis)
        elif pattern == "web_search":
            steps = await self._create_web_search_steps(goal_analysis, context_analysis)
        elif pattern in self.workflow_patterns:
            steps = await self._create_pattern_steps(pattern, goal_analysis, context_analysis)
        else:
            steps = await self._create_generic_steps(goal_analysis, context_analysis)
        
        return steps
    
    async def _create_google_search_steps(self, goal_analysis: Dict, context_analysis: Dict) -> List[WorkflowStep]:
        """
        Create optimized Google search workflow
        
        This specifically handles: "Search in google 'SEGEV HALFON'"
        When user is already on Google website
        """
        steps = []
        search_query = goal_analysis.get('parameters', {}).get('search_query', goal_analysis.get('target', ''))
        
        logger.info(f"Creating Google search workflow for query: '{search_query}'")
        
        # Step 1: Analyze current page to understand Google interface
        steps.append(WorkflowStep(
            step_number=1,
            action_type=ActionType.ANALYZE,
            target="google_page",
            description="Analyze Google page layout and search box location",
            expected_result="Identify search input field location",
            confidence=0.9
        ))
        
        # Step 2: Click on Google search box
        steps.append(WorkflowStep(
            step_number=2,
            action_type=ActionType.CLICK,
            target="search box",
            description="Click on Google search input field to focus it",
            expected_result="Search box becomes active and focused",
            confidence=0.8,
            fallback_strategies=[
                "Try clicking center of search area",
                "Use Tab key to focus search box",
                "Click on 'Google Search' text area"
            ]
        ))
        
        # Step 3: Clear any existing search text
        steps.append(WorkflowStep(
            step_number=3,
            action_type=ActionType.HOTKEY,
            target="cmd+a",
            description="Select all existing text in search box",
            expected_result="Any existing search text is selected",
            confidence=0.9
        ))
        
        # Step 4: Type the search query
        steps.append(WorkflowStep(
            step_number=4,
            action_type=ActionType.TYPE,
            target="search_query",
            value=search_query,
            description=f"Type the search query: '{search_query}'",
            expected_result=f"Search box contains '{search_query}'",
            confidence=0.9
        ))
        
        # Step 5: Execute search
        steps.append(WorkflowStep(
            step_number=5,
            action_type=ActionType.HOTKEY,
            target="enter",
            description="Press Enter to execute search",
            expected_result="Google search results page loads",
            confidence=0.9,
            fallback_strategies=[
                "Click Google Search button",
                "Click I'm Feeling Lucky button if visible"
            ]
        ))
        
        # Step 6: Wait for results
        steps.append(WorkflowStep(
            step_number=6,
            action_type=ActionType.WAIT,
            target="search_results",
            value="3",  # seconds
            description="Wait for search results to load",
            expected_result="Search results are displayed",
            confidence=0.8
        ))
        
        return steps
    
    async def _create_web_search_steps(self, goal_analysis: Dict, context_analysis: Dict) -> List[WorkflowStep]:
        """Create general web search workflow"""
        # Similar to Google search but more generic
        # Implementation for other search engines or when not on Google
        return []
    
    async def _create_pattern_steps(self, pattern: str, goal_analysis: Dict, context_analysis: Dict) -> List[WorkflowStep]:
        """Create steps based on predefined patterns"""
        if pattern not in self.workflow_patterns:
            return []
        
        pattern_data = self.workflow_patterns[pattern]
        pattern_steps = pattern_data["pattern"]
        
        steps = []
        for i, (action, target, description) in enumerate(pattern_steps):
            step = WorkflowStep(
                step_number=i + 1,
                action_type=ActionType(action),
                target=target,
                description=description,
                confidence=0.7
            )
            steps.append(step)
        
        return steps
    
    async def _create_generic_steps(self, goal_analysis: Dict, context_analysis: Dict) -> List[WorkflowStep]:
        """Create generic workflow steps when no specific pattern matches"""
        return [
            WorkflowStep(
                step_number=1,
                action_type=ActionType.ANALYZE,
                target="current_screen",
                description="Analyze current screen for relevant elements",
                confidence=0.6
            )
        ]
    
    async def _calculate_workflow_confidence(self, steps: List[WorkflowStep], context_analysis: Dict) -> float:
        """Calculate overall confidence in workflow success"""
        if not steps:
            return 0.0
        
        step_confidences = [step.confidence for step in steps if step.confidence > 0]
        base_confidence = sum(step_confidences) / len(step_confidences) if step_confidences else 0.5
        
        # Adjust based on context confidence
        context_confidence = context_analysis.get('context_confidence', 0.5)
        
        # Weight: 70% step confidence, 30% context confidence
        final_confidence = (base_confidence * 0.7) + (context_confidence * 0.3)
        
        return min(final_confidence, 1.0)
    
    def _estimate_workflow_duration(self, steps: List[WorkflowStep]) -> int:
        """Estimate workflow duration in seconds"""
        duration_map = {
            ActionType.CLICK: 0.5,
            ActionType.TYPE: 1.0,
            ActionType.WAIT: 2.0,
            ActionType.ANALYZE: 1.5,
            ActionType.SCROLL: 0.5,
            ActionType.HOTKEY: 0.3
        }
        
        total_duration = 0
        for step in steps:
            base_time = duration_map.get(step.action_type, 1.0)
            
            # Add extra time for typing based on content length
            if step.action_type == ActionType.TYPE and step.value:
                base_time += len(step.value) * 0.1
            
            # Add extra time for wait actions
            if step.action_type == ActionType.WAIT and step.value:
                try:
                    base_time = float(step.value)
                except ValueError:
                    pass
            
            total_duration += base_time
        
        return int(total_duration)
    
    async def _create_fallback_plan(self, goal: str, context_analysis: Dict) -> Optional[WorkflowPlan]:
        """Create a fallback plan for low-confidence workflows"""
        # Simplified fallback approach
        fallback_steps = [
            WorkflowStep(
                step_number=1,
                action_type=ActionType.ANALYZE,
                target="screen",
                description="Re-analyze screen for manual guidance",
                confidence=0.8
            )
        ]
        
        return WorkflowPlan(
            goal=f"Fallback: {goal}",
            context_analysis=context_analysis,
            steps=fallback_steps,
            estimated_duration=5,
            confidence=0.5
        )
    
    # Context analyzer methods
    async def _analyze_browser_context(self, context: Dict) -> Dict:
        """Analyze browser-specific context"""
        return {}
    
    async def _analyze_search_context(self, context: Dict) -> Dict:
        """Analyze search engine context"""
        return {}
    
    async def _analyze_application_context(self, context: Dict) -> Dict:
        """Analyze application-specific context"""
        return {}
    
    async def _analyze_desktop_context(self, context: Dict) -> Dict:
        """Analyze desktop environment context"""
        return {}

# Example usage and testing
async def test_google_search_workflow():
    """Test the Google search workflow creation"""
    planner = IntelligentWorkflowPlanner()
    
    # Simulate the case study scenario
    goal = "Search in google 'SEGEV HALFON'"
    
    # Mock context that represents user being on Google
    mock_context = {
        "layers": {
            "application_analysis": {
                "detected_app": "browsers",
                "confidence": 0.9
            },
            "window_context": {
                "application_name": "Safari"
            },
            "text_analysis": {
                "all_text": "Google Search I'm Feeling Lucky Google.com"
            },
            "ui_analysis": {
                "elements": [
                    {"type": "text_field", "position": {"x": 400, "y": 300, "width": 200, "height": 40}},
                    {"type": "button", "position": {"x": 450, "y": 350, "width": 100, "height": 30}}
                ]
            }
        }
    }
    
    workflow = await planner.create_workflow_plan(goal, mock_context)
    
    print(f"Created workflow for: {workflow.goal}")
    print(f"Confidence: {workflow.confidence:.2f}")
    print(f"Estimated duration: {workflow.estimated_duration}s")
    print(f"Steps: {len(workflow.steps)}")
    
    for step in workflow.steps:
        print(f"  {step.step_number}. {step.action_type.value}: {step.target} - {step.description}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_google_search_workflow())