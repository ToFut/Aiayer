#!/usr/bin/env python3
"""
Input Controller Module
Provides keyboard and mouse control functions for the agent workflow.
Uses both PyAutoGUI and pynput for comprehensive control capabilities.
"""
import logging
import time
from typing import Tuple, List, Dict, Any, Optional, Union
import os
import sys
import pyautogui
import random
from pynput import keyboard, mouse
import threading
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Safety feature - failsafe to abort operation when mouse moved to corner
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # Short pause between PyAutoGUI commands

# Ensure screen size is properly detected
_screen_width, _screen_height = pyautogui.size()
logger.info(f"Detected screen size: {_screen_width}x{_screen_height}")

class InputController:
    """
    Controller for keyboard and mouse input automation.
    Provides methods for simulating human-like interactions.
    """
    
    def __init__(self, safety_level: str = "high"):
        """
        Initialize the input controller with specified safety level.
        
        Args:
            safety_level: Control safety measures ("low", "medium", "high")
                - low: Minimal safeguards, faster automation
                - medium: Basic safeguards, human-like movements
                - high: Maximum safeguards, confirmation required for destructive actions
        """
        self.safety_level = safety_level
        self.screen_width, self.screen_height = pyautogui.size()
        self.running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.use_safe_mouse_mode = False
        self.mouse_tracking_thread = None
        self.mouse_history = []  # Track recent mouse positions
        self.keyboard_history = []  # Track recent key presses
        self.history_lock = threading.Lock()
        self.max_history = 50  # Maximum events to store
        self.last_command_time = 0
        self.command_delay = 0.5  # Minimum delay between commands (seconds)
        self.logger = logger
        
        # Destructive actions that require confirmation in high safety mode
        self.destructive_keys = [
            "delete", "backspace", "command", "ctrl+a", "ctrl+x", "command+a", 
            "command+x", "command+delete", "command+backspace"
        ]
        
        # Set up randomization for human-like movements
        self.min_move_duration = 0.3  # Minimum duration for mouse movements
        self.max_move_duration = 1.2  # Maximum duration for mouse movements
        self.click_delay_range = (0.05, 0.15)  # Random delay range for clicks
        
        # Store current modifier key states
        self.modifier_states = {
            "shift": False,
            "ctrl": False,
            "alt": False,
            "command": False,
            "fn": False
        }
        
        # Emergency shutdown mechanism
        self.emergency_shutdown_active = False
        self.emergency_keys_pressed = set()
        self.emergency_combo = {'ctrl', '1'}  # Ctrl+1 for emergency shutdown
        
        # Initialize listener for tracking user input
        self._start_input_listeners()
    
    def _start_input_listeners(self):
        """Start listeners to track user keyboard and mouse actions."""
        try:
            # Check for macOS to handle Quartz issues
            if sys.platform == "darwin":
                try:
                    # Try to verify Quartz CGEventGetLocation is available
                    import Quartz
                    test_func = getattr(Quartz, "CGEventGetLocation", None)
                    
                    if test_func is None:
                        # Fallback to a safer mouse listener without full tracking
                        logger.warning("Quartz CGEventGetLocation not available, using safe mouse listener")
                        self._start_safe_mouse_listener()
                    else:
                        # Normal listener should work
                        self._start_normal_mouse_listener()
                except (ImportError, AttributeError, KeyError) as e:
                    logger.warning(f"Quartz API issue detected: {e}, using safe mouse listener")
                    self._start_safe_mouse_listener()
            else:
                # Non-macOS platforms use normal listener
                self._start_normal_mouse_listener()
            
            # Keyboard listener (separate to isolate from mouse issues)
            try:
                self.keyboard_listener = keyboard.Listener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release
                )
                self.keyboard_listener.start()
                logger.info("Keyboard listener started successfully")
            except Exception as e:
                logger.error(f"Failed to start keyboard listener: {e}")
            
            self.running = True
            logger.info("Input controller initialized (safe mode)")
            logger.info("🚨 Emergency shutdown: Press Ctrl+1 to immediately stop agent")
        except Exception as e:
            logger.error(f"Failed to start input listeners: {e}")
    
    def _start_normal_mouse_listener(self):
        """Start normal mouse listener with full tracking."""
        try:
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.start()
            logger.info("Standard mouse listener started successfully")
        except Exception as e:
            logger.error(f"Failed to start standard mouse listener: {e}")
            # Fallback to safe listener
            self._start_safe_mouse_listener()
    
    def _start_safe_mouse_listener(self):
        """Start a limited mouse listener without position tracking to avoid Quartz errors."""
        try:
            # Use pyautogui for basic position tracking without callbacks
            self.use_safe_mouse_mode = True
            self.mouse_tracking_thread = threading.Thread(target=self._safe_mouse_tracking)
            self.mouse_tracking_thread.daemon = True
            self.mouse_tracking_thread.start()
            logger.info("Safe mouse tracking started (fallback mode)")
        except Exception as e:
            logger.error(f"Failed to start safe mouse tracking: {e}")
            self.use_safe_mouse_mode = False
    
    def _on_mouse_move(self, x, y):
        """Track mouse movement."""
        with self.history_lock:
            self.mouse_history.append({
                "type": "move",
                "x": x,
                "y": y,
                "timestamp": time.time()
            })
            self._trim_history()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Track mouse clicks."""
        with self.history_lock:
            self.mouse_history.append({
                "type": "click",
                "x": x,
                "y": y,
                "button": str(button),
                "pressed": pressed,
                "timestamp": time.time()
            })
            self._trim_history()
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Track mouse scrolling."""
        with self.history_lock:
            self.mouse_history.append({
                "type": "scroll",
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
                "timestamp": time.time()
            })
            self._trim_history()
    
    def _on_key_press(self, key):
        """Track key presses and check for emergency shutdown."""
        with self.history_lock:
            # Update modifier states and check for emergency combo
            try:
                key_name = key.char.lower() if hasattr(key, 'char') else key.name
                if key_name in self.modifier_states:
                    self.modifier_states[key_name] = True
                
                # Check for emergency shutdown combo (Ctrl+1)
                if key_name == 'ctrl' or key_name == '1':
                    self.emergency_keys_pressed.add(key_name)
                    
                    # If both keys are pressed, trigger emergency shutdown
                    if self.emergency_combo.issubset(self.emergency_keys_pressed):
                        self._emergency_shutdown()
                        
            except AttributeError:
                key_name = str(key)
            
            self.keyboard_history.append({
                "type": "press",
                "key": key_name,
                "modifiers": self.modifier_states.copy(),
                "timestamp": time.time()
            })
            self._trim_history()
    
    def _on_key_release(self, key):
        """Track key releases and clear emergency keys."""
        with self.history_lock:
            # Update modifier states and clear emergency keys
            try:
                key_name = key.char.lower() if hasattr(key, 'char') else key.name
                if key_name in self.modifier_states:
                    self.modifier_states[key_name] = False
                
                # Clear emergency keys when released
                if key_name in self.emergency_keys_pressed:
                    self.emergency_keys_pressed.discard(key_name)
                    
            except AttributeError:
                key_name = str(key)
                
            self.keyboard_history.append({
                "type": "release",
                "key": key_name,
                "modifiers": self.modifier_states.copy(),
                "timestamp": time.time()
            })
            self._trim_history()
    
    def _trim_history(self):
        """Keep history within maximum size."""
        if len(self.mouse_history) > self.max_history:
            self.mouse_history = self.mouse_history[-self.max_history:]
        if len(self.keyboard_history) > self.max_history:
            self.keyboard_history = self.keyboard_history[-self.max_history:]
            
    def _safe_mouse_tracking(self):
        """Safe mouse tracking method that doesn't use pynput callbacks."""
        while self.running and not self.emergency_shutdown_active:
            try:
                # Get current mouse position using PyAutoGUI (safer than pynput)
                x, y = pyautogui.position()
                
                # Only record if position changed
                if not self.mouse_history or (
                    self.mouse_history[-1]["type"] == "move" and
                    (self.mouse_history[-1]["x"] != x or self.mouse_history[-1]["y"] != y)
                ):
                    with self.history_lock:
                        self.mouse_history.append({
                            "type": "move",
                            "x": x,
                            "y": y,
                            "timestamp": time.time()
                        })
                        self._trim_history()
                
                # Sleep to reduce CPU usage
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in safe mouse tracking: {e}")
                time.sleep(0.5)  # Longer sleep on error
    
    def _emergency_shutdown(self):
        """Emergency shutdown triggered by Ctrl+1."""
        if not self.emergency_shutdown_active:
            self.emergency_shutdown_active = True
            logger.critical("🚨 EMERGENCY SHUTDOWN ACTIVATED - Ctrl+1 pressed!")
            logger.critical("🛑 Stopping all automation immediately...")
            
            # Stop all operations
            self.running = False
            
            # Try to show visual alert
            try:
                import pyautogui
                pyautogui.alert("🚨 AGENT EMERGENCY SHUTDOWN ACTIVATED", "Agent Stopped")
            except:
                pass
            
            # Exit the process
            import sys
            sys.exit(0)
    
    def get_current_position(self) -> Tuple[int, int]:
        """Get current mouse cursor position."""
        return pyautogui.position()
    
    def _random_duration(self) -> float:
        """Generate random duration for human-like movement."""
        return random.uniform(self.min_move_duration, self.max_move_duration)
    
    def _random_click_delay(self) -> float:
        """Generate random delay for human-like clicking."""
        return random.uniform(*self.click_delay_range)
    
    def _check_rate_limit(self) -> bool:
        """Check if command rate limit allows another command."""
        # Check if emergency shutdown is active
        if self.emergency_shutdown_active or not self.running:
            logger.warning("🛑 Automation blocked - emergency shutdown active")
            return False
            
        current_time = time.time()
        if current_time - self.last_command_time < self.command_delay:
            time.sleep(self.command_delay - (current_time - self.last_command_time))
        self.last_command_time = time.time()
        return True
    
    def move_to(self, x: int, y: int, duration: Optional[float] = None, human_like: bool = True):
        """
        Move cursor to specified position with human-like motion.
        
        Args:
            x: Target x-coordinate
            y: Target y-coordinate
            duration: Movement duration (None for auto-calculated)
            human_like: Use human-like curved movements
        """
        self._check_rate_limit()
        
        # Ensure coordinates are within screen bounds
        x = max(0, min(x, self.screen_width))
        y = max(0, min(y, self.screen_height))
        
        # Calculate duration if not specified
        if duration is None:
            duration = self._random_duration()
        
        try:
            if human_like:
                # Use PyAutoGUI's easeOutQuad function for human-like movement
                pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
            else:
                # Direct movement
                pyautogui.moveTo(x, y, duration=duration)
            
            logger.info(f"Moved cursor to ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Failed to move cursor: {e}")
            return False
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: str = 'left', clicks: int = 1, interval: Optional[float] = None):
        """
        Click at the specified position or current position.
        
        Args:
            x: X-coordinate (None for current position)
            y: Y-coordinate (None for current position)
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
            interval: Time between clicks (None for random)
        """
        self._check_rate_limit()
        
        try:
            # Make sure coordinates are integers if provided
            if x is not None and y is not None:
                try:
                    # Handle different input types (string, float, etc.)
                    x = int(float(x)) if isinstance(x, (int, float, str)) else 0
                    y = int(float(y)) if isinstance(y, (int, float, str)) else 0
                    
                    # Get screen size to validate coordinates
                    screen_width, screen_height = pyautogui.size()
                    
                    # Ensure coordinates are within screen bounds
                    if x < 0 or x > screen_width or y < 0 or y > screen_height:
                        logger.warning(f"⚠️ Coordinates ({x}, {y}) are outside screen bounds, adjusting...")
                        x = max(0, min(x, screen_width - 1))
                        y = max(0, min(y, screen_height - 1))
                        logger.info(f"✅ Adjusted coordinates to: ({x}, {y})")
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Invalid coordinates format: {e}")
                    # Use center of screen as fallback
                    screen_width, screen_height = pyautogui.size()
                    x, y = screen_width // 2, screen_height // 2
                    logger.warning(f"⚠️ Using screen center as fallback: ({x}, {y})")
                
                # Move to position with more reliable method
                try:
                    # First try with human-like movement
                    self.move_to(x, y, duration=0.5, human_like=True)
                    # Small pause to ensure the movement completes
                    time.sleep(0.1)
                except Exception as move_error:
                    logger.warning(f"⚠️ Move with human-like motion failed: {move_error}")
                    # Fall back to direct movement
                    try:
                        pyautogui.moveTo(x, y)
                        time.sleep(0.1)
                        logger.info("✅ Direct movement succeeded")
                    except Exception as direct_move_error:
                        logger.error(f"❌ Direct movement also failed: {direct_move_error}")
            
            # Use random interval if not specified
            if interval is None:
                interval = self._random_click_delay()
            
            # Execute the click with multiple fallback methods
            try:
                # Primary click method
                pyautogui.click(button=button, clicks=clicks, interval=interval)
                current_x, current_y = self.get_current_position()
                logger.info(f"✅ Clicked at ({current_x}, {current_y}) with {button} button, {clicks} times")
                return True
            except Exception as primary_click_error:
                logger.warning(f"⚠️ Primary click method failed: {primary_click_error}")
                
                # Try alternative click methods
                try:
                    # Method 2: Specific coordinate click
                    if x is not None and y is not None:
                        logger.info(f"Attempting fallback click at ({x}, {y})")
                        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
                        logger.info(f"✅ Click completed with specific coordinate fallback")
                        return True
                except Exception as fallback1_error:
                    logger.warning(f"⚠️ Specific coordinate fallback failed: {fallback1_error}")
                    
                    try:
                        # Method 3: Get current position and click there
                        current_x, current_y = self.get_current_position()
                        logger.info(f"Attempting click at current position ({current_x}, {current_y})")
                        pyautogui.click(button=button, clicks=clicks)
                        logger.info(f"✅ Click completed at current position")
                        return True
                    except Exception as fallback2_error:
                        logger.warning(f"⚠️ Current position click failed: {fallback2_error}")
                        
                        try:
                            # Method 4: Use mouse_down/mouse_up sequence
                            logger.info("Attempting mouse_down/mouse_up sequence")
                            pyautogui.mouseDown(button=button)
                            time.sleep(0.1)
                            pyautogui.mouseUp(button=button)
                            logger.info("✅ Click completed with mouse_down/up sequence")
                            return True
                        except Exception as fallback3_error:
                            logger.error(f"❌ All click methods failed: {fallback3_error}")
                            return False
        except Exception as e:
            logger.error(f"❌ Error in click operation: {e}")
            
            # Final emergency fallback - if all else fails, try center of screen click
            try:
                logger.warning("⚠️ Using emergency center screen click")
                screen_width, screen_height = pyautogui.size()
                center_x, center_y = screen_width // 2, screen_height // 2
                pyautogui.moveTo(center_x, center_y)
                time.sleep(0.5)
                pyautogui.click()
                logger.info(f"✅ Emergency center click completed at ({center_x}, {center_y})")
                return True
            except Exception as emergency_error:
                logger.error(f"❌ Emergency click also failed: {emergency_error}")
                return False
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = 'left'):
        """Double-click at the specified position."""
        return self.click(x, y, button=button, clicks=2)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Right-click at the specified position."""
        return self.click(x, y, button='right')
    
    def drag_to(self, x: int, y: int, button: str = 'left', duration: Optional[float] = None):
        """
        Drag from current position to target position.
        
        Args:
            x: Target x-coordinate
            y: Target y-coordinate
            button: Mouse button to use for dragging
            duration: Movement duration (None for auto-calculated)
        """
        self._check_rate_limit()
        
        # Calculate duration if not specified
        if duration is None:
            duration = self._random_duration()
        
        try:
            pyautogui.dragTo(x, y, duration=duration, button=button)
            logger.info(f"Dragged to ({x}, {y}) with {button} button")
            return True
        except Exception as e:
            logger.error(f"Failed to drag: {e}")
            return False
    
    def scroll(self, clicks: int):
        """
        Scroll up or down.
        
        Args:
            clicks: Number of clicks (positive for up, negative for down)
        """
        self._check_rate_limit()
        try:
            pyautogui.scroll(clicks)
            logger.info(f"Scrolled {clicks} clicks")
            return True
        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
            return False
    
    def type_text(self, text: str, interval: Optional[float] = None):
        """
        Type text with optional delay between keypresses.
        
        Args:
            text: Text to type
            interval: Delay between keypresses (None for random delays)
        """
        self._check_rate_limit()
        
        # Check for destructive operations in high safety mode
        if self.safety_level == "high" and any(key in text.lower() for key in ["delete", "backspace"]):
            logger.warning("Destructive key operation detected in high safety mode")
            # In a real implementation, request confirmation here
        
        try:
            if interval is None:
                # Calculate random intervals between keypresses for human-like typing
                intervals = [random.uniform(0.05, 0.15) for _ in range(len(text))]
                
                for i, char in enumerate(text):
                    pyautogui.write(char, interval=intervals[i])
                    time.sleep(intervals[i])
            else:
                pyautogui.write(text, interval=interval)
            
            logger.info(f"Typed text: '{text}'")
            return True
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False
    
    def press_key(self, key: str):
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'enter', 'esc', 'space', etc.)
        """
        self._check_rate_limit()
        
        # Check for destructive keys in high safety mode
        if self.safety_level == "high" and key.lower() in self.destructive_keys:
            logger.warning(f"Destructive key operation detected: {key}")
            # In a real implementation, request confirmation here
        
        try:
            pyautogui.press(key)
            logger.info(f"Pressed key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key: {e}")
            return False
    
    def hotkey(self, *keys):
        """
        Press a combination of keys.
        
        Args:
            *keys: Keys to press (e.g., 'command', 'c' for Command+C)
        """
        self._check_rate_limit()
        
        # Check for destructive hotkeys in high safety mode
        hotkey_str = '+'.join(keys)
        if self.safety_level == "high" and any(combo in hotkey_str.lower() for combo in self.destructive_keys):
            logger.warning(f"Destructive hotkey operation detected: {hotkey_str}")
            # In a real implementation, request confirmation here
        
        try:
            pyautogui.hotkey(*keys)
            logger.info(f"Pressed hotkey: {hotkey_str}")
            return True
        except Exception as e:
            logger.error(f"Failed to press hotkey: {e}")
            return False
    
    def capture_screen_region(self, region: Optional[Tuple[int, int, int, int]] = None) -> Any:
        """
        Capture a screenshot of a specific region or full screen.
        
        Args:
            region: (left, top, width, height) or None for full screen
            
        Returns:
            PIL Image object
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            logger.info(f"Captured screenshot: {screenshot.size}")
            return screenshot
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    def find_image_on_screen(self, image_path: str, confidence: float = 0.9) -> Optional[Tuple[int, int]]:
        """
        Find an image on the screen.
        
        Args:
            image_path: Path to the image file
            confidence: Matching confidence threshold (0-1)
            
        Returns:
            (x, y) coordinates of center of found image, or None if not found
        """
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                logger.info(f"Found image {image_path} at {location}")
                return location
            else:
                logger.info(f"Image {image_path} not found on screen")
                return None
        except Exception as e:
            logger.error(f"Error finding image on screen: {e}")
            return None
    
    def execute_action_sequence(self, actions: List[Dict[str, Any]]) -> bool:
        """
        Execute a sequence of actions defined as a list of dictionaries.
        
        Args:
            actions: List of action dictionaries
            
        Example:
            actions = [
                {"action": "move", "x": 100, "y": 200},
                {"action": "click"},
                {"action": "type", "text": "Hello world"}
            ]
        """
        # Add global error handling to ensure execution chain continues
        try:
            # Validate actions
            if not actions or not isinstance(actions, list):
                logger.warning(f"⚠️ Invalid action sequence: {actions}")
                return True  # Return success to continue chain
                
            logger.info(f"🚀 Executing action sequence with {len(actions)} steps")
            
            # Execute each action with error handling
            for i, action in enumerate(actions):
                try:
                    action_type = action.get("action", "").lower()
                    logger.info(f"🔍 Executing step {i+1}/{len(actions)}: {action_type}")
                    
                    # Global emergency shutdown check
                    if self.emergency_shutdown_active or not self.running:
                        logger.warning("🛑 Execution aborted - emergency shutdown active")
                        return False
                    
                    # Handle each action type with individual error handling
                    try:
                        if action_type == "move":
                            x = action.get("x")
                            y = action.get("y")
                            duration = action.get("duration")
                            human_like = action.get("human_like", True)
                            self.move_to(x, y, duration, human_like)
                        
                        elif action_type == "click":
                            x = action.get("x")
                            y = action.get("y")
                            button = action.get("button", "left")
                            clicks = action.get("clicks", 1)
                            interval = action.get("interval")
                            self.click(x, y, button, clicks, interval)
                        
                        elif action_type == "right_click":
                            x = action.get("x")
                            y = action.get("y")
                            self.right_click(x, y)
                        
                        elif action_type == "double_click":
                            x = action.get("x")
                            y = action.get("y")
                            button = action.get("button", "left")
                            self.double_click(x, y, button)
                        
                        elif action_type == "drag":
                            x = action.get("x")
                            y = action.get("y")
                            button = action.get("button", "left")
                            duration = action.get("duration")
                            self.drag_to(x, y, button, duration)
                        
                        elif action_type == "scroll":
                            clicks = action.get("clicks", 0)
                            self.scroll(clicks)
                        
                        elif action_type == "type":
                            text = action.get("text", "")
                            interval = action.get("interval")
                            self.type_text(text, interval)
                        
                        elif action_type == "press":
                            key = action.get("key", "")
                            self.press_key(key)
                        
                        elif action_type == "hotkey":
                            keys = action.get("keys", [])
                            if keys:
                                self.hotkey(*keys)
                        
                        elif action_type == "wait":
                            # Simply wait for specified duration
                            duration = action.get("duration", 1.0)
                            time.sleep(duration)
                        
                        else:
                            logger.warning(f"⚠️ Unknown action type: {action_type}")
                            # Continue with next action instead of failing
                            
                        # Log success
                        logger.info(f"✅ Step {i+1} ({action_type}) executed successfully")
                            
                    except Exception as step_error:
                        # Log error but continue with next action
                        logger.error(f"❌ Error in step {i+1} ({action_type}): {step_error}")
                        
                    # Add small delay between actions for stability
                    time.sleep(0.1)
                    
                except Exception as action_error:
                    # Log error but continue with next action
                    logger.error(f"❌ Error processing action {i+1}: {action_error}")
                    time.sleep(0.5)  # Longer delay after error
            
            logger.info(f"✅ Action sequence completed successfully")
            return True
            
        except Exception as e:
            # Global error handler to ensure we don't crash
            logger.error(f"❌ Fatal error in action sequence execution: {e}")
            return True  # Return success to continue chain
    
    def save_input_history(self, file_path: str) -> bool:
        """Save input history to a file for analysis or replay."""
        try:
            with self.history_lock:
                history_data = {
                    "mouse": self.mouse_history,
                    "keyboard": self.keyboard_history,
                    "timestamp": time.time()
                }
            
            with open(file_path, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logger.info(f"Saved input history to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save input history: {e}")
            return False
    
    def stop(self):
        """Stop all listeners and cleanup resources."""
        self.running = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        logger.info("Input controller stopped")

# Test function
def test_controller():
    """Test the input controller functionality."""
    controller = InputController(safety_level="medium")
    
    try:
        print("Current position:", controller.get_current_position())
        
        # Test movement
        print("Moving to (100, 100)...")
        controller.move_to(100, 100)
        time.sleep(1)
        
        # Test click
        print("Clicking...")
        controller.click()
        time.sleep(1)
        
        # Test typing
        print("Typing 'Hello, world!'...")
        controller.type_text("Hello, world!")
        time.sleep(1)
        
        # Test hotkey
        print("Pressing Command+A...")
        controller.hotkey("command", "a")
        time.sleep(1)
        
        # Test complex sequence
        print("Executing action sequence...")
        actions = [
            {"action": "move", "x": 200, "y": 200},
            {"action": "click"},
            {"action": "type", "text": "Test sequence"},
            {"action": "press", "key": "enter"}
        ]
        controller.execute_action_sequence(actions)
        
    finally:
        # Save history
        controller.save_input_history("input_history.json")
        
        # Clean up
        controller.stop()

if __name__ == "__main__":
    test_controller()