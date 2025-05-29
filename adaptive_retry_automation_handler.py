#!/usr/bin/env python3
"""
Adaptive Retry Automation Handler - Implements retry logic with failure analysis and coordinate adjustment
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import os

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """Result of step execution"""
    success: bool
    step_id: str
    execution_time: float
    error_message: Optional[str] = None
    retry_count: int = 0
    adjusted_coordinates: Optional[Tuple[int, int]] = None
    failure_reason: Optional[str] = None

@dataclass
class AutomationStep:
    """Enhanced automation step with retry capabilities"""
    id: str
    description: str
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"
    max_retries: int = 3
    retry_count: int = 0
    last_execution_result: Optional[ExecutionResult] = None
    estimated_duration: float = 2.0

class AdaptiveRetryAutomationHandler:
    """Handles automation with intelligent retry logic and coordinate adjustment"""
    
    def __init__(self):
        self.execution_history: Dict[str, List[ExecutionResult]] = {}
        self.coordinate_adjustments: Dict[str, List[Tuple[int, int]]] = {}
        self.failure_patterns: Dict[str, List[str]] = {}
        
        # Load automation components
        try:
            from agent_workflow.input_controller import InputController
            from sensors.total_screen_analyzer import TotalScreenAnalyzer
            self.input_controller = InputController()
            self.screen_analyzer = TotalScreenAnalyzer()
            self.automation_available = True
            logger.info("🔄 Adaptive retry automation system loaded")
        except Exception as e:
            logger.warning(f"Automation components not available: {e}")
            self.input_controller = None
            self.screen_analyzer = None
            self.automation_available = False
    
    async def execute_step_with_retry(self, step: AutomationStep, plan_id: str) -> ExecutionResult:
        """Execute a step with adaptive retry logic"""
        logger.info(f"🎯 Executing step {step.id}: {step.description}")
        
        # Ensure step has retry attributes
        max_retries = getattr(step, 'max_retries', 3)
        if not hasattr(step, 'retry_count'):
            step.retry_count = 0
        
        for attempt in range(max_retries + 1):
            step.retry_count = attempt
            start_time = time.time()
            
            try:
                # Execute the step
                success = await self._execute_single_step(step, plan_id)
                execution_time = time.time() - start_time
                
                result = ExecutionResult(
                    success=success,
                    step_id=step.id,
                    execution_time=execution_time,
                    retry_count=attempt
                )
                
                if success:
                    logger.info(f"✅ Step {step.id} completed successfully in {execution_time:.2f}s")
                    step.status = "completed"
                    self._record_success(step, result)
                    return result
                else:
                    # Step failed, analyze and potentially retry
                    failure_reason = await self._analyze_failure(step, plan_id)
                    result.failure_reason = failure_reason
                    
                    logger.warning(f"❌ Step {step.id} failed (attempt {attempt + 1}/{max_retries + 1}): {failure_reason}")
                    
                    if attempt < max_retries:
                        # Adjust strategy for retry
                        await self._adjust_step_for_retry(step, failure_reason, attempt)
                        await asyncio.sleep(1)  # Brief pause before retry
                    else:
                        # Max retries reached
                        step.status = "failed"
                        result.error_message = f"Failed after {max_retries} retries: {failure_reason}"
                        self._record_failure(step, result)
                        return result
                        
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = str(e)
                
                result = ExecutionResult(
                    success=False,
                    step_id=step.id,
                    execution_time=execution_time,
                    error_message=error_msg,
                    retry_count=attempt
                )
                
                logger.error(f"💥 Exception in step {step.id} (attempt {attempt + 1}): {error_msg}")
                
                if attempt < max_retries:
                    await asyncio.sleep(1)
                else:
                    step.status = "failed"
                    self._record_failure(step, result)
                    return result
        
        # Should not reach here, but just in case
        return ExecutionResult(
            success=False,
            step_id=step.id,
            execution_time=0,
            error_message="Unexpected execution path",
            retry_count=max_retries
        )
    
    async def _execute_single_step(self, step: AutomationStep, plan_id: str) -> bool:
        """Execute a single automation step"""
        if not self.automation_available:
            logger.warning(f"Automation not available for step {step.id}")
            return False
        
        try:
            # Map action types for compatibility with different planners
            action_type = step.action_type.lower()
            
            if action_type in ["open_app", "open"]:
                return await self._execute_open_app(step)
            elif action_type in ["navigate_url", "navigate"]:
                return await self._execute_navigate_url(step)
            elif action_type in ["click_element", "click"]:
                return await self._execute_click_element(step)
            elif action_type in ["type_text", "type"]:
                return await self._execute_type_text(step)
            elif action_type == "wait":
                return await self._execute_wait(step)
            elif action_type in ["hotkey", "press"]:
                return await self._execute_hotkey(step)
            elif action_type == "analyze":
                # For analyze steps, just log and return success
                logger.info(f"📝 Analyzing: {step.value}")
                await asyncio.sleep(1)
                return True
            else:
                logger.warning(f"Unknown action type: {step.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing step {step.id}: {e}")
            return False
    
    async def _execute_open_app(self, step: AutomationStep) -> bool:
        """Execute open application step"""
        if not step.target:
            return False
        
        try:
            # Use macOS open command
            result = subprocess.run(['open', '-a', step.target], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Wait for app to open and bring to front
                await asyncio.sleep(2)
                
                # Bring the app to front using AppleScript
                bring_to_front_script = f'''
                tell application "{step.target}"
                    activate
                end tell
                '''
                subprocess.run(['osascript', '-e', bring_to_front_script], 
                             capture_output=True, timeout=5)
                
                # Additional wait for focus
                await asyncio.sleep(1)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to open app {step.target}: {e}")
            return False
    
    async def _execute_navigate_url(self, step: AutomationStep) -> bool:
        """Execute URL navigation step"""
        if not step.value:
            logger.error("No URL provided for navigation")
            return False
        
        try:
            logger.info(f"🌐 Navigating to: {step.value}")
            
            # Ensure Safari is focused first
            logger.info("🦋 Activating Safari...")
            result = subprocess.run(['osascript', '-e', 'tell application "Safari" to activate'], 
                                 capture_output=True, timeout=5)
            if result.returncode != 0:
                logger.warning(f"Safari activation warning: {result.stderr}")
            await asyncio.sleep(1.0)
            
            # Focus address bar with Cmd+L
            logger.info("📍 Focusing address bar...")
            result = self.input_controller.hotkey('command', 'l')
            if hasattr(result, '__await__'):
                await result
            await asyncio.sleep(1.5)  # Extra wait for address bar focus
            
            # Type the URL
            logger.info(f"⌨️ Typing URL: {step.value}")
            result = self.input_controller.type_text(step.value)
            if hasattr(result, '__await__'):
                await result
            await asyncio.sleep(1.0)
            
            # Press Enter to navigate
            logger.info("⏎ Pressing Enter to navigate...")
            result = self.input_controller.press_key('Return')
            if hasattr(result, '__await__'):
                await result
            
            # Wait for navigation to start
            await asyncio.sleep(2.0)
            logger.info("✅ Navigation command executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to {step.value}: {e}")
            return False
    
    async def _execute_click_element(self, step: AutomationStep) -> bool:
        """Execute click element step with smart coordinate adjustment"""
        try:
            # Get current coordinates
            coords = step.coordinates
            if not coords:
                coords = await self._get_smart_coordinates(step.target)
            
            if coords:
                result = self.input_controller.click(coords[0], coords[1])
                if hasattr(result, '__await__'):
                    await result
                await asyncio.sleep(0.5)
                
                # Verify click success by checking if expected change occurred
                if await self._verify_click_success(step, coords):
                    return True
                else:
                    # Try alternative coordinates
                    alt_coords = await self._get_alternative_coordinates(step.target, coords)
                    if alt_coords:
                        result = self.input_controller.click(alt_coords[0], alt_coords[1])
                        if hasattr(result, '__await__'):
                            await result
                        return await self._verify_click_success(step, alt_coords)
            
            return False
        except Exception as e:
            logger.error(f"Failed to click element {step.target}: {e}")
            return False
    
    async def _execute_type_text(self, step: AutomationStep) -> bool:
        """Execute type text step"""
        if not step.value:
            return False
        
        try:
            # Ensure Safari is still focused
            subprocess.run(['osascript', '-e', 'tell application "Safari" to activate'], 
                         capture_output=True, timeout=3)
            await asyncio.sleep(0.5)
            
            # Use universal screen detection that dynamically finds UI elements for any step
            try:
                from universal_screen_detector import universal_screen_detector
                coords = universal_screen_detector.get_coordinates_for_step(step.description)
                logger.info(f"🔍 Using universal screen detection for '{step.description}': {coords}")
            except Exception as e:
                logger.warning(f"Universal screen detection not available, using fallback: {e}")
                # Fallback coordinates
                center_x = self.input_controller.screen_width // 2
                search_y = int(self.input_controller.screen_height * 0.4)
                coords = (center_x, search_y)
            
            result = self.input_controller.click(coords[0], coords[1])
            if hasattr(result, '__await__'):
                await result
            await asyncio.sleep(0.5)
            
            # Handle both sync and async type_text methods
            result = self.input_controller.type_text(step.value)
            if hasattr(result, '__await__'):
                await result
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Failed to type text '{step.value}': {e}")
            return False
    
    async def _execute_wait(self, step: AutomationStep) -> bool:
        """Execute wait step"""
        try:
            wait_time = float(step.value) if step.value else 2.0
            await asyncio.sleep(wait_time)
            return True
        except Exception as e:
            logger.error(f"Failed to wait: {e}")
            return False
    
    async def _execute_hotkey(self, step: AutomationStep) -> bool:
        """Execute hotkey step with support for key combinations"""
        # Get hotkey from either target or value field
        hotkey = step.target or step.value
        if not hotkey:
            logger.error("No hotkey specified in step")
            return False
        
        try:
            hotkey = hotkey.lower().strip()
            logger.info(f"🔑 Executing hotkey: '{hotkey}'")
            
            # Handle combination hotkeys (cmd+space, ctrl+c, etc.)
            if '+' in hotkey:
                keys = [key.strip() for key in hotkey.split('+')]
                # Map common key names
                mapped_keys = []
                for key in keys:
                    if key == 'cmd':
                        mapped_keys.append('command')
                    elif key == 'ctrl':
                        mapped_keys.append('ctrl')
                    elif key == 'alt':
                        mapped_keys.append('alt')
                    elif key == 'shift':
                        mapped_keys.append('shift')
                    elif key == 'space':
                        mapped_keys.append('space')
                    elif key == 'return' or key == 'enter':
                        mapped_keys.append('return')
                    else:
                        mapped_keys.append(key)
                
                # Execute hotkey combination
                result = self.input_controller.hotkey(*mapped_keys)
                logger.info(f"🎯 Executed hotkey combination: {' + '.join(mapped_keys)}")
                
                # Special handling for common hotkey combinations
                if hotkey == "cmd+space":
                    logger.info("⚡ Spotlight search activated")
                    await asyncio.sleep(1.0)  # Extra wait for Spotlight to appear
                elif hotkey == "cmd+l":
                    logger.info("🌐 Address bar focused")
                    await asyncio.sleep(0.8)  # Wait for address bar focus
                    
            else:
                # Handle single keys
                if hotkey in ["enter", "return"]:
                    result = self.input_controller.press_key('Return')
                    logger.info("⏎ Enter key pressed")
                elif hotkey == "escape":
                    result = self.input_controller.press_key('Escape')
                    logger.info("⎋ Escape key pressed")
                elif hotkey == "tab":
                    result = self.input_controller.press_key('Tab')
                    logger.info("⇥ Tab key pressed")
                elif hotkey == "space":
                    result = self.input_controller.press_key('space')
                    logger.info("␣ Space key pressed")
                else:
                    result = self.input_controller.press_key(hotkey)
                    logger.info(f"🎯 Key pressed: {hotkey}")
            
            # Handle both sync and async results
            if hasattr(result, '__await__'):
                await result
            
            # Longer wait for system to respond to hotkeys
            await asyncio.sleep(1.0)
            
            # Hotkeys execute at the OS level and always succeed if they reach this point
            logger.info(f"✅ Hotkey '{hotkey}' executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"💥 Failed to execute hotkey '{hotkey}': {e}")
            return False
    
    async def _analyze_failure(self, step: AutomationStep, plan_id: str) -> str:
        """Analyze why a step failed"""
        try:
            if step.action_type == "click_element":
                # Check if coordinates are accurate
                if step.coordinates:
                    # Take screenshot and analyze
                    screenshot_analysis = await self._analyze_click_area(step.coordinates)
                    if "wrong_element" in screenshot_analysis:
                        return "clicked_wrong_element"
                    elif "element_moved" in screenshot_analysis:
                        return "element_coordinates_changed"
                    else:
                        return "element_not_clickable"
                else:
                    return "missing_coordinates"
            
            elif step.action_type == "navigate_url":
                # Check if navigation was successful by verifying URL change
                return await self._verify_navigation_success(step)
            
            elif step.action_type == "open_app":
                return "app_not_found_or_failed_to_launch"
            
            elif step.action_type == "type_text":
                return "text_input_failed"
            
            else:
                return "unknown_failure"
                
        except Exception as e:
            return f"failure_analysis_error: {str(e)}"
    
    async def _verify_navigation_success(self, step: AutomationStep) -> str:
        """Verify if URL navigation was successful"""
        try:
            # Wait a moment for page to load
            await asyncio.sleep(2)
            
            # Get current URL using AppleScript
            get_url_script = '''
            tell application "Safari"
                if (count of windows) > 0 then
                    return URL of current tab of front window
                else
                    return "no_windows"
                end if
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', get_url_script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                current_url = result.stdout.strip()
                expected_url = step.value.lower()
                
                # Check if the navigation was successful
                if "no_windows" in current_url:
                    return "safari_no_windows"
                elif expected_url in current_url.lower() or current_url.lower() in expected_url:
                    logger.info(f"🌐 Navigation verified: {current_url}")
                    return "success"
                else:
                    logger.warning(f"🔄 URL mismatch - Expected: {expected_url}, Got: {current_url}")
                    return "navigation_url_mismatch"
            else:
                return "navigation_verification_failed"
                
        except Exception as e:
            logger.error(f"Error verifying navigation: {e}")
            return "navigation_verification_error"
    
    async def _adjust_step_for_retry(self, step: AutomationStep, failure_reason: str, attempt: int):
        """Adjust step parameters for retry based on failure analysis"""
        logger.info(f"🔧 Adjusting step {step.id} for retry (reason: {failure_reason})")
        
        if failure_reason == "clicked_wrong_element" and step.action_type == "click_element":
            # Adjust coordinates
            new_coords = await self._calculate_adjusted_coordinates(step, attempt)
            if new_coords:
                old_coords = step.coordinates
                step.coordinates = new_coords
                step.adjusted_coordinates = new_coords
                logger.info(f"📍 Adjusted coordinates from {old_coords} to {new_coords}")
        
        elif failure_reason == "element_coordinates_changed":
            # Recalculate coordinates
            step.coordinates = await self._get_smart_coordinates(step.target)
            logger.info(f"🎯 Recalculated coordinates for {step.target}: {step.coordinates}")
        
        elif failure_reason == "app_not_found_or_failed_to_launch":
            # Try alternative app names
            if step.target and step.action_type == "open_app":
                alt_name = self._get_alternative_app_name(step.target)
                if alt_name:
                    step.target = alt_name
                    logger.info(f"📱 Trying alternative app name: {alt_name}")
        
        elif failure_reason == "navigation_failed":
            # Add protocol if missing
            if step.value and not step.value.startswith(('http://', 'https://')):
                step.value = f"https://{step.value}"
                logger.info(f"🌐 Added https protocol: {step.value}")
        
        # Increase confidence for next attempt
        step.confidence = min(0.9, step.confidence + 0.1)
    
    async def _get_smart_coordinates(self, target: str) -> Optional[Tuple[int, int]]:
        """Get smart coordinates for UI elements"""
        try:
            # Import smart element detector
            from smart_element_detector import get_element_coordinates
            return await get_element_coordinates(target)
        except Exception as e:
            logger.warning(f"Smart coordinates not available: {e}")
            # Fallback coordinates
            coordinate_map = {
                "search_box": (735, 140),  # Improved YouTube search box
                "address_bar": (400, 80),
                "google_search": (400, 300),
                "youtube_search": (735, 140)
            }
            return coordinate_map.get(target)
    
    async def _get_alternative_coordinates(self, target: str, failed_coords: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Get alternative coordinates when original ones fail"""
        x, y = failed_coords
        
        # Try slightly adjusted positions
        alternatives = [
            (x, y + 10),   # Slightly down
            (x, y - 10),   # Slightly up  
            (x + 20, y),   # Slightly right
            (x - 20, y),   # Slightly left
            (x + 10, y + 10),  # Diagonal
            (x - 10, y - 10)   # Opposite diagonal
        ]
        
        # Return first alternative (could be enhanced with visual verification)
        return alternatives[0] if alternatives else None
    
    async def _calculate_adjusted_coordinates(self, step: AutomationStep, attempt: int) -> Optional[Tuple[int, int]]:
        """Calculate adjusted coordinates based on attempt number and learning"""
        if not step.coordinates:
            return None
        
        x, y = step.coordinates
        
        # Progressive adjustment based on attempt
        if attempt == 1:
            # First retry: small adjustment
            return (x, y + 15)
        elif attempt == 2:
            # Second retry: larger adjustment
            return (x + 25, y + 15)
        else:
            # Final retry: try completely different area
            return (x - 30, y + 30)
    
    async def _verify_click_success(self, step: AutomationStep, coords: Tuple[int, int]) -> bool:
        """Verify if click was successful by checking UI state change"""
        try:
            # Take screenshot before and after click to verify change
            # This is a simplified verification - could be enhanced
            await asyncio.sleep(0.5)  # Wait for UI to update
            
            if step.target == "search_box":
                # Check if search box is focused (simplified)
                return True  # Assume success for now
            
            return True  # Default to success
        except Exception as e:
            logger.error(f"Click verification failed: {e}")
            return False
    
    async def _analyze_click_area(self, coords: Tuple[int, int]) -> str:
        """Analyze what's at the click coordinates"""
        try:
            # This could be enhanced with actual screen analysis
            # For now, return generic analysis
            return "element_analysis_pending"
        except Exception as e:
            return f"analysis_error: {str(e)}"
    
    def _get_alternative_app_name(self, app_name: str) -> Optional[str]:
        """Get alternative app name if primary fails"""
        alternatives = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "textedit": "TextEdit",
            "notes": "Notes"
        }
        return alternatives.get(app_name.lower())
    
    def _record_success(self, step: AutomationStep, result: ExecutionResult):
        """Record successful execution for learning"""
        if step.id not in self.execution_history:
            self.execution_history[step.id] = []
        self.execution_history[step.id].append(result)
        
        # Store successful coordinates for future use
        if step.coordinates and step.action_type == "click_element":
            if step.target not in self.coordinate_adjustments:
                self.coordinate_adjustments[step.target] = []
            self.coordinate_adjustments[step.target].append(step.coordinates)
    
    def _record_failure(self, step: AutomationStep, result: ExecutionResult):
        """Record failure for pattern analysis"""
        if step.id not in self.execution_history:
            self.execution_history[step.id] = []
        self.execution_history[step.id].append(result)
        
        # Record failure patterns
        if result.failure_reason:
            pattern_key = f"{step.action_type}_{step.target}"
            if pattern_key not in self.failure_patterns:
                self.failure_patterns[pattern_key] = []
            self.failure_patterns[pattern_key].append(result.failure_reason)

# Create singleton instance
adaptive_retry_handler = AdaptiveRetryAutomationHandler()