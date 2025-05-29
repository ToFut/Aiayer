#!/usr/bin/env python3
"""
Intelligent Automation Planner - AI-powered task analysis and execution planning
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

class IntelligentAutomationPlanner:
    """AI-powered automation planner that understands any user intent"""
    
    def __init__(self):
        self.active_plans: Dict[str, AutomationPlan] = {}
        self.automation_available = True
        
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
    
    async def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent using AI-like parsing"""
        message_lower = message.lower()
        
        # Extract key information
        intent_analysis = {
            "primary_action": self._extract_primary_action(message_lower),
            "applications": self._extract_applications(message_lower),
            "websites": self._extract_websites(message_lower),
            "search_terms": self._extract_search_terms(message),
            "text_to_type": self._extract_text_to_type(message),
            "sequential_actions": self._extract_sequential_actions(message_lower),
            "complexity_score": self._calculate_complexity(message_lower),
            "user_intent": message
        }
        
        logger.info(f"🧠 Intent analysis: {intent_analysis['primary_action']} with {len(intent_analysis['sequential_actions'])} actions")
        return intent_analysis
    
    def _extract_primary_action(self, message_lower: str) -> str:
        """Extract the primary action from the message"""
        action_patterns = {
            "open_and_search": ["open.*search", "launch.*find", "go to.*look for"],
            "search_web": ["search.*for", "find.*on", "look for.*in"],
            "open_app": ["open", "launch", "start", "run"],
            "navigate_web": ["go to", "visit", "browse", "navigate to"],
            "type_text": ["write", "type", "enter", "input"],
            "automate_workflow": ["automate", "do", "perform", "execute"]
        }
        
        for action, patterns in action_patterns.items():
            if any(re.search(pattern, message_lower) for pattern in patterns):
                return action
        
        return "general_automation"
    
    def _extract_applications(self, message_lower: str) -> List[str]:
        """Extract application names from the message"""
        app_patterns = {
            "safari": ["safari", "browser"],
            "chrome": ["chrome", "google chrome"],
            "firefox": ["firefox"],
            "textedit": ["textedit", "text editor", "notepad"],
            "cursor": ["cursor", "curser", "code editor"],
            "vscode": ["vscode", "visual studio code", "vs code"],
            "notes": ["notes", "apple notes"],
            "calculator": ["calculator", "calc"],
            "finder": ["finder", "file manager"],
            "terminal": ["terminal", "command line"],
            "spotify": ["spotify", "music app"],
            "youtube": ["youtube app"],
            "mail": ["mail", "email app"]
        }
        
        detected_apps = []
        for app, patterns in app_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                detected_apps.append(app)
        
        return detected_apps
    
    def _extract_websites(self, message_lower: str) -> List[str]:
        """Extract websites from the message"""
        website_patterns = {
            "youtube.com": ["youtube", "yt"],
            "google.com": ["google", "google search"],
            "facebook.com": ["facebook", "fb"],
            "twitter.com": ["twitter", "x.com"],
            "instagram.com": ["instagram", "ig"],
            "reddit.com": ["reddit"],
            "linkedin.com": ["linkedin"],
            "github.com": ["github"],
            "stackoverflow.com": ["stackoverflow", "stack overflow"]
        }
        
        detected_sites = []
        for site, patterns in website_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                detected_sites.append(site)
        
        return detected_sites
    
    def _extract_search_terms(self, message: str) -> List[str]:
        """Extract search terms from the message"""
        search_patterns = [
            r'search (?:for |)(.+?)(?:\son\s|\sin\s|$)',
            r'find (.+?)(?:\son\s|\sin\s|$)',
            r'look for (.+?)(?:\son\s|\sin\s|$)',
            r'"([^"]+)"',  # Quoted text
            r"'([^']+)'"   # Single quoted text
        ]
        
        search_terms = []
        for pattern in search_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip()
                if len(term) > 2 and term not in search_terms:
                    search_terms.append(term)
        
        # Special handling for common patterns
        if "search" in message.lower() and "Omer Adam" in message:
            search_terms = ["Omer Adam"]
        elif "latest news" in message.lower():
            search_terms = ["latest news"]
        elif "google" in message.lower() and "news" in message.lower():
            search_terms = ["latest news"]
        
        # Fallback: if no specific patterns, try to extract meaningful terms
        if not search_terms:
            words = message.split()
            meaningful_words = [w for w in words if len(w) > 2 and w.lower() not in 
                             ['open', 'search', 'find', 'look', 'youtube', 'google', 'safari', 'and', 'for', 'on', 'in']]
            if meaningful_words:
                search_terms.append(' '.join(meaningful_words[:3]))  # Take first 3 meaningful words
        
        return search_terms
    
    def _extract_text_to_type(self, message: str) -> List[str]:
        """Extract text that should be typed"""
        type_patterns = [
            r'write (.+?)(?:\sin\s|\son\s|$)',
            r'type (.+?)(?:\sin\s|\son\s|$)',
            r'enter (.+?)(?:\sin\s|\son\s|$)',
            r'"([^"]+)"',
            r"'([^']+)'"
        ]
        
        text_to_type = []
        for pattern in type_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                text = match.group(1).strip()
                if text and text not in text_to_type:
                    text_to_type.append(text)
        
        # Special handling for common patterns like "open X and write Y"
        if "and write" in message.lower():
            parts = message.split("and write")  # Keep original case
            if len(parts) > 1:
                text_part = parts[1].strip()
                # Remove common words but preserve case
                text_part = re.sub(r'\b(in|on|the|a|an)\b', '', text_part, flags=re.IGNORECASE).strip()
                if text_part and text_part.lower() not in [t.lower() for t in text_to_type]:
                    text_to_type.append(text_part)
        
        return text_to_type
    
    def _extract_sequential_actions(self, message_lower: str) -> List[str]:
        """Extract sequential actions from the message"""
        # Split by common connectors
        connectors = [' and ', ' then ', ', ', ' after ', ' next ']
        
        parts = [message_lower]
        for connector in connectors:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(connector))
            parts = new_parts
        
        # Clean and filter parts
        actions = []
        for part in parts:
            part = part.strip()
            if len(part) > 3:  # Minimum meaningful length
                actions.append(part)
        
        return actions
    
    def _calculate_complexity(self, message_lower: str) -> float:
        """Calculate complexity score of the automation request"""
        complexity_factors = {
            "multiple_apps": len(re.findall(r'\b(?:open|launch|start)\b', message_lower)) * 0.2,
            "web_navigation": len(re.findall(r'\b(?:navigate|browse|visit|go to)\b', message_lower)) * 0.15,
            "search_operations": len(re.findall(r'\b(?:search|find|look for)\b', message_lower)) * 0.1,
            "text_input": len(re.findall(r'\b(?:write|type|enter)\b', message_lower)) * 0.1,
            "sequential_steps": len([c for c in [' and ', ' then ', ', '] if c in message_lower]) * 0.3,
            "website_interaction": len(re.findall(r'\b(?:youtube|google|facebook|twitter)\b', message_lower)) * 0.15
        }
        
        total_complexity = sum(complexity_factors.values())
        return min(1.0, max(0.1, total_complexity))  # Clamp between 0.1 and 1.0
    
    async def create_intelligent_plan(self, message: str, session_id: str) -> AutomationPlan:
        """Create an intelligent automation plan based on user intent"""
        start_time = time.time()
        
        # Analyze user intent
        intent = await self.analyze_user_intent(message)
        
        # Generate unique task ID
        task_id = f"task_{int(time.time())}_{session_id}"
        
        # Create comprehensive steps based on intent
        steps = await self._generate_intelligent_steps(intent)
        
        # Calculate total estimated duration
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Create plan
        plan = AutomationPlan(
            task_id=task_id,
            title=self._generate_plan_title(intent),
            description=f"AI-generated automation plan for: {message}",
            steps=steps,
            estimated_duration=total_duration,
            requires_approval=True,
            user_intent=message,
            complexity_score=intent["complexity_score"]
        )
        
        # Store plan
        self.active_plans[task_id] = plan
        
        processing_time = time.time() - start_time
        logger.info(f"🎯 Created intelligent plan '{plan.title}' with {len(steps)} steps in {processing_time:.3f}s")
        
        return plan
    
    def _generate_plan_title(self, intent: Dict[str, Any]) -> str:
        """Generate a descriptive title for the automation plan"""
        primary_action = intent["primary_action"]
        apps = intent["applications"]
        websites = intent["websites"]
        search_terms = intent["search_terms"]
        
        if primary_action == "open_and_search" and apps and search_terms:
            return f"Open {apps[0].title()} and Search for {search_terms[0]}"
        elif primary_action == "search_web" and websites and search_terms:
            return f"Search {websites[0]} for {search_terms[0]}"
        elif primary_action == "open_app" and apps:
            return f"Open {apps[0].title()}"
        elif websites and search_terms:
            return f"Browse {websites[0]} for {search_terms[0]}"
        else:
            # Generate from sequential actions
            actions = intent["sequential_actions"]
            if len(actions) > 1:
                return f"{actions[0].title()} and {len(actions)-1} more steps"
            else:
                return intent["user_intent"][:50] + "..." if len(intent["user_intent"]) > 50 else intent["user_intent"]
    
    async def _generate_intelligent_steps(self, intent: Dict[str, Any]) -> List[AutomationStep]:
        """Generate intelligent automation steps based on intent analysis"""
        steps = []
        step_counter = 1
        
        primary_action = intent["primary_action"]
        apps = intent["applications"]
        websites = intent["websites"]
        search_terms = intent["search_terms"]
        text_to_type = intent["text_to_type"]
        
        if primary_action == "open_and_search":
            # Complex workflow: Open app/browser → Navigate → Search
            browser = "safari"  # Default browser
            if "safari" in apps or "chrome" in apps or "firefox" in apps:
                browser = apps[0] if apps else "safari"
            
            # Always create browser workflow for web searches
            if websites or not apps:
                steps.extend(await self._create_browser_search_workflow(browser, websites, search_terms, step_counter))
            elif apps:
                steps.extend(await self._create_app_workflow(apps[0], search_terms, step_counter))
        
        elif primary_action == "search_web":
            # Direct web search
            browser = "safari"  # Default browser
            if apps:
                browser = apps[0]
            steps.extend(await self._create_web_search_workflow(browser, websites, search_terms, step_counter))
        
        
        elif primary_action == "type_text":
            # Text input workflow
            if text_to_type:
                if apps:
                    # Open app first, then type
                    steps.append(AutomationStep(
                        id=f"step_{step_counter}",
                        description=f"Open {apps[0].title()} application",
                        action_type="open_app",
                        target=apps[0],
                        estimated_duration=3.0
                    ))
                    step_counter += 1
                
                for text in text_to_type:
                    steps.append(AutomationStep(
                        id=f"step_{step_counter}",
                        description=f"Type '{text}'",
                        action_type="type_text",
                        value=text,
                        estimated_duration=2.0
                    ))
                    step_counter += 1
        
        elif primary_action == "open_app":
            # Enhanced app opening with text typing
            for app in apps:
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open {app.title()} application",
                    action_type="open_app",
                    target=app,
                    estimated_duration=3.0,
                    confidence=0.9
                ))
                step_counter += 1
                
                # If there's text to type after opening app
                if text_to_type:
                    for text in text_to_type:
                        steps.append(AutomationStep(
                            id=f"step_{step_counter}",
                            description=f"Type '{text}' in {app.title()}",
                            action_type="type_text",
                            value=text,
                            estimated_duration=2.0
                        ))
                        step_counter += 1
        
        else:
            # Universal intelligent planning - convert ANY message to actionable steps
            steps.extend(await self._create_universal_automation_plan(intent, step_counter))
        
        return steps
    
    async def _create_browser_search_workflow(self, browser: str, websites: List[str], search_terms: List[str], start_step: int) -> List[AutomationStep]:
        """Create browser + search workflow"""
        steps = []
        step_counter = start_step
        
        # Step 1: Open browser
        steps.append(AutomationStep(
            id=f"step_{step_counter}",
            description=f"Open {browser.title()} browser",
            action_type="open_app",
            target=browser,
            estimated_duration=3.0,
            confidence=0.9
        ))
        step_counter += 1
        
        # Step 2: Wait for browser to load
        steps.append(AutomationStep(
            id=f"step_{step_counter}",
            description=f"Wait for {browser.title()} to load",
            action_type="wait",
            value="3",
            estimated_duration=3.0,
            confidence=1.0
        ))
        step_counter += 1
        
        # Step 3: Navigate to website or search
        if websites:
            website = websites[0]
            steps.append(AutomationStep(
                id=f"step_{step_counter}",
                description=f"Navigate to {website}",
                action_type="navigate_url",
                target="address_bar",
                value=website,
                estimated_duration=3.0,
                confidence=0.8
            ))
            step_counter += 1
            
            # Step 4: Wait for website to load
            steps.append(AutomationStep(
                id=f"step_{step_counter}",
                description=f"Wait for {website} to load",
                action_type="wait",
                value="3",
                estimated_duration=3.0,
                confidence=1.0
            ))
            step_counter += 1
            
            # Step 5: Find and click search box (if YouTube)
            if "youtube" in website:
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description="Click on YouTube search box",
                    action_type="click_element",
                    target="search_box",
                    estimated_duration=2.0,
                    confidence=0.7
                ))
                step_counter += 1
        
        # Step 6: Enter search term
        if search_terms:
            search_term = search_terms[0]
            steps.append(AutomationStep(
                id=f"step_{step_counter}",
                description=f"Search for '{search_term}'",
                action_type="type_text",
                value=search_term,
                estimated_duration=2.0,
                confidence=0.8
            ))
            step_counter += 1
            
            # Step 7: Press Enter to search
            steps.append(AutomationStep(
                id=f"step_{step_counter}",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                estimated_duration=1.0,
                confidence=0.9
            ))
            step_counter += 1
        
        return steps
    
    async def _create_web_search_workflow(self, browser: str, websites: List[str], search_terms: List[str], start_step: int) -> List[AutomationStep]:
        """Create web search workflow"""
        return await self._create_browser_search_workflow(browser, websites, search_terms, start_step)
    
    async def _create_app_workflow(self, app: str, search_terms: List[str], start_step: int) -> List[AutomationStep]:
        """Create app-specific workflow"""
        steps = []
        step_counter = start_step
        
        # Open app
        steps.append(AutomationStep(
            id=f"step_{step_counter}",
            description=f"Open {app.title()} application",
            action_type="open_app",
            target=app,
            estimated_duration=3.0,
            confidence=0.9
        ))
        step_counter += 1
        
        # Wait for app to load
        steps.append(AutomationStep(
            id=f"step_{step_counter}",
            description=f"Wait for {app.title()} to load",
            action_type="wait",
            value="3",
            estimated_duration=3.0,
            confidence=1.0
        ))
        step_counter += 1
        
        # App-specific actions
        if search_terms:
            # Try to search within the app
            steps.append(AutomationStep(
                id=f"step_{step_counter}",
                description=f"Search for '{search_terms[0]}' in {app.title()}",
                action_type="type_text",
                value=search_terms[0],
                estimated_duration=2.0,
                confidence=0.6
            ))
            step_counter += 1
        
        return steps
    
    async def _parse_sequential_actions(self, intent: Dict[str, Any], start_step: int) -> List[AutomationStep]:
        """Parse sequential actions from intent"""
        steps = []
        step_counter = start_step
        
        sequential_actions = intent["sequential_actions"]
        
        for action in sequential_actions[:5]:  # Limit to 5 actions for safety
            # Basic action parsing
            if "open" in action:
                app_name = self._extract_app_from_action(action)
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open {app_name}",
                    action_type="open_app",
                    target=app_name.lower(),
                    estimated_duration=3.0
                ))
            elif "search" in action or "find" in action:
                search_term = self._extract_search_from_action(action)
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Search for '{search_term}'",
                    action_type="type_text",
                    value=search_term,
                    estimated_duration=2.0
                ))
            elif "write" in action or "type" in action:
                text = self._extract_text_from_action(action)
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Type '{text}'",
                    action_type="type_text",
                    value=text,
                    estimated_duration=2.0
                ))
            else:
                # Generic action
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=action.title(),
                    action_type="general",
                    estimated_duration=2.0
                ))
            
            step_counter += 1
        
        return steps
    
    def _extract_app_from_action(self, action: str) -> str:
        """Extract app name from action text"""
        apps = ["safari", "chrome", "firefox", "textedit", "notes", "calculator", "finder"]
        for app in apps:
            if app in action.lower():
                return app.title()
        return "Application"
    
    def _extract_search_from_action(self, action: str) -> str:
        """Extract search term from action text"""
        # Simple extraction - look for words after search/find
        words = action.split()
        search_words = []
        found_search = False
        
        for word in words:
            if word.lower() in ["search", "find", "look"]:
                found_search = True
                continue
            if found_search and word.lower() not in ["for", "in", "on"]:
                search_words.append(word)
        
        return " ".join(search_words) if search_words else "search term"
    
    def _extract_text_from_action(self, action: str) -> str:
        """Extract text to type from action text"""
        # Look for quoted text or words after write/type
        quoted_match = re.search(r'["\']([^"\']+)["\']', action)
        if quoted_match:
            return quoted_match.group(1)
        
        words = action.split()
        text_words = []
        found_write = False
        
        for word in words:
            if word.lower() in ["write", "type", "enter"]:
                found_write = True
                continue
            if found_write:
                text_words.append(word)
        
        return " ".join(text_words) if text_words else "text"
    
    async def _create_universal_automation_plan(self, intent: Dict[str, Any], start_step: int) -> List[AutomationStep]:
        """Universal automation planner - converts ANY user message into actionable steps"""
        steps = []
        step_counter = start_step
        user_message = intent["user_intent"]
        
        logger.info(f"🌍 Creating universal automation plan for: '{user_message}'")
        
        # Analyze what the user wants to do
        apps = intent["applications"]
        websites = intent["websites"]
        search_terms = intent["search_terms"]
        text_to_type = intent["text_to_type"]
        sequential_actions = intent["sequential_actions"]
        
        # Strategy 1: If apps mentioned, start with opening them
        if apps:
            for app in apps:
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open {app.title()} application",
                    action_type="open_app",
                    target=app,
                    estimated_duration=3.0,
                    confidence=0.9
                ))
                step_counter += 1
                
                # Add wait for app to load
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Wait for {app.title()} to load",
                    action_type="wait",
                    value="2",
                    estimated_duration=2.0,
                    confidence=1.0
                ))
                step_counter += 1
        
        # Strategy 2: If websites mentioned, navigate to them
        if websites:
            if not apps:  # No app opened yet, open browser
                browser = "safari"
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open {browser.title()} browser",
                    action_type="open_app",
                    target=browser,
                    estimated_duration=3.0,
                    confidence=0.9
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Wait for {browser.title()} to load",
                    action_type="wait",
                    value="3",
                    estimated_duration=3.0,
                    confidence=1.0
                ))
                step_counter += 1
            
            # Navigate to each website
            for website in websites:
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Navigate to {website}",
                    action_type="navigate_url",
                    target="address_bar",
                    value=website,
                    estimated_duration=3.0,
                    confidence=0.8
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Wait for {website} to load",
                    action_type="wait",
                    value="3",
                    estimated_duration=3.0,
                    confidence=1.0
                ))
                step_counter += 1
        
        # Strategy 3: If search terms mentioned, perform search
        if search_terms:
            if not websites and not apps:  # No app/website opened, open browser for search
                browser = "safari"
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open {browser.title()} browser",
                    action_type="open_app",
                    target=browser,
                    estimated_duration=3.0,
                    confidence=0.9
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Wait for {browser.title()} to load",
                    action_type="wait",
                    value="3",
                    estimated_duration=3.0,
                    confidence=1.0
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description="Navigate to Google",
                    action_type="navigate_url",
                    target="address_bar",
                    value="google.com",
                    estimated_duration=3.0,
                    confidence=0.8
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description="Wait for Google to load",
                    action_type="wait",
                    value="3",
                    estimated_duration=3.0,
                    confidence=1.0
                ))
                step_counter += 1
            
            # Perform search for each search term
            for search_term in search_terms:
                if websites and "youtube" in websites[0]:
                    # YouTube search
                    steps.append(AutomationStep(
                        id=f"step_{step_counter}",
                        description="Click on YouTube search box",
                        action_type="click_element",
                        target="youtube_search",
                        estimated_duration=2.0,
                        confidence=0.7
                    ))
                    step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Search for '{search_term}'",
                    action_type="type_text",
                    value=search_term,
                    estimated_duration=2.0,
                    confidence=0.8
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description="Press Enter to search",
                    action_type="hotkey",
                    target="enter",
                    estimated_duration=1.0,
                    confidence=0.9
                ))
                step_counter += 1
        
        # Strategy 4: If text to type mentioned, handle typing
        if text_to_type:
            if not apps:  # No app opened, open a text editor
                text_app = "textedit"
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open {text_app.title()} application",
                    action_type="open_app",
                    target=text_app,
                    estimated_duration=3.0,
                    confidence=0.9
                ))
                step_counter += 1
                
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Wait for {text_app.title()} to load",
                    action_type="wait",
                    value="2",
                    estimated_duration=2.0,
                    confidence=1.0
                ))
                step_counter += 1
            
            # Type each text
            for text in text_to_type:
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Type '{text}'",
                    action_type="type_text",
                    value=text,
                    estimated_duration=2.0,
                    confidence=0.8
                ))
                step_counter += 1
        
        # Strategy 5: Parse sequential actions if no specific patterns found
        if not steps and sequential_actions:
            steps.extend(await self._parse_sequential_actions(intent, step_counter))
        
        # Strategy 6: Last resort - create a generic plan based on keywords
        if not steps:
            steps.extend(await self._create_generic_plan_from_keywords(user_message, step_counter))
        
        logger.info(f"🎯 Universal planner created {len(steps)} steps for: '{user_message}'")
        return steps
    
    async def _create_generic_plan_from_keywords(self, message: str, start_step: int) -> List[AutomationStep]:
        """Create a generic automation plan based on keywords in the message"""
        steps = []
        step_counter = start_step
        message_lower = message.lower()
        
        # Keyword-based action mapping
        keyword_actions = {
            "open": ("open_app", "textedit"),
            "write": ("type_text", message.split("write")[-1].strip() if "write" in message_lower else "text"),
            "type": ("type_text", message.split("type")[-1].strip() if "type" in message_lower else "text"),
            "search": ("navigate_url", "google.com"),
            "find": ("navigate_url", "google.com"),
            "browse": ("navigate_url", "google.com"),
            "visit": ("navigate_url", ""),
            "click": ("click_element", "center"),
            "press": ("hotkey", "enter"),
        }
        
        # Extract actions from keywords
        found_actions = []
        for keyword, (action_type, default_value) in keyword_actions.items():
            if keyword in message_lower:
                found_actions.append((action_type, default_value))
        
        # Create steps from found actions
        for action_type, value in found_actions:
            if action_type == "open_app":
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Open application",
                    action_type=action_type,
                    target=value,
                    estimated_duration=3.0
                ))
                step_counter += 1
            elif action_type == "type_text":
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Type text: {value}",
                    action_type=action_type,
                    value=value,
                    estimated_duration=2.0
                ))
                step_counter += 1
            elif action_type == "navigate_url":
                steps.append(AutomationStep(
                    id=f"step_{step_counter}",
                    description=f"Navigate to website",
                    action_type=action_type,
                    target="address_bar",
                    value=value if value else "google.com",
                    estimated_duration=3.0
                ))
                step_counter += 1
        
        # If still no steps, create a basic "analyze and attempt" step
        if not steps:
            steps.append(AutomationStep(
                id=f"step_{step_counter}",
                description=f"Analyze request: {message}",
                action_type="analyze",
                value=message,
                estimated_duration=2.0,
                confidence=0.5
            ))
        
        return steps

# Create singleton instance
intelligent_planner = IntelligentAutomationPlanner()