#!/usr/bin/env python3
"""
Ultra Fast Agent Automation System
- No screen capture dependency
- Uses OS accessibility APIs and intelligent caching
- Sub-second response times
- Minimal resource usage
"""

import asyncio
import json
import logging
import os
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from agent_workflow.input_controller import InputController
from fast_ui_detector import FastUIDetector, UIElement
from system_ui_monitor import IntelligentUISystem

# Configure lightweight logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger('ultra_fast_automation')

@dataclass
class ActionResult:
    """Result of an automation action"""
    success: bool
    action_type: str
    target_element: Optional[Dict]
    execution_time: float
    error_message: Optional[str] = None
    details: Optional[Dict] = None

class UltraFastAutomation:
    """Ultra-fast automation system using intelligent UI detection"""
    
    def __init__(self):
        self.input_controller = InputController(safety_level="low")  # Fast mode
        self.ui_system = IntelligentUISystem()
        
        # Command patterns for fast parsing
        self.action_patterns = {
            'click': [
                r'click\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'press\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'tap\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'click\s*(.+)',
                r'select\s+(.+)'
            ],
            'type': [
                r'type\s+"([^"]+)"',
                r'type\s+(.+)',
                r'enter\s+"([^"]+)"',
                r'input\s+"([^"]+)"',
                r'write\s+"([^"]+)"',
                r'enter\s+(.+)',
                r'input\s+(.+)',
                r'write\s+(.+)'
            ],
            'scroll': [
                r'scroll\s+(up|down|left|right)',
                r'(scroll|swipe)\s+(.+?)'
            ],
            'wait': [
                r'wait\s+(\d+\.?\d*)\s*(?:seconds?)?',
                r'pause\s+(\d+\.?\d*)'
            ],
            'describe': [
                r'describe\s+(?:the\s+)?(.+)',
                r'what\s+(?:is\s+)?(?:on\s+)?(?:the\s+)?(.+)',
                r'show\s+(?:me\s+)?(?:the\s+)?(.+)'
            ]
        }
        
        # Element matching shortcuts
        self.element_shortcuts = {
            'button': ['btn', 'button', 'click'],
            'input': ['input', 'field', 'textbox', 'search'],
            'link': ['link', 'url', 'href'],
            'menu': ['menu', 'dropdown', 'select']
        }
        
    async def start(self):
        """Start the ultra-fast automation system"""
        await self.ui_system.start()
        logger.info("Ultra-fast automation system started")
    
    def stop(self):
        """Stop the automation system"""
        self.ui_system.stop()
        logger.info("Ultra-fast automation system stopped")
    
    async def execute_command(self, command: str) -> ActionResult:
        """Execute a command with ultra-fast response"""
        start_time = time.time()
        
        try:
            # Fast command parsing (no LLM needed)
            action_type, target, value = self._parse_command_fast(command)
            
            if not action_type:
                return ActionResult(
                    success=False,
                    action_type='unknown',
                    target_element=None,
                    execution_time=time.time() - start_time,
                    error_message=f"Could not understand command: {command}"
                )
            
            # Execute action based on type
            if action_type == 'click':
                result = await self._execute_click(target)
            elif action_type == 'type':
                result = await self._execute_type(value, target)
            elif action_type == 'scroll':
                result = await self._execute_scroll(target, value)
            elif action_type == 'wait':
                result = await self._execute_wait(float(target))
            elif action_type == 'describe':
                result = await self._execute_describe(target)
            else:
                result = ActionResult(
                    success=False,
                    action_type=action_type,
                    target_element=None,
                    execution_time=time.time() - start_time,
                    error_message=f"Unsupported action: {action_type}"
                )
            
            result.execution_time = time.time() - start_time
            logger.info(f"Command '{command}' executed in {result.execution_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return ActionResult(
                success=False,
                action_type='error',
                target_element=None,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _parse_command_fast(self, command: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse command using regex patterns (much faster than LLM)"""
        command_lower = command.lower().strip()
        
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command_lower)
                if match:
                    groups = match.groups()
                    if action_type == 'click':
                        return action_type, groups[0].strip(), None
                    elif action_type == 'type':
                        return action_type, None, groups[0]
                    elif action_type == 'scroll':
                        direction = groups[0] if len(groups) == 1 else groups[1]
                        return action_type, direction, None
                    elif action_type == 'wait':
                        return action_type, groups[0], None
                    elif action_type == 'describe':
                        return action_type, groups[0].strip(), None
        
        # Fallback: try to detect simple patterns
        if any(word in command_lower for word in ['click', 'press', 'tap']):
            # Extract target after action word
            words = command_lower.split()
            action_word_idx = next((i for i, word in enumerate(words) 
                                  if word in ['click', 'press', 'tap']), -1)
            if action_word_idx >= 0 and action_word_idx < len(words) - 1:
                target = ' '.join(words[action_word_idx + 1:])
                return 'click', target, None
        
        return None, None, None
    
    async def _execute_click(self, target: str) -> ActionResult:
        """Execute click action using fast element detection"""
        if not target:
            return ActionResult(False, 'click', None, 0, "No target specified")
        
        # Find element using intelligent UI system
        element = await self.ui_system.find_element(target)
        
        if not element:
            # Try alternative search terms
            for element_type, keywords in self.element_shortcuts.items():
                if any(keyword in target for keyword in keywords):
                    elements = await self.ui_system.get_elements()
                    for elem in elements:
                        if elem.get('type') == element_type:
                            element = elem
                            break
                    if element:
                        break
            
            # If still no element and target is generic like "button", get first button
            if not element and target.lower() in ['button', 'btn']:
                elements = await self.ui_system.get_elements()
                for elem in elements:
                    if elem.get('type') == 'button':
                        element = elem
                        break
        
        if not element:
            return ActionResult(False, 'click', None, 0, f"Element '{target}' not found")
        
        # Extract coordinates
        bounds = element.get('bounds')
        if not bounds or len(bounds) < 4:
            return ActionResult(False, 'click', element, 0, "Invalid element bounds")
        
        # Calculate click position (center of element)
        x = bounds[0] + bounds[2] // 2
        y = bounds[1] + bounds[3] // 2
        
        # Execute click
        try:
            await self.input_controller.move_mouse_to(x, y)
            await self.input_controller.click_at(x, y)
            
            return ActionResult(
                success=True,
                action_type='click',
                target_element=element,
                execution_time=0,  # Will be set by caller
                details={'position': (x, y)}
            )
            
        except Exception as e:
            return ActionResult(False, 'click', element, 0, f"Click execution failed: {e}")
    
    async def _execute_type(self, text: str, target: Optional[str] = None) -> ActionResult:
        """Execute typing action"""
        if not text:
            return ActionResult(False, 'type', None, 0, "No text to type")
        
        element = None
        
        # If target specified, click on it first
        if target:
            click_result = await self._execute_click(target)
            if not click_result.success:
                return ActionResult(False, 'type', None, 0, f"Could not click target: {target}")
            element = click_result.target_element
            await asyncio.sleep(0.1)  # Brief pause after click
        
        # Type the text
        try:
            self.input_controller.type_text(text)
            
            return ActionResult(
                success=True,
                action_type='type',
                target_element=element,
                execution_time=0,
                details={'text': text}
            )
            
        except Exception as e:
            return ActionResult(False, 'type', element, 0, f"Typing failed: {e}")
    
    async def _execute_scroll(self, direction: str, amount: Optional[str] = None) -> ActionResult:
        """Execute scroll action"""
        try:
            scroll_amount = 3  # Default scroll amount
            if amount and amount.isdigit():
                scroll_amount = int(amount)
            
            if direction in ['up', 'down']:
                scroll_direction = 'up' if direction == 'up' else 'down'
                await self.input_controller.scroll(direction=scroll_direction, amount=scroll_amount)
            else:
                return ActionResult(False, 'scroll', None, 0, f"Unsupported scroll direction: {direction}")
            
            return ActionResult(
                success=True,
                action_type='scroll',
                target_element=None,
                execution_time=0,
                details={'direction': direction, 'amount': scroll_amount}
            )
            
        except Exception as e:
            return ActionResult(False, 'scroll', None, 0, f"Scroll failed: {e}")
    
    async def _execute_wait(self, duration: float) -> ActionResult:
        """Execute wait action"""
        try:
            await asyncio.sleep(duration)
            
            return ActionResult(
                success=True,
                action_type='wait',
                target_element=None,
                execution_time=0,
                details={'duration': duration}
            )
            
        except Exception as e:
            return ActionResult(False, 'wait', None, 0, f"Wait failed: {e}")
    
    async def _execute_describe(self, target: str) -> ActionResult:
        """Execute describe action"""
        try:
            if target.lower() in ['screen', 'ui', 'interface', 'current']:
                description = await self.describe_current_ui()
            else:
                # Describe specific element
                element = await self.ui_system.find_element(target)
                if element:
                    description = f"Found {element.get('type', 'element')}"
                    if element.get('text'):
                        description += f" with text '{element['text']}'"
                    bounds = element.get('bounds')
                    if bounds:
                        description += f" at position ({bounds[0]}, {bounds[1]})"
                else:
                    description = f"No element matching '{target}' found"
            
            return ActionResult(
                success=True,
                action_type='describe',
                target_element=None,
                execution_time=0,
                details={'description': description}
            )
            
        except Exception as e:
            return ActionResult(False, 'describe', None, 0, f"Describe failed: {e}")
    
    async def get_available_elements(self) -> List[Dict]:
        """Get list of available UI elements for user reference"""
        return await self.ui_system.get_elements()
    
    async def describe_current_ui(self) -> str:
        """Describe current UI state in natural language"""
        elements = await self.get_available_elements()
        
        if not elements:
            return "No UI elements detected on current screen."
        
        # Count elements by type
        element_counts = {}
        for element in elements:
            elem_type = element.get('type', 'unknown')
            element_counts[elem_type] = element_counts.get(elem_type, 0) + 1
        
        # Generate description
        descriptions = []
        for elem_type, count in element_counts.items():
            if count == 1:
                descriptions.append(f"1 {elem_type}")
            else:
                descriptions.append(f"{count} {elem_type}s")
        
        description = f"Current screen has {', '.join(descriptions)}."
        
        # Add some specific elements
        buttons = [e for e in elements if e.get('type') == 'button' and e.get('text')]
        if buttons:
            button_names = [b['text'] for b in buttons[:3]]  # First 3 buttons
            description += f" Available buttons: {', '.join(button_names)}"
            if len(buttons) > 3:
                description += f" and {len(buttons) - 3} more."
        
        return description

# Test function
async def test_ultra_fast():
    """Test ultra-fast automation"""
    automation = UltraFastAutomation()
    
    try:
        await automation.start()
        
        print("Testing ultra-fast automation...")
        
        # Test UI description
        description = await automation.describe_current_ui()
        print(f"Current UI: {description}")
        
        # Test simple commands
        test_commands = [
            "describe the screen",
            "click the button",
            "type hello world",
            "wait 1 second"
        ]
        
        for command in test_commands:
            print(f"\nExecuting: '{command}'")
            result = await automation.execute_command(command)
            print(f"Result: {result.success} ({result.execution_time:.3f}s)")
            if not result.success:
                print(f"Error: {result.error_message}")
            
    finally:
        automation.stop()

if __name__ == "__main__":
    asyncio.run(test_ultra_fast())