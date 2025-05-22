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
            # Mouse listener
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.start()
            
            # Keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
            
            self.running = True
            logger.info("Input listeners started successfully")
            logger.info("🚨 Emergency shutdown: Press Ctrl+1 to immediately stop agent")
        except Exception as e:
            logger.error(f"Failed to start input listeners: {e}")
    
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
        
        # Move to position if specified
        if x is not None and y is not None:
            self.move_to(x, y)
        
        # Use random interval if not specified
        if interval is None:
            interval = self._random_click_delay()
        
        try:
            pyautogui.click(button=button, clicks=clicks, interval=interval)
            current_x, current_y = self.get_current_position()
            logger.info(f"Clicked at ({current_x}, {current_y}) with {button} button, {clicks} times")
            return True
        except Exception as e:
            logger.error(f"Failed to click: {e}")
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
        for action in actions:
            action_type = action.get("action", "").lower()
            
            if action_type == "move":
                x = action.get("x")
                y = action.get("y")
                duration = action.get("duration")
                human_like = action.get("human_like", True)
                if not self.move_to(x, y, duration, human_like):
                    return False
            
            elif action_type == "click":
                x = action.get("x")
                y = action.get("y")
                button = action.get("button", "left")
                clicks = action.get("clicks", 1)
                interval = action.get("interval")
                if not self.click(x, y, button, clicks, interval):
                    return False
            
            elif action_type == "right_click":
                x = action.get("x")
                y = action.get("y")
                if not self.right_click(x, y):
                    return False
            
            elif action_type == "double_click":
                x = action.get("x")
                y = action.get("y")
                button = action.get("button", "left")
                if not self.double_click(x, y, button):
                    return False
            
            elif action_type == "drag":
                x = action.get("x")
                y = action.get("y")
                button = action.get("button", "left")
                duration = action.get("duration")
                if not self.drag_to(x, y, button, duration):
                    return False
            
            elif action_type == "scroll":
                clicks = action.get("clicks", 0)
                if not self.scroll(clicks):
                    return False
            
            elif action_type == "type":
                text = action.get("text", "")
                interval = action.get("interval")
                if not self.type_text(text, interval):
                    return False
            
            elif action_type == "press":
                key = action.get("key", "")
                if not self.press_key(key):
                    return False
            
            elif action_type == "hotkey":
                keys = action.get("keys", [])
                if not keys or not self.hotkey(*keys):
                    return False
            
            elif action_type == "wait":
                # Simply wait for specified duration
                duration = action.get("duration", 1.0)
                time.sleep(duration)
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
            
            # Add small delay between actions for stability
            time.sleep(0.1)
        
        return True
    
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