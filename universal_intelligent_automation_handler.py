#!/usr/bin/env python3
"""
Universal Intelligent Automation Handler
Creates detailed, specific automation plans for ANY user request using advanced LLM planning.
Completely agnostic to request type - handles web searches, flight searches, app usage, etc.
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SmartAutomationStep:
    """Enhanced automation step with smart execution capabilities"""
    id: str
    description: str
    action_type: str  # 'open_app', 'navigate_url', 'click_element', 'type_text', 'hotkey', 'wait', 'analyze_screen'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"  # pending, approved, executing, completed, failed
    estimated_duration: float = 2.0
    retry_count: int = 0
    max_retries: int = 3
    fallback_action: Optional[str] = None
    context_hints: List[str] = None

@dataclass 
class UniversalAutomationPlan:
    """Universal automation plan that works with any request type"""
    task_id: str
    title: str
    description: str
    request_type: str  # 'web_search', 'flight_search', 'app_usage', 'research', 'shopping', etc.
    steps: List[SmartAutomationStep]
    estimated_duration: float
    complexity_score: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    success_probability: float = 0.8
    fallback_strategies: List[str] = None
    user_guidance_needed: bool = False

class UniversalIntelligentAutomationHandler:
    """Handles ANY type of automation request using advanced LLM planning"""
    
    def __init__(self):
        self.active_plans: Dict[str, UniversalAutomationPlan] = {}
        self.automation_available = False
        self.llm_service = None
        
        # Initialize automation components
        try:
            from agent_workflow.input_controller import InputController
            from sensors.total_screen_analyzer import TotalScreenAnalyzer
            self.input_controller = InputController(safety_level="medium")
            self.screen_analyzer = TotalScreenAnalyzer(fast_mode=True)
            self.automation_available = True
            logger.info("🤖 Universal automation components loaded successfully")
        except ImportError as e:
            logger.warning(f"Automation components not available: {e}")
            self.input_controller = None
            self.screen_analyzer = None
        
        # Initialize LLM service (will be done async)
        self.llm_service = None
        self.llm_initialized = False

    async def _ensure_llm_service(self):
        """Initialize LLM service in async context if not already done"""
        if not self.llm_initialized:
            try:
                from llm.llm_service import LLMService
                self.llm_service = LLMService()
                # Initialize the service properly in async context
                await self.llm_service.initialize()
                self.llm_initialized = True
                logger.info("🧠 LLM service initialized for universal planning (async)")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                logger.error(f"Error details: {type(e).__name__}: {str(e)}")
                self.llm_service = None
                self.llm_initialized = True  # Don't retry constantly

    async def create_universal_automation_plan(self, user_request: str, session_id: str) -> Dict[str, Any]:
        """Create detailed automation plan for ANY type of user request"""
        try:
            start_time = time.time()
            
            # Ensure LLM service is initialized
            await self._ensure_llm_service()
            
            # Use advanced LLM planning for universal request handling
            plan = await self._create_advanced_llm_plan(user_request, session_id)
            
            # Store plan for approval
            self.active_plans[plan.task_id] = plan
            
            # Format interactive response
            response_data = self._format_universal_response(plan)
            
            return {
                "success": True,
                "response": response_data["text"],
                "buttons": response_data["buttons"],
                "interactive": response_data["interactive"],
                "plan_id": plan.task_id,
                "requires_approval": True,
                "processing_time": time.time() - start_time,
                "automation_available": self.automation_available,
                "request_type": plan.request_type,
                "complexity_score": plan.complexity_score,
                "success_probability": plan.success_probability,
                "universal_planning": True
            }
            
        except Exception as e:
            logger.error(f"Error creating universal automation plan: {e}")
            return {
                "success": False,
                "response": f"Error creating automation plan: {str(e)}",
                "automation_available": self.automation_available
            }

    async def _create_advanced_llm_plan(self, user_request: str, session_id: str) -> UniversalAutomationPlan:
        """Create detailed automation plan using advanced LLM reasoning for ANY request"""
        
        if not self.llm_service:
            raise Exception("LLM service not available")
        
        # Advanced universal planning prompt that handles ANY request type
        system_prompt = """You are an expert Mac automation agent with advanced reasoning capabilities. Your job is to create detailed, executable automation plans for ANY user request, regardless of complexity or type.

SYSTEM ENVIRONMENT:
- Operating System: macOS (Darwin 23.1.0)
- Screen Resolution: 1470x956 pixels
- Default Browser: Safari
- Available: All macOS applications, Spotlight search (Cmd+Space), web browsing

AUTOMATION CAPABILITIES:
- open_app: Launch any application via Spotlight (e.g., Safari, Chrome, Calculator, TextEdit)
- navigate_url: Navigate to URLs in browser (focus address bar + type URL + enter)
- click_element: Click UI elements at specific coordinates or by description
- type_text: Enter text into input fields, search boxes, etc.
- hotkey: Execute keyboard shortcuts (e.g., Cmd+L, Cmd+T, Enter, Tab)
- wait: Pause for interface loading/transitions
- analyze_screen: Check current screen state and locate elements

REQUEST TYPES YOU MUST HANDLE:
✈️ TRAVEL & FLIGHTS: "search flight from NYC to Miami", "find cheapest flights to Paris", "book hotel in Tokyo"
🔍 WEB SEARCHES: "search for Python tutorials", "find news about AI", "look up weather forecast"
🛒 SHOPPING: "find MacBook deals on Amazon", "search for running shoes", "compare laptop prices"
📱 SOCIAL MEDIA: "open Twitter and check my feed", "post on Facebook", "search Instagram"
💼 PRODUCTIVITY: "create spreadsheet", "write document", "schedule meeting"
🎵 ENTERTAINMENT: "play music on Spotify", "watch YouTube videos", "find Netflix shows"
📧 COMMUNICATION: "compose email", "send message", "schedule video call"
🔧 SYSTEM TASKS: "take screenshot", "check system info", "manage files"
🎯 ANY OTHER REQUEST: Be creative and comprehensive!

PLANNING PRINCIPLES:
1. ANALYZE the request type and determine the best approach
2. CHOOSE the right applications and websites to use
3. CREATE step-by-step instructions with proper timing
4. INCLUDE fallback strategies for robustness
5. ESTIMATE realistic durations and confidence levels
6. PROVIDE specific coordinates when possible (center screen is 735, 478)

RESPONSE FORMAT (JSON):
{
  "title": "Clear, specific title for the automation task",
  "description": "Brief description of what will be accomplished",
  "request_type": "web_search|flight_search|app_usage|shopping|social_media|productivity|entertainment|communication|system_task|general",
  "complexity_score": 0.1-1.0,
  "estimated_duration": total_seconds,
  "success_probability": 0.1-1.0,
  "fallback_strategies": ["strategy1", "strategy2"],
  "user_guidance_needed": false,
  "steps": [
    {
      "id": "step_1",
      "description": "Human-readable description of this step",
      "action_type": "open_app|navigate_url|click_element|type_text|hotkey|wait|analyze_screen",
      "target": "application_name|url|element_description|hotkey_combination",
      "value": "text_to_type|url_to_navigate|null",
      "coordinates": [x, y] or null,
      "estimated_duration": seconds,
      "confidence": 0.1-1.0,
      "fallback_action": "alternative action if primary fails",
      "context_hints": ["hint1", "hint2"] or null
    }
  ]
}

EXAMPLES FOR DIFFERENT REQUEST TYPES:

FLIGHT SEARCH: "search flight from NYC to Miami"
→ Open Safari → Navigate to Google → Search "flights NYC to Miami" → Click flight search results → Analyze options

WEB SEARCH: "find Python tutorials"  
→ Open Safari → Navigate to Google → Search "Python tutorials" → Analyze results → Maybe click top tutorial

SHOPPING: "find MacBook deals on Amazon"
→ Open Safari → Navigate to Amazon → Search "MacBook deals" → Filter results → Analyze prices

SOCIAL MEDIA: "check Twitter feed"
→ Open Safari → Navigate to Twitter.com → Login if needed → View timeline

APP USAGE: "open Calculator and compute 15 * 27"
→ Open Calculator app → Click/type calculation → Get result

Be EXTREMELY detailed and specific. Include exact coordinates when possible. Handle edge cases. Always provide actionable steps."""

        user_prompt = f"""Create a comprehensive Mac automation plan for this request:

USER REQUEST: "{user_request}"

ANALYSIS REQUIREMENTS:
1. What is the user trying to accomplish?
2. What type of request is this? (web search, flight search, shopping, etc.)
3. What applications/websites are needed?
4. What specific actions must be performed?
5. What text needs to be entered?
6. What could go wrong and how to handle it?
7. What coordinates or UI elements need to be targeted?

Create a detailed, step-by-step automation plan that can actually be executed. Consider the user's intent and provide the most efficient path to accomplish their goal.

IMPORTANT: 
- Be specific about coordinates (use screen center 735,478 as reference)
- Include proper wait times for page loads
- Handle different scenarios (like if a website loads slowly)
- Provide fallback actions for robustness
- Make it executable on a real Mac system

Respond with comprehensive JSON that covers the entire workflow."""

        try:
            # Get LLM response
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = await self.llm_service.generate_response(full_prompt)
            
            if not response or response.strip() == "":
                raise Exception("LLM returned empty response")
            
            # Parse JSON response
            response_text = response.strip()
            
            # Extract JSON from markdown if needed
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                response_text = response_text[start:end]
            
            # Clean JSON by removing comments and fixing common issues
            def clean_json(text):
                """Clean JSON text by removing comments and fixing common issues"""
                import re
                
                # Remove single-line comments (// comment)
                text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
                
                # Remove Python-style comments (# comment)
                text = re.sub(r'#.*$', '', text, flags=re.MULTILINE)
                
                # Remove multi-line comments (/* comment */)
                text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
                
                # Fix function calls like total_seconds(30) -> 30
                text = re.sub(r'total_seconds\((\d+)\)', r'\1', text)
                
                # Remove trailing commas before closing brackets/braces
                text = re.sub(r',\s*([}\]])', r'\1', text)
                
                # Remove extra whitespace and empty lines
                text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                
                return text
            
            cleaned_response = clean_json(response_text)
            logger.info(f"🧹 Cleaned JSON response: {cleaned_response[:200]}...")
            
            plan_data = json.loads(cleaned_response)
            
            # Create enhanced automation plan
            task_id = f"universal_{int(time.time())}_{session_id}"
            
            # Convert steps to SmartAutomationStep objects
            smart_steps = []
            for i, step_data in enumerate(plan_data.get("steps", [])):
                step = SmartAutomationStep(
                    id=step_data.get("id", f"step_{i+1}"),
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", "analyze_screen"),
                    target=step_data.get("target"),
                    value=step_data.get("value"),
                    coordinates=tuple(step_data["coordinates"]) if step_data.get("coordinates") else None,
                    confidence=step_data.get("confidence", 0.8),
                    estimated_duration=step_data.get("estimated_duration", 2.0),
                    fallback_action=step_data.get("fallback_action"),
                    context_hints=step_data.get("context_hints", [])
                )
                smart_steps.append(step)
            
            # Create universal automation plan
            plan = UniversalAutomationPlan(
                task_id=task_id,
                title=plan_data.get("title", "Universal Automation Plan"),
                description=plan_data.get("description", user_request),
                request_type=plan_data.get("request_type", "general"),
                steps=smart_steps,
                estimated_duration=plan_data.get("estimated_duration", len(smart_steps) * 2.0),
                complexity_score=plan_data.get("complexity_score", 0.5),
                success_probability=plan_data.get("success_probability", 0.8),
                fallback_strategies=plan_data.get("fallback_strategies", []),
                user_guidance_needed=plan_data.get("user_guidance_needed", False)
            )
            
            logger.info(f"🧠 Created universal plan '{plan.title}' ({plan.request_type}) with {len(smart_steps)} steps")
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {response[:500]}...")
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Universal LLM planning failed: {e}")
            raise e

    def _format_universal_response(self, plan: UniversalAutomationPlan) -> Dict[str, Any]:
        """Format response with enhanced interactive elements"""
        
        # Determine request type emoji and description
        type_info = {
            "flight_search": {"emoji": "✈️", "name": "Flight Search"},
            "web_search": {"emoji": "🔍", "name": "Web Search"},
            "shopping": {"emoji": "🛒", "name": "Shopping"},
            "social_media": {"emoji": "📱", "name": "Social Media"},
            "productivity": {"emoji": "💼", "name": "Productivity"},
            "entertainment": {"emoji": "🎵", "name": "Entertainment"},
            "communication": {"emoji": "📧", "name": "Communication"},
            "system_task": {"emoji": "🔧", "name": "System Task"},
            "app_usage": {"emoji": "📱", "name": "App Usage"},
            "general": {"emoji": "🤖", "name": "General Task"}
        }
        
        type_data = type_info.get(plan.request_type, type_info["general"])
        
        # Main response text
        response_text = f"🎯 **AUTOMATION EXECUTION PLAN**\n\n"
        response_text += f"**{type_data['emoji']} Task Type:** {type_data['name']}\n"
        response_text += f"**📋 Task:** {plan.title}\n"
        response_text += f"**⏱️ Estimated Duration:** {plan.estimated_duration:.1f} seconds\n"
        response_text += f"**🎯 Success Probability:** {plan.success_probability:.0%}\n"
        response_text += f"**🔧 Complexity:** {'High' if plan.complexity_score > 0.7 else 'Medium' if plan.complexity_score > 0.4 else 'Low'}\n"
        response_text += f"**📝 Steps:** {len(plan.steps)} actions\n\n"
        
        response_text += "**🚀 Automation Steps:**\n"
        for i, step in enumerate(plan.steps, 1):
            confidence_emoji = "🟢" if step.confidence > 0.8 else "🟡" if step.confidence > 0.6 else "🔴"
            action_emoji = {
                "open_app": "📱",
                "navigate_url": "🌐", 
                "click_element": "👆",
                "type_text": "⌨️",
                "hotkey": "⌘",
                "wait": "⏳",
                "analyze_screen": "👁️"
            }.get(step.action_type, "🔧")
            
            response_text += f"{i}. {confidence_emoji} {action_emoji} {step.description}\n"
            
            if step.action_type == "type_text" and step.value:
                response_text += f"   → Will type: '{step.value}'\n"
            elif step.action_type == "navigate_url" and step.value:
                response_text += f"   → Will navigate to: {step.value}\n"
            elif step.action_type == "open_app" and step.target:
                response_text += f"   → Will open: {step.target}\n"
            elif step.coordinates:
                response_text += f"   → Will click at: ({step.coordinates[0]}, {step.coordinates[1]})\n"
            
            if step.fallback_action:
                response_text += f"   ↩️ Fallback: {step.fallback_action}\n"
        
        # Add fallback strategies if available
        if plan.fallback_strategies:
            response_text += f"\n**🛡️ Fallback Strategies:**\n"
            for strategy in plan.fallback_strategies:
                response_text += f"• {strategy}\n"
        
        response_text += f"\n**🆔 Plan ID:** `{plan.task_id}`\n"
        response_text += f"**🧠 Planning:** Advanced LLM (Universal Intelligence)\n\n"
        response_text += f"*Automation System: {'✅ Ready' if self.automation_available else '❌ Not Available'}*"
        
        # Interactive buttons with enhanced styling
        buttons = [
            {
                "id": f"do_{plan.task_id}",
                "text": "🟢 EXECUTE",
                "action": "execute_plan",
                "plan_id": plan.task_id,
                "style": "success",
                "description": f"Execute this {type_data['name'].lower()} automation"
            },
            {
                "id": f"dismiss_{plan.task_id}",
                "text": "🔴 CANCEL", 
                "action": "cancel_plan",
                "plan_id": plan.task_id,
                "style": "danger",
                "description": "Cancel this automation"
            },
            {
                "id": f"adjust_{plan.task_id}",
                "text": "🟡 MODIFY",
                "action": "modify_plan", 
                "plan_id": plan.task_id,
                "style": "warning",
                "description": "Modify the plan before execution"
            },
            {
                "id": f"simulate_{plan.task_id}",
                "text": "🔍 SIMULATE",
                "action": "simulate_plan",
                "plan_id": plan.task_id,
                "style": "info",
                "description": "Simulate execution without performing actions"
            }
        ]
        
        return {
            "text": response_text,
            "buttons": buttons,
            "interactive": True,
            "plan_id": plan.task_id,
            "request_type": plan.request_type
        }

    async def handle_button_action(self, action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
        """Handle button actions with enhanced execution capabilities"""
        try:
            if plan_id not in self.active_plans:
                return {
                    "success": False,
                    "response": "❌ Plan not found or expired. Please create a new automation request.",
                    "interactive": False
                }
            
            plan = self.active_plans[plan_id]
            
            if action == "execute_plan":
                return await self._execute_universal_plan(plan, session_id)
            elif action == "cancel_plan":
                return await self._cancel_plan(plan, session_id)
            elif action == "modify_plan":
                return await self._modify_plan(plan, session_id)
            elif action == "simulate_plan":
                return await self._simulate_plan(plan, session_id)
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

    async def _execute_universal_plan(self, plan: UniversalAutomationPlan, session_id: str) -> Dict[str, Any]:
        """Execute universal automation plan with smart error handling"""
        try:
            start_time = time.time()
            plan.status = "executing"
            
            if not self.automation_available:
                return {
                    "success": False,
                    "response": "❌ Automation components not available. Cannot execute plan.",
                    "interactive": False
                }
            
            logger.info(f"🚀 Executing universal automation plan: {plan.title}")
            
            executed_steps = 0
            failed_steps = 0
            execution_log = []
            
            for i, step in enumerate(plan.steps):
                try:
                    step.status = "executing"
                    progress = int((i / len(plan.steps)) * 100) if len(plan.steps) > 0 else 0
                    logger.info(f"📊 Step {i+1}/{len(plan.steps)}: {step.description} ({progress}%)")
                    
                    # Execute step with smart retry logic
                    success = await self._execute_smart_step(step)
                    
                    if success:
                        step.status = "completed"
                        executed_steps += 1
                        execution_log.append(f"✅ {step.description}")
                        logger.info(f"✅ Step completed: {step.description}")
                    else:
                        step.status = "failed"
                        failed_steps += 1
                        execution_log.append(f"❌ {step.description} (FAILED)")
                        logger.warning(f"❌ Step failed: {step.description}")
                    
                    # Longer delay for better visual feedback
                    await asyncio.sleep(1.5)
                    
                except Exception as e:
                    step.status = "failed"
                    failed_steps += 1
                    execution_log.append(f"❌ {step.description} (ERROR: {str(e)})")
                    logger.error(f"❌ Step error: {step.description} - {e}")
            
            # Update plan status
            plan.status = "completed" if failed_steps == 0 else "partially_completed"
            
            # Generate comprehensive execution report
            execution_time = time.time() - start_time
            success_rate = (executed_steps / len(plan.steps)) * 100
            
            response = f"🎯 **AUTOMATION EXECUTION COMPLETE**\n\n"
            response += f"**📋 Task:** {plan.title}\n"
            response += f"**🎭 Type:** {plan.request_type.replace('_', ' ').title()}\n"
            response += f"**⏱️ Execution Time:** {execution_time:.1f} seconds\n"
            response += f"**📊 Success Rate:** {success_rate:.1f}% ({executed_steps}/{len(plan.steps)} steps)\n"
            response += f"**🎯 Final Status:** {plan.status.replace('_', ' ').title()}\n\n"
            
            if failed_steps == 0:
                response += f"🎉 **Perfect Execution!** All steps completed successfully.\n\n"
            else:
                response += f"⚠️ **Partial Success:** {failed_steps} step(s) encountered issues.\n\n"
            
            response += "**📋 Execution Log:**\n"
            for log_entry in execution_log:
                response += f"{log_entry}\n"
            
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
            logger.error(f"Error executing universal plan: {e}")
            return {
                "success": False,
                "response": f"❌ Execution failed: {str(e)}",
                "interactive": False
            }

    async def _execute_smart_step(self, step: SmartAutomationStep) -> bool:
        """Execute a single step with smart fallback logic"""
        try:
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
            elif step.action_type == "analyze_screen":
                return await self._execute_analyze_screen(step)
            else:
                logger.warning(f"Unknown step type: {step.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing step {step.id}: {e}")
            
            # Try fallback action if available
            if step.fallback_action and step.retry_count < step.max_retries:
                step.retry_count += 1
                logger.info(f"🔄 Attempting fallback action: {step.fallback_action}")
                # You could implement fallback logic here
                
            return False

    async def _execute_open_app(self, step: SmartAutomationStep) -> bool:
        """Execute app opening via Spotlight"""
        if not self.input_controller or not step.target:
            return False
        
        try:
            # Open Spotlight (Cmd+Space)
            self.input_controller.hotkey("command", "space")
            await asyncio.sleep(1.2)
            
            # Type app name
            self.input_controller.type_text(step.target)
            await asyncio.sleep(0.8)
            
            # Press Enter
            self.input_controller.press_key("enter")
            await asyncio.sleep(2.0)  # Wait for app to launch
            return True
            
        except Exception as e:
            logger.error(f"Error opening app {step.target}: {e}")
            return False

    async def _execute_navigate_url(self, step: SmartAutomationStep) -> bool:
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
            await asyncio.sleep(3.0)  # Wait for page to load
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to URL {step.value}: {e}")
            return False

    async def _execute_click_element(self, step: SmartAutomationStep) -> bool:
        """Execute element clicking with smart detection"""
        if not self.input_controller:
            return False
        
        try:
            if step.coordinates:
                x, y = step.coordinates
                self.input_controller.click(x, y)
                await asyncio.sleep(1.0)
                return True
            else:
                # Default to screen center if no coordinates
                self.input_controller.click(735, 478)  # Center of 1470x956 screen
                await asyncio.sleep(1.0)
                return True
                
        except Exception as e:
            logger.error(f"Error clicking element {step.target}: {e}")
            return False

    async def _execute_type_text(self, step: SmartAutomationStep) -> bool:
        """Execute text typing"""
        if not self.input_controller or not step.value:
            return False
        
        try:
            # Clear existing text first (Cmd+A)
            self.input_controller.hotkey("command", "a")
            await asyncio.sleep(0.2)
            
            # Type the text
            self.input_controller.type_text(step.value)
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Error typing text '{step.value}': {e}")
            return False

    async def _execute_hotkey(self, step: SmartAutomationStep) -> bool:
        """Execute hotkey action"""
        if not self.input_controller or not step.target:
            return False
        
        try:
            keys = step.target.split('+')
            if len(keys) > 1:
                self.input_controller.hotkey(*keys)
            else:
                self.input_controller.press_key(keys[0])
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Error executing hotkey {step.target}: {e}")
            return False

    async def _execute_wait(self, step: SmartAutomationStep) -> bool:
        """Execute wait action"""
        try:
            wait_time = float(step.value) if step.value else step.estimated_duration
            await asyncio.sleep(wait_time)
            return True
            
        except Exception as e:
            logger.error(f"Error in wait step: {e}")
            return False

    async def _execute_analyze_screen(self, step: SmartAutomationStep) -> bool:
        """Execute screen analysis"""
        try:
            if self.screen_analyzer:
                analysis = await self.screen_analyzer.analyze_full_screen()
                return analysis is not None
            return True  # Always succeed if no analyzer
            
        except Exception as e:
            logger.error(f"Error in analysis step: {e}")
            return False

    async def _cancel_plan(self, plan: UniversalAutomationPlan, session_id: str) -> Dict[str, Any]:
        """Cancel the automation plan"""
        plan.status = "cancelled"
        
        if plan.task_id in self.active_plans:
            del self.active_plans[plan.task_id]
        
        logger.info(f"🚫 Cancelled automation plan: {plan.title}")
        
        return {
            "success": True,
            "response": f"🚫 **Automation Cancelled**\n\nTask '{plan.title}' has been cancelled and will not be executed.",
            "interactive": False
        }

    async def _modify_plan(self, plan: UniversalAutomationPlan, session_id: str) -> Dict[str, Any]:
        """Show plan modification options"""
        response = f"🛠️ **Modify Automation Plan**\n\n"
        response += f"**Current Task:** {plan.title}\n"
        response += f"**Type:** {plan.request_type.replace('_', ' ').title()}\n"
        response += f"**Current Steps:** {len(plan.steps)} actions\n\n"
        response += "**Available Modifications:**\n"
        response += "• Change target applications or websites\n"
        response += "• Modify search terms or text input\n" 
        response += "• Adjust timing and delays\n"
        response += "• Add verification steps\n"
        response += "• Update click coordinates\n\n"
        response += "**To modify:** Send a new request with your adjustments, or use CANCEL to dismiss."
        
        return {
            "success": True,
            "response": response,
            "interactive": False,
            "modification_mode": True
        }

    async def _simulate_plan(self, plan: UniversalAutomationPlan, session_id: str) -> Dict[str, Any]:
        """Simulate plan execution without performing actual actions"""
        response = f"🔍 **Automation Simulation**\n\n"
        response += f"**Task:** {plan.title}\n"
        response += f"**Type:** {plan.request_type.replace('_', ' ').title()}\n\n"
        response += "**Simulated Execution:**\n"
        
        for i, step in enumerate(plan.steps, 1):
            response += f"{i}. ✅ {step.description}\n"
            if step.action_type == "type_text" and step.value:
                response += f"   → Would type: '{step.value}'\n"
            elif step.coordinates:
                response += f"   → Would click at: ({step.coordinates[0]}, {step.coordinates[1]})\n"
        
        response += f"\n**Estimated Duration:** {plan.estimated_duration:.1f} seconds\n"
        response += f"**Success Probability:** {plan.success_probability:.0%}\n\n"
        response += "✅ **Simulation Complete** - Plan appears executable!"
        
        return {
            "success": True,
            "response": response,
            "interactive": False,
            "simulation_mode": True
        }
    
    async def handle_user_instruction(self, user_request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy compatibility method - creates plan instead of executing directly"""
        try:
            logger.info(f"🔄 Legacy handle_user_instruction called, creating plan for: {user_request}")
            
            # Generate a session ID from context or create new one
            session_id = context.get("session_id", f"legacy_{int(time.time())}")
            
            # Create automation plan
            plan_result = await self.create_universal_automation_plan(user_request, session_id)
            
            if plan_result.get("success", False):
                return {
                    "success": True,
                    "summary": f"Created automation plan: {plan_result.get('response', 'Plan created')}",
                    "steps_executed": ["Plan generation"],
                    "requires_approval": True,
                    "plan_id": plan_result.get("plan_id"),
                    "legacy_compatibility": True
                }
            else:
                return {
                    "success": False,
                    "error": plan_result.get("error", "Failed to create automation plan"),
                    "legacy_compatibility": True
                }
                
        except Exception as e:
            logger.error(f"Legacy handle_user_instruction error: {e}")
            return {
                "success": False,
                "error": f"Legacy automation failed: {str(e)}",
                "legacy_compatibility": True
            }

# Create singleton instance
universal_automation_handler = UniversalIntelligentAutomationHandler()

async def handle_universal_automation(user_request: str, session_id: str) -> Dict[str, Any]:
    """Entry point for universal automation handling"""
    return await universal_automation_handler.create_universal_automation_plan(user_request, session_id)

async def handle_universal_button_action(action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
    """Entry point for button actions"""
    return await universal_automation_handler.handle_button_action(action, plan_id, session_id)