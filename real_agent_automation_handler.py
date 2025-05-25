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
        """Handle agent request with interactive automation planning"""
        try:
            start_time = time.time()
            
            # Create automation plan
            plan = await self._create_automation_plan(message, session_id)
            
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
                "interactive_mode": True
            }
            
        except Exception as e:
            logger.error(f"Error handling agent request: {e}")
            return {
                "success": False,
                "response": f"Error creating automation plan: {str(e)}",
                "automation_available": self.automation_available
            }
    
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
            confidence=0.9
        ))
        
        # Step 2: Wait for browser to load
        steps.append(AutomationStep(
            id="step_2",
            description=f"Wait for {browser} to load",
            action_type="wait",
            value="3",
            confidence=1.0
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
                confidence=0.7
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
                confidence=0.8
            ),
            AutomationStep(
                id="step_4",
                description="Wait for YouTube to load",
                action_type="wait",
                value="3",
                confidence=1.0
            ),
            AutomationStep(
                id="step_5",
                description="Click on search box",
                action_type="click",
                target="search_box",
                confidence=0.7
            ),
            AutomationStep(
                id="step_6",
                description=f"Search for '{search_term}'",
                action_type="type",
                value=search_term,
                confidence=0.8
            ),
            AutomationStep(
                id="step_7",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=0.9
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
                confidence=0.8
            ),
            AutomationStep(
                id="step_4",
                description="Wait for Google to load",
                action_type="wait",
                value="2",
                confidence=1.0
            ),
            AutomationStep(
                id="step_5",
                description=f"Search for '{search_term}'",
                action_type="type",
                value=search_term,
                confidence=0.8
            ),
            AutomationStep(
                id="step_6",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=0.9
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
            confidence=0.9
        ))
        
        # Step 2: Wait for app to load
        steps.append(AutomationStep(
            id="step_2", 
            description="Wait for TextEdit to open",
            action_type="wait",
            value="2",
            confidence=1.0
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
                confidence=0.8
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
                confidence=0.8
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
                confidence=0.9
            ),
            AutomationStep(
                id="step_2",
                description="Wait for Safari to load",
                action_type="wait",
                value="2",
                confidence=1.0
            ),
            AutomationStep(
                id="step_3",
                description="Navigate to Google.com",
                action_type="hotkey",
                target="command+l",
                confidence=0.9
            ),
            AutomationStep(
                id="step_4",
                description="Type Google URL",
                action_type="type",
                value="google.com",
                confidence=0.9
            ),
            AutomationStep(
                id="step_5",
                description="Press Enter to navigate",
                action_type="hotkey",
                target="enter",
                confidence=1.0
            ),
            AutomationStep(
                id="step_6",
                description="Wait for Google to load",
                action_type="wait",
                value="3",
                confidence=1.0
            ),
            AutomationStep(
                id="step_7",
                description="Click on search box",
                action_type="click",
                target="search box",
                confidence=0.7
            ),
            AutomationStep(
                id="step_8",
                description=f"Type search term: {search_term}",
                action_type="type",
                value=search_term,
                confidence=0.9
            ),
            AutomationStep(
                id="step_9",
                description="Press Enter to search",
                action_type="hotkey",
                target="enter",
                confidence=1.0
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
                confidence=0.9
            ),
            AutomationStep(
                id="step_2",
                description="Wait for Notes to open",
                action_type="wait",
                value="2",
                confidence=1.0
            ),
            AutomationStep(
                id="step_3",
                description="Create new note for daily workflow",
                action_type="hotkey",
                target="command+n",
                confidence=0.9
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
                confidence=1.0
            )
        ]
    
    async def _create_generic_steps(self, message: str) -> List[AutomationStep]:
        """Create generic automation steps"""
        return [
            AutomationStep(
                id="step_1",
                description=f"Analyze request: {message[:50]}...",
                action_type="analyze",
                confidence=0.8
            ),
            AutomationStep(
                id="step_2",
                description="Execute appropriate action based on analysis",
                action_type="execute",
                confidence=0.6
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
        
        response_text += f"\n**Plan ID:** `{plan.task_id}`\n\n"
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
            
            # Execute each step with progress updates
            executed_steps = 0
            failed_steps = 0
            
            for i, step in enumerate(plan.steps):
                try:
                    step.status = "executing"
                    progress = int((i / len(plan.steps)) * 100)
                    logger.info(f"📊 Step {i+1}/{len(plan.steps)}: {step.description} ({progress}%)")
                    
                    success = await self._execute_step(step)
                    
                    if success:
                        step.status = "completed"
                        executed_steps += 1
                        logger.info(f"✅ Step completed: {step.description}")
                    else:
                        step.status = "failed"
                        failed_steps += 1
                        logger.warning(f"❌ Step failed: {step.description}")
                    
                    # Progress update after each step
                    progress = int(((i + 1) / len(plan.steps)) * 100)
                    logger.info(f"📊 Progress: {progress}% ({i+1}/{len(plan.steps)} steps)")
                    
                    # Small delay between steps
                    await asyncio.sleep(1.0)  # Increase delay to see progress
                    
                except Exception as e:
                    step.status = "failed"
                    failed_steps += 1
                    logger.error(f"❌ Step error: {step.description} - {e}")
            
            # Update plan status
            plan.status = "completed" if failed_steps == 0 else "partially_completed"
            
            # Generate execution report
            execution_time = time.time() - start_time
            success_rate = (executed_steps / len(plan.steps)) * 100
            
            response = f"🎯 **Automation Execution Complete**\n\n"
            response += f"**Task:** {plan.title}\n"
            response += f"**Execution Time:** {execution_time:.1f} seconds\n"
            response += f"**Success Rate:** {success_rate:.1f}% ({executed_steps}/{len(plan.steps)} steps)\n"
            response += f"**Status:** {plan.status.replace('_', ' ').title()}\n\n"
            
            if failed_steps > 0:
                response += f"⚠️ **Note:** {failed_steps} step(s) failed during execution.\n"
            else:
                response += f"✅ **All steps executed successfully!**\n"
            
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
        """Execute a single automation step"""
        try:
            if step.action_type == "open":
                return await self._execute_open_app(step)
            elif step.action_type == "click":
                return await self._execute_click(step)
            elif step.action_type == "type":
                return await self._execute_type(step)
            elif step.action_type == "hotkey":
                return await self._execute_hotkey(step)
            elif step.action_type == "wait":
                return await self._execute_wait(step)
            elif step.action_type == "analyze":
                return await self._execute_analyze(step)
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
            await asyncio.sleep(1)
            
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

# Create singleton instance
real_agent_handler = RealAgentAutomationHandler()

async def handle_real_agent_automation(message: str, session_id: str) -> Dict[str, Any]:
    """Entry point for real agent automation"""
    return await real_agent_handler.handle_agent_request(message, session_id)