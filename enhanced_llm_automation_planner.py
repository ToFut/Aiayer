#!/usr/bin/env python3
"""
Enhanced LLM Automation Planner - AI-powered task analysis using LLM
Uses real LLM reasoning to understand complex user requests and generate intelligent automation plans
"""

import asyncio
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

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
    llm_generated: bool = True

class EnhancedLLMAutomationPlanner:
    """LLM-powered automation planner that understands complex user intents"""
    
    def __init__(self):
        self.active_plans: Dict[str, AutomationPlan] = {}
        self.automation_available = True
        self.llm_service = None
        
        # Load existing automation components
        try:
            from agent_workflow.input_controller import InputController
            from sensors.total_screen_analyzer import TotalScreenAnalyzer
            self.input_controller = InputController()
            self.screen_analyzer = TotalScreenAnalyzer()
            logger.info("🤖 Automation components loaded successfully")
        except Exception as e:
            logger.warning(f"Automation components not available: {e}")
            self.input_controller = None
            self.screen_analyzer = None
            self.automation_available = False
        
        # Initialize LLM service
        try:
            from backend.llm.llm_service import LLMService
            self.llm_service = LLMService()
            logger.info("🧠 LLM service loaded for intelligent planning")
        except Exception as e:
            logger.warning(f"LLM service not available: {e}")
            self.llm_service = None
    
    async def analyze_user_intent_with_llm(self, message: str) -> Dict[str, Any]:
        """Analyze user intent using LLM for intelligent understanding"""
        if not self.llm_service:
            # Fallback to pattern-based analysis
            return await self._fallback_intent_analysis(message)
        
        try:
            await self.llm_service.initialize()
            
            # Create a detailed prompt for the LLM to analyze the user's automation request
            analysis_prompt = f"""You are an automation planning assistant for macOS. Analyze this user request and break it down into actionable automation steps.

SYSTEM ENVIRONMENT:
- Operating System: macOS (Darwin 23.1.0)
- Screen Resolution: 1470x956
- Default Browser: Safari
- Available Applications: Safari, Chrome, Firefox, TextEdit, Notes, Calculator, Finder, Terminal
- Automation Methods: Spotlight search (Cmd+Space), keyboard shortcuts, mouse clicks, typing

USER REQUEST: "{message}"

MANDATORY: Provide ONLY a valid JSON response with this exact structure:
{{
    "intent_analysis": {{
        "primary_goal": "What the user ultimately wants to achieve",
        "applications_needed": ["Safari"],
        "websites_needed": ["youtube.com"],
        "search_terms": ["SEGEV"],
        "text_to_type": ["SEGEV"],
        "sequential_actions": ["open browser", "navigate to youtube", "search"],
        "complexity_score": 0.7
    }},
    "automation_steps": [
        {{
            "id": "step_1",
            "description": "Open Safari using Spotlight",
            "action_type": "open_app",
            "target": "Safari",
            "value": null,
            "estimated_duration": 3.0,
            "confidence": 0.9
        }},
        {{
            "id": "step_2",
            "description": "Wait for Safari to load",
            "action_type": "wait",
            "target": null,
            "value": "3",
            "estimated_duration": 3.0,
            "confidence": 1.0
        }},
        {{
            "id": "step_3",
            "description": "Navigate to YouTube.com",
            "action_type": "navigate_url",
            "target": "address_bar",
            "value": "youtube.com",
            "estimated_duration": 4.0,
            "confidence": 0.8
        }},
        {{
            "id": "step_4",
            "description": "Wait for YouTube to load",
            "action_type": "wait",
            "target": null,
            "value": "3",
            "estimated_duration": 3.0,
            "confidence": 1.0
        }},
        {{
            "id": "step_5",
            "description": "Click on YouTube search box",
            "action_type": "click_element",
            "target": "search_box",
            "value": null,
            "estimated_duration": 1.0,
            "confidence": 0.7
        }},
        {{
            "id": "step_6",
            "description": "Type 'SEGEV' in search box",
            "action_type": "type_text",
            "target": null,
            "value": "SEGEV",
            "estimated_duration": 2.0,
            "confidence": 0.9
        }},
        {{
            "id": "step_7",
            "description": "Press Enter to search",
            "action_type": "hotkey",
            "target": "enter",
            "value": null,
            "estimated_duration": 1.0,
            "confidence": 0.9
        }}
    ]
}}

CRITICAL RULES:
1. ONLY use these action_types: open_app, navigate_url, click_element, type_text, wait, hotkey
2. For macOS, use Safari as default browser
3. Use Spotlight (Cmd+Space) to open applications
4. Include proper wait times between steps
5. For wait actions, value must be a number string like "3"
6. Generate 5-8 detailed steps for complex tasks
7. Return ONLY valid JSON, no explanatory text before or after

            # Get LLM analysis
            llm_response = await self.llm_service.generate_response(analysis_prompt)
            logger.info(f"🧠 LLM analysis generated: {len(llm_response)} characters")
            
            # Parse JSON response
            try:
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analysis_data = json.loads(json_str)
                else:
                    # If no JSON found, try parsing the whole response
                    analysis_data = json.loads(llm_response)
                
                logger.info(f"✅ Successfully parsed LLM analysis")
                return analysis_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                logger.info(f"Raw LLM response: {llm_response[:500]}...")
                # Fallback to pattern-based analysis
                return await self._fallback_intent_analysis(message)
                
        except Exception as e:
            logger.error(f"Error in LLM intent analysis: {e}")
            # Fallback to pattern-based analysis
            return await self._fallback_intent_analysis(message)
    
    async def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback pattern-based analysis when LLM is not available"""
        message_lower = message.lower()
        
        # Enhanced pattern-based analysis for ChatGPT specifically
        intent_analysis = {
            "primary_goal": self._extract_primary_goal(message),
            "applications_needed": self._extract_applications(message_lower),
            "websites_needed": self._extract_websites(message_lower),
            "search_terms": self._extract_search_terms(message),
            "text_to_type": [],
            "sequential_actions": self._extract_sequential_actions(message_lower),
            "complexity_score": self._calculate_complexity(message_lower)
        }
        
        # Special handling for ChatGPT
        if "chatgpt" in message_lower:
            intent_analysis["websites_needed"] = ["chat.openai.com"]
            intent_analysis["applications_needed"] = ["safari"]  # Browser needed
        
        # Generate automation steps using enhanced pattern matching
        automation_steps = await self._generate_fallback_steps(intent_analysis, message)
        
        return {
            "intent_analysis": intent_analysis,
            "automation_steps": automation_steps
        }
    
    def _extract_primary_goal(self, message: str) -> str:
        """Extract the primary goal from the message"""
        message_lower = message.lower()
        
        if "chatgpt" in message_lower and "search" in message_lower:
            return "Open ChatGPT and perform a search"
        elif "open" in message_lower and "search" in message_lower:
            return "Open application and search for information"
        elif "search" in message_lower:
            return "Search for information"
        elif "open" in message_lower:
            return "Open application or website"
        else:
            return message[:50] + "..." if len(message) > 50 else message
    
    def _extract_applications(self, message_lower: str) -> List[str]:
        """Extract application names, handling ChatGPT as a web service"""
        apps = []
        
        # Browser apps needed for web services
        if any(term in message_lower for term in ["chatgpt", "chat.openai", "openai"]):
            apps.append("safari")  # Need browser for ChatGPT
        
        # Traditional applications
        app_patterns = {
            "safari": ["safari", "browser"],
            "chrome": ["chrome", "google chrome"],
            "firefox": ["firefox"],
            "textedit": ["textedit", "text editor", "notepad"],
            "notes": ["notes", "apple notes"],
            "calculator": ["calculator", "calc"],
            "finder": ["finder", "file manager"],
            "terminal": ["terminal", "command line"]
        }
        
        for app, patterns in app_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                if app not in apps:  # Avoid duplicates
                    apps.append(app)
        
        return apps
    
    def _extract_websites(self, message_lower: str) -> List[str]:
        """Extract websites, with special handling for ChatGPT"""
        websites = []
        
        # Special handling for ChatGPT
        if any(term in message_lower for term in ["chatgpt", "chat gpt", "openai"]):
            websites.append("chat.openai.com")
        
        # Other websites
        website_patterns = {
            "youtube.com": ["youtube", "yt"],
            "google.com": ["google", "google search"],
            "facebook.com": ["facebook", "fb"],
            "twitter.com": ["twitter", "x.com"],
            "instagram.com": ["instagram", "ig"],
            "reddit.com": ["reddit"],
            "linkedin.com": ["linkedin"],
            "github.com": ["github"]
        }
        
        for site, patterns in website_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                if site not in websites:  # Avoid duplicates
                    websites.append(site)
        
        return websites
    
    def _extract_search_terms(self, message: str) -> List[str]:
        """Extract search terms with better parsing"""
        search_terms = []
        
        # Look for quoted text first
        quotes_pattern = r'["\']([^"\']+)["\']'
        quotes_matches = re.findall(quotes_pattern, message)
        search_terms.extend(quotes_matches)
        
        # Look for search patterns
        search_patterns = [
            r'search (?:for |)(.+?)(?:\s+on\s|\s+in\s|$)',
            r'find (.+?)(?:\s+on\s|\s+in\s|$)',
            r'look for (.+?)(?:\s+on\s|\s+in\s|$)',
        ]
        
        for pattern in search_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip()
                # Clean up the term
                term = re.sub(r'\s+and\s+.*$', '', term)  # Remove "and ..." part
                if len(term) > 1 and term not in search_terms:
                    search_terms.append(term)
        
        # Special case: if "SEGEV" is mentioned specifically
        if "SEGEV" in message and "SEGEV" not in search_terms:
            search_terms.append("SEGEV")
        
        return search_terms
    
    def _extract_sequential_actions(self, message_lower: str) -> List[str]:
        """Extract sequential actions"""
        connectors = [' and ', ' then ', ', ', ' after ', ' next ']
        
        parts = [message_lower]
        for connector in connectors:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(connector))
            parts = new_parts
        
        actions = []
        for part in parts:
            part = part.strip()
            if len(part) > 3:
                actions.append(part)
        
        return actions
    
    def _calculate_complexity(self, message_lower: str) -> float:
        """Calculate complexity score"""
        complexity_factors = {
            "chatgpt": 0.3,  # ChatGPT requires web navigation
            "multiple_steps": len([c for c in [' and ', ' then ', ', '] if c in message_lower]) * 0.2,
            "search_operations": len(re.findall(r'\b(?:search|find|look for)\b', message_lower)) * 0.15,
            "web_navigation": 0.2 if any(site in message_lower for site in ["chatgpt", "youtube", "google"]) else 0,
        }
        
        total_complexity = sum(complexity_factors.values())
        return min(1.0, max(0.3, total_complexity))
    
    async def _generate_fallback_steps(self, intent_analysis: Dict[str, Any], original_message: str) -> List[Dict[str, Any]]:
        """Generate automation steps using enhanced pattern matching"""
        steps = []
        step_counter = 1
        
        apps = intent_analysis["applications_needed"]
        websites = intent_analysis["websites_needed"]
        search_terms = intent_analysis["search_terms"]
        
        # Special ChatGPT workflow
        if "chat.openai.com" in websites or "chatgpt" in original_message.lower():
            return await self._generate_chatgpt_workflow_steps(search_terms, step_counter)
        
        # Generic browser workflow
        if apps and websites:
            browser = apps[0] if apps[0] in ["safari", "chrome", "firefox"] else "safari"
            
            # Open browser
            steps.append({
                "id": f"step_{step_counter}",
                "description": f"Open {browser.title()} browser",
                "action_type": "open_app",
                "target": browser,
                "value": None,
                "estimated_duration": 3.0,
                "confidence": 0.9
            })
            step_counter += 1
            
            # Wait for browser
            steps.append({
                "id": f"step_{step_counter}",
                "description": f"Wait for {browser.title()} to load",
                "action_type": "wait",
                "target": None,
                "value": "3",
                "estimated_duration": 3.0,
                "confidence": 1.0
            })
            step_counter += 1
            
            # Navigate to website
            for website in websites:
                steps.append({
                    "id": f"step_{step_counter}",
                    "description": f"Navigate to {website}",
                    "action_type": "navigate_url",
                    "target": "address_bar",
                    "value": website,
                    "estimated_duration": 3.0,
                    "confidence": 0.8
                })
                step_counter += 1
                
                # Wait for website
                steps.append({
                    "id": f"step_{step_counter}",
                    "description": f"Wait for {website} to load",
                    "action_type": "wait",
                    "target": None,
                    "value": "3",
                    "estimated_duration": 3.0,
                    "confidence": 1.0
                })
                step_counter += 1
            
            # Add search steps
            for search_term in search_terms:
                steps.append({
                    "id": f"step_{step_counter}",
                    "description": f"Search for '{search_term}'",
                    "action_type": "type_text",
                    "target": None,
                    "value": search_term,
                    "estimated_duration": 2.0,
                    "confidence": 0.8
                })
                step_counter += 1
                
                steps.append({
                    "id": f"step_{step_counter}",
                    "description": "Press Enter to search",
                    "action_type": "hotkey",
                    "target": "enter",
                    "value": None,
                    "estimated_duration": 1.0,
                    "confidence": 0.9
                })
                step_counter += 1
        
        return steps
    
    async def _generate_chatgpt_workflow_steps(self, search_terms: List[str], start_step: int) -> List[Dict[str, Any]]:
        """Generate specific workflow for ChatGPT"""
        steps = []
        step_counter = start_step
        
        # Step 1: Open Safari
        steps.append({
            "id": f"step_{step_counter}",
            "description": "Open Safari browser",
            "action_type": "open_app",
            "target": "safari",
            "value": None,
            "estimated_duration": 3.0,
            "confidence": 0.9
        })
        step_counter += 1
        
        # Step 2: Wait for Safari
        steps.append({
            "id": f"step_{step_counter}",
            "description": "Wait for Safari to load",
            "action_type": "wait",
            "target": None,
            "value": "3",
            "estimated_duration": 3.0,
            "confidence": 1.0
        })
        step_counter += 1
        
        # Step 3: Navigate to ChatGPT
        steps.append({
            "id": f"step_{step_counter}",
            "description": "Navigate to ChatGPT (chat.openai.com)",
            "action_type": "navigate_url",
            "target": "address_bar",
            "value": "chat.openai.com",
            "estimated_duration": 4.0,
            "confidence": 0.8
        })
        step_counter += 1
        
        # Step 4: Wait for ChatGPT to load
        steps.append({
            "id": f"step_{step_counter}",
            "description": "Wait for ChatGPT to load",
            "action_type": "wait",
            "target": None,
            "value": "5",
            "estimated_duration": 5.0,
            "confidence": 1.0
        })
        step_counter += 1
        
        # Step 5: Click on chat input area
        steps.append({
            "id": f"step_{step_counter}",
            "description": "Click on ChatGPT input area",
            "action_type": "click_element",
            "target": "chat_input",
            "value": None,
            "estimated_duration": 2.0,
            "confidence": 0.7
        })
        step_counter += 1
        
        # Step 6-7: Type search terms and send
        for search_term in search_terms:
            steps.append({
                "id": f"step_{step_counter}",
                "description": f"Type '{search_term}' in ChatGPT",
                "action_type": "type_text",
                "target": None,
                "value": search_term,
                "estimated_duration": 2.0,
                "confidence": 0.8
            })
            step_counter += 1
            
            steps.append({
                "id": f"step_{step_counter}",
                "description": "Press Enter to send message",
                "action_type": "hotkey",
                "target": "enter",
                "value": None,
                "estimated_duration": 1.0,
                "confidence": 0.9
            })
            step_counter += 1
        
        return steps
    
    async def create_intelligent_plan(self, message: str, session_id: str) -> AutomationPlan:
        """Create an intelligent automation plan using LLM analysis"""
        start_time = time.time()
        
        # Get LLM analysis
        analysis_data = await self.analyze_user_intent_with_llm(message)
        
        # Generate unique task ID
        task_id = f"task_{int(time.time())}_{session_id}"
        
        # Extract intent and steps from LLM analysis
        intent_analysis = analysis_data.get("intent_analysis", {})
        llm_steps = analysis_data.get("automation_steps", [])
        
        # Convert LLM steps to AutomationStep objects
        steps = []
        for step_data in llm_steps:
            steps.append(AutomationStep(
                id=step_data.get("id", f"step_{len(steps)+1}"),
                description=step_data.get("description", "Automation step"),
                action_type=step_data.get("action_type", "general"),
                target=step_data.get("target"),
                value=step_data.get("value"),
                confidence=step_data.get("confidence", 0.8),
                estimated_duration=step_data.get("estimated_duration", 2.0)
            ))
        
        # Calculate total estimated duration
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Generate plan title
        title = intent_analysis.get("primary_goal", message[:50] + "..." if len(message) > 50 else message)
        
        # Create plan
        plan = AutomationPlan(
            task_id=task_id,
            title=title,
            description=f"LLM-generated automation plan for: {message}",
            steps=steps,
            estimated_duration=total_duration,
            requires_approval=True,
            user_intent=message,
            complexity_score=intent_analysis.get("complexity_score", 0.5),
            llm_generated=True
        )
        
        # Store plan
        self.active_plans[task_id] = plan
        
        processing_time = time.time() - start_time
        logger.info(f"🎯 Created LLM-powered plan '{plan.title}' with {len(steps)} steps in {processing_time:.3f}s")
        
        return plan

# Create singleton instance
enhanced_llm_planner = EnhancedLLMAutomationPlanner()