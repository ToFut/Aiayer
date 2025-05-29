#!/usr/bin/env python3
"""
Smart Fallback Automation Handler
Provides intelligent automation plans when the LLM service is not available.
Creates specific, detailed plans for common tasks without requiring LLM.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SmartStep:
    """Smart automation step with detailed information"""
    id: str
    description: str
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    estimated_duration: float = 2.0

class SmartFallbackAutomationHandler:
    """Smart fallback automation handler for when LLM is not available"""
    
    def __init__(self):
        self.task_patterns = {
            # Flight search patterns
            "flight": {
                "keywords": ["flight", "fly", "airline", "airport", "travel", "ticket"],
                "destinations": ["nyc", "miami", "new york", "florida", "jfk", "lga", "mia"],
                "generator": self._create_flight_search_plan
            },
            # Web search patterns  
            "web_search": {
                "keywords": ["search", "find", "look for", "google"],
                "generator": self._create_web_search_plan
            },
            # Shopping patterns
            "shopping": {
                "keywords": ["buy", "shop", "deal", "price", "amazon", "store"],
                "generator": self._create_shopping_plan
            },
            # App usage patterns
            "app": {
                "keywords": ["open", "launch", "start", "calculator", "notes", "safari"],
                "generator": self._create_app_usage_plan
            },
            # Social media patterns
            "social": {
                "keywords": ["twitter", "facebook", "instagram", "social", "post"],
                "generator": self._create_social_media_plan
            }
        }
    
    async def create_universal_automation_plan(self, user_request: str, session_id: str) -> Dict[str, Any]:
        """Create smart automation plan using pattern matching"""
        try:
            start_time = time.time()
            
            # Analyze request to determine pattern
            request_type, pattern_data = self._analyze_request_pattern(user_request)
            
            # Generate plan using appropriate pattern
            if pattern_data:
                plan = await pattern_data["generator"](user_request, session_id)
            else:
                plan = await self._create_generic_plan(user_request, session_id)
            
            # Format response
            plan_id = f"smart_{int(time.time())}_{session_id}"
            
            response_text = f"🎯 **AUTOMATION EXECUTION PLAN**\n\n"
            response_text += f"**📋 Task:** {plan['title']}\n"
            response_text += f"**🎭 Type:** {plan['request_type']}\n"
            response_text += f"**⏱️ Estimated Duration:** {plan['estimated_duration']:.1f} seconds\n"
            response_text += f"**📝 Steps:** {len(plan['steps'])} actions\n\n"
            
            response_text += "**🚀 Automation Steps:**\n"
            for i, step in enumerate(plan['steps'], 1):
                confidence_emoji = "🟢" if step.confidence > 0.8 else "🟡" if step.confidence > 0.6 else "🔴"
                response_text += f"{i}. {confidence_emoji} {step.description}\n"
                
                if step.action_type == "type_text" and step.value:
                    response_text += f"   → Will type: '{step.value}'\n"
                elif step.action_type == "navigate_url" and step.value:
                    response_text += f"   → Will navigate to: {step.value}\n"
                elif step.action_type == "open_app" and step.target:
                    response_text += f"   → Will open: {step.target}\n"
            
            response_text += f"\n**🆔 Plan ID:** `{plan_id}`\n"
            response_text += f"**🧠 Planning:** Smart Pattern-Based (Offline)\n\n"
            response_text += f"*Ready to execute - choose an action below:*"
            
            # Create interactive buttons
            buttons = [
                {
                    "id": f"do_{plan_id}",
                    "text": "🟢 EXECUTE",
                    "action": "execute_plan",
                    "plan_id": plan_id,
                    "style": "success",
                    "description": f"Execute this {request_type} automation"
                },
                {
                    "id": f"dismiss_{plan_id}",
                    "text": "🔴 CANCEL",
                    "action": "cancel_plan",
                    "plan_id": plan_id,
                    "style": "danger",
                    "description": "Cancel this automation"
                }
            ]
            
            return {
                "success": True,
                "response": response_text,
                "buttons": buttons,
                "interactive": True,
                "plan_id": plan_id,
                "requires_approval": True,
                "processing_time": time.time() - start_time,
                "automation_available": True,
                "request_type": request_type,
                "complexity_score": 0.7,
                "success_probability": 0.8,
                "smart_fallback": True
            }
            
        except Exception as e:
            logger.error(f"Error in smart fallback automation: {e}")
            return {
                "success": False,
                "response": f"Error creating automation plan: {str(e)}",
                "automation_available": False
            }
    
    def _analyze_request_pattern(self, request: str) -> Tuple[str, Optional[Dict]]:
        """Analyze request to determine the best pattern"""
        request_lower = request.lower()
        
        for pattern_name, pattern_data in self.task_patterns.items():
            keywords = pattern_data["keywords"]
            if any(keyword in request_lower for keyword in keywords):
                return pattern_name, pattern_data
        
        return "general", None
    
    async def _create_flight_search_plan(self, request: str, session_id: str) -> Dict[str, Any]:
        """Create flight search automation plan"""
        
        # Extract locations from request
        departure, destination = self._extract_flight_locations(request)
        
        steps = [
            SmartStep(
                id="step_1",
                description="Open Safari browser",
                action_type="open_app",
                target="Safari",
                confidence=0.9,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_2",
                description="Navigate to Google Flights",
                action_type="navigate_url",
                value="https://www.google.com/travel/flights",
                confidence=0.9,
                estimated_duration=4.0
            ),
            SmartStep(
                id="step_3",
                description="Wait for Google Flights to load",
                action_type="wait",
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_4",
                description=f"Enter departure city: {departure}",
                action_type="type_text",
                value=departure,
                coordinates=(400, 300),
                confidence=0.8,
                estimated_duration=2.0
            ),
            SmartStep(
                id="step_5",
                description=f"Enter destination city: {destination}",
                action_type="type_text",
                value=destination,
                coordinates=(600, 300),
                confidence=0.8,
                estimated_duration=2.0
            ),
            SmartStep(
                id="step_6",
                description="Click search button",
                action_type="click_element",
                target="search_button",
                coordinates=(500, 400),
                confidence=0.7,
                estimated_duration=1.0
            ),
            SmartStep(
                id="step_7",
                description="Analyze flight results",
                action_type="analyze_screen",
                confidence=0.9,
                estimated_duration=5.0
            )
        ]
        
        return {
            "title": f"Search flights from {departure} to {destination}",
            "request_type": "Flight Search",
            "steps": steps,
            "estimated_duration": sum(step.estimated_duration for step in steps)
        }
    
    async def _create_web_search_plan(self, request: str, session_id: str) -> Dict[str, Any]:
        """Create web search automation plan"""
        
        search_term = self._extract_search_term(request)
        
        steps = [
            SmartStep(
                id="step_1",
                description="Open Safari browser",
                action_type="open_app",
                target="Safari",
                confidence=0.9,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_2",
                description="Navigate to Google",
                action_type="navigate_url",
                value="https://www.google.com",
                confidence=0.9,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_3",
                description=f"Search for: {search_term}",
                action_type="type_text",
                value=search_term,
                coordinates=(735, 300),
                confidence=0.8,
                estimated_duration=2.0
            ),
            SmartStep(
                id="step_4",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=0.9,
                estimated_duration=1.0
            ),
            SmartStep(
                id="step_5",
                description="Analyze search results",
                action_type="analyze_screen",
                confidence=0.9,
                estimated_duration=3.0
            )
        ]
        
        return {
            "title": f"Search for {search_term}",
            "request_type": "Web Search",
            "steps": steps,
            "estimated_duration": sum(step.estimated_duration for step in steps)
        }
    
    async def _create_shopping_plan(self, request: str, session_id: str) -> Dict[str, Any]:
        """Create shopping automation plan"""
        
        product = self._extract_product_name(request)
        
        steps = [
            SmartStep(
                id="step_1",
                description="Open Safari browser",
                action_type="open_app",
                target="Safari",
                confidence=0.9,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_2",
                description="Navigate to Amazon",
                action_type="navigate_url",
                value="https://www.amazon.com",
                confidence=0.9,
                estimated_duration=4.0
            ),
            SmartStep(
                id="step_3",
                description=f"Search for: {product}",
                action_type="type_text",
                value=product,
                coordinates=(500, 150),
                confidence=0.8,
                estimated_duration=2.0
            ),
            SmartStep(
                id="step_4",
                description="Click search button",
                action_type="click_element",
                target="search_button",
                coordinates=(600, 150),
                confidence=0.8,
                estimated_duration=1.0
            ),
            SmartStep(
                id="step_5",
                description="Browse product results",
                action_type="analyze_screen",
                confidence=0.9,
                estimated_duration=5.0
            )
        ]
        
        return {
            "title": f"Search for {product} on Amazon",
            "request_type": "Shopping",
            "steps": steps,
            "estimated_duration": sum(step.estimated_duration for step in steps)
        }
    
    async def _create_app_usage_plan(self, request: str, session_id: str) -> Dict[str, Any]:
        """Create app usage automation plan"""
        
        app_name = self._extract_app_name(request)
        
        steps = [
            SmartStep(
                id="step_1",
                description=f"Open {app_name} using Spotlight",
                action_type="hotkey",
                target="command+space",
                confidence=0.9,
                estimated_duration=1.0
            ),
            SmartStep(
                id="step_2",
                description=f"Type {app_name}",
                action_type="type_text",
                value=app_name,
                confidence=0.9,
                estimated_duration=1.0
            ),
            SmartStep(
                id="step_3",
                description="Press Enter to launch",
                action_type="hotkey",
                target="enter",
                confidence=0.9,
                estimated_duration=1.0
            ),
            SmartStep(
                id="step_4",
                description=f"Wait for {app_name} to open",
                action_type="wait",
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            )
        ]
        
        return {
            "title": f"Open {app_name}",
            "request_type": "App Usage",
            "steps": steps,
            "estimated_duration": sum(step.estimated_duration for step in steps)
        }
    
    async def _create_social_media_plan(self, request: str, session_id: str) -> Dict[str, Any]:
        """Create social media automation plan"""
        
        platform = self._extract_social_platform(request)
        
        steps = [
            SmartStep(
                id="step_1",
                description="Open Safari browser",
                action_type="open_app",
                target="Safari",
                confidence=0.9,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_2",
                description=f"Navigate to {platform}",
                action_type="navigate_url",
                value=f"https://www.{platform.lower()}.com",
                confidence=0.9,
                estimated_duration=4.0
            ),
            SmartStep(
                id="step_3",
                description=f"Wait for {platform} to load",
                action_type="wait",
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_4",
                description=f"Browse {platform} feed",
                action_type="analyze_screen",
                confidence=0.8,
                estimated_duration=5.0
            )
        ]
        
        return {
            "title": f"Check {platform}",
            "request_type": "Social Media",
            "steps": steps,
            "estimated_duration": sum(step.estimated_duration for step in steps)
        }
    
    async def _create_generic_plan(self, request: str, session_id: str) -> Dict[str, Any]:
        """Create generic automation plan"""
        
        steps = [
            SmartStep(
                id="step_1",
                description="Analyze the request",
                action_type="analyze_screen",
                confidence=0.8,
                estimated_duration=2.0
            ),
            SmartStep(
                id="step_2",
                description="Determine appropriate action",
                action_type="analyze_screen",
                confidence=0.7,
                estimated_duration=3.0
            ),
            SmartStep(
                id="step_3",
                description="Execute determined action",
                action_type="click_element",
                coordinates=(735, 478),  # Screen center
                confidence=0.6,
                estimated_duration=2.0
            )
        ]
        
        return {
            "title": f"Process: {request[:50]}...",
            "request_type": "General Task",
            "steps": steps,
            "estimated_duration": sum(step.estimated_duration for step in steps)
        }
    
    def _extract_flight_locations(self, request: str) -> Tuple[str, str]:
        """Extract departure and destination from flight request"""
        request_lower = request.lower()
        
        # Common location mappings
        locations = {
            "nyc": "New York City",
            "new york": "New York City", 
            "jfk": "New York (JFK)",
            "lga": "New York (LGA)",
            "miami": "Miami",
            "mia": "Miami (MIA)",
            "florida": "Florida",
            "los angeles": "Los Angeles",
            "lax": "Los Angeles (LAX)",
            "chicago": "Chicago",
            "ord": "Chicago (ORD)"
        }
        
        departure = "New York City"  # Default
        destination = "Miami"  # Default
        
        # Look for "from X to Y" pattern
        if " from " in request_lower and " to " in request_lower:
            parts = request_lower.split(" from ")[1].split(" to ")
            if len(parts) >= 2:
                dep_part = parts[0].strip()
                dest_part = parts[1].strip()
                
                # Map to full names
                for key, value in locations.items():
                    if key in dep_part:
                        departure = value
                    if key in dest_part:
                        destination = value
        
        return departure, destination
    
    def _extract_search_term(self, request: str) -> str:
        """Extract search term from request"""
        # Remove common prefixes
        search_term = request.lower()
        prefixes = ["search for", "find", "look for", "google"]
        
        for prefix in prefixes:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):].strip()
                break
        
        return search_term or "search query"
    
    def _extract_product_name(self, request: str) -> str:
        """Extract product name from shopping request"""
        request_lower = request.lower()
        
        # Remove shopping-related words
        shopping_words = ["buy", "shop", "find", "search", "deals", "price", "on amazon", "amazon"]
        product = request_lower
        
        for word in shopping_words:
            product = product.replace(word, "").strip()
        
        return product or "product"
    
    def _extract_app_name(self, request: str) -> str:
        """Extract app name from request"""
        app_mapping = {
            "calculator": "Calculator",
            "notes": "Notes",
            "safari": "Safari",
            "finder": "Finder",
            "terminal": "Terminal",
            "textedit": "TextEdit",
            "calendar": "Calendar"
        }
        
        request_lower = request.lower()
        for keyword, app_name in app_mapping.items():
            if keyword in request_lower:
                return app_name
        
        # Try to extract from "open X" pattern
        if "open" in request_lower:
            words = request.split()
            for i, word in enumerate(words):
                if word.lower() == "open" and i + 1 < len(words):
                    return words[i + 1].title()
        
        return "Application"
    
    def _extract_social_platform(self, request: str) -> str:
        """Extract social media platform from request"""
        platforms = ["Twitter", "Facebook", "Instagram", "LinkedIn", "TikTok"]
        
        request_lower = request.lower()
        for platform in platforms:
            if platform.lower() in request_lower:
                return platform
        
        return "Twitter"  # Default

# Create singleton instance
smart_fallback_handler = SmartFallbackAutomationHandler()

async def handle_smart_fallback_automation(user_request: str, session_id: str) -> Dict[str, Any]:
    """Entry point for smart fallback automation"""
    return await smart_fallback_handler.create_universal_automation_plan(user_request, session_id)