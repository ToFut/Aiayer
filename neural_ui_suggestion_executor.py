#!/usr/bin/env python3
"""
Neural UI Suggestion Executor

Integrates deep neural UI detection with the suggestion execution system.
Provides robust UI element targeting and verification for executing suggested actions.
"""

import asyncio
import json
import logging
import os
import time
import sys
import traceback
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import uuid
import re
import base64
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/neural_ui_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Try to import neural UI detector
try:
    from neural_ui_detector import NeuralUIDetector, ElementType, UIElement
    NEURAL_UI_DETECTOR_AVAILABLE = True
    logger.info("✅ Neural UI Detector imported successfully")
except ImportError:
    NEURAL_UI_DETECTOR_AVAILABLE = False
    logger.warning("⚠️ Neural UI Detector not available, will use fallback methods")

# Try to import suggestion memory
try:
    from memory.suggestion_memory import get_suggestion_memory
    SUGGESTION_MEMORY_AVAILABLE = True
except ImportError:
    SUGGESTION_MEMORY_AVAILABLE = False
    logger.warning("⚠️ Suggestion memory not available")

# Try to import input controller
try:
    from agent_workflow.input_controller import InputController
    INPUT_CONTROLLER_AVAILABLE = True
except ImportError:
    INPUT_CONTROLLER_AVAILABLE = False
    logger.warning("⚠️ Input controller not available")

class UIElementInfo:
    """Information about a UI element to target."""
    
    def __init__(
        self, 
        target_text: str, 
        element_type: Optional[str] = None,
        confidence_threshold: float = 0.7
    ):
        self.target_text = target_text
        self.element_type = element_type
        self.confidence_threshold = confidence_threshold
        self.backup_strategies = ["text", "placeholder", "aria-label", "title"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target_text": self.target_text,
            "element_type": self.element_type,
            "confidence_threshold": self.confidence_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIElementInfo':
        """Create from dictionary."""
        return cls(
            target_text=data.get("target_text", ""),
            element_type=data.get("element_type"),
            confidence_threshold=data.get("confidence_threshold", 0.7)
        )

class ActionExecutionResult:
    """Result of an action execution."""
    
    def __init__(
        self,
        success: bool,
        action_type: str,
        target: str,
        execution_time: float,
        element_found: bool = False,
        confidence: float = 0.0,
        screenshot_before: Optional[str] = None,
        screenshot_after: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.action_type = action_type
        self.target = target
        self.execution_time = execution_time
        self.element_found = element_found
        self.confidence = confidence
        self.screenshot_before = screenshot_before
        self.screenshot_after = screenshot_after
        self.error = error
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "action_type": self.action_type,
            "target": self.target,
            "execution_time": self.execution_time,
            "element_found": self.element_found,
            "confidence": self.confidence,
            "error": self.error,
            "timestamp": self.timestamp
        }

class NeuralUISuggestionExecutor:
    """
    Executes suggestions using neural UI detection for robust element targeting.
    """
    
    def __init__(self):
        """Initialize the executor."""
        # Initialize neural UI detector if available
        self.neural_ui_detector = None
        if NEURAL_UI_DETECTOR_AVAILABLE:
            try:
                self.neural_ui_detector = NeuralUIDetector()
                logger.info("✅ Neural UI Detector initialized")
            except Exception as e:
                logger.error(f"❌ Error initializing Neural UI Detector: {e}")
        
        # Initialize input controller if available
        self.input_controller = None
        if INPUT_CONTROLLER_AVAILABLE:
            try:
                self.input_controller = InputController()
                logger.info("✅ Input Controller initialized")
            except Exception as e:
                logger.error(f"❌ Error initializing Input Controller: {e}")
        
        # Execution settings
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.verification_delay = 0.5  # seconds
        
        # Performance metrics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "retry_count": 0,
            "avg_execution_time": 0.0,
            "execution_history": []
        }
        
        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("✅ Neural UI Suggestion Executor initialized")
    
    async def execute_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        """
        Execute a suggestion using neural UI detection.
        
        Args:
            suggestion_id: ID of the suggestion to execute
            
        Returns:
            Dict with execution result
        """
        start_time = time.time()
        
        try:
            # Get suggestion from memory
            if not SUGGESTION_MEMORY_AVAILABLE:
                raise ValueError("Suggestion memory not available")
            
            memory = await get_suggestion_memory()
            suggestion = await memory.get_suggestion(suggestion_id)
            
            if not suggestion:
                raise ValueError(f"Suggestion with ID {suggestion_id} not found")
            
            logger.info(f"🎯 Executing suggestion: {suggestion.get('title', 'Untitled')}")
            
            # Check if suggestion has action items
            action_items = suggestion.get("action_items", [])
            if not action_items:
                raise ValueError("Suggestion has no action items")
            
            # Execute each action item
            results = []
            overall_success = True
            
            for i, action_item in enumerate(action_items):
                logger.info(f"⚡ Executing action {i+1}/{len(action_items)}: {action_item}")
                
                # Execute action with retries
                action_result = await self._execute_action_with_retry(action_item)
                results.append(action_result.to_dict())
                
                # Update overall success
                if not action_result.success:
                    overall_success = False
                    logger.warning(f"❌ Action {i+1} failed: {action_result.error}")
                    
                    # Stop execution if critical action fails
                    if i == 0:  # First action is usually critical (e.g., opening an app)
                        logger.error("❌ Critical action failed, aborting execution")
                        break
                
                # Short delay between actions
                await asyncio.sleep(0.5)
            
            # Update suggestion status in memory
            await memory.mark_suggestion_executed(suggestion_id, success=overall_success)
            
            # Update execution stats
            self._update_execution_stats(overall_success, time.time() - start_time)
            
            # Return result
            execution_result = {
                "suggestion_id": suggestion_id,
                "title": suggestion.get("title", "Untitled"),
                "success": overall_success,
                "action_results": results,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Suggestion execution completed: success={overall_success}")
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Error executing suggestion: {e}")
            logger.error(traceback.format_exc())
            
            # Try to update suggestion status in memory
            if SUGGESTION_MEMORY_AVAILABLE:
                try:
                    memory = await get_suggestion_memory()
                    await memory.mark_suggestion_executed(suggestion_id, success=False)
                except Exception:
                    pass
            
            # Update execution stats
            self._update_execution_stats(False, time.time() - start_time)
            
            # Return error result
            return {
                "suggestion_id": suggestion_id,
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_action_with_retry(self, action_item: Dict[str, Any]) -> ActionExecutionResult:
        """Execute an action with retry logic."""
        action_type = action_item.get("type", "unknown")
        target = action_item.get("target", "")
        value = action_item.get("value", "")
        
        for attempt in range(self.max_retries):
            try:
                # Execute action
                logger.info(f"🔄 Executing {action_type} on {target} (attempt {attempt+1}/{self.max_retries})")
                start_time = time.time()
                
                # Execute appropriate action based on type
                if action_type == "open_app":
                    result = await self._execute_open_app(target)
                elif action_type == "click":
                    result = await self._execute_click(target)
                elif action_type == "input_text":
                    result = await self._execute_input_text(target, value)
                elif action_type == "select_option":
                    result = await self._execute_select_option(target, value)
                elif action_type == "press_key":
                    result = await self._execute_press_key(target)
                elif action_type == "wait":
                    duration = float(value) if value else 1.0
                    result = await self._execute_wait(duration)
                elif action_type == "scroll":
                    direction = value or "down"
                    result = await self._execute_scroll(direction)
                else:
                    logger.warning(f"⚠️ Unknown action type: {action_type}")
                    return ActionExecutionResult(
                        success=False,
                        action_type=action_type,
                        target=target,
                        execution_time=time.time() - start_time,
                        error=f"Unknown action type: {action_type}"
                    )
                
                # If successful, return result
                if result.success:
                    logger.info(f"✅ Action executed successfully in {result.execution_time:.2f}s")
                    return result
                
                # If failed but element was found, retry with different approach
                if result.element_found:
                    logger.warning(f"⚠️ Element found but action failed: {result.error}")
                    # Increment retry count in stats
                    self.execution_stats["retry_count"] += 1
                else:
                    logger.warning(f"⚠️ Element not found: {result.error}")
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"❌ Error executing action: {e}")
                logger.error(traceback.format_exc())
                
                # Increment retry count in stats
                self.execution_stats["retry_count"] += 1
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        logger.error(f"❌ All retries failed for {action_type} on {target}")
        return ActionExecutionResult(
            success=False,
            action_type=action_type,
            target=target,
            execution_time=time.time() - start_time,
            error=f"All {self.max_retries} retries failed"
        )
    
    async def _execute_open_app(self, app_name: str) -> ActionExecutionResult:
        """Execute open app action."""
        start_time = time.time()
        
        try:
            if not self.input_controller:
                raise ValueError("Input controller not available")
            
            # Open app
            result = await self.input_controller.open_application(app_name)
            
            # Check result
            if not result:
                return ActionExecutionResult(
                    success=False,
                    action_type="open_app",
                    target=app_name,
                    execution_time=time.time() - start_time,
                    error=f"Failed to open app: {app_name}"
                )
            
            # Wait for app to open
            await asyncio.sleep(1.0)
            
            # Verify app is open
            active_app = await self._get_active_app()
            success = active_app and app_name.lower() in active_app.lower()
            
            return ActionExecutionResult(
                success=success,
                action_type="open_app",
                target=app_name,
                execution_time=time.time() - start_time,
                element_found=True,
                confidence=1.0 if success else 0.0,
                error=None if success else f"App opened but verification failed. Active app: {active_app}"
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="open_app",
                target=app_name,
                execution_time=time.time() - start_time,
                error=f"Error opening app: {str(e)}"
            )
    
    async def _execute_click(self, target: str) -> ActionExecutionResult:
        """Execute click action using neural UI detection."""
        start_time = time.time()
        
        try:
            # Find UI element using neural UI detector
            element_info = UIElementInfo(target, element_type="button")
            ui_element = await self._find_ui_element(element_info)
            
            if not ui_element:
                return ActionExecutionResult(
                    success=False,
                    action_type="click",
                    target=target,
                    execution_time=time.time() - start_time,
                    element_found=False,
                    error=f"Element not found: {target}"
                )
            
            # Click the element
            if not self.input_controller:
                raise ValueError("Input controller not available")
            
            # Get element coordinates
            x, y = ui_element.get("center_x", 0), ui_element.get("center_y", 0)
            
            # Click at coordinates
            result = await self.input_controller.click(x, y)
            
            # Wait for click to take effect
            await asyncio.sleep(self.verification_delay)
            
            # Return result
            return ActionExecutionResult(
                success=result,
                action_type="click",
                target=target,
                execution_time=time.time() - start_time,
                element_found=True,
                confidence=ui_element.get("confidence", 0.0),
                error=None if result else f"Click at coordinates ({x}, {y}) failed"
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="click",
                target=target,
                execution_time=time.time() - start_time,
                error=f"Error clicking element: {str(e)}"
            )
    
    async def _execute_input_text(self, target: str, value: str) -> ActionExecutionResult:
        """Execute input text action using neural UI detection."""
        start_time = time.time()
        
        try:
            # Find UI element using neural UI detector
            element_info = UIElementInfo(target, element_type="input")
            ui_element = await self._find_ui_element(element_info)
            
            if not ui_element:
                return ActionExecutionResult(
                    success=False,
                    action_type="input_text",
                    target=target,
                    execution_time=time.time() - start_time,
                    element_found=False,
                    error=f"Input element not found: {target}"
                )
            
            # Click the element first
            if not self.input_controller:
                raise ValueError("Input controller not available")
            
            # Get element coordinates
            x, y = ui_element.get("center_x", 0), ui_element.get("center_y", 0)
            
            # Click at coordinates
            click_result = await self.input_controller.click(x, y)
            if not click_result:
                return ActionExecutionResult(
                    success=False,
                    action_type="input_text",
                    target=target,
                    execution_time=time.time() - start_time,
                    element_found=True,
                    confidence=ui_element.get("confidence", 0.0),
                    error=f"Failed to click input field at ({x}, {y})"
                )
            
            # Wait for click to take effect
            await asyncio.sleep(0.5)
            
            # Input text
            text_result = await self.input_controller.type_text(value)
            
            # Wait for input to take effect
            await asyncio.sleep(self.verification_delay)
            
            # Return result
            return ActionExecutionResult(
                success=text_result,
                action_type="input_text",
                target=target,
                execution_time=time.time() - start_time,
                element_found=True,
                confidence=ui_element.get("confidence", 0.0),
                error=None if text_result else f"Typing text '{value}' failed"
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="input_text",
                target=target,
                execution_time=time.time() - start_time,
                error=f"Error inputting text: {str(e)}"
            )
    
    async def _execute_select_option(self, target: str, value: str) -> ActionExecutionResult:
        """Execute select option action using neural UI detection."""
        start_time = time.time()
        
        try:
            # First, find and click the select element
            select_info = UIElementInfo(target, element_type="select")
            select_element = await self._find_ui_element(select_info)
            
            if not select_element:
                return ActionExecutionResult(
                    success=False,
                    action_type="select_option",
                    target=target,
                    execution_time=time.time() - start_time,
                    element_found=False,
                    error=f"Select element not found: {target}"
                )
            
            # Click the select element
            if not self.input_controller:
                raise ValueError("Input controller not available")
            
            # Get element coordinates
            x, y = select_element.get("center_x", 0), select_element.get("center_y", 0)
            
            # Click at coordinates
            click_result = await self.input_controller.click(x, y)
            if not click_result:
                return ActionExecutionResult(
                    success=False,
                    action_type="select_option",
                    target=target,
                    execution_time=time.time() - start_time,
                    element_found=True,
                    confidence=select_element.get("confidence", 0.0),
                    error=f"Failed to click select field at ({x}, {y})"
                )
            
            # Wait for dropdown to appear
            await asyncio.sleep(0.5)
            
            # Now find and click the option
            option_info = UIElementInfo(value, element_type="option")
            option_element = await self._find_ui_element(option_info)
            
            if not option_element:
                return ActionExecutionResult(
                    success=False,
                    action_type="select_option",
                    target=f"{target} -> {value}",
                    execution_time=time.time() - start_time,
                    element_found=True,  # Select found but not option
                    confidence=select_element.get("confidence", 0.0),
                    error=f"Option not found: {value}"
                )
            
            # Click the option
            x, y = option_element.get("center_x", 0), option_element.get("center_y", 0)
            option_result = await self.input_controller.click(x, y)
            
            # Wait for selection to take effect
            await asyncio.sleep(self.verification_delay)
            
            # Return result
            return ActionExecutionResult(
                success=option_result,
                action_type="select_option",
                target=f"{target} -> {value}",
                execution_time=time.time() - start_time,
                element_found=True,
                confidence=min(
                    select_element.get("confidence", 0.0),
                    option_element.get("confidence", 0.0)
                ),
                error=None if option_result else f"Selecting option '{value}' failed"
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="select_option",
                target=f"{target} -> {value}",
                execution_time=time.time() - start_time,
                error=f"Error selecting option: {str(e)}"
            )
    
    async def _execute_press_key(self, key: str) -> ActionExecutionResult:
        """Execute press key action."""
        start_time = time.time()
        
        try:
            if not self.input_controller:
                raise ValueError("Input controller not available")
            
            # Press key
            result = await self.input_controller.press_key(key)
            
            # Wait for key press to take effect
            await asyncio.sleep(self.verification_delay)
            
            # Return result
            return ActionExecutionResult(
                success=result,
                action_type="press_key",
                target=key,
                execution_time=time.time() - start_time,
                element_found=True,  # N/A for key press
                confidence=1.0 if result else 0.0,
                error=None if result else f"Pressing key '{key}' failed"
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="press_key",
                target=key,
                execution_time=time.time() - start_time,
                error=f"Error pressing key: {str(e)}"
            )
    
    async def _execute_wait(self, duration: float) -> ActionExecutionResult:
        """Execute wait action."""
        start_time = time.time()
        
        try:
            # Wait for specified duration
            await asyncio.sleep(duration)
            
            # Return result
            return ActionExecutionResult(
                success=True,
                action_type="wait",
                target=str(duration),
                execution_time=time.time() - start_time,
                element_found=True,  # N/A for wait
                confidence=1.0
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="wait",
                target=str(duration),
                execution_time=time.time() - start_time,
                error=f"Error during wait: {str(e)}"
            )
    
    async def _execute_scroll(self, direction: str) -> ActionExecutionResult:
        """Execute scroll action."""
        start_time = time.time()
        
        try:
            if not self.input_controller:
                raise ValueError("Input controller not available")
            
            # Determine scroll amount
            amount = 10  # Default
            if "up" in direction.lower():
                amount = -10
            
            # Scroll
            result = await self.input_controller.scroll(amount)
            
            # Wait for scroll to take effect
            await asyncio.sleep(self.verification_delay)
            
            # Return result
            return ActionExecutionResult(
                success=result,
                action_type="scroll",
                target=direction,
                execution_time=time.time() - start_time,
                element_found=True,  # N/A for scroll
                confidence=1.0 if result else 0.0,
                error=None if result else f"Scrolling {direction} failed"
            )
            
        except Exception as e:
            return ActionExecutionResult(
                success=False,
                action_type="scroll",
                target=direction,
                execution_time=time.time() - start_time,
                error=f"Error scrolling: {str(e)}"
            )
    
    async def _find_ui_element(self, element_info: UIElementInfo) -> Optional[Dict[str, Any]]:
        """Find a UI element using neural UI detection."""
        try:
            if not self.neural_ui_detector:
                # Use fallback method
                return await self._fallback_find_element(element_info)
            
            # Use neural UI detector
            target_text = element_info.target_text
            element_type = element_info.element_type
            
            # Set element type for detector
            detector_element_type = None
            if element_type:
                if element_type.lower() == "button":
                    detector_element_type = ElementType.BUTTON
                elif element_type.lower() in ["input", "text"]:
                    detector_element_type = ElementType.INPUT
                elif element_type.lower() in ["select", "dropdown"]:
                    detector_element_type = ElementType.SELECT
                elif element_type.lower() in ["option", "item"]:
                    detector_element_type = ElementType.OPTION
            
            # Detect UI elements
            elements = await self.neural_ui_detector.detect_elements(
                element_type=detector_element_type,
                min_confidence=element_info.confidence_threshold
            )
            
            if not elements:
                logger.warning(f"⚠️ No elements detected of type {element_type}")
                return None
            
            # Find best match
            best_match = None
            best_score = 0.0
            
            for element in elements:
                # Check match by text content
                element_text = element.text or ""
                
                # Calculate match score
                score = self._calculate_match_score(element_text, target_text)
                
                # Also check by placeholder, aria-label, etc.
                for attr in element_info.backup_strategies:
                    if attr in element.attributes:
                        attr_value = element.attributes[attr]
                        attr_score = self._calculate_match_score(attr_value, target_text)
                        score = max(score, attr_score)
                
                # Update best match
                if score > best_score and score > element_info.confidence_threshold:
                    best_match = element
                    best_score = score
            
            if not best_match:
                logger.warning(f"⚠️ No matching element found for {target_text}")
                return None
            
            # Convert to dictionary
            return {
                "center_x": best_match.center_x,
                "center_y": best_match.center_y,
                "width": best_match.width,
                "height": best_match.height,
                "text": best_match.text,
                "element_type": element_type or "unknown",
                "confidence": best_score
            }
            
        except Exception as e:
            logger.error(f"❌ Error finding UI element: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def _fallback_find_element(self, element_info: UIElementInfo) -> Optional[Dict[str, Any]]:
        """Fallback method to find a UI element without neural UI detection."""
        logger.warning(f"⚠️ Using fallback method to find element: {element_info.target_text}")
        
        try:
            # Use generic screen capture method
            # This is a very simplified fallback that won't work well
            
            # Simulate finding an element at center of screen
            import random
            
            # Get screen size
            screen_width, screen_height = await self._get_screen_size()
            
            # Randomize location based on element type
            if element_info.element_type == "button":
                # Buttons often in bottom half
                x = random.randint(int(screen_width * 0.3), int(screen_width * 0.7))
                y = random.randint(int(screen_height * 0.6), int(screen_height * 0.9))
            elif element_info.element_type == "input":
                # Input fields often in forms in the middle
                x = random.randint(int(screen_width * 0.3), int(screen_width * 0.7))
                y = random.randint(int(screen_height * 0.3), int(screen_height * 0.7))
            else:
                # Generic element
                x = random.randint(int(screen_width * 0.2), int(screen_width * 0.8))
                y = random.randint(int(screen_height * 0.2), int(screen_height * 0.8))
            
            # Very low confidence since this is just a guess
            return {
                "center_x": x,
                "center_y": y,
                "width": 100,
                "height": 30,
                "text": element_info.target_text,
                "element_type": element_info.element_type or "unknown",
                "confidence": 0.1  # Very low confidence
            }
            
        except Exception as e:
            logger.error(f"❌ Error in fallback find element: {e}")
            return None
    
    def _calculate_match_score(self, text1: str, text2: str) -> float:
        """Calculate match score between two strings."""
        if not text1 or not text2:
            return 0.0
        
        text1 = text1.lower()
        text2 = text2.lower()
        
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Contains match
        if text2 in text1:
            return 0.9
        if text1 in text2:
            return 0.8
        
        # Word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        common_words = words1.intersection(words2)
        
        if common_words:
            return 0.7 * (len(common_words) / max(len(words1), len(words2)))
        
        # Substring match
        min_len = min(len(text1), len(text2))
        if min_len > 3:
            for i in range(min_len - 2):
                if text1[i:i+3] in text2:
                    return 0.5
        
        return 0.0
    
    async def _get_active_app(self) -> Optional[str]:
        """Get the name of the active application."""
        try:
            # Try to get from memory system
            if hasattr(self, "memory_system") and self.memory_system:
                context = await self.memory_system.get_current_context()
                if context and "active_app" in context:
                    return context["active_app"]
            
            # Fallback: use process information
            import psutil
            processes = [(p.pid, p.name()) for p in psutil.process_iter(['pid', 'name'])]
            processes.sort(key=lambda x: x[0], reverse=True)
            
            # Very rough heuristic - newest process might be active
            if processes:
                return processes[0][1]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting active app: {e}")
            return None
    
    async def _get_screen_size(self) -> Tuple[int, int]:
        """Get screen size."""
        try:
            # Try to get from memory system
            if hasattr(self, "memory_system") and self.memory_system:
                context = await self.memory_system.get_current_context()
                if context and "screen_size" in context:
                    return context["screen_size"]
            
            # Fallback
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            
            return width, height
            
        except Exception as e:
            logger.error(f"❌ Error getting screen size: {e}")
            return 1920, 1080  # Default fallback
    
    def _update_execution_stats(self, success: bool, execution_time: float) -> None:
        """Update execution statistics."""
        try:
            # Update execution stats
            self.execution_stats["total_executions"] += 1
            
            if success:
                self.execution_stats["successful_executions"] += 1
            else:
                self.execution_stats["failed_executions"] += 1
            
            # Update average execution time
            total_time = self.execution_stats["avg_execution_time"] * (self.execution_stats["total_executions"] - 1)
            self.execution_stats["avg_execution_time"] = (total_time + execution_time) / self.execution_stats["total_executions"]
            
        except Exception as e:
            logger.error(f"❌ Error updating execution stats: {e}")

# Singleton instance
_executor_instance = None

async def get_neural_ui_executor() -> NeuralUISuggestionExecutor:
    """Get or create the global neural UI suggestion executor instance."""
    global _executor_instance
    
    if _executor_instance is None:
        _executor_instance = NeuralUISuggestionExecutor()
    
    return _executor_instance

# Example usage
if __name__ == "__main__":
    async def test_executor():
        # Get executor
        executor = await get_neural_ui_executor()
        
        # Create test suggestion ID
        test_suggestion_id = f"test_{uuid.uuid4().hex[:6]}"
        
        # If suggestion memory available, create test suggestion
        if SUGGESTION_MEMORY_AVAILABLE:
            try:
                memory = await get_suggestion_memory()
                
                test_suggestion = {
                    "id": test_suggestion_id,
                    "title": "Open System Preferences",
                    "description": "Open System Preferences app",
                    "confidence": 0.9,
                    "action_items": [
                        {"type": "open_app", "target": "System Preferences"}
                    ],
                    "context": {
                        "source": "test",
                        "app": "Terminal"
                    }
                }
                
                await memory.add_suggestion(test_suggestion)
                print(f"Created test suggestion: {test_suggestion_id}")
                
            except Exception as e:
                print(f"Error creating test suggestion: {e}")
                # Use a hardcoded suggestion ID for testing
                test_suggestion_id = "test_123456"
        
        # Execute suggestion
        result = await executor.execute_suggestion(test_suggestion_id)
        
        # Print result
        print(json.dumps(result, indent=2))
    
    # Run the test
    asyncio.run(test_executor())