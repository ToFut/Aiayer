#!/usr/bin/env python3
"""
Real Agent Automation Handler - Interactive UI Automation
Provides Do/Dismiss/Adjust workflow with actual screen interaction
"""

import asyncio
import json
import time
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Import plan persistence
try:
    from plan_persistence import save_plan, load_plan, delete_plan, generate_plan_id
    PERSISTENCE_AVAILABLE = True
    logger.info("✅ Plan persistence module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Plan persistence not available, plans will not persist: {e}")
    PERSISTENCE_AVAILABLE = False

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
        self.automation_available = True  # Always available with basic functionality
        logger.info("🤖 Basic automation handler initialized")
    
    async def handle_user_instruction(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user instruction with basic automation planning"""
        try:
            start_time = time.time()
            
            # Create a basic plan based on the message
            plan = await self._create_basic_plan(message)
            
            # Store plan for approval
            self.active_plans[plan.task_id] = plan
            
            # Save to persistent storage if available
            if PERSISTENCE_AVAILABLE:
                try:
                    # Convert AutomationPlan to dictionary before saving
                    plan_dict = {
                        "task_id": plan.task_id,
                        "title": plan.title,
                        "description": plan.description,
                        "steps": [
                            {
                                "id": step.id,
                                "description": step.description,
                                "action_type": step.action_type,
                                "target": step.target,
                                "value": step.value,
                                "coordinates": step.coordinates,
                                "confidence": step.confidence,
                                "status": step.status,
                                "estimated_duration": step.estimated_duration
                            }
                            for step in plan.steps
                        ],
                        "estimated_duration": plan.estimated_duration,
                        "requires_approval": plan.requires_approval,
                        "status": plan.status,
                        "timestamp": time.time(),
                        "created": time.time()
                    }
                    
                    saved = await save_plan(plan.task_id, plan_dict)
                    if saved:
                        logger.info(f"💾 Plan {plan.task_id} saved to persistent storage")
                    else:
                        logger.warning(f"⚠️ Failed to save plan {plan.task_id} to persistent storage")
                except Exception as save_error:
                    logger.warning(f"⚠️ Error saving plan to persistent storage: {save_error}")
            
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
                "ai_powered": False,
                "llm_generated": False,
                "complexity_score": 0.5,
                "persistent": PERSISTENCE_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Error handling user instruction: {e}")
            return {
                "success": False,
                "response": f"Error creating automation plan: {str(e)}",
                "automation_available": self.automation_available
            }
    
    async def _create_basic_plan(self, message: str) -> AutomationPlan:
        """Create a basic automation plan based on the message"""
        message_lower = message.lower()
        
        # Generate a unique task ID
        task_id = f"task_{int(time.time())}_{os.urandom(4).hex()}"
        
        # Create steps based on message content
        steps = []
        
        # Log that we're using the real agent automation handler instead of the fixed one
        logger.warning(f"⚠️ Using real_agent_automation_handler for request: {message}. This indicates that the fixed_universal_automation_handler is not being used properly.")
        
        # Handle Google search
        if "google" in message_lower and "search" in message_lower:
            search_term = message.replace("google", "").replace("search", "").strip()
            steps = [
                AutomationStep(
                    id="step_1",
                    description="Open Safari browser",
                    action_type="open",
                    target="Safari",
                    estimated_duration=2.0
                ),
                AutomationStep(
                    id="step_2",
                    description="Navigate to Google",
                    action_type="navigate_url",
                    target="https://www.google.com",
                    estimated_duration=3.0
                ),
                AutomationStep(
                    id="step_3",
                    description=f"Search for '{search_term}'",
                    action_type="type",
                    target="search_box",
                    value=search_term,
                    estimated_duration=2.0
                ),
                AutomationStep(
                    id="step_4",
                    description="Press Enter to search",
                    action_type="hotkey",
                    target="return",
                    estimated_duration=1.0
                )
            ]
            title = f"Google Search: {search_term}"
            description = f"Search Google for '{search_term}'"
            estimated_duration = 8.0
            
        # Handle general search (including searches for specific applications)
        elif "search" in message_lower:
            # Extract what to search and where
            parts = message.split("in")
            search_term = parts[0].replace("search", "").strip()
            app_name = parts[1].strip() if len(parts) > 1 else "Safari"
            
            steps = [
                AutomationStep(
                    id="step_1",
                    description=f"Open {app_name}",
                    action_type="open",
                    target=app_name,
                    estimated_duration=2.0
                ),
                AutomationStep(
                    id="step_2",
                    description=f"Focus on search area",
                    action_type="click",
                    target="search_area",
                    estimated_duration=1.0
                ),
                AutomationStep(
                    id="step_3",
                    description=f"Search for '{search_term}'",
                    action_type="type",
                    target="search_box",
                    value=search_term,
                    estimated_duration=2.0
                ),
                AutomationStep(
                    id="step_4",
                    description="Press Enter to search",
                    action_type="hotkey",
                    target="return",
                    estimated_duration=1.0
                )
            ]
            title = f"Search for {search_term} in {app_name}"
            description = f"Search for '{search_term}' in {app_name}"
            estimated_duration = 6.0
            
        # Handle app opening
        elif "open" in message_lower:
            app_name = message.replace("open", "").strip()
            steps = [
                AutomationStep(
                    id="step_1",
                    description=f"Open {app_name}",
                    action_type="open",
                    target=app_name,
                    estimated_duration=3.0
                )
            ]
            title = f"Open {app_name}"
            description = f"Launch {app_name} application"
            estimated_duration = 3.0
            
        # Default plan for other requests
        else:
            steps = [
                AutomationStep(
                    id="step_1",
                    description="Analyze request",
                    action_type="analyze",
                    estimated_duration=1.0
                ),
                AutomationStep(
                    id="step_2",
                    description="Determine appropriate action",
                    action_type="analyze",
                    estimated_duration=1.0
                ),
                AutomationStep(
                    id="step_3",
                    description=f"Execute: {message}",
                    action_type="custom",
                    target="system",
                    value=message,
                    estimated_duration=3.0
                )
            ]
            title = "Execute Custom Request"
            description = f"Handle request: {message}"
            estimated_duration = 5.0
        
        return AutomationPlan(
            task_id=task_id,
            title=title,
            description=description,
            steps=steps,
            estimated_duration=estimated_duration
        )
    
    def _format_interactive_response(self, plan: AutomationPlan) -> Dict[str, Any]:
        """Format the plan into an interactive response"""
        response_text = f"🎯 **{plan.title}**\n\n"
        response_text += f"{plan.description}\n\n"
        response_text += "**Steps:**\n"
        
        for i, step in enumerate(plan.steps, 1):
            response_text += f"{i}. {step.description}\n"
        
        response_text += f"\nEstimated duration: {plan.estimated_duration} seconds"
        
        buttons = [
            {
                "text": "🚀 Execute",
                "action": "execute_plan",
                "style": "execute-btn",
                "description": "Execute this plan"
            },
            {
                "text": "❌ Cancel",
                "action": "cancel_plan",
                "style": "cancel-btn",
                "description": "Cancel this plan"
            }
        ]
        
        return {
            "text": response_text,
            "buttons": buttons,
            "interactive": True
        }
    
    async def handle_button_action(self, action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
        """Handle button actions (execute/cancel)"""
        if plan_id not in self.active_plans:
            return {
                "success": False,
                "response": "Plan not found"
            }
        
        plan = self.active_plans[plan_id]
        
        if action == "execute_plan":
            return await self._execute_plan(plan, session_id)
        elif action == "cancel_plan":
            return await self._cancel_plan(plan, session_id)
        else:
            return {
                "success": False,
                "response": f"Unknown action: {action}"
            }
    
    async def _execute_plan(self, plan: AutomationPlan, session_id: str) -> Dict[str, Any]:
        """Execute the automation plan"""
        try:
            plan.status = "executing"
            steps_executed = []
            
            for step in plan.steps:
                step.status = "executing"
                success = await self._execute_step(step)
                step.status = "completed" if success else "failed"
                steps_executed.append(step.description)
            
            plan.status = "completed"
            
            return {
                "success": True,
                "response": "Plan executed successfully",
                "steps_executed": steps_executed
            }
            
        except Exception as e:
            plan.status = "failed"
            return {
                "success": False,
                "response": f"Error executing plan: {str(e)}"
            }
    
    async def _cancel_plan(self, plan: AutomationPlan, session_id: str) -> Dict[str, Any]:
        """Cancel the automation plan"""
        plan.status = "cancelled"
        return {
            "success": True,
            "response": "Plan cancelled"
        }
    
    async def _execute_step(self, step: AutomationStep) -> bool:
        """Execute a single automation step"""
        try:
            if step.action_type == "open":
                # Use osascript to open applications
                os.system(f'osascript -e \'tell application "{step.target}" to activate\'')
            elif step.action_type == "navigate_url":
                # Use osascript to open URLs in Safari
                os.system(f'osascript -e \'tell application "Safari" to open location "{step.target}"\'')
            elif step.action_type == "type":
                # Use osascript to type text
                if step.value:
                    os.system(f'osascript -e \'tell application "System Events" to keystroke "{step.value}"\'')
            elif step.action_type == "hotkey":
                # Use osascript for keyboard shortcuts
                if step.target == "return":
                    os.system('osascript -e \'tell application "System Events" to key code 36\'')
            elif step.action_type == "analyze":
                # Just wait for analysis
                await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            return False

# Create singleton instance
real_agent_handler = RealAgentAutomationHandler()

async def handle_real_agent_automation(message: str, session_id: str) -> Dict[str, Any]:
    """Entry point for real agent automation"""
    return await real_agent_handler.handle_user_instruction(message, {})