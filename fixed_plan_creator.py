#!/usr/bin/env python3
"""
Fixed Plan Creator - Generates accurate, executable plans for input controller
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AccurateStep:
    """Accurate automation step that maps to input controller methods"""
    id: str
    description: str
    action_type: str  # 'hotkey', 'type_text', 'press_key', 'click', 'wait'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[tuple] = None
    confidence: float = 0.9
    estimated_duration: float = 2.0

@dataclass
class AccuratePlan:
    """Accurate automation plan with proper input controller mapping"""
    task_id: str
    title: str
    description: str
    request_type: str
    steps: List[AccurateStep]
    estimated_duration: float
    complexity_score: float
    success_probability: float

class FixedPlanCreator:
    """Creates accurate, executable plans for input controller"""
    
    def __init__(self):
        self.screen_width = 1470
        self.screen_height = 956
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
    
    def create_accurate_plan(self, user_request: str, session_id: str) -> Dict[str, Any]:
        """Create accurate plan that maps to input controller capabilities"""
        
        request_lower = user_request.lower()
        steps = []
        
        # Analyze request intent and create appropriate steps
        if "search" in request_lower:
            # Web search request - always use Safari for web searches
            search_term = self._extract_search_term(user_request)
            steps = self._create_web_search_plan(search_term)
        elif any(word in request_lower for word in ["safari", "browser", "web"]):
            # Just open Safari
            steps = self._create_open_safari_plan()
                
        elif any(word in request_lower for word in ["calculator", "calc"]):
            # Calculator request
            steps = self._create_calculator_plan()
            
        elif any(word in request_lower for word in ["textedit", "notes", "text"]):
            # Text editing request
            steps = self._create_text_editor_plan()
            
        else:
            # Generic plan
            steps = self._create_generic_plan(user_request)
        
        # Create plan
        plan = AccuratePlan(
            task_id=f"accurate_plan_{int(time.time())}",
            title=self._generate_title(user_request),
            description=user_request,
            request_type=self._determine_request_type(request_lower),
            steps=steps,
            estimated_duration=sum(step.estimated_duration for step in steps),
            complexity_score=self._calculate_complexity(steps),
            success_probability=0.95
        )
        
        return self._format_plan_response(plan)
    
    def _extract_search_term(self, user_request: str) -> str:
        """Extract search term from request"""
        request_lower = user_request.lower()
        
        # Handle "Search X in Google" format
        if "search" in request_lower and "in" in request_lower:
            parts = request_lower.split("search", 1)
            if len(parts) > 1:
                search_part = parts[1]
                if "in" in search_part:
                    search_term = search_part.split("in")[0].strip()
                    if search_term:
                        return search_term
        
        # Handle "Search for X" format
        if "search" in request_lower and "for" in request_lower:
            parts = request_lower.split("search", 1)
            if len(parts) > 1:
                search_part = parts[1]
                if "for" in search_part:
                    search_term = search_part.split("for", 1)[1].strip()
                    if search_term:
                        return search_term
        
        # Handle "Search X" format
        if "search" in request_lower:
            parts = request_lower.split("search", 1)
            if len(parts) > 1:
                search_term = parts[1].strip()
                if search_term:
                    return search_term
        
        # Handle "for X" format
        if "for" in request_lower:
            parts = request_lower.split("for", 1)
            if len(parts) > 1:
                return parts[1].strip()
        
        return "segev"  # Default
    
    def _create_web_search_plan(self, search_term: str) -> List[AccurateStep]:
        """Create plan for web search"""
        return [
            AccurateStep(
                id="step_1",
                description="Open Safari using Spotlight",
                action_type="hotkey",
                target="cmd+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_2",
                description="Type Safari in Spotlight",
                action_type="type_text",
                value="Safari",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_3",
                description="Press Enter to open Safari",
                action_type="press_key",
                target="return",
                confidence=0.95,
                estimated_duration=0.5
            ),
            AccurateStep(
                id="step_4",
                description="Wait for Safari to load",
                action_type="wait",
                value="3.0",
                confidence=0.9,
                estimated_duration=3.0
            ),
            AccurateStep(
                id="step_5",
                description=f"Type search term: {search_term}",
                action_type="type_text",
                value=search_term,
                confidence=0.9,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_6",
                description="Press Enter to search",
                action_type="press_key",
                target="return",
                confidence=0.9,
                estimated_duration=0.5
            )
        ]
    
    def _create_open_safari_plan(self) -> List[AccurateStep]:
        """Create plan to just open Safari"""
        return [
            AccurateStep(
                id="step_1",
                description="Open Safari using Spotlight",
                action_type="hotkey",
                target="cmd+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_2",
                description="Type Safari in Spotlight",
                action_type="type_text",
                value="Safari",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_3",
                description="Press Enter to open Safari",
                action_type="press_key",
                target="return",
                confidence=0.95,
                estimated_duration=0.5
            )
        ]
    
    def _create_calculator_plan(self) -> List[AccurateStep]:
        """Create plan for Calculator"""
        return [
            AccurateStep(
                id="step_1",
                description="Open Calculator using Spotlight",
                action_type="hotkey",
                target="cmd+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_2",
                description="Type Calculator in Spotlight",
                action_type="type_text",
                value="Calculator",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_3",
                description="Press Enter to open Calculator",
                action_type="press_key",
                target="return",
                confidence=0.95,
                estimated_duration=0.5
            )
        ]
    
    def _create_text_editor_plan(self) -> List[AccurateStep]:
        """Create plan for text editor"""
        return [
            AccurateStep(
                id="step_1",
                description="Open TextEdit using Spotlight",
                action_type="hotkey",
                target="cmd+space",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_2",
                description="Type TextEdit in Spotlight",
                action_type="type_text",
                value="TextEdit",
                confidence=0.95,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_3",
                description="Press Enter to open TextEdit",
                action_type="press_key",
                target="return",
                confidence=0.95,
                estimated_duration=0.5
            )
        ]
    
    def _create_generic_plan(self, user_request: str) -> List[AccurateStep]:
        """Create generic plan for unknown requests"""
        return [
            AccurateStep(
                id="step_1",
                description="Analyze current screen",
                action_type="wait",
                value="1.0",
                confidence=0.8,
                estimated_duration=1.0
            ),
            AccurateStep(
                id="step_2",
                description="Click center of screen",
                action_type="click",
                coordinates=(self.center_x, self.center_y),
                confidence=0.7,
                estimated_duration=1.0
            )
        ]
    
    def _generate_title(self, user_request: str) -> str:
        """Generate plan title from request"""
        if "search" in user_request.lower():
            search_term = self._extract_search_term(user_request)
            return f"Search for {search_term}"
        elif "open" in user_request.lower():
            parts = user_request.split('open', 1)
            if len(parts) > 1:
                return f"Open {parts[1].strip()}"
            else:
                return user_request
        else:
            return user_request
    
    def _determine_request_type(self, request_lower: str) -> str:
        """Determine request type"""
        if "search" in request_lower:
            return "web_search"
        elif "calculator" in request_lower:
            return "app_usage"
        elif "text" in request_lower or "edit" in request_lower:
            return "productivity"
        else:
            return "general"
    
    def _calculate_complexity(self, steps: List[AccurateStep]) -> float:
        """Calculate plan complexity score"""
        if len(steps) <= 2:
            return 0.2
        elif len(steps) <= 4:
            return 0.4
        else:
            return 0.6
    
    def _format_plan_response(self, plan: AccuratePlan) -> Dict[str, Any]:
        """Format plan for response"""
        return {
            "success": True,
            "plan_id": plan.task_id,
            "title": plan.title,
            "description": plan.description,
            "request_type": plan.request_type,
            "steps": [
                {
                    "id": step.id,
                    "description": step.description,
                    "action_type": step.action_type,
                    "target": step.target,
                    "value": step.value,
                    "coordinates": step.coordinates,
                    "confidence": step.confidence,
                    "estimated_duration": step.estimated_duration
                }
                for step in plan.steps
            ],
            "estimated_duration": plan.estimated_duration,
            "complexity_score": plan.complexity_score,
            "success_probability": plan.success_probability,
            "requires_approval": True,
            "automation_available": True
        }

# Test the fixed plan creator
async def test_fixed_plan_creator():
    creator = FixedPlanCreator()
    
    # Test different request types
    test_requests = [
        "Open Safari and search for segev",
        "Open Calculator",
        "Open TextEdit",
        "Click on the screen"
    ]
    
    for request in test_requests:
        print(f"\n🧪 Testing: {request}")
        result = creator.create_accurate_plan(request, "test_session")
        
        if result["success"]:
            print(f"✅ Plan created: {result['title']}")
            print(f"📋 Steps: {len(result['steps'])}")
            print(f"⏱️ Duration: {result['estimated_duration']}s")
            print(f"🎯 Success probability: {result['success_probability']}")
        else:
            print(f"❌ Failed: {result.get('response', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_fixed_plan_creator()) 