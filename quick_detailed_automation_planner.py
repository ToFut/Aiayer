#!/usr/bin/env python3
"""
Quick Detailed Automation Planner
Generates Mac-specific, detailed automation plans instantly without LLM delays
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class AutomationStep:
    """Represents a single automation step"""
    id: str
    description: str
    action_type: str  # 'open_app', 'navigate_url', 'click_element', 'type_text', 'wait', 'hotkey'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"
    estimated_duration: float = 2.0

@dataclass
class AutomationPlan:
    """Complete automation plan"""
    task_id: str
    title: str
    description: str
    steps: List[AutomationStep]
    estimated_duration: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    user_intent: str = ""
    complexity_score: float = 0.5
    llm_generated: bool = False

class QuickDetailedPlanner:
    """Fast, detailed automation planner optimized for Mac environment"""
    
    def __init__(self):
        self.screen_width = 1470
        self.screen_height = 956
        self.default_browser = "Safari"
        self.active_plans: Dict[str, AutomationPlan] = {}
    
    async def create_detailed_plan(self, message: str, session_id: str) -> AutomationPlan:
        """Create a detailed automation plan instantly"""
        start_time = time.time()
        task_id = f"task_{int(time.time())}_{session_id}"
        
        # Analyze the request
        analysis = self._analyze_request(message)
        
        # Generate detailed steps
        steps = await self._generate_detailed_steps(analysis, message)
        
        # Calculate duration
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Create plan
        plan = AutomationPlan(
            task_id=task_id,
            title=analysis["title"],
            description=f"Detailed Mac automation: {message}",
            steps=steps,
            estimated_duration=total_duration,
            requires_approval=True,
            user_intent=message,
            complexity_score=analysis["complexity"],
            llm_generated=False  # This is template-based
        )
        
        # Store plan
        self.active_plans[task_id] = plan
        
        processing_time = time.time() - start_time
        logger.info(f"🎯 Created detailed plan '{plan.title}' with {len(steps)} steps in {processing_time:.3f}s")
        
        return plan
    
    def _analyze_request(self, message: str) -> Dict[str, Any]:
        """Analyze the user request to understand intent"""
        message_lower = message.lower()
        
        analysis = {
            "title": "Unknown Task",
            "complexity": 0.5,
            "browser_needed": False,
            "applications": [],
            "websites": [],
            "search_terms": [],
            "workflow_type": "unknown"
        }
        
        # Detect YouTube workflow
        if "youtube" in message_lower:
            analysis.update({
                "title": "YouTube Search Automation",
                "complexity": 0.7,
                "browser_needed": True,
                "applications": ["Safari"],
                "websites": ["youtube.com"],
                "search_terms": self._extract_search_terms(message),
                "workflow_type": "youtube_search"
            })
        
        # Detect general web search
        elif any(term in message_lower for term in ["google", "search", "web"]):
            analysis.update({
                "title": "Web Search Automation",
                "complexity": 0.6,
                "browser_needed": True,
                "applications": ["Safari"],
                "websites": ["google.com"],
                "search_terms": self._extract_search_terms(message),
                "workflow_type": "web_search"
            })
        
        # Detect app opening
        elif "open" in message_lower:
            app_name = self._extract_app_name(message)
            analysis.update({
                "title": f"Open {app_name}",
                "complexity": 0.3,
                "browser_needed": False,
                "applications": [app_name],
                "websites": [],
                "search_terms": [],
                "workflow_type": "app_launch"
            })
        
        # Detect Safari-specific
        elif "safari" in message_lower:
            analysis.update({
                "title": "Safari Browser Automation",
                "complexity": 0.4,
                "browser_needed": True,
                "applications": ["Safari"],
                "websites": [],
                "search_terms": [],
                "workflow_type": "browser_launch"
            })
        
        return analysis
    
    async def _generate_detailed_steps(self, analysis: Dict[str, Any], original_message: str) -> List[AutomationStep]:
        """Generate detailed automation steps based on analysis"""
        workflow_type = analysis["workflow_type"]
        
        if workflow_type == "youtube_search":
            return await self._create_youtube_workflow(analysis)
        elif workflow_type == "web_search":
            return await self._create_web_search_workflow(analysis)
        elif workflow_type == "app_launch":
            return await self._create_app_launch_workflow(analysis)
        elif workflow_type == "browser_launch":
            return await self._create_browser_launch_workflow(analysis)
        else:
            return await self._create_generic_workflow(analysis, original_message)
    
    async def _create_youtube_workflow(self, analysis: Dict[str, Any]) -> List[AutomationStep]:
        """Create detailed YouTube search workflow"""
        search_terms = analysis.get("search_terms", [])
        search_term = search_terms[0] if search_terms else "search"
        
        steps = [
            AutomationStep(
                id="step_1",
                description="Open Spotlight search (Cmd+Space)",
                action_type="hotkey",
                target="command+space",
                value=None,
                confidence=0.95,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_2",
                description="Wait for Spotlight to open",
                action_type="wait",
                target=None,
                value="1",
                confidence=1.0,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_3",
                description="Type 'Safari' to open browser",
                action_type="type_text",
                target=None,
                value="Safari",
                confidence=0.9,
                estimated_duration=1.5
            ),
            AutomationStep(
                id="step_4",
                description="Press Enter to launch Safari",
                action_type="hotkey",
                target="enter",
                value=None,
                confidence=0.95,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_5",
                description="Wait for Safari to fully load",
                action_type="wait",
                target=None,
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_6",
                description="Focus address bar (Cmd+L)",
                action_type="hotkey",
                target="command+l",
                value=None,
                confidence=0.95,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_7",
                description="Type YouTube URL",
                action_type="type_text",
                target=None,
                value="youtube.com",
                confidence=0.9,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_8",
                description="Press Enter to navigate to YouTube",
                action_type="hotkey",
                target="enter",
                value=None,
                confidence=0.95,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_9",
                description="Wait for YouTube to load completely",
                action_type="wait",
                target=None,
                value="4",
                confidence=1.0,
                estimated_duration=4.0
            ),
            AutomationStep(
                id="step_10",
                description="Click on YouTube search box",
                action_type="click_element",
                target="search_box",
                value=None,
                coordinates=(735, 140),  # Center top of screen for YouTube search
                confidence=0.8,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_11",
                description=f"Type search term '{search_term}'",
                action_type="type_text",
                target=None,
                value=search_term,
                confidence=0.9,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_12",
                description="Press Enter to execute search",
                action_type="hotkey",
                target="enter",
                value=None,
                confidence=0.95,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_13",
                description="Wait for search results to load",
                action_type="wait",
                target=None,
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            )
        ]
        
        return steps
    
    async def _create_web_search_workflow(self, analysis: Dict[str, Any]) -> List[AutomationStep]:
        """Create detailed web search workflow"""
        search_terms = analysis.get("search_terms", [])
        search_term = search_terms[0] if search_terms else "search"
        
        steps = [
            AutomationStep(
                id="step_1",
                description="Open Spotlight search",
                action_type="hotkey",
                target="command+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_2",
                description="Type 'Safari'",
                action_type="type_text",
                value="Safari",
                confidence=0.9,
                estimated_duration=1.5
            ),
            AutomationStep(
                id="step_3",
                description="Launch Safari",
                action_type="hotkey",
                target="enter",
                confidence=0.95,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_4",
                description="Navigate to Google",
                action_type="navigate_url",
                target="address_bar",
                value="google.com",
                confidence=0.9,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_5",
                description="Search for term",
                action_type="type_text",
                value=search_term,
                confidence=0.9,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_6",
                description="Execute search",
                action_type="hotkey",
                target="enter",
                confidence=0.95,
                estimated_duration=1.0
            )
        ]
        
        return steps
    
    async def _create_app_launch_workflow(self, analysis: Dict[str, Any]) -> List[AutomationStep]:
        """Create app launch workflow"""
        applications = analysis.get("applications", ["Application"])
        app_name = applications[0] if applications else "Application"
        
        steps = [
            AutomationStep(
                id="step_1",
                description="Open Spotlight search",
                action_type="hotkey",
                target="command+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_2",
                description="Wait for Spotlight",
                action_type="wait",
                value="1",
                confidence=1.0,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_3",
                description=f"Type '{app_name}'",
                action_type="type_text",
                value=app_name,
                confidence=0.9,
                estimated_duration=1.5
            ),
            AutomationStep(
                id="step_4",
                description=f"Launch {app_name}",
                action_type="hotkey",
                target="enter",
                confidence=0.95,
                estimated_duration=2.0
            )
        ]
        
        return steps
    
    async def _create_browser_launch_workflow(self, analysis: Dict[str, Any]) -> List[AutomationStep]:
        """Create browser launch workflow"""
        steps = [
            AutomationStep(
                id="step_1",
                description="Open Spotlight search",
                action_type="hotkey",
                target="command+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_2",
                description="Type 'Safari'",
                action_type="type_text",
                value="Safari",
                confidence=0.9,
                estimated_duration=1.5
            ),
            AutomationStep(
                id="step_3",
                description="Launch Safari browser",
                action_type="hotkey",
                target="enter",
                confidence=0.95,
                estimated_duration=3.0
            )
        ]
        
        return steps
    
    async def _create_generic_workflow(self, analysis: Dict[str, Any], message: str) -> List[AutomationStep]:
        """Create generic workflow for unknown requests"""
        steps = [
            AutomationStep(
                id="step_1",
                description=f"Analyze request: {message[:30]}...",
                action_type="wait",
                value="1",
                confidence=0.8,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_2",
                description="Execute appropriate action",
                action_type="hotkey",
                target="command+space",
                confidence=0.6,
                estimated_duration=2.0
            )
        ]
        
        return steps
    
    def _extract_search_terms(self, message: str) -> List[str]:
        """Extract search terms from message"""
        # Look for quoted terms
        quoted_terms = re.findall(r'["\']([^"\']+)["\']', message)
        if quoted_terms:
            return quoted_terms
        
        # Look for common search patterns
        patterns = [
            r'search (?:for |)(.+?)(?:\s+on|\s+in|$)',
            r'find (.+?)(?:\s+on|\s+in|$)',
            r'look for (.+?)(?:\s+on|\s+in|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                return [term]
        
        # Check for specific terms
        if "SEGEV" in message:
            return ["SEGEV"]
        
        return ["search term"]
    
    def _extract_app_name(self, message: str) -> str:
        """Extract application name from message"""
        app_patterns = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "textedit": "TextEdit",
            "notes": "Notes",
            "calculator": "Calculator",
            "finder": "Finder",
            "terminal": "Terminal"
        }
        
        message_lower = message.lower()
        for pattern, app_name in app_patterns.items():
            if pattern in message_lower:
                return app_name
        
        return "Application"

# Create singleton instance
quick_planner = QuickDetailedPlanner()

async def create_quick_detailed_plan(message: str, session_id: str) -> AutomationPlan:
    """Entry point for creating quick detailed plans"""
    return await quick_planner.create_detailed_plan(message, session_id)