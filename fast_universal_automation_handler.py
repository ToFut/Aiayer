#!/usr/bin/env python3
"""
Fast Universal Intelligent Automation Handler
Optimized for 10-20 second response times with aggressive timeouts and fallback mechanisms.
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
class FastAutomationStep:
    """Optimized automation step for fast execution"""
    id: str
    description: str
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"
    estimated_duration: float = 1.0  # Reduced default duration
    retry_count: int = 0
    max_retries: int = 2  # Reduced retries
    fallback_action: Optional[str] = None
    context_hints: List[str] = None

@dataclass 
class FastAutomationPlan:
    """Fast automation plan optimized for quick execution"""
    task_id: str
    title: str
    description: str
    request_type: str
    steps: List[FastAutomationStep]
    estimated_duration: float
    complexity_score: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    success_probability: float = 0.8
    fallback_strategies: List[str] = None
    user_guidance_needed: bool = False

class FastUniversalAutomationHandler:
    """Fast automation handler with aggressive timeouts for 10-20s response times"""
    
    def __init__(self):
        self.active_plans: Dict[str, FastAutomationPlan] = {}
        self.automation_available = False
        self.llm_service = None
        self.fallback_handler = None
        
        # Aggressive timeout settings for fast response
        self.llm_timeout = 8.0  # 8 seconds max for LLM response
        self.fallback_timeout = 2.0  # 2 seconds for fallback generation
        self.max_planning_time = 15.0  # Total max planning time
        
        # Initialize efficient automation components (replaces screen capture)
        try:
            from agent_workflow.input_controller import InputController
            from enhanced_realtime_system_bridge import EnhancedRealtimeSystemBridge
            
            self.input_controller = InputController(safety_level="medium")
            self.system_bridge = EnhancedRealtimeSystemBridge()
            self.automation_available = True
            self.efficient_mode = True
            logger.info("🚀 Fast automation with efficient system integration loaded")
            logger.info("⚡ No more screen capture overhead - using OS integration!")
        except ImportError as e:
            logger.warning(f"Efficient system bridge not available: {e}")
            # Fallback to old screen analyzer
            try:
                from sensors.total_screen_analyzer import TotalScreenAnalyzer
                self.screen_analyzer = TotalScreenAnalyzer(fast_mode=True)
                self.system_bridge = None
                self.efficient_mode = False
                logger.info("⚠️ Using fallback screen analyzer")
            except ImportError as e2:
                logger.warning(f"No automation components available: {e2}")
                self.input_controller = None
                self.screen_analyzer = None
                self.system_bridge = None
                self.efficient_mode = False
        
        # Initialize fast LLM service with warmup manager for instant responses
        self.llm_service = None
        self.warmup_manager = None
        self.use_warmup_manager = False
        
        try:
            # Try to use warmup manager for instant responses
            from llm_warmup_manager import get_warmup_manager
            self.use_warmup_manager = True
            logger.info("🔥 Fast automation will use warmup manager for instant responses")
            
            # ALSO initialize LLM service for planning (both can coexist)
            try:
                from llm.llm_service import LLMService
                self.llm_service = LLMService(model_name="llama3.2:1b")
                logger.info("🧠 Fast LLM service initialized alongside warmup manager")
            except Exception as e:
                logger.warning(f"Could not initialize LLM service with warmup manager: {e}")
                
        except ImportError:
            # Fallback to LLM service only
            try:
                from llm.llm_service import LLMService
                self.llm_service = LLMService(model_name="llama3.2:1b")
                logger.info("🧠 Fast LLM service initialized (fallback)")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
        
        # Initialize smart fallback handler
        try:
            from smart_fallback_automation_handler import smart_fallback_handler
            self.fallback_handler = smart_fallback_handler
            logger.info("🔄 Fallback handler initialized")
        except ImportError as e:
            logger.warning(f"Fallback handler not available: {e}")

    async def create_universal_automation_plan(self, user_request: str, session_id: str) -> Dict[str, Any]:
        """Create automation plan with aggressive timeout for fast response"""
        start_time = time.time()
        
        try:
            # Start both LLM and fallback generation concurrently
            tasks = []
            
            # Task 1: Try LLM generation with timeout
            if self.llm_service:
                llm_task = asyncio.create_task(
                    self._create_fast_llm_plan(user_request, session_id)
                )
                tasks.append(("llm", llm_task))
            
            # Task 2: Generate fallback plan concurrently
            if self.fallback_handler:
                fallback_task = asyncio.create_task(
                    self._create_fast_fallback_plan(user_request, session_id)
                )
                tasks.append(("fallback", fallback_task))
            
            # If no handlers available, create basic plan
            if not tasks:
                return await self._create_basic_plan(user_request, session_id)
            
            # Wait for first successful result or timeout
            plan = None
            completed_tasks = []
            
            # Use asyncio.wait with timeout
            done, pending = await asyncio.wait(
                [task[1] for task in tasks],
                timeout=self.max_planning_time,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get first successful result
            for task in done:
                try:
                    result = await task
                    if result:
                        plan = result
                        break
                except Exception as e:
                    logger.warning(f"Task failed: {e}")
                    continue
            
            # If no plan generated, use basic fallback
            if not plan:
                logger.warning("All planning methods failed, using basic plan")
                plan = await self._create_basic_plan(user_request, session_id)
            
            # Store and format response
            self.active_plans[plan.task_id] = plan
            response_data = self._format_fast_response(plan)
            
            processing_time = time.time() - start_time
            logger.info(f"⚡ Fast plan created in {processing_time:.2f}s")
            
            return {
                "success": True,
                "response": response_data["text"],
                "buttons": response_data["buttons"],
                "interactive": response_data["interactive"],
                "plan_id": plan.task_id,
                "requires_approval": True,
                "processing_time": processing_time,
                "automation_available": self.automation_available,
                "request_type": plan.request_type,
                "fast_mode": True
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in fast automation planning: {e}")
            return {
                "success": False,
                "response": f"⚡ Quick automation failed: {str(e)}\n\nTry a simpler request or check system status.",
                "processing_time": processing_time,
                "fast_mode": True
            }

    async def _create_fast_llm_plan(self, user_request: str, session_id: str) -> Optional[FastAutomationPlan]:
        """Create LLM plan with aggressive timeout using warmup manager"""
        try:
            logger.info("⚡ Starting INSTANT LLM planning with warmup manager...")
            
            # Initialize warmup manager if using it
            if self.use_warmup_manager and not self.warmup_manager:
                from llm_warmup_manager import get_warmup_manager
                self.warmup_manager = await get_warmup_manager()
            
            # Simplified, shorter prompt for faster response
            system_prompt = """You are a fast Mac automation agent. Create quick, executable automation plans.

CAPABILITIES: open_app, navigate_url, click_element, type_text, hotkey, wait, analyze_screen
SCREEN: 1470x956 pixels, center: (735, 478)

Respond with JSON only:
{
  "title": "Brief task title",
  "request_type": "flight_search|web_search|shopping|app_usage|general",
  "steps": [
    {
      "id": "step_1",
      "description": "Action description",
      "action_type": "open_app|navigate_url|type_text|click_element|hotkey",
      "target": "app_name|url|text|coordinates",
      "value": "text_to_type|url",
      "coordinates": [x, y],
      "estimated_duration": 1.0
    }
  ]
}

Keep it simple and fast!"""

            user_prompt = f"Create fast automation for: {user_request}"
            
            # Use warmup manager for instant response
            if self.use_warmup_manager and self.warmup_manager:
                logger.info("⚡ Using warmup manager for instant planning response...")
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                # Get instant response from warmed model
                response = await asyncio.wait_for(
                    self.warmup_manager.fast_generate_response(messages, max_tokens=500, temperature=0.7),
                    timeout=self.llm_timeout
                )
            else:
                # Fallback to LLM service
                logger.info("🐌 Using fallback LLM service...")
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = await asyncio.wait_for(
                    self.llm_service.generate_response(full_prompt),
                    timeout=self.llm_timeout
                )
            
            if not response:
                return None
            
            # Quick JSON parsing
            response_text = response.strip()
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                response_text = response_text[start:end]
            
            plan_data = json.loads(response_text)
            return self._build_fast_plan(plan_data, user_request, session_id, "llm")
            
        except asyncio.TimeoutError:
            logger.warning(f"LLM timeout after {self.llm_timeout}s")
            return None
        except Exception as e:
            logger.warning(f"LLM planning failed: {e}")
            return None

    async def _create_fast_fallback_plan(self, user_request: str, session_id: str) -> Optional[FastAutomationPlan]:
        """Create fallback plan quickly"""
        try:
            logger.info("🔄 Creating fast fallback plan...")
            
            # Use timeout for fallback handler
            result = await asyncio.wait_for(
                self.fallback_handler.create_universal_automation_plan(user_request, session_id),
                timeout=self.fallback_timeout
            )
            
            if result and result.get("success"):
                # Convert to fast plan format
                plan_data = {
                    "title": result.get("title", "Fallback Plan"),
                    "request_type": result.get("request_type", "general"),
                    "steps": result.get("steps", [])
                }
                return self._build_fast_plan(plan_data, user_request, session_id, "fallback")
            
            return None
            
        except asyncio.TimeoutError:
            logger.warning(f"Fallback timeout after {self.fallback_timeout}s")
            return None
        except Exception as e:
            logger.warning(f"Fallback planning failed: {e}")
            return None

    async def _create_basic_plan(self, user_request: str, session_id: str) -> FastAutomationPlan:
        """Create basic plan when all else fails"""
        logger.info("📝 Creating basic automation plan...")
        
        # Determine request type
        request_lower = user_request.lower()
        if "flight" in request_lower or "fly" in request_lower or "airport" in request_lower:
            request_type = "flight_search"
            steps = [
                FastAutomationStep(
                    id="step_1",
                    description="Open Safari browser",
                    action_type="open_app",
                    target="Safari",
                    estimated_duration=2.0
                ),
                FastAutomationStep(
                    id="step_2",
                    description="Navigate to Google Flights",
                    action_type="navigate_url",
                    value="https://www.google.com/travel/flights",
                    estimated_duration=3.0
                ),
                FastAutomationStep(
                    id="step_3",
                    description="Search for flights",
                    action_type="type_text",
                    value=user_request,
                    estimated_duration=2.0
                )
            ]
        elif "search" in request_lower or "find" in request_lower or "look" in request_lower:
            request_type = "web_search"
            steps = [
                FastAutomationStep(
                    id="step_1",
                    description="Open Safari browser",
                    action_type="open_app",
                    target="Safari",
                    estimated_duration=2.0
                ),
                FastAutomationStep(
                    id="step_2",
                    description="Navigate to Google",
                    action_type="navigate_url",
                    value="https://www.google.com",
                    estimated_duration=2.0
                ),
                FastAutomationStep(
                    id="step_3",
                    description="Perform search",
                    action_type="type_text",
                    value=user_request,
                    estimated_duration=1.0
                )
            ]
        else:
            request_type = "general"
            steps = [
                FastAutomationStep(
                    id="step_1",
                    description="Analyze current screen",
                    action_type="analyze_screen",
                    estimated_duration=1.0
                ),
                FastAutomationStep(
                    id="step_2",
                    description=f"Execute: {user_request}",
                    action_type="type_text",
                    value=user_request,
                    estimated_duration=2.0
                )
            ]
        
        task_id = f"basic_{int(time.time())}_{session_id}"
        
        return FastAutomationPlan(
            task_id=task_id,
            title=f"Basic {request_type.replace('_', ' ').title()}",
            description=user_request,
            request_type=request_type,
            steps=steps,
            estimated_duration=sum(step.estimated_duration for step in steps),
            complexity_score=0.3,
            success_probability=0.7,
            fallback_strategies=["Manual execution", "Try simpler approach"]
        )

    def _build_fast_plan(self, plan_data: Dict[str, Any], user_request: str, session_id: str, source: str) -> FastAutomationPlan:
        """Build fast automation plan from data"""
        task_id = f"fast_{source}_{int(time.time())}_{session_id}"
        
        # Convert steps
        fast_steps = []
        for i, step_data in enumerate(plan_data.get("steps", [])):
            step = FastAutomationStep(
                id=step_data.get("id", f"step_{i+1}"),
                description=step_data.get("description", ""),
                action_type=step_data.get("action_type", "analyze_screen"),
                target=step_data.get("target"),
                value=step_data.get("value"),
                coordinates=tuple(step_data["coordinates"]) if step_data.get("coordinates") else None,
                confidence=step_data.get("confidence", 0.8),
                estimated_duration=min(step_data.get("estimated_duration", 1.0), 3.0)  # Cap at 3s per step
            )
            fast_steps.append(step)
        
        return FastAutomationPlan(
            task_id=task_id,
            title=plan_data.get("title", "Fast Automation"),
            description=user_request,
            request_type=plan_data.get("request_type", "general"),
            steps=fast_steps,
            estimated_duration=sum(step.estimated_duration for step in fast_steps),
            complexity_score=plan_data.get("complexity_score", 0.4),
            success_probability=plan_data.get("success_probability", 0.8),
            fallback_strategies=["Quick retry", "Basic execution"]
        )

    def _format_fast_response(self, plan: FastAutomationPlan) -> Dict[str, Any]:
        """Format response for fast display"""
        
        type_emojis = {
            "flight_search": "✈️",
            "web_search": "🔍", 
            "shopping": "🛒",
            "app_usage": "📱",
            "general": "⚡"
        }
        
        emoji = type_emojis.get(plan.request_type, "⚡")
        
        response_text = f"⚡ **FAST AUTOMATION PLAN**\n\n"
        response_text += f"**{emoji} Type:** {plan.request_type.replace('_', ' ').title()}\n"
        response_text += f"**📋 Task:** {plan.title}\n"
        response_text += f"**⏱️ Duration:** {plan.estimated_duration:.1f}s\n"
        response_text += f"**📊 Steps:** {len(plan.steps)} actions\n\n"
        
        response_text += "**🚀 Quick Steps:**\n"
        for i, step in enumerate(plan.steps, 1):
            action_emoji = {
                "open_app": "📱",
                "navigate_url": "🌐",
                "click_element": "👆", 
                "type_text": "⌨️",
                "hotkey": "⌘",
                "wait": "⏳",
                "analyze_screen": "👁️"
            }.get(step.action_type, "⚡")
            
            response_text += f"{i}. {action_emoji} {step.description}\n"
        
        response_text += f"\n**🆔 Plan ID:** `{plan.task_id}`\n"
        response_text += "**⚡ Mode:** Fast Execution (10-20s target)\n"
        
        buttons = [
            {
                "id": f"do_{plan.task_id}",
                "text": "🟢 EXECUTE",
                "action": "execute_plan",
                "plan_id": plan.task_id,
                "style": "success"
            },
            {
                "id": f"dismiss_{plan.task_id}",
                "text": "🔴 CANCEL",
                "action": "cancel_plan", 
                "plan_id": plan.task_id,
                "style": "danger"
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
        """Handle button actions with fast execution"""
        try:
            if plan_id not in self.active_plans:
                return {
                    "success": False,
                    "response": "❌ Plan expired. Please create a new request.",
                    "interactive": False
                }
            
            plan = self.active_plans[plan_id]
            
            if action == "execute_plan":
                return await self._execute_fast_plan(plan, session_id)
            elif action == "cancel_plan":
                return await self._cancel_plan(plan, session_id)
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
                "response": f"❌ Error: {str(e)}",
                "interactive": False
            }

    async def _execute_fast_plan(self, plan: FastAutomationPlan, session_id: str) -> Dict[str, Any]:
        """Execute plan with fast timing"""
        try:
            start_time = time.time()
            plan.status = "executing"
            
            if not self.automation_available:
                return {
                    "success": False,
                    "response": "❌ Automation not available",
                    "interactive": False
                }
            
            logger.info(f"⚡ Fast executing: {plan.title}")
            
            executed_steps = 0
            
            for i, step in enumerate(plan.steps):
                try:
                    step.status = "executing"
                    success = await self._execute_fast_step(step)
                    
                    if success:
                        step.status = "completed"
                        executed_steps += 1
                    else:
                        step.status = "failed"
                    
                    # Minimal delay for fast execution
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    step.status = "failed"
                    logger.error(f"Step error: {e}")
            
            execution_time = time.time() - start_time
            success_rate = (executed_steps / len(plan.steps)) * 100
            
            response = f"⚡ **FAST EXECUTION COMPLETE**\n\n"
            response += f"**📋 Task:** {plan.title}\n"
            response += f"**⏱️ Time:** {execution_time:.1f}s\n"
            response += f"**📊 Success:** {success_rate:.0f}% ({executed_steps}/{len(plan.steps)})\n\n"
            
            if executed_steps == len(plan.steps):
                response += "🎉 **Perfect execution!**"
            else:
                response += f"⚠️ **Partial success** - {len(plan.steps) - executed_steps} steps failed"
            
            # Clean up
            if plan.task_id in self.active_plans:
                del self.active_plans[plan.task_id]
            
            return {
                "success": True,
                "response": response,
                "execution_time": execution_time,
                "success_rate": success_rate,
                "interactive": False
            }
            
        except Exception as e:
            logger.error(f"Fast execution error: {e}")
            return {
                "success": False,
                "response": f"❌ Execution failed: {str(e)}",
                "interactive": False
            }

    async def _execute_fast_step(self, step: FastAutomationStep) -> bool:
        """Execute step with efficient system integration or fallback to basic actions"""
        try:
            # Use efficient system bridge when available
            if self.efficient_mode and self.system_bridge:
                return await self._execute_step_efficient(step)
            else:
                return await self._execute_step_fallback(step)
                
        except Exception as e:
            logger.error(f"Fast step execution error: {e}")
            return False
    
    async def _execute_step_efficient(self, step: FastAutomationStep) -> bool:
        """Execute step using efficient system bridge (NEW FAST METHOD)"""
        try:
            if step.action_type == "open_app" and step.target:
                # Use system bridge to launch application
                result = await self.system_bridge.execute_system_action("launch_app", {"name": step.target})
                await asyncio.sleep(0.5)  # Brief wait for app to start
                return result.get('success', False)
                
            elif step.action_type == "navigate_url" and step.value:
                # Use system bridge to navigate URL in browser
                result = await self.system_bridge.execute_system_action("navigate_url", {"url": step.value})
                await asyncio.sleep(0.5)
                return result.get('success', False)
                
            elif step.action_type == "type_text" and step.value:
                # Get current focused element and type directly
                system_state = await self.system_bridge.get_current_system_state()
                if system_state and system_state.visible_ui_elements:
                    # Find text input element
                    text_elements = [elem for elem in system_state.visible_ui_elements 
                                   if elem.get('type') in ['textfield', 'textarea', 'input']]
                    if text_elements:
                        target_element = text_elements[0]  # Use first available text field
                        result = await self.system_bridge.execute_system_action("type_text", {
                            "element_id": target_element.get('id'),
                            "text": step.value
                        })
                        return result.get('success', False)
                # Fallback to hotkey method
                self.input_controller.hotkey("command", "a")
                await asyncio.sleep(0.1)
                self.input_controller.type_text(step.value)
                await asyncio.sleep(0.3)
                return True
                
            elif step.action_type == "click_element":
                # Use system bridge to find and click exact element
                system_state = await self.system_bridge.get_current_system_state()
                if system_state and system_state.visible_ui_elements:
                    # Try to find element by target text or type
                    target_elements = []
                    if step.target:
                        # Find by text content
                        target_elements = [elem for elem in system_state.visible_ui_elements 
                                         if step.target.lower() in elem.get('text', '').lower()]
                    
                    if not target_elements and step.coordinates:
                        # Find element at coordinates
                        x, y = step.coordinates
                        target_elements = [elem for elem in system_state.visible_ui_elements 
                                         if self._point_in_bounds(x, y, elem.get('bounds', {}))]
                    
                    if target_elements:
                        target_element = target_elements[0]
                        result = await self.system_bridge.execute_system_action("click_element", {
                            "element_id": target_element.get('id'),
                            "element_type": target_element.get('type')
                        })
                        if result.get('success', False):
                            logger.info(f"✅ Clicked element: {target_element.get('text', 'unnamed')}")
                            return True
                
                # Fallback to coordinate clicking
                if step.coordinates:
                    x, y = step.coordinates
                    self.input_controller.click(x, y)
                else:
                    # Get center of screen from system state
                    system_state = await self.system_bridge.get_current_system_state()
                    if system_state and system_state.visible_ui_elements:
                        # Click first clickable element
                        clickable = [elem for elem in system_state.visible_ui_elements 
                                   if elem.get('clickable', False)]
                        if clickable:
                            bounds = clickable[0].get('bounds', {})
                            center_x = bounds.get('x', 735) + bounds.get('width', 0) // 2
                            center_y = bounds.get('y', 478) + bounds.get('height', 0) // 2
                            self.input_controller.click(center_x, center_y)
                        else:
                            self.input_controller.click(735, 478)  # Default center
                    else:
                        self.input_controller.click(735, 478)  # Default center
                await asyncio.sleep(0.2)  # Reduced delay
                return True
                
            elif step.action_type == "analyze_screen":
                # Get rich system state instead of screen analysis
                system_state = await self.system_bridge.get_current_system_state()
                if system_state:
                    logger.info(f"🎯 System analysis: {system_state.active_application} - {len(system_state.visible_ui_elements)} UI elements")
                    return True
                return False
                
            return False
            
        except Exception as e:
            logger.error(f"Efficient step execution error: {e}")
            return False
    
    def _point_in_bounds(self, x: int, y: int, bounds: Dict[str, Any]) -> bool:
        """Check if point is within element bounds"""
        if not bounds:
            return False
        elem_x = bounds.get('x', 0)
        elem_y = bounds.get('y', 0)
        elem_width = bounds.get('width', 0)
        elem_height = bounds.get('height', 0)
        return (elem_x <= x <= elem_x + elem_width and 
                elem_y <= y <= elem_y + elem_height)
    
    async def _execute_step_fallback(self, step: FastAutomationStep) -> bool:
        """Execute step using fallback methods (OLD METHOD)"""
        try:
            if step.action_type == "open_app" and step.target:
                self.input_controller.hotkey("command", "space")
                await asyncio.sleep(0.8)
                self.input_controller.type_text(step.target)
                await asyncio.sleep(0.5)
                self.input_controller.press_key("enter")
                await asyncio.sleep(1.5)
                return True
                
            elif step.action_type == "navigate_url" and step.value:
                self.input_controller.hotkey("command", "l")
                await asyncio.sleep(0.3)
                self.input_controller.type_text(step.value)
                await asyncio.sleep(0.3)
                self.input_controller.press_key("enter")
                await asyncio.sleep(2.0)
                return True
                
            elif step.action_type == "type_text" and step.value:
                self.input_controller.hotkey("command", "a")
                await asyncio.sleep(0.1)
                self.input_controller.type_text(step.value)
                await asyncio.sleep(0.3)
                return True
                
            elif step.action_type == "click_element":
                if step.coordinates:
                    x, y = step.coordinates
                    self.input_controller.click(x, y)
                else:
                    self.input_controller.click(735, 478)  # Center click
                await asyncio.sleep(0.5)
                return True
                
            elif step.action_type == "analyze_screen":
                return True  # Always succeed for speed
                
            return False
            
        except Exception as e:
            logger.error(f"Fast step execution error: {e}")
            return False

    async def _cancel_plan(self, plan: FastAutomationPlan, session_id: str) -> Dict[str, Any]:
        """Cancel plan quickly"""
        plan.status = "cancelled"
        
        if plan.task_id in self.active_plans:
            del self.active_plans[plan.task_id]
        
        return {
            "success": True,
            "response": f"🚫 **Cancelled:** {plan.title}",
            "interactive": False
        }

# Create fast singleton instance
fast_universal_automation_handler = FastUniversalAutomationHandler()

async def handle_fast_universal_automation(user_request: str, session_id: str) -> Dict[str, Any]:
    """Fast entry point for automation handling"""
    return await fast_universal_automation_handler.create_universal_automation_plan(user_request, session_id)

async def handle_fast_button_action(action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
    """Fast entry point for button actions"""
    return await fast_universal_automation_handler.handle_button_action(action, plan_id, session_id)