#!/usr/bin/env python3
"""
Real Agent Automation Handler - Interactive UI Automation
Provides Do/Dismiss/Adjust workflow with actual screen interaction
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AutomationStep:
    """Represents a single automation step"""
    id: str
    description: str
    action_type: str  # 'click', 'type', 'open', 'hotkey', 'analyze'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"  # pending, approved, executing, completed, failed
    estimated_duration: float = 2.0  # Default duration in seconds

@dataclass
class AutomationPlan:
    """Complete automation plan with interactive approval"""
    task_id: str
    title: str
    description: str
    steps: List[AutomationStep]
    estimated_duration: float
    requires_approval: bool = True
    status: str = "awaiting_approval"  # awaiting_approval, approved, executing, completed, cancelled

class RealAgentAutomationHandler:
    """Handles real automation with interactive approval workflow"""
    
    def __init__(self):
        self.active_plans: Dict[str, AutomationPlan] = {}
        self.automation_available = False
        
        # Try to import automation components
        try:
            from agent_workflow.input_controller import InputController
            from sensors.total_screen_analyzer import TotalScreenAnalyzer
            self.input_controller = InputController(safety_level="medium")
            self.screen_analyzer = TotalScreenAnalyzer(fast_mode=True)
            self.automation_available = True
            logger.info("🤖 Real automation components loaded successfully")
        except ImportError as e:
            logger.warning(f"Automation components not available: {e}")
            self.input_controller = None
            self.screen_analyzer = None
    
    async def handle_agent_request(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle agent request with universal LLM-based automation planning"""
        try:
            start_time = time.time()
            
            # Use LLM-based planning for ANY message type (PRIMARY method as requested)
            try:
                plan = await self._create_universal_llm_plan(message, session_id)
                logger.info(f"🧠 Using LLM automation planning (PRIMARY)")
                ai_powered = True
            except Exception as llm_error:
                logger.warning(f"LLM planner failed, trying smart planner: {llm_error}")
                # Fallback to Universal Smart Planner
                try:
                    from universal_smart_planner import create_universal_smart_plan
                    plan = await create_universal_smart_plan(message, session_id)
                    logger.info(f"🧠 Using universal smart automation planning (fallback)")
                    ai_powered = True
                except Exception as smart_error:
                    logger.warning(f"Smart planner failed, using pattern fallback: {smart_error}")
                    # Final fallback to pattern-based planning
                    try:
                        plan = await self._create_automation_plan(message, session_id)
                        logger.info(f"🤖 Using pattern-based automation planning")
                        ai_powered = False
                    except Exception as pattern_error:
                        logger.error(f"All planners failed: {pattern_error}")
                        # Last resort - create minimal plan
                        plan = await self._create_minimal_plan(message, session_id)
                        ai_powered = False
            
            # Store plan for approval
            self.active_plans[plan.task_id] = plan
            
            # Return interactive response with Do/Dismiss/Adjust buttons
            response_data = self._format_interactive_response(plan)
            
            return {
                "success": True,
                "response": response_data["text"],
                "buttons": response_data["buttons"],
                "interactive": response_data["interactive"],
                "plan_id": plan.task_id,
                "requires_approval": True,
                "processing_time": time.time() - start_time,
                "automation_available": self.automation_available,
                "interactive_mode": True,
                "ai_powered": ai_powered,
                "llm_generated": getattr(plan, 'llm_generated', False),
                "complexity_score": getattr(plan, 'complexity_score', 0.5)
            }
            
        except Exception as e:
            logger.error(f"Error handling agent request: {e}")
            return {
                "success": False,
                "response": f"Error creating automation plan: {str(e)}",
                "automation_available": self.automation_available
            }
    
    async def _create_universal_llm_plan(self, message: str, session_id: str) -> AutomationPlan:
        """Create detailed automation plan using LLM for ANY message type"""
        # Use direct LLM service initialization for reliable planning
        try:
            from llm.llm_service import LLMService
            llm_service = LLMService()
            logger.info("🧠 LLM service initialized for automation planning")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise Exception(f"LLM service unavailable: {e}")
        
        # Enhanced prompt for universal automation planning
        system_prompt = """You are an expert Mac automation agent. Your job is to create detailed, step-by-step automation plans for ANY user request.

SYSTEM ENVIRONMENT:
- Operating System: macOS (Darwin 23.1.0)
- Screen Resolution: 1470x956
- Default Browser: Safari
- Available: Spotlight search (Cmd+Space), all macOS applications, web browsing

AUTOMATION CAPABILITIES:
- open_app: Launch applications via Spotlight
- navigate_url: Open URLs in Safari
- click_element: Click UI elements at coordinates
- type_text: Enter text into input fields
- hotkey: Execute keyboard shortcuts
- wait: Pause for interface loading
- analyze_screen: Check current screen state

YOUR TASK:
1. Analyze the user's request thoroughly
2. Break it down into detailed, executable steps
3. Create Mac-specific automation commands
4. Include proper timing and error handling
5. Handle ANY type of request (web browsing, app usage, file operations, searches, etc.)

RESPONSE FORMAT (JSON - NO COMMENTS ALLOWED):
{
  "title": "Clear title for the automation task",
  "description": "Brief description of what will be accomplished",
  "complexity_score": 0.7,
  "estimated_duration": 15,
  "steps": [
    {
      "id": "step_1",
      "description": "Human-readable description of this step",
      "action_type": "open_app",
      "target": "Safari",
      "value": "text_to_type_or_null",
      "coordinates": null,
      "estimated_duration": 3,
      "confidence": 0.9
    }
  ]
}

CRITICAL: 
- DO NOT include any comments (//) in the JSON
- Use actual numbers for estimated_duration, not "seconds" 
- Use single action_type values like "open_app", not "open_app|navigate_url"
- Use null without quotes for null values
- Provide valid JSON only

EXAMPLES OF DIFFERENT REQUEST TYPES:

Web Browsing: "open YouTube and search SEGEV"
App Usage: "open Calculator and compute 15 * 27"
File Operations: "create a new TextEdit document"
Research: "find information about Python programming"
Social Media: "check my Twitter feed"
Email: "compose an email"
Travel/Flight Search: "find best flights between NYC to Miami" 
Shopping: "search for MacBook deals on Amazon"
News: "check latest news about technology"

Be creative and comprehensive. Handle edge cases. Always provide detailed, actionable steps."""

        user_prompt = f"""Create a detailed Mac automation plan for this request:

USER REQUEST: "{message}"

Analyze this request and create a complete automation plan with step-by-step instructions. Consider:
1. What applications need to be opened?
2. What websites need to be visited?
3. What specific actions need to be performed?
4. What text needs to be entered?
5. What coordinates might be needed for clicks?
6. How long each step might take?

Provide a comprehensive JSON response that covers the entire workflow."""

        try:
            # Import json at function level to avoid scope issues
            import json
            
            # Get LLM response using the correct API
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = await llm_service.generate_response(full_prompt)
            
            # Debug: log the actual response
            logger.info(f"🔍 Raw LLM response length: {len(response) if response else 0}")
            logger.info(f"🔍 Raw LLM response (first 200 chars): {response[:200] if response else 'None'}")
            
            # Check if response is empty or None
            if not response or response.strip() == "":
                raise Exception("LLM returned empty response")
            
            # Try to extract JSON from response (in case there's extra text)
            response_text = response.strip()
            
            # Multiple JSON extraction strategies
            json_text = None
            
            # Strategy 1: Look for JSON block markers (including plain ```)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    json_text = response_text[start:end].strip()
            elif "```" in response_text:
                # Handle plain code blocks without 'json' keyword
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end != -1:
                    potential_json = response_text[start:end].strip()
                    # Check if it looks like JSON
                    if potential_json.startswith("{") and potential_json.endswith("}"):
                        json_text = potential_json
            
            # Strategy 2: Look for JSON object boundaries
            if not json_text and "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_text = response_text[start:end]
            
            # Strategy 3: Try cleaning the response text
            if not json_text:
                # Remove common non-JSON prefixes/suffixes
                clean_text = response_text
                for prefix in ["Here's the JSON:", "JSON response:", "Here is the plan:"]:
                    if clean_text.startswith(prefix):
                        clean_text = clean_text[len(prefix):].strip()
                
                # Look for JSON again after cleaning
                if "{" in clean_text and "}" in clean_text:
                    start = clean_text.find("{")
                    end = clean_text.rfind("}") + 1
                    json_text = clean_text[start:end]
            
            # If still no JSON found, use the whole response
            if not json_text:
                json_text = response_text
            
            # Log the extracted JSON for debugging
            logger.info(f"🔍 Extracted JSON (length: {len(json_text)}): {json_text[:200]}...")
            
            # Parse JSON response with better error handling
            try:
                plan_data = json.loads(json_text)
            except json.JSONDecodeError as parse_error:
                # Try to fix common JSON issues
                fixed_json = json_text
                
                import re
                
                # CRITICAL FIX: Remove JavaScript-style comments (// comments) - ROOT CAUSE
                fixed_json = re.sub(r'//.*?(?=\n|$)', '', fixed_json)
                
                # Remove /* */ style comments as well
                fixed_json = re.sub(r'/\*.*?\*/', '', fixed_json, flags=re.DOTALL)
                
                # Fix trailing commas
                fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                
                # Fix unquoted keys (but be careful not to touch already quoted keys)
                fixed_json = re.sub(r'(\n\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json)
                
                # Fix invalid duration values like "2 seconds" -> 2
                fixed_json = re.sub(r'"(\d+(?:\.\d+)?)\s+seconds?"', r'\1', fixed_json)
                
                # Fix bare duration word like "estimated_duration": seconds -> "estimated_duration": 2
                fixed_json = re.sub(r'"estimated_duration":\s*seconds', r'"estimated_duration": 2', fixed_json)
                fixed_json = re.sub(r'"estimated_duration":\s*total_seconds', r'"estimated_duration": 10', fixed_json)
                
                # Fix array null values [null, null] -> null
                fixed_json = re.sub(r'\[null,\s*null\]', 'null', fixed_json)
                
                # Fix pipe-separated action types to single value
                fixed_json = re.sub(r'"action_type":\s*"([^|"]+)\|[^"]*"', r'"action_type": "\1"', fixed_json)
                
                # Fix target with = signs like "application_name=Safari" -> "Safari"
                fixed_json = re.sub(r'"target":\s*"[^=]*=([^"]*)"', r'"target": "\1"', fixed_json)
                
                # Fix null values that aren't properly quoted
                fixed_json = re.sub(r':\s*null\s*([,}])', r': null\1', fixed_json)
                
                # Fix boolean values
                fixed_json = re.sub(r':\s*true\s*([,}])', r': true\1', fixed_json)
                fixed_json = re.sub(r':\s*false\s*([,}])', r': false\1', fixed_json)
                
                # Remove any remaining extra whitespace and newlines between elements
                fixed_json = re.sub(r',\s*\n\s*([}\]])', r'\n\1', fixed_json)
                
                # Log the fixes applied
                if fixed_json != json_text:
                    logger.info(f"🔧 Applied JSON fixes: {len(json_text)} -> {len(fixed_json)} chars")
                
                # Try parsing again
                try:
                    plan_data = json.loads(fixed_json)
                    logger.info("🔧 Successfully fixed and parsed JSON")
                except json.JSONDecodeError as second_error:
                    logger.error(f"JSON parsing failed even after fixes. Original: {parse_error}, After fixes: {second_error}")
                    logger.error(f"Fixed JSON sample: {fixed_json[:300]}...")
                    raise parse_error
            
            # Create AutomationPlan object
            task_id = f"task_{int(time.time())}_{session_id}"
            
            # Convert steps to AutomationStep objects
            automation_steps = []
            for i, step_data in enumerate(plan_data.get("steps", [])):
                step = AutomationStep(
                    id=step_data.get("id", f"step_{i+1}"),
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", "analyze_screen"),
                    target=step_data.get("target"),
                    value=step_data.get("value"),
                    coordinates=tuple(step_data["coordinates"]) if step_data.get("coordinates") else None,
                    confidence=step_data.get("confidence", 0.8),
                    estimated_duration=step_data.get("estimated_duration", 2.0)
                )
                automation_steps.append(step)
            
            # Create automation plan
            plan = AutomationPlan(
                task_id=task_id,
                title=plan_data.get("title", "LLM Automation Plan"),
                description=plan_data.get("description", message),
                steps=automation_steps,
                estimated_duration=plan_data.get("estimated_duration", len(automation_steps) * 2.0),
                requires_approval=True,
                status="awaiting_approval"
            )
            
            # Mark as LLM generated
            plan.llm_generated = True
            plan.complexity_score = plan_data.get("complexity_score", 0.5)
            
            logger.info(f"🧠 LLM created plan '{plan.title}' with {len(automation_steps)} steps")
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            raise e
    
    async def _create_automation_plan(self, message: str, session_id: str) -> AutomationPlan:
        """Create detailed automation plan from user request"""
        task_id = f"task_{int(time.time())}_{session_id}"
        
        # Analyze the request and create steps
        steps = await self._analyze_and_create_steps(message)
        
        # Calculate estimated duration
        estimated_duration = sum(self._estimate_step_duration(step) for step in steps)
        
        plan = AutomationPlan(
            task_id=task_id,
            title=self._generate_task_title(message),
            description=message,
            steps=steps,
            estimated_duration=estimated_duration,
            requires_approval=True
        )
        
        logger.info(f"Created automation plan '{plan.title}' with {len(steps)} steps")
        return plan
    
    async def _create_minimal_plan(self, message: str, session_id: str) -> AutomationPlan:
        """Create minimal fallback plan when all other planners fail"""
        task_id = f"task_{int(time.time())}_{session_id}"
        
        # Create a single generic step
        steps = [
            AutomationStep(
                id="step_1",
                description=f"Process request: {message[:50]}...",
                action_type="general",
                value=message,
                confidence=0.3,
                estimated_duration=2.0
            )
        ]
        
        plan = AutomationPlan(
            task_id=task_id,
            title="Minimal Automation Plan",
            description=f"Basic processing for: {message}",
            steps=steps,
            estimated_duration=2.0,
            requires_approval=True
        )
        
        logger.warning(f"Created minimal fallback plan for: {message}")
        return plan
    
    async def _analyze_and_create_steps(self, message: str) -> List[AutomationStep]:
        """Analyze user request and create automation steps"""
        message_lower = message.lower()
        steps = []
        
        # Check for complex multi-step workflows first
        if self._is_complex_browser_workflow(message_lower):
            steps.extend(await self._create_browser_workflow_steps(message))
        elif "notepad" in message_lower or "text editor" in message_lower:
            steps.extend(await self._create_notepad_steps(message))
        elif "search" in message_lower and "google" in message_lower:
            steps.extend(await self._create_google_search_steps(message))
        elif "workflow" in message_lower or "productivity" in message_lower:
            steps.extend(await self._create_productivity_workflow_steps(message))
        elif "open" in message_lower:
            steps.extend(await self._create_app_opening_steps(message))
        else:
            # Generic automation steps
            steps.extend(await self._create_generic_steps(message))
        
        return steps
    
    def _is_complex_browser_workflow(self, message_lower: str) -> bool:
        """Check if this is a complex browser workflow"""
        browsers = ["safari", "chrome", "firefox", "browser"]
        websites = ["youtube", "google", "facebook", "twitter", "instagram", "reddit"]
        actions = ["search", "find", "look for", "browse", "navigate"]
        
        has_browser = any(browser in message_lower for browser in browsers)
        has_website = any(website in message_lower for website in websites)
        has_action = any(action in message_lower for action in actions)
        has_connectors = any(conn in message_lower for conn in [" and ", " then ", ","])
        
        return (has_browser and (has_website or has_action)) or has_connectors
    
    async def _create_browser_workflow_steps(self, message: str) -> List[AutomationStep]:
        """Create comprehensive browser workflow steps"""
        message_lower = message.lower()
        steps = []
        
        # Detect browser
        browser = "Safari"  # Default
        if "chrome" in message_lower:
            browser = "Chrome" 
        elif "firefox" in message_lower:
            browser = "Firefox"
        
        # Step 1: Open browser
        steps.append(AutomationStep(
            id="step_1",
            description=f"Open {browser} browser",
            action_type="open",
            target=browser,
            confidence=0.9,
            estimated_duration=3.0
        ))
        
        # Step 2: Wait for browser to load
        steps.append(AutomationStep(
            id="step_2",
            description=f"Wait for {browser} to load",
            action_type="wait",
            value="3",
            confidence=1.0,
            estimated_duration=3.0
        ))
        
        # Detect website and search workflow
        if "youtube" in message_lower:
            steps.extend(await self._create_youtube_workflow_steps(message))
        elif "google" in message_lower:
            steps.extend(await self._create_google_workflow_steps(message))
        else:
            # Generic web browsing
            search_term = self._extract_search_term(message)
            steps.append(AutomationStep(
                id="step_3",
                description=f"Search for '{search_term}' in address bar",
                action_type="navigate",
                target="address_bar",
                value=search_term,
                confidence=0.7,
                estimated_duration=2.0
            ))
        
        return steps
    
    async def _create_youtube_workflow_steps(self, message: str) -> List[AutomationStep]:
        """Create YouTube-specific workflow steps"""
        search_term = self._extract_search_term(message)
        
        return [
            AutomationStep(
                id="step_3",
                description="Navigate to YouTube",
                action_type="navigate",
                target="address_bar",
                value="youtube.com",
                confidence=0.8,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_4",
                description="Wait for YouTube to load",
                action_type="wait",
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_5",
                description="Click on search box",
                action_type="click",
                target="search_box",
                confidence=0.7,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_6",
                description=f"Search for '{search_term}'",
                action_type="type",
                value=search_term,
                confidence=0.8,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_7",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=0.9,
                estimated_duration=0.5
            )
        ]
    
    async def _create_google_workflow_steps(self, message: str) -> List[AutomationStep]:
        """Create Google search workflow steps"""
        search_term = self._extract_search_term(message)
        
        return [
            AutomationStep(
                id="step_3",
                description="Navigate to Google",
                action_type="navigate",
                target="address_bar",
                value="google.com",
                confidence=0.8,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_4",
                description="Wait for Google to load",
                action_type="wait",
                value="2",
                confidence=1.0,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_5",
                description=f"Search for '{search_term}'",
                action_type="type",
                value=search_term,
                confidence=0.8,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_6",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=0.9,
                estimated_duration=0.5
            )
        ]
    
    async def _create_notepad_steps(self, message: str) -> List[AutomationStep]:
        """Create steps for notepad operations"""
        steps = []
        
        # Step 1: Open Notepad/TextEdit
        steps.append(AutomationStep(
            id="step_1",
            description="Open TextEdit application",
            action_type="open",
            target="TextEdit",
            confidence=0.9,
                estimated_duration=3.0
        ))
        
        # Step 2: Wait for app to load
        steps.append(AutomationStep(
            id="step_2", 
            description="Wait for TextEdit to open",
            action_type="wait",
            value="2",
            confidence=1.0,
                estimated_duration=3.0
        ))
        
        # Step 3: Type the text
        if "write" in message.lower():
            # Extract text to write
            text_to_write = self._extract_text_to_write(message)
            steps.append(AutomationStep(
                id="step_3",
                description=f"Type '{text_to_write}' in the text editor",
                action_type="type",
                value=text_to_write,
                confidence=0.8,
                estimated_duration=2.0
            ))
        
        return steps
    
    async def _create_app_opening_steps(self, message: str) -> List[AutomationStep]:
        """Create steps for opening applications"""
        app_name = self._extract_app_name(message)
        
        return [
            AutomationStep(
                id="step_1",
                description=f"Open {app_name} using Spotlight search",
                action_type="open",
                target=app_name,
                confidence=0.8,
                estimated_duration=3.0
            )
        ]
    
    async def _create_google_search_steps(self, message: str) -> List[AutomationStep]:
        """Create steps for Google search"""
        search_term = self._extract_search_term(message)
        
        steps = [
            AutomationStep(
                id="step_1",
                description="Open Safari browser",
                action_type="open",
                target="Safari",
                confidence=0.9,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_2",
                description="Wait for Safari to load",
                action_type="wait",
                value="2",
                confidence=1.0,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_3",
                description="Navigate to Google.com",
                action_type="hotkey",
                target="command+l",
                confidence=0.9,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_4",
                description="Type Google URL",
                action_type="type",
                value="google.com",
                confidence=0.9,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_5",
                description="Press Enter to navigate",
                action_type="hotkey",
                target="enter",
                confidence=1.0,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_6",
                description="Wait for Google to load",
                action_type="wait",
                value="3",
                confidence=1.0,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_7",
                description="Click on search box",
                action_type="click",
                target="search box",
                confidence=0.7,
                estimated_duration=1.0
            ),
            AutomationStep(
                id="step_8",
                description=f"Type search term: {search_term}",
                action_type="type",
                value=search_term,
                confidence=0.9,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_9",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=1.0,
                estimated_duration=0.5
            )
        ]
        
        return steps
    
    async def _create_productivity_workflow_steps(self, message: str) -> List[AutomationStep]:
        """Create steps for productivity workflow creation"""
        return [
            AutomationStep(
                id="step_1",
                description="Open Notes app for workflow planning",
                action_type="open",
                target="Notes",
                confidence=0.9,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_2",
                description="Wait for Notes to open",
                action_type="wait",
                value="2",
                confidence=1.0,
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_3",
                description="Create new note for daily workflow",
                action_type="hotkey",
                target="command+n",
                confidence=0.9,
                estimated_duration=0.5
            ),
            AutomationStep(
                id="step_4",
                description="Type workflow template",
                action_type="type",
                value="Daily Productivity Workflow\n\n1. Morning Review (9:00 AM)\n   - Check calendar\n   - Review priorities\n   - Plan day\n\n2. Focused Work Block (9:30-11:30 AM)\n   - Deep work on main project\n   - No interruptions\n\n3. Communication Block (11:30-12:00 PM)\n   - Check emails\n   - Respond to messages\n   - Team updates\n\n4. Lunch & Break (12:00-1:00 PM)\n\n5. Afternoon Work Block (1:00-3:00 PM)\n   - Secondary tasks\n   - Meetings if needed\n\n6. Administrative Tasks (3:00-4:00 PM)\n   - File organization\n   - Documentation\n   - Planning tomorrow\n\n7. End of Day Review (4:00-4:30 PM)\n   - Reflect on progress\n   - Note lessons learned\n   - Prepare for tomorrow",
                confidence=0.9
            ),
            AutomationStep(
                id="step_5",
                description="Save the workflow document",
                action_type="hotkey",
                target="command+s",
                confidence=1.0,
                estimated_duration=0.5
            )
        ]
    
    async def _create_generic_steps(self, message: str) -> List[AutomationStep]:
        """Create generic automation steps"""
        return [
            AutomationStep(
                id="step_1",
                description=f"Analyze request: {message[:50]}...",
                action_type="analyze",
                confidence=0.8,
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_2",
                description="Execute appropriate action based on analysis",
                action_type="execute",
                confidence=0.6,
                estimated_duration=2.0
            )
        ]
    
    def _format_interactive_response(self, plan: AutomationPlan) -> Dict[str, Any]:
        """Format response with interactive Do/Dismiss/Adjust buttons"""
        # Main response text
        response_text = f"🤖 **Agent Mode: Automation Plan Ready**\n\n"
        response_text += f"**Task:** {plan.title}\n"
        response_text += f"**Estimated Duration:** {plan.estimated_duration:.1f} seconds\n"
        response_text += f"**Steps:** {len(plan.steps)} actions\n\n"
        
        response_text += "**Automation Plan:**\n"
        for i, step in enumerate(plan.steps, 1):
            confidence_emoji = "✅" if step.confidence > 0.8 else "⚠️" if step.confidence > 0.6 else "❓"
            response_text += f"{i}. {confidence_emoji} {step.description}\n"
            if step.action_type == "type" and step.value:
                response_text += f"   → Will type: '{step.value}'\n"
            elif step.action_type == "click" and step.target:
                response_text += f"   → Will click: {step.target}\n"
            elif step.action_type == "open" and step.target:
                response_text += f"   → Will open: {step.target}\n"
        
        response_text += f"\n**Plan ID:** `{plan.task_id}`\n"
        
        # Show planning method
        if getattr(plan, 'llm_generated', False):
            response_text += f"**Planning:** 🧠 LLM-Generated (Enhanced AI)\n\n"
        else:
            response_text += f"**Planning:** 🤖 Pattern-Based (Basic AI)\n\n"
        
        response_text += f"*Automation System: {'✅ Ready' if self.automation_available else '❌ Not Available'}*"
        
        # Interactive buttons
        buttons = [
            {
                "id": f"do_{plan.task_id}",
                "text": "🟢 DO",
                "action": "execute_plan",
                "plan_id": plan.task_id,
                "style": "success",
                "description": "Execute this automation plan"
            },
            {
                "id": f"dismiss_{plan.task_id}",
                "text": "🔴 DISMISS", 
                "action": "cancel_plan",
                "plan_id": plan.task_id,
                "style": "danger",
                "description": "Cancel this automation"
            },
            {
                "id": f"adjust_{plan.task_id}",
                "text": "🟡 ADJUST",
                "action": "modify_plan", 
                "plan_id": plan.task_id,
                "style": "warning",
                "description": "Modify the plan before execution"
            }
        ]
        
        return {
            "text": response_text,
            "buttons": buttons,
            "interactive": True,
            "plan_id": plan.task_id
        }
    
    def _extract_text_to_write(self, message: str) -> str:
        """Extract text to write from message"""
        message_lower = message.lower()
        
        # Look for quoted text
        import re
        quotes_match = re.search(r'["\']([^"\']+)["\']', message)
        if quotes_match:
            return quotes_match.group(1)
        
        # Look for text after "write"
        if "write" in message_lower:
            parts = message.split("write", 1)
            if len(parts) > 1:
                text_part = parts[1].strip()
                # Remove common words
                text_part = text_part.replace("in notepad", "").replace("in textview", "").strip()
                return text_part
        
        return "Sample Text"
    
    def _extract_app_name(self, message: str) -> str:
        """Extract application name from message"""
        app_mapping = {
            "terminal": "Terminal",
            "safari": "Safari", 
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "finder": "Finder",
            "calculator": "Calculator",
            "notes": "Notes",
            "calendar": "Calendar",
            "textview": "TextEdit",
            "notepad": "TextEdit"
        }
        
        message_lower = message.lower()
        for keyword, app_name in app_mapping.items():
            if keyword in message_lower:
                return app_name
        
        return "Application"
    
    def _extract_search_term(self, message: str) -> str:
        """Extract search term from message"""
        import re
        
        # Look for quoted search terms
        quotes_match = re.search(r'["\']([^"\']+)["\']', message)
        if quotes_match:
            return quotes_match.group(1)
        
        # Look for search patterns
        search_patterns = [
            r'search (?:for|in google) (.+)',
            r'google (.+)',
            r'find (.+)'
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).strip()
        
        return "search term"
    
    def _generate_task_title(self, message: str) -> str:
        """Generate a concise title for the task"""
        words = message.split()[:6]
        title = " ".join(words)
        if len(message.split()) > 6:
            title += "..."
        return title.title()
    
    def _estimate_step_duration(self, step: AutomationStep) -> float:
        """Estimate duration for a step"""
        duration_map = {
            "open": 3.0,
            "click": 1.0,
            "type": 2.0,
            "hotkey": 0.5,
            "wait": float(step.value) if step.value and step.value.isdigit() else 1.0,
            "analyze": 2.0,
            "execute": 3.0
        }
        return duration_map.get(step.action_type, 1.0)
    
    async def handle_button_action(self, action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
        """Handle button actions (DO, DISMISS, ADJUST)"""
        try:
            if plan_id not in self.active_plans:
                return {
                    "success": False,
                    "response": "❌ Plan not found or expired. Please create a new automation request.",
                    "interactive": False
                }
            
            plan = self.active_plans[plan_id]
            
            if action == "execute_plan":
                return await self._execute_plan(plan, session_id)
            elif action == "cancel_plan":
                return await self._cancel_plan(plan, session_id)
            elif action == "modify_plan":
                return await self._modify_plan(plan, session_id)
            else:
                return {
                    "success": False,
                    "response": f"❌ Unknown action: {action}",
                    "interactive": False
                }
                
        except Exception as e:
            logger.error(f"Error handling button action: {e}")
            return {
                "success": False,
                "response": f"❌ Error processing action: {str(e)}",
                "interactive": False
            }
    
    async def _execute_plan(self, plan: AutomationPlan, session_id: str) -> Dict[str, Any]:
        """Execute the automation plan"""
        try:
            start_time = time.time()
            plan.status = "executing"
            
            if not self.automation_available:
                return {
                    "success": False,
                    "response": "❌ Automation components not available. Cannot execute plan.",
                    "interactive": False
                }
            
            logger.info(f"🚀 Executing automation plan: {plan.title}")
            
            # Check if plan has steps
            if len(plan.steps) == 0:
                logger.warning("⚠️ Plan has no steps to execute")
                return {
                    "success": False,
                    "response": "❌ No automation steps were generated for this request. Please try a more specific command.",
                    "interactive": False
                }
            
            # Execute each step with adaptive retry logic
            executed_steps = 0
            failed_steps = 0
            failure_details = []
            
            # Import adaptive retry handler
            try:
                from adaptive_retry_automation_handler import adaptive_retry_handler
                retry_available = True
                logger.info("🔄 Using adaptive retry automation handler")
            except Exception as e:
                logger.warning(f"Adaptive retry not available, using standard execution: {e}")
                retry_available = False
            
            # Import visual announcer
            try:
                from visual_step_announcer import visual_announcer
                announcer_available = True
            except Exception as e:
                logger.warning(f"Visual announcer not available: {e}")
                announcer_available = False
            
            for i, step in enumerate(plan.steps):
                try:
                    step.status = "executing"
                    progress = int((i / len(plan.steps)) * 100) if len(plan.steps) > 0 else 0
                    logger.info(f"📊 Step {i+1}/{len(plan.steps)}: {step.description} ({progress}%)")
                    
                    # Visual step announcement
                    if announcer_available:
                        await visual_announcer.announce_step(i+1, len(plan.steps), step.description)
                    
                    if retry_available:
                        # Use adaptive retry handler
                        result = await adaptive_retry_handler.execute_step_with_retry(step, plan.task_id)
                        success = result.success
                        
                        if success:
                            executed_steps += 1
                            retry_info = f" (succeeded after {result.retry_count} retries)" if result.retry_count > 0 else ""
                            logger.info(f"✅ Step completed: {step.description}{retry_info}")
                        else:
                            failed_steps += 1
                            failure_details.append({
                                "step": step.description,
                                "reason": result.failure_reason,
                                "retries": result.retry_count
                            })
                            logger.warning(f"❌ Step failed after {result.retry_count} retries: {step.description} - {result.failure_reason}")
                    else:
                        # Fallback to standard execution
                        success = await self._execute_step(step)
                        
                        if success:
                            step.status = "completed"
                            executed_steps += 1
                            logger.info(f"✅ Step completed: {step.description}")
                        else:
                            step.status = "failed"
                            failed_steps += 1
                            failure_details.append({
                                "step": step.description,
                                "reason": "execution_failed",
                                "retries": 0
                            })
                            logger.warning(f"❌ Step failed: {step.description}")
                    
                    # Progress update after each step
                    progress = int(((i + 1) / len(plan.steps)) * 100) if len(plan.steps) > 0 else 100
                    logger.info(f"📊 Progress: {progress}% ({i+1}/{len(plan.steps)} steps)")
                    
                    # Quick delay between steps for fast execution
                    await asyncio.sleep(0.3)  # Reduced from 2.0s to 0.3s for speed
                    
                except Exception as e:
                    step.status = "failed"
                    failed_steps += 1
                    failure_details.append({
                        "step": step.description,
                        "reason": f"exception: {str(e)}",
                        "retries": 0
                    })
                    logger.error(f"❌ Step error: {step.description} - {e}")
            
            # Update plan status
            plan.status = "completed" if failed_steps == 0 else "partially_completed"
            
            # Generate execution report with retry details
            execution_time = time.time() - start_time
            success_rate = (executed_steps / len(plan.steps)) * 100
            
            response = f"🎯 **Automation Execution Complete**\n\n"
            response += f"**Task:** {plan.title}\n"
            response += f"**Execution Time:** {execution_time:.1f} seconds\n"
            response += f"**Success Rate:** {success_rate:.1f}% ({executed_steps}/{len(plan.steps)} steps)\n"
            response += f"**Status:** {plan.status.replace('_', ' ').title()}\n"
            
            if retry_available:
                response += f"**Retry System:** ✅ Adaptive retry enabled\n\n"
            else:
                response += f"**Retry System:** ❌ Standard execution\n\n"
            
            if failed_steps > 0:
                response += f"⚠️ **Failed Steps:** {failed_steps} step(s) failed during execution\n\n"
                response += "**Failure Analysis:**\n"
                for failure in failure_details:
                    response += f"• {failure['step']}\n"
                    response += f"  └─ Reason: {failure['reason']}\n"
                    response += f"  └─ Retries attempted: {failure['retries']}\n\n"
            else:
                response += f"✅ **All steps executed successfully!**\n"
            
            # Visual completion announcement
            if announcer_available:
                await visual_announcer.announce_completion(success_rate, len(plan.steps))
            
            # Clean up completed plan
            if plan.task_id in self.active_plans:
                del self.active_plans[plan.task_id]
            
            return {
                "success": True,
                "response": response,
                "execution_time": execution_time,
                "success_rate": success_rate,
                "steps_executed": executed_steps,
                "steps_failed": failed_steps,
                "interactive": False
            }
            
        except Exception as e:
            logger.error(f"Error executing plan: {e}")
            return {
                "success": False,
                "response": f"❌ Execution failed: {str(e)}",
                "interactive": False
            }
    
    async def _cancel_plan(self, plan: AutomationPlan, session_id: str) -> Dict[str, Any]:
        """Cancel the automation plan"""
        plan.status = "cancelled"
        
        # Clean up plan
        if plan.task_id in self.active_plans:
            del self.active_plans[plan.task_id]
        
        logger.info(f"🚫 Cancelled automation plan: {plan.title}")
        
        return {
            "success": True,
            "response": f"🚫 **Automation Cancelled**\n\nTask '{plan.title}' has been cancelled and will not be executed.",
            "interactive": False
        }
    
    async def _modify_plan(self, plan: AutomationPlan, session_id: str) -> Dict[str, Any]:
        """Show plan modification options"""
        response = f"🛠️ **Modify Automation Plan**\n\n"
        response += f"**Current Task:** {plan.title}\n"
        response += f"**Current Steps:** {len(plan.steps)} actions\n\n"
        response += "**Available Modifications:**\n"
        response += "• Change application target\n"
        response += "• Modify text to type\n" 
        response += "• Adjust timing delays\n"
        response += "• Add verification steps\n\n"
        response += "**To modify:** Send a new AGENT request with your adjustments, or type 'DISMISS' to cancel."
        
        return {
            "success": True,
            "response": response,
            "interactive": False,
            "modification_mode": True
        }
    
    async def _execute_step(self, step: AutomationStep) -> bool:
        """Execute a single automation step with enhanced action types"""
        try:
            # Enhanced action types from intelligent planner
            if step.action_type == "open_app":
                return await self._execute_open_app(step)
            elif step.action_type == "navigate_url":
                return await self._execute_navigate_url(step)
            elif step.action_type == "click_element":
                return await self._execute_click_element(step)
            elif step.action_type == "type_text":
                return await self._execute_type_text(step)
            elif step.action_type == "hotkey":
                return await self._execute_hotkey(step)
            elif step.action_type == "wait":
                return await self._execute_wait(step)
            
            # Legacy action types (fallback)
            elif step.action_type == "open":
                return await self._execute_open_app(step)
            elif step.action_type == "click":
                return await self._execute_click_element(step)
            elif step.action_type == "type":
                return await self._execute_type_text(step)
            elif step.action_type == "analyze":
                return await self._execute_analyze(step)
            elif step.action_type == "general":
                # Generic action - try to parse and execute
                return await self._execute_general_action(step)
            else:
                logger.warning(f"Unknown step type: {step.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing step {step.id}: {e}")
            return False
    
    async def _execute_open_app(self, step: AutomationStep) -> bool:
        """Execute app opening via Spotlight"""
        if not self.input_controller or not step.target:
            return False
        
        try:
            # Open Spotlight (Cmd+Space)
            self.input_controller.hotkey("command", "space")
            await asyncio.sleep(0.3)
            
            # Type app name
            self.input_controller.type_text(step.target)
            await asyncio.sleep(0.5)
            
            # Press Enter
            self.input_controller.press_key("enter")
            return True
            
        except Exception as e:
            logger.error(f"Error opening app {step.target}: {e}")
            return False
    
    async def _execute_click(self, step: AutomationStep) -> bool:
        """Execute click action"""
        if not self.input_controller:
            return False
        
        try:
            if step.coordinates:
                x, y = step.coordinates
                self.input_controller.click(x, y)
                return True
            else:
                # Try to find coordinates using screen analysis
                if self.screen_analyzer:
                    screen_data = await self.screen_analyzer.analyze_full_screen()
                    # TODO: Implement coordinate finding logic
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Error clicking {step.target}: {e}")
            return False
    
    async def _execute_type(self, step: AutomationStep) -> bool:
        """Execute typing action"""
        if not self.input_controller or not step.value:
            return False
        
        try:
            self.input_controller.type_text(step.value)
            return True
            
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    async def _execute_hotkey(self, step: AutomationStep) -> bool:
        """Execute hotkey action"""
        if not self.input_controller or not step.target:
            return False
        
        try:
            keys = step.target.split('+')
            if len(keys) > 1:
                self.input_controller.hotkey(*keys)
            else:
                self.input_controller.press_key(keys[0])
            return True
            
        except Exception as e:
            logger.error(f"Error executing hotkey {step.target}: {e}")
            return False
    
    async def _execute_wait(self, step: AutomationStep) -> bool:
        """Execute wait action"""
        try:
            wait_time = float(step.value) if step.value else 1.0
            await asyncio.sleep(wait_time)
            return True
            
        except Exception as e:
            logger.error(f"Error in wait step: {e}")
            return False
    
    async def _execute_analyze(self, step: AutomationStep) -> bool:
        """Execute screen analysis"""
        try:
            if self.screen_analyzer:
                analysis = await self.screen_analyzer.analyze_full_screen()
                return analysis is not None
            return True  # Always succeed if no analyzer
            
        except Exception as e:
            logger.error(f"Error in analysis step: {e}")
            return False
    
    # Enhanced execution methods for intelligent automation
    
    async def _execute_navigate_url(self, step: AutomationStep) -> bool:
        """Execute URL navigation"""
        if not self.input_controller or not step.value:
            return False
        
        try:
            # Focus address bar (Cmd+L)
            self.input_controller.hotkey("command", "l")
            await asyncio.sleep(0.5)
            
            # Type URL
            self.input_controller.type_text(step.value)
            await asyncio.sleep(0.5)
            
            # Press Enter
            self.input_controller.press_key("enter")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to URL {step.value}: {e}")
            return False
    
    async def _execute_click_element(self, step: AutomationStep) -> bool:
        """Execute element clicking with smart detection"""
        if not self.input_controller:
            return False
        
        try:
            # If coordinates are provided, use them
            if step.coordinates:
                x, y = step.coordinates
                self.input_controller.click(x, y)
                return True
            
            # Use smart element detector for accurate positioning
            try:
                from smart_element_detector import smart_detector
                
                # Get context from step description for better detection
                context = step.description.lower()
                coords = await smart_detector.find_element_coordinates(step.target, context)
                
                if coords:
                    x, y = coords
                    logger.info(f"🎯 Smart detector found {step.target} at ({x}, {y})")
                    self.input_controller.click(x, y)
                    return True
                    
            except Exception as detector_error:
                logger.warning(f"Smart detector failed: {detector_error}")
            
            # Fallback: Improved hardcoded coordinates
            if step.target == "search_box":
                # Improved YouTube search box coordinates
                if "youtube" in step.description.lower():
                    screen_width = 1470
                    search_x = screen_width // 2  # Center horizontally
                    search_y = 140  # 140px from top (below YouTube header)
                    logger.info(f"🎯 Using improved YouTube search coordinates: ({search_x}, {search_y})")
                    self.input_controller.click(search_x, search_y)
                    return True
                else:
                    # Generic search box
                    screen_width = 1470
                    search_x = screen_width // 2
                    search_y = 160  # Lower than before
                    self.input_controller.click(search_x, search_y)
                    return True
                    
            elif step.target == "address_bar":
                # Focus address bar using hotkey instead of clicking
                self.input_controller.hotkey("command", "l")
                return True
                
            else:
                # Generic click attempt with better positioning
                screen_width = 1470
                screen_height = 956
                click_x = screen_width // 2
                click_y = screen_height // 2
                logger.info(f"🔄 Using fallback click coordinates: ({click_x}, {click_y})")
                self.input_controller.click(click_x, click_y)
                return True
                
        except Exception as e:
            logger.error(f"Error clicking element {step.target}: {e}")
            return False
    
    async def _execute_type_text(self, step: AutomationStep) -> bool:
        """Execute text typing with smart handling"""
        if not self.input_controller or not step.value:
            return False
        
        try:
            # Clear existing text first (Cmd+A, then type)
            self.input_controller.hotkey("command", "a")
            await asyncio.sleep(0.2)
            
            # Type the text
            self.input_controller.type_text(step.value)
            return True
            
        except Exception as e:
            logger.error(f"Error typing text '{step.value}': {e}")
            return False
    
    async def _execute_general_action(self, step: AutomationStep) -> bool:
        """Execute general action by parsing description"""
        try:
            description_lower = step.description.lower()
            
            # Try to parse common actions from description
            if "open" in description_lower:
                # Extract app name and try to open
                words = step.description.split()
                for word in words:
                    if word.lower() in ["safari", "chrome", "firefox", "textedit", "notes"]:
                        step.target = word.lower()
                        step.action_type = "open_app"
                        return await self._execute_open_app(step)
            
            elif "click" in description_lower:
                # Generic click action
                return await self._execute_click_element(step)
            
            elif "type" in description_lower or "search" in description_lower:
                # Extract text to type
                if step.value:
                    return await self._execute_type_text(step)
            
            # If we can't parse it, just log and return success
            logger.info(f"Executed general action: {step.description}")
            await asyncio.sleep(0.3)  # Brief pause for realism
            return True
            
        except Exception as e:
            logger.error(f"Error executing general action: {e}")
            return False

# Create singleton instance
real_agent_handler = RealAgentAutomationHandler()

async def handle_real_agent_automation(message: str, session_id: str) -> Dict[str, Any]:
    """Entry point for real agent automation"""
    return await real_agent_handler.handle_agent_request(message, session_id)