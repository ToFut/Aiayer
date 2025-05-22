#!/usr/bin/env python3
"""
AutomationAgent - Enterprise-grade mouse and keyboard automation agent.

This agent provides enhanced automation capabilities with:
- Precise mouse/keyboard control
- Human-like movement patterns
- Safety mechanisms and emergency stops
- Performance optimization
- Learning from user interactions
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import pyautogui
import random
from dataclasses import dataclass
from enum import Enum

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from execution.core.agent_base import AgentBase, AgentConfig, AgentCapability
from execution.memory.agent_memory import AgentMemory, MemoryType
from agent_workflow.input_controller import InputController

logger = logging.getLogger(__name__)


class AutomationType(Enum):
    """Types of automation actions."""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    TYPE_TEXT = "type_text"
    KEY_PRESS = "key_press"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    MOVE_MOUSE = "move_mouse"
    SCREENSHOT = "screenshot"
    FIND_ELEMENT = "find_element"


class SafetyLevel(Enum):
    """Safety levels for automation."""
    MAXIMUM = "maximum"  # Requires confirmation for all actions
    HIGH = "high"       # Default - confirms destructive actions
    MEDIUM = "medium"   # Minimal confirmations
    LOW = "low"         # No confirmations (use with caution)


@dataclass
class AutomationAction:
    """Represents a single automation action."""
    action_id: str
    action_type: AutomationType
    parameters: Dict[str, Any]
    safety_level: SafetyLevel = SafetyLevel.HIGH
    requires_confirmation: bool = True
    estimated_duration: float = 1.0
    retry_count: int = 0
    max_retries: int = 3
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class AutomationSequence:
    """Represents a sequence of automation actions."""
    sequence_id: str
    name: str
    description: str
    actions: List[AutomationAction]
    total_estimated_duration: float = 0.0
    
    def __post_init__(self):
        self.total_estimated_duration = sum(action.estimated_duration for action in self.actions)


class AutomationAgent(AgentBase):
    """
    Enterprise-grade automation agent for mouse and keyboard control.
    
    Features:
    - Enhanced InputController integration
    - Human-like movement patterns
    - Advanced safety mechanisms
    - Performance optimization
    - Learning from user patterns
    - Emergency shutdown (Ctrl+1)
    - Context-aware automation
    - Memory integration for improvement
    """
    
    def __init__(self, config: AgentConfig, memory: AgentMemory, 
                 safety_level: SafetyLevel = SafetyLevel.HIGH):
        """Initialize the automation agent."""
        super().__init__(config)
        
        self.memory = memory
        self.safety_level = safety_level
        
        # Enhanced input controller
        self.input_controller = InputController(safety_level=safety_level.value)
        
        # Action tracking
        self.active_sequences: Dict[str, AutomationSequence] = {}
        self.completed_actions: List[AutomationAction] = []
        self.failed_actions: List[AutomationAction] = []
        
        # Performance optimization
        self.action_patterns: Dict[str, List[float]] = {}  # Track timing patterns
        self.user_preferences: Dict[str, Any] = {}
        self.learned_shortcuts: Dict[str, List[AutomationAction]] = {}
        
        # Safety and emergency
        self.emergency_stop_active = False
        self.confirmation_required_actions = {
            AutomationType.TYPE_TEXT,
            AutomationType.KEY_PRESS,
            AutomationType.HOTKEY
        }
        
        # Screen analysis
        self.screen_width, self.screen_height = pyautogui.size()
        self.current_screenshot = None
        self.element_cache: Dict[str, Tuple[int, int]] = {}
        
        # Performance metrics
        self.actions_executed = 0
        self.actions_successful = 0
        self.total_execution_time = 0.0
        self.user_interruptions = 0
        
        logger.info(f"AutomationAgent initialized with {safety_level.value} safety level")
    
    async def initialize(self) -> None:
        """Initialize the automation agent."""
        try:
            # Start input controller
            self.input_controller.start_listeners()
            
            # Load user preferences from memory
            await self._load_user_preferences()
            
            # Start screen monitoring
            await self._initialize_screen_monitoring()
            
            self.logger.info("AutomationAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AutomationAgent: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup automation resources."""
        try:
            # Stop input controller
            self.input_controller.stop_listeners()
            
            # Save user preferences to memory
            await self._save_user_preferences()
            
            # Store final performance metrics
            self.memory.store_memory(MemoryType.PERFORMANCE_METRIC, {
                'agent_type': 'AutomationAgent',
                'actions_executed': self.actions_executed,
                'actions_successful': self.actions_successful,
                'success_rate': self.actions_successful / max(1, self.actions_executed),
                'total_execution_time': self.total_execution_time,
                'user_interruptions': self.user_interruptions,
                'session_duration': time.time() - self.start_time
            })
            
            self.logger.info("AutomationAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def _load_user_preferences(self) -> None:
        """Load user preferences from memory."""
        try:
            # Search for user preferences in memory
            prefs_entries = self.memory.search_memory(
                "user_preferences", 
                MemoryType.USER_INTERACTION,
                tags={"automation", "preferences"}
            )
            
            if prefs_entries:
                latest_prefs = prefs_entries[0]  # Most recent
                self.user_preferences = latest_prefs.data.get("preferences", {})
                self.logger.info("Loaded user preferences from memory")
            else:
                # Set default preferences
                self.user_preferences = {
                    "mouse_speed": "medium",
                    "click_delay": 0.1,
                    "typing_speed": "medium",
                    "confirmation_timeout": 30.0,
                    "enable_sound": True
                }
                
        except Exception as e:
            self.logger.error(f"Failed to load user preferences: {e}")
    
    async def _save_user_preferences(self) -> None:
        """Save user preferences to memory."""
        try:
            self.memory.store_memory(MemoryType.USER_INTERACTION, {
                "event_type": "user_preferences",
                "preferences": self.user_preferences,
                "timestamp": time.time()
            }, tags={"automation", "preferences"})
            
        except Exception as e:
            self.logger.error(f"Failed to save user preferences: {e}")
    
    async def _initialize_screen_monitoring(self) -> None:
        """Initialize screen monitoring capabilities."""
        try:
            # Take initial screenshot
            self.current_screenshot = pyautogui.screenshot()
            
            # Initialize element cache
            self.element_cache.clear()
            
            self.logger.info("Screen monitoring initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize screen monitoring: {e}")
    
    # ========== Core Task Processing ==========
    
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """Process automation task."""
        action_type = task_data.get("action", "unknown")
        parameters = task_data.get("parameters", {})
        
        try:
            if action_type == "execute_action":
                return await self._execute_single_action(parameters)
                
            elif action_type == "execute_sequence":
                return await self._execute_action_sequence(parameters)
                
            elif action_type == "find_element":
                return await self._find_screen_element(parameters)
                
            elif action_type == "take_screenshot":
                return await self._take_screenshot()
                
            elif action_type == "emergency_stop":
                return await self._emergency_stop()
                
            elif action_type == "set_safety_level":
                return await self._set_safety_level(parameters)
                
            else:
                self.logger.warning(f"Unknown automation action: {action_type}")
                return {"error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            self.logger.error(f"Error processing automation task: {e}")
            return {"error": str(e)}
    
    async def _execute_single_action(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single automation action."""
        action_type_str = parameters.get("type", "")
        
        try:
            action_type = AutomationType(action_type_str)
        except ValueError:
            return {"error": f"Invalid action type: {action_type_str}"}
        
        # Create action object
        action = AutomationAction(
            action_id=str(uuid.uuid4()),
            action_type=action_type,
            parameters=parameters,
            safety_level=self.safety_level
        )
        
        # Check if confirmation is required
        if self._requires_confirmation(action):
            confirmation_result = await self._request_confirmation(action)
            if not confirmation_result:
                return {"error": "Action cancelled by user"}
        
        # Check for emergency stop
        if self.emergency_stop_active:
            return {"error": "Emergency stop is active"}
        
        # Execute the action
        start_time = time.time()
        success = await self._perform_automation_action(action)
        execution_time = time.time() - start_time
        
        # Update metrics
        self.actions_executed += 1
        if success:
            self.actions_successful += 1
            self.completed_actions.append(action)
        else:
            self.failed_actions.append(action)
        
        self.total_execution_time += execution_time
        
        # Store in memory
        self.memory.store_memory(MemoryType.SYSTEM_EVENT, {
            "event_type": "automation_action",
            "action_id": action.action_id,
            "action_type": action.action_type.value,
            "parameters": action.parameters,
            "success": success,
            "execution_time": execution_time,
            "timestamp": time.time()
        }, tags={"automation", action.action_type.value})
        
        self.logger.info(f"Executed action {action.action_type.value}: {'success' if success else 'failed'}")
        
        return {
            "action_id": action.action_id,
            "success": success,
            "execution_time": execution_time,
            "action_type": action.action_type.value
        }
    
    async def _execute_action_sequence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sequence of automation actions."""
        sequence_data = parameters.get("sequence", {})
        sequence_name = sequence_data.get("name", "Unnamed Sequence")
        actions_data = sequence_data.get("actions", [])
        
        # Create sequence
        sequence = AutomationSequence(
            sequence_id=str(uuid.uuid4()),
            name=sequence_name,
            description=sequence_data.get("description", ""),
            actions=[]
        )
        
        # Create actions
        for action_data in actions_data:
            try:
                action_type = AutomationType(action_data.get("type", ""))
            except ValueError:
                continue
                
            action = AutomationAction(
                action_id=str(uuid.uuid4()),
                action_type=action_type,
                parameters=action_data.get("parameters", {}),
                safety_level=self.safety_level
            )
            sequence.actions.append(action)
        
        self.active_sequences[sequence.sequence_id] = sequence
        
        # Execute sequence
        successful_actions = 0
        failed_actions = 0
        total_time = 0.0
        
        for i, action in enumerate(sequence.actions):
            if self.emergency_stop_active:
                break
                
            start_time = time.time()
            success = await self._perform_automation_action(action)
            execution_time = time.time() - start_time
            total_time += execution_time
            
            if success:
                successful_actions += 1
            else:
                failed_actions += 1
                
                # Stop sequence on failure if safety level is high
                if self.safety_level in [SafetyLevel.HIGH, SafetyLevel.MAXIMUM]:
                    self.logger.warning(f"Stopping sequence due to failed action: {action.action_type.value}")
                    break
        
        # Clean up
        del self.active_sequences[sequence.sequence_id]
        
        # Store sequence result in memory
        self.memory.store_memory(MemoryType.SYSTEM_EVENT, {
            "event_type": "automation_sequence",
            "sequence_id": sequence.sequence_id,
            "sequence_name": sequence_name,
            "total_actions": len(sequence.actions),
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "total_execution_time": total_time,
            "timestamp": time.time()
        }, tags={"automation", "sequence"})
        
        self.logger.info(f"Executed sequence '{sequence_name}': {successful_actions}/{len(sequence.actions)} successful")
        
        return {
            "sequence_id": sequence.sequence_id,
            "total_actions": len(sequence.actions),
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "total_execution_time": total_time,
            "success_rate": successful_actions / len(sequence.actions) if sequence.actions else 0
        }
    
    async def _perform_automation_action(self, action: AutomationAction) -> bool:
        """Perform the actual automation action."""
        try:
            action_type = action.action_type
            params = action.parameters
            
            if action_type == AutomationType.CLICK:
                x = params.get("x", 0)
                y = params.get("y", 0)
                button = params.get("button", "left")
                clicks = params.get("clicks", 1)
                return self.input_controller.click(x, y, button, clicks)
                
            elif action_type == AutomationType.DOUBLE_CLICK:
                x = params.get("x", 0)
                y = params.get("y", 0)
                return self.input_controller.double_click(x, y)
                
            elif action_type == AutomationType.RIGHT_CLICK:
                x = params.get("x", 0)
                y = params.get("y", 0)
                return self.input_controller.right_click(x, y)
                
            elif action_type == AutomationType.DRAG:
                x = params.get("x", 0)
                y = params.get("y", 0)
                button = params.get("button", "left")
                duration = params.get("duration")
                return self.input_controller.drag_to(x, y, button, duration)
                
            elif action_type == AutomationType.TYPE_TEXT:
                text = params.get("text", "")
                interval = params.get("interval")
                return self.input_controller.type_text(text, interval)
                
            elif action_type == AutomationType.KEY_PRESS:
                key = params.get("key", "")
                return self.input_controller.press_key(key)
                
            elif action_type == AutomationType.HOTKEY:
                keys = params.get("keys", [])
                return self.input_controller.hotkey(*keys)
                
            elif action_type == AutomationType.SCROLL:
                clicks = params.get("clicks", 1)
                return self.input_controller.scroll(clicks)
                
            elif action_type == AutomationType.MOVE_MOUSE:
                x = params.get("x", 0)
                y = params.get("y", 0)
                duration = params.get("duration")
                human_like = params.get("human_like", True)
                return self.input_controller.move_to(x, y, duration, human_like)
                
            elif action_type == AutomationType.SCREENSHOT:
                region = params.get("region")
                screenshot = self.input_controller.capture_screen_region(region)
                return screenshot is not None
                
            else:
                self.logger.error(f"Unsupported action type: {action_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error performing action {action.action_type.value}: {e}")
            return False
    
    # ========== Safety and Confirmation ==========
    
    def _requires_confirmation(self, action: AutomationAction) -> bool:
        """Check if action requires user confirmation."""
        if self.safety_level == SafetyLevel.LOW:
            return False
        elif self.safety_level == SafetyLevel.MAXIMUM:
            return True
        elif self.safety_level == SafetyLevel.HIGH:
            return action.action_type in self.confirmation_required_actions
        else:  # MEDIUM
            return action.action_type in self.confirmation_required_actions and \
                   self._is_potentially_destructive(action)
    
    def _is_potentially_destructive(self, action: AutomationAction) -> bool:
        """Check if action is potentially destructive."""
        if action.action_type == AutomationType.TYPE_TEXT:
            text = action.parameters.get("text", "").lower()
            destructive_keywords = ["delete", "remove", "clear", "format", "reset"]
            return any(keyword in text for keyword in destructive_keywords)
        
        elif action.action_type == AutomationType.KEY_PRESS:
            key = action.parameters.get("key", "").lower()
            return key in ["delete", "backspace", "f4", "f12"]
        
        elif action.action_type == AutomationType.HOTKEY:
            keys = action.parameters.get("keys", [])
            destructive_combos = [
                ["cmd", "a"],  # Select all
                ["ctrl", "a"],
                ["cmd", "d"],  # Delete
                ["ctrl", "d"],
                ["alt", "f4"]  # Close window
            ]
            return any(combo in [keys] for combo in destructive_combos)
        
        return False
    
    async def _request_confirmation(self, action: AutomationAction) -> bool:
        """Request user confirmation for action."""
        # In a real implementation, this would show a dialog or send a message
        # to the frontend asking for confirmation
        
        confirmation_message = {
            "type": "automation_confirmation_request",
            "action_id": action.action_id,
            "action_type": action.action_type.value,
            "parameters": action.parameters,
            "description": self._get_action_description(action),
            "timeout": self.user_preferences.get("confirmation_timeout", 30.0)
        }
        
        # Store confirmation request in memory
        self.memory.store_memory(MemoryType.USER_INTERACTION, {
            "event_type": "confirmation_request",
            "action_id": action.action_id,
            "confirmation_message": confirmation_message,
            "timestamp": time.time()
        }, tags={"automation", "confirmation"})
        
        # For now, assume user confirms (in real implementation, would wait for response)
        # This would be handled by the frontend/user interface
        self.logger.info(f"Requesting confirmation for {action.action_type.value}")
        
        # Simulate confirmation (in production, this would be actual user input)
        await asyncio.sleep(0.1)  # Brief delay to simulate user response time
        return True  # Assume confirmed for now
    
    def _get_action_description(self, action: AutomationAction) -> str:
        """Get human-readable description of action."""
        action_type = action.action_type
        params = action.parameters
        
        if action_type == AutomationType.CLICK:
            return f"Click at ({params.get('x', 0)}, {params.get('y', 0)})"
        elif action_type == AutomationType.TYPE_TEXT:
            text = params.get("text", "")
            if len(text) > 20:
                text = text[:20] + "..."
            return f"Type text: '{text}'"
        elif action_type == AutomationType.KEY_PRESS:
            return f"Press key: {params.get('key', '')}"
        elif action_type == AutomationType.HOTKEY:
            keys = params.get("keys", [])
            return f"Press key combination: {'+'.join(keys)}"
        else:
            return f"Execute {action_type.value}"
    
    # ========== Screen Analysis ==========
    
    async def _find_screen_element(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Find element on screen."""
        element_name = parameters.get("element", "")
        search_method = parameters.get("method", "template")  # template, color, text
        
        try:
            if search_method == "template" and "template_path" in parameters:
                # Template matching
                template_path = parameters["template_path"]
                location = pyautogui.locateOnScreen(template_path, confidence=0.8)
                if location:
                    center = pyautogui.center(location)
                    self.element_cache[element_name] = (center.x, center.y)
                    return {"found": True, "x": center.x, "y": center.y}
                else:
                    return {"found": False}
                    
            elif search_method == "text" and "text" in parameters:
                # OCR text search (would require additional libraries like pytesseract)
                # For now, return not implemented
                return {"found": False, "error": "Text search not implemented"}
                
            else:
                return {"found": False, "error": "Invalid search method"}
                
        except Exception as e:
            self.logger.error(f"Error finding screen element: {e}")
            return {"found": False, "error": str(e)}
    
    async def _take_screenshot(self) -> Dict[str, Any]:
        """Take screenshot and return path."""
        try:
            screenshot = pyautogui.screenshot()
            timestamp = int(time.time())
            screenshot_path = f"logs/screenshots/automation_{timestamp}.png"
            
            # Ensure directory exists
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            
            screenshot.save(screenshot_path)
            self.current_screenshot = screenshot
            
            return {
                "success": True,
                "path": screenshot_path,
                "timestamp": timestamp,
                "size": {"width": screenshot.width, "height": screenshot.height}
            }
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== Emergency and Safety ==========
    
    async def _emergency_stop(self) -> Dict[str, Any]:
        """Execute emergency stop."""
        self.emergency_stop_active = True
        
        # Cancel all active sequences
        for sequence_id in list(self.active_sequences.keys()):
            del self.active_sequences[sequence_id]
        
        # Stop input controller
        self.input_controller.stop_listeners()
        
        # Log emergency stop
        self.memory.store_memory(MemoryType.SYSTEM_EVENT, {
            "event_type": "emergency_stop",
            "timestamp": time.time(),
            "active_sequences_cancelled": len(self.active_sequences)
        }, tags={"automation", "emergency"})
        
        self.user_interruptions += 1
        
        self.logger.critical("🚨 EMERGENCY STOP ACTIVATED")
        
        return {
            "success": True,
            "message": "Emergency stop activated",
            "sequences_cancelled": len(self.active_sequences)
        }
    
    async def _set_safety_level(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Set safety level."""
        try:
            new_level_str = parameters.get("level", "")
            new_level = SafetyLevel(new_level_str)
            old_level = self.safety_level
            
            self.safety_level = new_level
            self.input_controller.safety_level = new_level.value
            
            self.logger.info(f"Safety level changed: {old_level.value} -> {new_level.value}")
            
            return {
                "success": True,
                "old_level": old_level.value,
                "new_level": new_level.value
            }
            
        except ValueError:
            return {"success": False, "error": "Invalid safety level"}
    
    # ========== Health and Monitoring ==========
    
    async def health_check(self) -> bool:
        """Perform health check."""
        # Check input controller
        if not self.input_controller.running:
            self.logger.warning("Input controller not running")
            return False
        
        # Check for emergency stop
        if self.emergency_stop_active:
            self.logger.warning("Emergency stop is active")
            return False
        
        # Check screen accessibility
        try:
            pyautogui.position()  # Test if we can get mouse position
        except Exception as e:
            self.logger.warning(f"Screen access issue: {e}")
            return False
        
        return True
    
    async def handle_unhealthy_state(self) -> None:
        """Handle unhealthy state."""
        self.logger.info("Attempting to recover automation agent")
        
        try:
            # Restart input controller if not running
            if not self.input_controller.running:
                self.input_controller.start_listeners()
            
            # Clear emergency stop if active
            if self.emergency_stop_active:
                self.emergency_stop_active = False
                self.logger.info("Emergency stop cleared")
            
            self.logger.info("Automation agent recovery successful")
            
        except Exception as e:
            self.logger.error(f"Recovery failed: {e}")
    
    # ========== Statistics and Analytics ==========
    
    def get_automation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive automation statistics."""
        success_rate = self.actions_successful / max(1, self.actions_executed)
        avg_execution_time = self.total_execution_time / max(1, self.actions_executed)
        
        return {
            "actions_executed": self.actions_executed,
            "actions_successful": self.actions_successful,
            "success_rate": success_rate,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": avg_execution_time,
            "user_interruptions": self.user_interruptions,
            "emergency_stops": self.user_interruptions,  # For now, same as interruptions
            "active_sequences": len(self.active_sequences),
            "safety_level": self.safety_level.value,
            "emergency_stop_active": self.emergency_stop_active,
            "element_cache_size": len(self.element_cache)
        }