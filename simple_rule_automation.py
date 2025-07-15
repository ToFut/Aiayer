#!/usr/bin/env python3
"""
Simple Rule-Based Automation Handler
Generates automation plans using predefined rules instead of slow LLM
"""

import json
import logging
import re
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleRuleAutomation:
    """Simple rule-based automation that generates proper steps"""
    
    def __init__(self):
        self.rules = {
            # Web search patterns
            r"search\s+(.+?)\s+in\s+google": self._create_google_search_plan,
            r"open\s+(.+?)\s+in\s+google": self._create_google_search_plan,
            r"google\s+(.+)": self._create_google_search_plan,
            
            # App opening patterns
            r"open\s+(safari|chrome|firefox|terminal|finder|notes|mail|calendar)": self._create_app_open_plan,
            r"launch\s+(safari|chrome|firefox|terminal|finder|notes|mail|calendar)": self._create_app_open_plan,
            
            # General patterns
            r"open\s+(.+)": self._create_generic_open_plan,
        }
    
    def create_plan(self, user_request: str) -> Dict[str, Any]:
        """Create automation plan based on user request"""
        user_request_lower = user_request.lower().strip()
        
        # Try to match rules
        for pattern, handler in self.rules.items():
            match = re.search(pattern, user_request_lower)
            if match:
                return handler(user_request, match)
        
        # Default fallback
        return self._create_fallback_plan(user_request)
    
    def _create_google_search_plan(self, user_request: str, match) -> Dict[str, Any]:
        """Create plan for Google search"""
        search_term = match.group(1).strip()
        
        steps = [
            {
                "id": "step_1",
                "description": "Open Safari browser",
                "action_type": "open_app",
                "target": "Safari",
                "value": None,
                "coordinates": None,
                "confidence": 0.9,
                "status": "pending",
                "estimated_duration": 2.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            },
            {
                "id": "step_2", 
                "description": "Navigate to Google search",
                "action_type": "navigate_url",
                "target": "https://www.google.com",
                "value": None,
                "coordinates": None,
                "confidence": 0.9,
                "status": "pending",
                "estimated_duration": 3.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            },
            {
                "id": "step_3",
                "description": f"Type search term: {search_term}",
                "action_type": "type_text",
                "target": "search_box",
                "value": search_term,
                "coordinates": None,
                "confidence": 0.8,
                "status": "pending",
                "estimated_duration": 2.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            },
            {
                "id": "step_4",
                "description": "Press Enter to search",
                "action_type": "hotkey",
                "target": "enter",
                "value": None,
                "coordinates": None,
                "confidence": 0.9,
                "status": "pending",
                "estimated_duration": 1.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            }
        ]
        
        return {
            "task_id": f"plan_{int(datetime.now().timestamp())}",
            "title": f"Search '{search_term}' on Google",
            "description": f"Automate Google search for: {search_term}",
            "request_type": "web_search",
            "steps": steps,
            "estimated_duration": 8.0,
            "complexity_score": 0.3,
            "requires_approval": False,
            "status": "ready",
            "success_probability": 0.9,
            "fallback_strategies": [],
            "user_guidance_needed": False,
            "timestamp": datetime.now().timestamp(),
            "created": datetime.now().timestamp(),
            "plan_id": f"plan_{int(datetime.now().timestamp())}",
            "id": f"plan_{int(datetime.now().timestamp())}"
        }
    
    def _create_app_open_plan(self, user_request: str, match) -> Dict[str, Any]:
        """Create plan for opening apps"""
        app_name = match.group(1).strip()
        
        steps = [
            {
                "id": "step_1",
                "description": f"Open {app_name.capitalize()} using Spotlight",
                "action_type": "open_app",
                "target": app_name.capitalize(),
                "value": None,
                "coordinates": None,
                "confidence": 0.9,
                "status": "pending",
                "estimated_duration": 3.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            }
        ]
        
        return {
            "task_id": f"plan_{int(datetime.now().timestamp())}",
            "title": f"Open {app_name.capitalize()}",
            "description": f"Launch {app_name.capitalize()} application",
            "request_type": "app_usage",
            "steps": steps,
            "estimated_duration": 3.0,
            "complexity_score": 0.2,
            "requires_approval": False,
            "status": "ready",
            "success_probability": 0.95,
            "fallback_strategies": [],
            "user_guidance_needed": False,
            "timestamp": datetime.now().timestamp(),
            "created": datetime.now().timestamp(),
            "plan_id": f"plan_{int(datetime.now().timestamp())}",
            "id": f"plan_{int(datetime.now().timestamp())}"
        }
    
    def _create_generic_open_plan(self, user_request: str, match) -> Dict[str, Any]:
        """Create generic open plan"""
        target = match.group(1).strip()
        
        steps = [
            {
                "id": "step_1",
                "description": f"Open {target} using Spotlight",
                "action_type": "open_app",
                "target": target,
                "value": None,
                "coordinates": None,
                "confidence": 0.7,
                "status": "pending",
                "estimated_duration": 3.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            }
        ]
        
        return {
            "task_id": f"plan_{int(datetime.now().timestamp())}",
            "title": f"Open {target}",
            "description": f"Launch {target}",
            "request_type": "app_usage",
            "steps": steps,
            "estimated_duration": 3.0,
            "complexity_score": 0.3,
            "requires_approval": False,
            "status": "ready",
            "success_probability": 0.8,
            "fallback_strategies": [],
            "user_guidance_needed": False,
            "timestamp": datetime.now().timestamp(),
            "created": datetime.now().timestamp(),
            "plan_id": f"plan_{int(datetime.now().timestamp())}",
            "id": f"plan_{int(datetime.now().timestamp())}"
        }
    
    def _create_fallback_plan(self, user_request: str) -> Dict[str, Any]:
        """Create fallback plan when no rules match"""
        steps = [
            {
                "id": "step_1",
                "description": "Analyze user request",
                "action_type": "analyze_screen",
                "target": None,
                "value": None,
                "coordinates": None,
                "confidence": 0.5,
                "status": "pending",
                "estimated_duration": 2.0,
                "retry_count": 0,
                "max_retries": 3,
                "fallback_action": None,
                "context_hints": []
            }
        ]
        
        return {
            "task_id": f"plan_{int(datetime.now().timestamp())}",
            "title": f"Process: {user_request}",
            "description": f"Handle user request: {user_request}",
            "request_type": "general",
            "steps": steps,
            "estimated_duration": 5.0,
            "complexity_score": 0.5,
            "requires_approval": True,
            "status": "awaiting_approval",
            "success_probability": 0.6,
            "fallback_strategies": [],
            "user_guidance_needed": True,
            "timestamp": datetime.now().timestamp(),
            "created": datetime.now().timestamp(),
            "plan_id": f"plan_{int(datetime.now().timestamp())}",
            "id": f"plan_{int(datetime.now().timestamp())}"
        } 