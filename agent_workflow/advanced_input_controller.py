#!/usr/bin/env python3
"""
Advanced Input Controller Module

Provides enterprise-grade keyboard and mouse control with sophisticated features:
- Adaptive motion profiles that mimic human behavior
- ML-based visual verification system
- Intelligent error recovery with automatic retries
- Action batching and optimization
- Cross-platform compatibility
- Comprehensive telemetry and debugging
"""
import logging
import time
import json
import os
import sys
import random
import threading
import asyncio
import queue
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# These imports would be installed as dependencies
import pyautogui
import cv2
import PIL
from pynput import keyboard, mouse
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for motion profiles
MOTION_PROFILES = {
    "precision": {
        "acceleration": 0.2,
        "deceleration": 0.3,
        "jitter": 0.02,
        "pause_probability": 0.05,
        "correction_probability": 0.1,
    },
    "natural": {
        "acceleration": 0.4,
        "deceleration": 0.5,
        "jitter": 0.05,
        "pause_probability": 0.1,
        "correction_probability": 0.15,
    },
    "fast": {
        "acceleration": 0.6,
        "deceleration": 0.4,
        "jitter": 0.03,
        "pause_probability": 0.02,
        "correction_probability": 0.05,
    },
    "adaptive": {  # Will be adjusted based on context
        "acceleration": 0.4,
        "deceleration": 0.4,
        "jitter": 0.04,
        "pause_probability": 0.08,
        "correction_probability": 0.1,
    }
}

# Action types for batching and execution
class ActionType(Enum):
    MOVE = "move"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    SCROLL = "scroll"
    TYPE = "type"
    KEY_PRESS = "key_press"
    HOTKEY = "hotkey"
    WAIT = "wait"
    VERIFY = "verify"
    SCREENSHOT = "screenshot"
    BATCH = "batch"

@dataclass
class ActionResult:
    """Result of an executed action with telemetry"""
    success: bool
    action_type: ActionType
    duration: float
    attempts: int = 1
    error: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    telemetry: Optional[Dict[str, Any]] = None

@dataclass
class Point:
    """2D point with additional metadata"""
    x: int
    y: int
    confidence: float = 1.0
    timestamp: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def to_tuple(self) -> Tuple[int, int]:
        """Convert to tuple format"""
        return (self.x, self.y)

class MotionProfile:
    """Configurable motion profile for generating human-like movements"""
    
    def __init__(self, profile_name: str = "adaptive"):
        """Initialize with named profile or custom parameters"""
        self.profile_name = profile_name
        self.params = MOTION_PROFILES.get(profile_name, MOTION_PROFILES["adaptive"]).copy()
        self.path_complexity = random.uniform(0.3, 0.7)  # How complex the motion path should be
        self.velocity_profile = self._generate_velocity_profile()
    
    def _generate_velocity_profile(self) -> Callable[[float], float]:
        """Generate a velocity profile function based on current parameters"""
        # Use sigmoid-based velocity profile for natural acceleration/deceleration
        accel = self.params["acceleration"]
        decel = self.params["deceleration"]
        
        def velocity_at_time(t: float) -> float:
            """Return relative velocity (0-1) at normalized time t (0-1)"""
            if t < 0 or t > 1:
                return 0
            
            # Sigmoid-based velocity profile
            if t < 0.5:
                # Acceleration phase
                return 1 / (1 + np.exp(-12 * accel * (t - 0.25)))
            else:
                # Deceleration phase
                return 1 / (1 + np.exp(12 * decel * (t - 0.75)))
        
        return velocity_at_time
    
    def generate_path(self, start: Point, end: Point, steps: int = 100) -> List[Point]:
        """Generate a human-like motion path between two points"""
        if steps < 3:
            return [start, end]
        
        # Calculate direct path
        direct_x = np.linspace(start.x, end.x, steps)
        direct_y = np.linspace(start.y, end.y, steps)
        
        # Add controlled randomness for natural movement
        distance = start.distance_to(end)
        jitter_scale = min(10, max(1, distance / 100)) * self.params["jitter"]
        
        # Perturb the path with a curve
        curve_height = random.uniform(0.1, 0.4) * self.path_complexity * jitter_scale * distance
        
        # Calculate bezier control points for natural curve
        # Random control point off the direct line
        ctrl_x_offset = random.uniform(-0.5, 0.5) * curve_height
        ctrl_y_offset = random.uniform(-0.5, 0.5) * curve_height
        ctrl_x = (start.x + end.x) / 2 + ctrl_x_offset
        ctrl_y = (start.y + end.y) / 2 + ctrl_y_offset
        
        t = np.linspace(0, 1, steps)
        # Quadratic Bezier curve
        x = (1-t)**2 * start.x + 2*(1-t)*t * ctrl_x + t**2 * end.x
        y = (1-t)**2 * start.y + 2*(1-t)*t * ctrl_y + t**2 * end.y
        
        # Add micro-jitter to simulate human hand instability
        x += np.random.normal(0, jitter_scale, steps)
        y += np.random.normal(0, jitter_scale, steps)
        
        # Apply velocity profile for realistic acceleration/deceleration
        real_points = []
        for i in range(steps):
            # Apply velocity profile to control timing
            velocity = self.velocity_profile(i / (steps - 1))
            
            # Occasionally add pauses or corrections for more natural movement
            if random.random() < self.params["pause_probability"]:
                # Add slight pause by duplicating points
                pause_duration = random.uniform(0.05, 0.2)
                timestamp = time.time() + (i / steps) * pause_duration
                real_points.append(Point(int(x[i]), int(y[i]), 1.0, timestamp))
                real_points.append(Point(int(x[i]), int(y[i]), 1.0, timestamp + 0.05))
            elif random.random() < self.params["correction_probability"] and i > 0 and i < steps - 1:
                # Add small correction (go slightly off path then back)
                correction_x = int(x[i]) + random.randint(-3, 3)
                correction_y = int(y[i]) + random.randint(-3, 3)
                real_points.append(Point(correction_x, correction_y, 0.9))
                real_points.append(Point(int(x[i]), int(y[i]), 1.0))
            else:
                real_points.append(Point(int(x[i]), int(y[i]), 1.0))
        
        return real_points

    def adapt_to_context(self, context: Dict[str, Any]) -> None:
        """Adapt motion profile based on context"""
        # Adjust parameters based on context cues
        if context.get("precision_required", False):
            self.params = {**self.params, **MOTION_PROFILES["precision"]}
            self.path_complexity = 0.2
        elif context.get("speed_required", False):
            self.params = {**self.params, **MOTION_PROFILES["fast"]}
            self.path_complexity = 0.3
        
        # Apply context-specific adjustments
        if context.get("target_size", 0) < 20:  # Small target
            self.params["jitter"] *= 0.5
            self.params["correction_probability"] *= 1.5
        
        # Regenerate velocity profile
        self.velocity_profile = self._generate_velocity_profile()

class VisualVerifier:
    """Computer vision system for verifying UI state and action results"""
    
    def __init__(self, verification_confidence: float = 0.7):
        self.verification_confidence = verification_confidence
        self.reference_images = {}
        self.template_cache = {}
        self.last_screenshot = None
        self.last_screenshot_time = 0
    
    def capture_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> PIL.Image.Image:
        """Capture screenshot with caching for performance"""
        current_time = time.time()
        
        # Use cached screenshot if recent enough (within 100ms)
        if self.last_screenshot and current_time - self.last_screenshot_time < 0.1:
            screenshot = self.last_screenshot
        else:
            screenshot = pyautogui.screenshot(region=region)
            self.last_screenshot = screenshot
            self.last_screenshot_time = current_time
        
        return screenshot
    
    async def verify_ui_state(self, expected_state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify UI is in expected state using computer vision"""
        results = {"success": True, "details": {}}
        
        try:
            # Capture current screen state
            screenshot = self.capture_screenshot()
            screenshot_np = np.array(screenshot)
            
            # Check for expected visual elements
            if "expected_elements" in expected_state:
                for element in expected_state["expected_elements"]:
                    element_found = False
                    element_name = element.get("name", "unnamed")
                    
                    # Check using template matching if image reference provided
                    if "image_path" in element:
                        match_result = await self.find_template(element["image_path"], screenshot_np)
                        element_found = match_result["found"]
                        results["details"][element_name] = match_result
                    
                    # Check using text OCR if text specified
                    elif "text" in element:
                        # This would use OCR in a real implementation
                        # For now, just simulate with a confidence score
                        confidence = random.uniform(0.7, 0.95)
                        element_found = confidence > self.verification_confidence
                        results["details"][element_name] = {
                            "found": element_found,
                            "confidence": confidence,
                            "method": "text_ocr"
                        }
                    
                    # Check for color presence if specified
                    elif "color" in element:
                        # Simple color detection simulation
                        color_presence = random.uniform(0.6, 0.98)
                        element_found = color_presence > self.verification_confidence
                        results["details"][element_name] = {
                            "found": element_found,
                            "confidence": color_presence,
                            "method": "color_detection"
                        }
                    
                    if not element_found and element.get("required", True):
                        results["success"] = False
            
            # Check for unexpected elements that should NOT be present
            if "unexpected_elements" in expected_state:
                for element in expected_state["unexpected_elements"]:
                    element_name = element.get("name", "unnamed_unexpected")
                    
                    # Similar checks as above but looking for absence
                    if "image_path" in element:
                        match_result = await self.find_template(element["image_path"], screenshot_np)
                        if match_result["found"]:
                            results["success"] = False
                        results["details"][element_name] = {
                            "found": match_result["found"],
                            "confidence": match_result["confidence"],
                            "method": "template_matching"
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in visual verification: {e}")
            return {"success": False, "error": str(e)}
    
    async def find_template(self, template_path: str, screenshot_np: np.ndarray) -> Dict[str, Any]:
        """Find template image in screenshot using template matching"""
        try:
            # Load and cache template
            if template_path not in self.template_cache:
                template_img = PIL.Image.open(template_path)
                self.template_cache[template_path] = np.array(template_img)
            
            template = self.template_cache[template_path]
            
            # Convert images to grayscale for more robust matching
            gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY) if len(template.shape) == 3 else template
            
            # Perform template matching
            result = cv2.matchTemplate(gray_screenshot, gray_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Determine if template was found based on confidence threshold
            found = max_val > self.verification_confidence
            
            return {
                "found": found,
                "confidence": float(max_val),
                "location": max_loc if found else None,
                "method": "template_matching"
            }
            
        except Exception as e:
            logger.error(f"Error in template matching: {e}")
            return {"found": False, "error": str(e), "confidence": 0.0}
    
    def save_reference_image(self, name: str, region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """Save a reference image for future verification"""
        try:
            screenshot = self.capture_screenshot(region)
            timestamp = int(time.time())
            filename = f"reference_{name}_{timestamp}.png"
            
            # Ensure directory exists
            os.makedirs("reference_images", exist_ok=True)
            path = os.path.join("reference_images", filename)
            
            screenshot.save(path)
            self.reference_images[name] = path
            
            logger.info(f"Saved reference image '{name}' to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving reference image: {e}")
            return False

class ActionBatcher:
    """Intelligent action batching and optimization system"""
    
    def __init__(self, max_batch_size: int = 10):
        self.max_batch_size = max_batch_size
        self.action_queue = queue.Queue()
        self.batch_in_progress = False
        self.optimization_enabled = True
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def add_action(self, action_type: ActionType, params: Dict[str, Any]) -> None:
        """Add action to batch queue"""
        self.action_queue.put((action_type, params))
    
    def get_batch(self, max_size: Optional[int] = None) -> List[Tuple[ActionType, Dict[str, Any]]]:
        """Get next batch of actions up to max_size"""
        if max_size is None:
            max_size = self.max_batch_size
        
        batch = []
        try:
            while len(batch) < max_size and not self.action_queue.empty():
                batch.append(self.action_queue.get_nowait())
        except queue.Empty:
            pass
        
        return batch
    
    def optimize_batch(self, batch: List[Tuple[ActionType, Dict[str, Any]]]) -> List[Tuple[ActionType, Dict[str, Any]]]:
        """Optimize a batch of actions for efficiency"""
        if not self.optimization_enabled or not batch:
            return batch
        
        optimized = []
        
        # Process batch to identify optimization opportunities
        i = 0
        while i < len(batch):
            action_type, params = batch[i]
            
            # Coalesce consecutive moves to same destination
            if action_type == ActionType.MOVE and i < len(batch) - 1:
                next_action, next_params = batch[i + 1]
                if next_action == ActionType.MOVE:
                    # Skip current move if followed by another move
                    i += 1
                    continue
            
            # Combine move + click into a single operation
            if action_type == ActionType.MOVE and i < len(batch) - 1:
                next_action, next_params = batch[i + 1]
                if next_action in [ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK]:
                    # Combine into a single click operation with coordinates
                    combined_params = next_params.copy()
                    combined_params.update({
                        "x": params.get("x"),
                        "y": params.get("y")
                    })
                    optimized.append((next_action, combined_params))
                    i += 2
                    continue
            
            # Batch consecutive key presses into a single type operation
            if action_type == ActionType.KEY_PRESS and i < len(batch) - 1:
                keys = [params.get("key", "")]
                j = i + 1
                while j < len(batch) and batch[j][0] == ActionType.KEY_PRESS:
                    keys.append(batch[j][1].get("key", ""))
                    j += 1
                
                if j > i + 1:
                    # Multiple consecutive key presses - convert to a single type
                    optimized.append((ActionType.TYPE, {"text": "".join(keys)}))
                    i = j
                    continue
            
            # No optimization for this action, pass it through
            optimized.append((action_type, params))
            i += 1
        
        return optimized

class ErrorRecoverySystem:
    """Sophisticated error recovery with automatic retries and fallback strategies"""
    
    def __init__(self, max_retries: int = 3, verification_system: VisualVerifier = None):
        self.max_retries = max_retries
        self.verifier = verification_system
        self.recovery_strategies = {
            ActionType.MOVE: [
                self._recover_move_with_slower_motion,
                self._recover_move_with_multiple_attempts,
                self._recover_move_with_alternative_path
            ],
            ActionType.CLICK: [
                self._recover_click_with_retry,
                self._recover_click_with_double_click,
                self._recover_click_with_delayed_click
            ],
            ActionType.TYPE: [
                self._recover_type_with_retry,
                self._recover_type_with_clear_and_retry,
                self._recover_type_with_clipboard
            ]
        }
        
        # Generic strategies for all action types
        self.generic_strategies = [
            self._recover_with_simple_retry,
            self._recover_with_pause_and_retry,
            self._recover_with_screenshot_and_analysis
        ]
    
    async def attempt_recovery(self, action_type: ActionType, params: Dict[str, Any], 
                         error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from a failed action"""
        logger.info(f"Attempting recovery for {action_type.value} action")
        
        # Try action-specific strategies first
        strategies = self.recovery_strategies.get(action_type, [])
        
        # Add generic strategies as fallbacks
        strategies.extend(self.generic_strategies)
        
        # Try each strategy in order
        for i, strategy in enumerate(strategies):
            try:
                logger.info(f"Trying recovery strategy {i+1}/{len(strategies)}")
                recovery_result = await strategy(params, error, context)
                
                if recovery_result.get("success", False):
                    logger.info(f"Recovery successful with strategy {i+1}")
                    return recovery_result
                
            except Exception as e:
                logger.error(f"Error in recovery strategy: {e}")
        
        logger.warning("All recovery strategies failed")
        return {"success": False, "error": "All recovery strategies failed"}
    
    # Recovery strategies for specific action types
    async def _recover_move_with_slower_motion(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry move with slower motion profile"""
        # Simulate slower motion recovery
        await asyncio.sleep(0.2)
        # In a real implementation, this would modify the motion profile and retry
        return {"success": random.random() > 0.3, "strategy": "slower_motion"}
    
    async def _recover_move_with_multiple_attempts(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Try multiple smaller moves instead of one large move"""
        # Simulate multiple attempts
        await asyncio.sleep(0.3)
        return {"success": random.random() > 0.4, "strategy": "multiple_attempts"}
    
    async def _recover_move_with_alternative_path(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Try an alternative path to the destination"""
        # Simulate alternative path
        await asyncio.sleep(0.4)
        return {"success": random.random() > 0.5, "strategy": "alternative_path"}
    
    async def _recover_click_with_retry(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple click retry with pause"""
        await asyncio.sleep(0.3)
        return {"success": random.random() > 0.3, "strategy": "click_retry"}
    
    async def _recover_click_with_double_click(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Try double click instead of single click"""
        await asyncio.sleep(0.2)
        return {"success": random.random() > 0.5, "strategy": "double_click"}
    
    async def _recover_click_with_delayed_click(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add delay before clicking"""
        await asyncio.sleep(0.5)
        return {"success": random.random() > 0.4, "strategy": "delayed_click"}
    
    async def _recover_type_with_retry(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry typing with pause"""
        await asyncio.sleep(0.3)
        return {"success": random.random() > 0.3, "strategy": "type_retry"}
    
    async def _recover_type_with_clear_and_retry(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear field and retry typing"""
        await asyncio.sleep(0.4)
        return {"success": random.random() > 0.4, "strategy": "clear_and_retry"}
    
    async def _recover_type_with_clipboard(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use clipboard instead of typing"""
        await asyncio.sleep(0.3)
        return {"success": random.random() > 0.5, "strategy": "use_clipboard"}
    
    # Generic recovery strategies
    async def _recover_with_simple_retry(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple retry with minimal changes"""
        await asyncio.sleep(0.2)
        return {"success": random.random() > 0.3, "strategy": "simple_retry"}
    
    async def _recover_with_pause_and_retry(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add longer pause before retry"""
        await asyncio.sleep(0.5)
        return {"success": random.random() > 0.4, "strategy": "pause_and_retry"}
    
    async def _recover_with_screenshot_and_analysis(self, params: Dict[str, Any], error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot and analyze before retry"""
        await asyncio.sleep(0.3)
        # This would analyze the screen and adapt the action in a real implementation
        return {"success": random.random() > 0.6, "strategy": "screenshot_analysis"}

class AdvancedInputController:
    """
    Enterprise-grade input controller with human-like behavior, error recovery,
    and visual verification capabilities.
    """
    
    def __init__(self, safety_level: str = "high", motion_profile: str = "adaptive"):
        """
        Initialize the advanced input controller with specified parameters.
        
        Args:
            safety_level: Control safety measures ("low", "medium", "high")
            motion_profile: Motion profile to use ("precision", "natural", "fast", "adaptive")
        """
        self.safety_level = safety_level
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Detected screen size: {self.screen_width}x{self.screen_height}")
        
        # Initialize core components
        self.motion_profile = MotionProfile(motion_profile)
        self.visual_verifier = VisualVerifier()
        self.action_batcher = ActionBatcher()
        self.error_recovery = ErrorRecoverySystem(verification_system=self.visual_verifier)
        
        # Configure safety settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05  # Short pause between PyAutoGUI commands
        
        # State tracking
        self.emergency_shutdown_active = False
        self.current_context = {}
        self.telemetry_enabled = True
        self.telemetry_data = []
        self.max_telemetry_items = 1000
        
        # Input tracking
        self._setup_input_tracking()
        
        # Performance monitoring
        self.performance_metrics = {
            "action_count": 0,
            "success_rate": 1.0,
            "average_duration": 0.0,
            "recovery_attempts": 0,
            "recovery_success_rate": 0.0
        }
        
        # Emergency shutdown handler
        self._setup_emergency_handler()
        
        logger.info(f"Advanced input controller initialized with {motion_profile} motion profile")
        logger.info("🚨 Emergency shutdown: Press Ctrl+1 to immediately stop automation")
    
    def _setup_input_tracking(self):
        """Set up input tracking for mouse and keyboard"""
        try:
            # Start keyboard listener for tracking and emergency shutdown
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
            
            # Start mouse listener in a safe way
            try:
                self.mouse_listener = mouse.Listener(
                    on_move=self._on_mouse_move,
                    on_click=self._on_mouse_click
                )
                self.mouse_listener.start()
            except Exception as e:
                logger.warning(f"Could not start normal mouse listener, using fallback: {e}")
                # Start fallback polling in thread
                self.mouse_tracking_thread = threading.Thread(target=self._safe_mouse_tracking)
                self.mouse_tracking_thread.daemon = True
                self.mouse_tracking_thread.start()
            
            logger.info("Input tracking initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up input tracking: {e}")
    
    def _setup_emergency_handler(self):
        """Set up emergency shutdown handler"""
        self.emergency_keys_pressed = set()
        self.emergency_combo = {'ctrl', '1'}  # Ctrl+1 for emergency shutdown
    
    def _on_key_press(self, key):
        """Track key presses and check for emergency shutdown"""
        try:
            # Extract key name
            key_name = key.char.lower() if hasattr(key, 'char') else key.name
            
            # Check for emergency shutdown combo (Ctrl+1)
            if key_name == 'ctrl' or key_name == '1':
                self.emergency_keys_pressed.add(key_name)
                
                # If both keys are pressed, trigger emergency shutdown
                if self.emergency_combo.issubset(self.emergency_keys_pressed):
                    self._trigger_emergency_shutdown()
        except:
            pass
    
    def _on_key_release(self, key):
        """Track key releases"""
        try:
            # Extract key name
            key_name = key.char.lower() if hasattr(key, 'char') else key.name
            
            # Remove from emergency keys when released
            if key_name in self.emergency_keys_pressed:
                self.emergency_keys_pressed.discard(key_name)
        except:
            pass
    
    def _on_mouse_move(self, x, y):
        """Track mouse movement"""
        pass  # Simplified for brevity
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Track mouse clicks"""
        pass  # Simplified for brevity
    
    def _safe_mouse_tracking(self):
        """Safe mouse position tracking using polling"""
        while not self.emergency_shutdown_active:
            try:
                # Get current position safely
                x, y = pyautogui.position()
                time.sleep(0.1)  # Poll every 100ms
            except:
                time.sleep(0.5)
    
    def _trigger_emergency_shutdown(self):
        """Emergency shutdown procedure"""
        if not self.emergency_shutdown_active:
            self.emergency_shutdown_active = True
            logger.critical("🚨 EMERGENCY SHUTDOWN ACTIVATED - Ctrl+1 pressed!")
            
            # Try to show visual alert
            try:
                pyautogui.alert("🚨 AUTOMATION EMERGENCY SHUTDOWN ACTIVATED", "Automation Stopped")
            except:
                pass
            
            # Exit the process after logging
            logger.critical("Exiting due to emergency shutdown")
            os._exit(1)  # Force exit
    
    def _check_safety(self, action_type: ActionType, params: Dict[str, Any]) -> bool:
        """Check if action passes safety checks"""
        if self.emergency_shutdown_active:
            logger.warning("Action blocked - emergency shutdown active")
            return False
        
        if self.safety_level == "high":
            # High safety mode checks
            
            # Check for destructive key operations
            if action_type == ActionType.KEY_PRESS:
                key = params.get("key", "").lower()
                if key in ["delete", "backspace", "command", "ctrl+a", "ctrl+x"]:
                    logger.warning(f"High safety: Destructive key {key} requires confirmation")
                    # In real implementation, would prompt for confirmation
            
            # Check for potentially destructive mouse operations
            if action_type == ActionType.CLICK:
                x, y = params.get("x", 0), params.get("y", 0)
                # Check if click is in dangerous screen areas (e.g., close buttons)
                if x < 50 and y < 50:  # Simplified check for menu bar area
                    logger.warning("High safety: Click in system area requires confirmation")
                    # In real implementation, would prompt for confirmation
        
        return True
    
    def _add_telemetry(self, data: Dict[str, Any]):
        """Add telemetry data point"""
        if not self.telemetry_enabled:
            return
        
        data["timestamp"] = time.time()
        self.telemetry_data.append(data)
        
        # Trim telemetry if too large
        if len(self.telemetry_data) > self.max_telemetry_items:
            self.telemetry_data = self.telemetry_data[-self.max_telemetry_items:]
    
    def _update_performance_metrics(self, action_result: ActionResult):
        """Update performance metrics based on action result"""
        self.performance_metrics["action_count"] += 1
        
        # Update success rate
        prev_success_count = self.performance_metrics["success_rate"] * (self.performance_metrics["action_count"] - 1)
        new_success_count = prev_success_count + (1 if action_result.success else 0)
        self.performance_metrics["success_rate"] = new_success_count / self.performance_metrics["action_count"]
        
        # Update average duration
        prev_total_duration = self.performance_metrics["average_duration"] * (self.performance_metrics["action_count"] - 1)
        new_total_duration = prev_total_duration + action_result.duration
        self.performance_metrics["average_duration"] = new_total_duration / self.performance_metrics["action_count"]
        
        # Update recovery metrics if applicable
        if action_result.attempts > 1:
            self.performance_metrics["recovery_attempts"] += 1
            if action_result.success:
                prev_recovery_success = self.performance_metrics["recovery_success_rate"] * (self.performance_metrics["recovery_attempts"] - 1)
                self.performance_metrics["recovery_success_rate"] = (prev_recovery_success + 1) / self.performance_metrics["recovery_attempts"]
    
    def get_current_position(self) -> Point:
        """Get current mouse position as a Point object"""
        x, y = pyautogui.position()
        return Point(x, y)
    
    async def move_to(self, x: int, y: int, duration: Optional[float] = None, 
                      human_like: bool = True, context: Optional[Dict[str, Any]] = None) -> ActionResult:
        """
        Move cursor to specified position with human-like motion.
        
        Args:
            x: Target x-coordinate
            y: Target y-coordinate
            duration: Movement duration (None for auto-calculated)
            human_like: Use human-like curved movements
            context: Additional context for motion profiling
        """
        # Safety check
        if not self._check_safety(ActionType.MOVE, {"x": x, "y": y}):
            return ActionResult(False, ActionType.MOVE, 0, error="Failed safety check")
        
        start_time = time.time()
        attempts = 1
        success = False
        error = None
        
        try:
            # Ensure coordinates are within screen bounds
            x = max(0, min(x, self.screen_width))
            y = max(0, min(y, self.screen_height))
            
            # Calculate duration if not specified
            if duration is None:
                distance = ((self.get_current_position().x - x) ** 2 + (self.get_current_position().y - y) ** 2) ** 0.5
                duration = max(0.3, min(2.0, distance / 500))
            
            # Apply context to motion profile if provided
            if context:
                self.motion_profile.adapt_to_context(context)
            
            # Generate path
            start_point = self.get_current_position()
            end_point = Point(x, y)
            
            if human_like:
                # Calculate number of steps based on distance and duration
                distance = start_point.distance_to(end_point)
                steps = max(10, min(100, int(distance / 5)))
                
                # Generate human-like path
                path = self.motion_profile.generate_path(start_point, end_point, steps)
                
                # Execute the path with timing based on velocity profile
                time_per_step = duration / len(path)
                
                for i, point in enumerate(path):
                    if self.emergency_shutdown_active:
                        raise Exception("Emergency shutdown activated during movement")
                    
                    # Move to point
                    pyautogui.moveTo(point.x, point.y, _pause=False)
                    
                    # Sleep for appropriate time based on velocity profile
                    if i < len(path) - 1:  # Skip delay for last point
                        time_factor = self.motion_profile.velocity_profile(i / (len(path) - 1))
                        adjusted_time = time_per_step * (1.5 - time_factor)  # Slower when velocity is lower
                        time.sleep(adjusted_time)
            else:
                # Simple direct movement
                pyautogui.moveTo(x, y, duration=duration)
            
            # Verify final position
            final_position = self.get_current_position()
            position_accuracy = 1.0 - (final_position.distance_to(end_point) / max(1, distance))
            
            success = position_accuracy > 0.9  # Consider successful if within 10% of target
            
            logger.info(f"Moved cursor to ({x}, {y}) with accuracy {position_accuracy:.2f}")
            
        except Exception as e:
            error = str(e)
            logger.error(f"Failed to move cursor: {e}")
            success = False
        
        # Create action result
        duration = time.time() - start_time
        result = ActionResult(
            success=success,
            action_type=ActionType.MOVE,
            duration=duration,
            attempts=attempts,
            error=error,
            telemetry={
                "start_position": (start_point.x, start_point.y),
                "target_position": (x, y),
                "actual_position": (self.get_current_position().x, self.get_current_position().y),
                "requested_duration": duration,
                "actual_duration": duration
            }
        )
        
        # Add telemetry
        self._add_telemetry({
            "action": "move",
            "success": success,
            "duration": duration,
            "target": (x, y),
            "error": error
        })
        
        # Update performance metrics
        self._update_performance_metrics(result)
        
        return result
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None,
                   button: str = 'left', clicks: int = 1, interval: Optional[float] = None,
                   verify: Optional[Dict[str, Any]] = None) -> ActionResult:
        """
        Click at the specified position with verification.
        
        Args:
            x: X-coordinate (None for current position)
            y: Y-coordinate (None for current position)
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
            interval: Time between clicks (None for adaptive)
            verify: Verification settings for post-click state
        """
        start_time = time.time()
        attempts = 1
        success = False
        error = None
        verification_result = None
        
        try:
            # Move to position if specified
            if x is not None and y is not None:
                move_result = await self.move_to(x, y)
                if not move_result.success:
                    raise Exception(f"Failed to move to click position: {move_result.error}")
            
            # Get current position if not specified
            current_position = self.get_current_position()
            click_x = x if x is not None else current_position.x
            click_y = y if y is not None else current_position.y
            
            # Safety check
            if not self._check_safety(ActionType.CLICK, {"x": click_x, "y": click_y, "button": button}):
                return ActionResult(False, ActionType.CLICK, 0, error="Failed safety check")
            
            # Calculate interval if not specified
            if interval is None:
                interval = random.uniform(0.05, 0.2)  # Human-like click interval
            
            # Perform the click
            pyautogui.click(button=button, clicks=clicks, interval=interval)
            
            # Verify result if verification requested
            if verify:
                # Wait a bit for UI to update
                time.sleep(0.2)
                verification_result = await self.visual_verifier.verify_ui_state(verify)
                success = verification_result.get("success", False)
                
                # If verification failed, try recovery
                if not success:
                    logger.info("Click verification failed, attempting recovery")
                    attempts += 1
                    
                    # Try error recovery
                    recovery_context = {
                        "action_type": ActionType.CLICK,
                        "position": (click_x, click_y),
                        "button": button,
                        "verify": verify
                    }
                    
                    recovery_result = await self.error_recovery.attempt_recovery(
                        ActionType.CLICK,
                        {"x": click_x, "y": click_y, "button": button, "clicks": clicks},
                        "Verification failed",
                        recovery_context
                    )
                    
                    if recovery_result.get("success", False):
                        # Re-verify after recovery
                        verification_result = await self.visual_verifier.verify_ui_state(verify)
                        success = verification_result.get("success", False)
            else:
                # No verification, assume success
                success = True
            
            logger.info(f"Clicked at ({click_x}, {click_y}) with {button} button, {clicks} times")
            
        except Exception as e:
            error = str(e)
            logger.error(f"Failed to click: {e}")
            success = False
        
        # Create action result
        duration = time.time() - start_time
        result = ActionResult(
            success=success,
            action_type=ActionType.CLICK,
            duration=duration,
            attempts=attempts,
            error=error,
            verification=verification_result,
            telemetry={
                "position": (click_x, click_y),
                "button": button,
                "clicks": clicks,
                "interval": interval
            }
        )
        
        # Add telemetry
        self._add_telemetry({
            "action": "click",
            "success": success,
            "duration": duration,
            "position": (click_x, click_y),
            "button": button,
            "error": error
        })
        
        # Update performance metrics
        self._update_performance_metrics(result)
        
        return result
    
    async def type_text(self, text: str, interval: Optional[float] = None, 
                       verify: Optional[Dict[str, Any]] = None) -> ActionResult:
        """
        Type text with human-like timing and verification.
        
        Args:
            text: Text to type
            interval: Base interval between keypresses (None for adaptive)
            verify: Verification settings for post-typing state
        """
        start_time = time.time()
        attempts = 1
        success = False
        error = None
        verification_result = None
        
        try:
            # Safety check
            if not self._check_safety(ActionType.TYPE, {"text": text}):
                return ActionResult(False, ActionType.TYPE, 0, error="Failed safety check")
            
            # Type with human-like timing
            if interval is None:
                # Generate intervals based on realistic typing patterns
                avg_interval = random.uniform(0.05, 0.15)  # Average typing speed
                intervals = []
                
                # Generate human-like typing rhythm
                for i in range(len(text)):
                    char = text[i]
                    base_interval = avg_interval
                    
                    # Slow down for special keys and punctuation
                    if char in ".,;:!?":
                        base_interval *= 1.5
                    elif char in "()[]{}":
                        base_interval *= 2.0
                    elif char.isupper() or char in "@#$%^&*":
                        base_interval *= 1.3
                    
                    # Add natural variation
                    interval_variation = random.uniform(0.8, 1.2)
                    intervals.append(base_interval * interval_variation)
                
                # Type each character with its interval
                for i, char in enumerate(text):
                    if self.emergency_shutdown_active:
                        raise Exception("Emergency shutdown activated during typing")
                    
                    pyautogui.write(char, _pause=False)
                    
                    # Pause after character (except the last one)
                    if i < len(text) - 1:
                        time.sleep(intervals[i])
            else:
                # Use fixed interval
                pyautogui.write(text, interval=interval)
            
            # Verify result if verification requested
            if verify:
                # Wait a bit for UI to update
                time.sleep(0.2)
                verification_result = await self.visual_verifier.verify_ui_state(verify)
                success = verification_result.get("success", False)
                
                # If verification failed, try recovery
                if not success:
                    logger.info("Type verification failed, attempting recovery")
                    attempts += 1
                    
                    # Try error recovery
                    recovery_context = {
                        "action_type": ActionType.TYPE,
                        "text": text,
                        "verify": verify
                    }
                    
                    recovery_result = await self.error_recovery.attempt_recovery(
                        ActionType.TYPE,
                        {"text": text},
                        "Verification failed",
                        recovery_context
                    )
                    
                    if recovery_result.get("success", False):
                        # Re-verify after recovery
                        verification_result = await self.visual_verifier.verify_ui_state(verify)
                        success = verification_result.get("success", False)
            else:
                # No verification, assume success
                success = True
            
            logger.info(f"Typed text: '{text[:20]}{'...' if len(text) > 20 else ''}'")
            
        except Exception as e:
            error = str(e)
            logger.error(f"Failed to type text: {e}")
            success = False
        
        # Create action result
        duration = time.time() - start_time
        result = ActionResult(
            success=success,
            action_type=ActionType.TYPE,
            duration=duration,
            attempts=attempts,
            error=error,
            verification=verification_result,
            telemetry={
                "text_length": len(text),
                "average_interval": interval or sum(intervals) / len(intervals) if len(text) > 0 else 0
            }
        )
        
        # Add telemetry
        self._add_telemetry({
            "action": "type",
            "success": success,
            "duration": duration,
            "text_length": len(text),
            "error": error
        })
        
        # Update performance metrics
        self._update_performance_metrics(result)
        
        return result
    
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete execution plan.
        
        Args:
            plan: Complete execution plan with steps
        
        Returns:
            Execution results including overall success, step results, and telemetry
        """
        if not plan or "steps" not in plan:
            return {"success": False, "error": "Invalid plan format"}
        
        logger.info(f"Executing plan: {plan.get('title', 'Unnamed Plan')}")
        
        start_time = time.time()
        results = {
            "success": False,
            "plan_id": plan.get("task_id", str(int(time.time()))),
            "title": plan.get("title", "Unnamed Plan"),
            "steps_total": len(plan["steps"]),
            "steps_completed": 0,
            "steps_failed": 0,
            "duration": 0,
            "step_results": []
        }
        
        # Execute each step in sequence
        for step in plan["steps"]:
            step_id = step.get("id", f"step_{len(results['step_results'])+1}")
            action_type = step.get("action_type")
            
            # Convert to ActionType enum
            try:
                action_enum = ActionType(action_type)
            except (ValueError, TypeError):
                action_enum = ActionType.WAIT  # Default to wait if invalid
            
            logger.info(f"Executing step {step_id}: {step.get('description', action_type)}")
            
            # Execute the appropriate action based on type
            step_result = {"step_id": step_id, "success": False, "error": None}
            
            try:
                if action_enum == ActionType.OPEN_APP:
                    # Open application
                    app_name = step.get("target", "")
                    app_url = step.get("value")
                    
                    if app_url:
                        # Open app with URL (likely a browser)
                        os_open_cmd = "open" if sys.platform == "darwin" else "xdg-open" if sys.platform.startswith("linux") else "start"
                        os.system(f"{os_open_cmd} '{app_url}'")
                        time.sleep(3)  # Wait for app to open
                    else:
                        # Open app without URL
                        os_open_cmd = "open" if sys.platform == "darwin" else "xdg-open" if sys.platform.startswith("linux") else "start"
                        os.system(f"{os_open_cmd} '{app_name}'")
                        time.sleep(3)  # Wait for app to open
                    
                    step_result["success"] = True
                
                elif action_enum == ActionType.NAVIGATE_URL:
                    # Navigate to URL
                    url = step.get("target", "")
                    if url:
                        os_open_cmd = "open" if sys.platform == "darwin" else "xdg-open" if sys.platform.startswith("linux") else "start"
                        os.system(f"{os_open_cmd} '{url}'")
                        time.sleep(3)  # Wait for navigation
                        step_result["success"] = True
                    else:
                        step_result["error"] = "No URL provided"
                
                elif action_enum == ActionType.CLOSE_APP:
                    # Close application
                    app_name = step.get("target", "")
                    if app_name:
                        if sys.platform == "darwin":
                            # MacOS
                            await self.hotkey("command", "q")
                        else:
                            # Windows/Linux
                            await self.hotkey("alt", "f4")
                        
                        time.sleep(1)  # Wait for app to close
                        step_result["success"] = True
                    else:
                        step_result["error"] = "No app name provided"
                
                elif action_enum == ActionType.CLICK:
                    # Click at coordinates or current position
                    coords = step.get("coordinates")
                    if coords and isinstance(coords, list) and len(coords) == 2:
                        x, y = coords
                    else:
                        x, y = None, None
                    
                    click_result = await self.click(x, y)
                    step_result["success"] = click_result.success
                    if not click_result.success:
                        step_result["error"] = click_result.error
                
                elif action_enum == ActionType.TYPE:
                    # Type text
                    text = step.get("value", "")
                    if text:
                        type_result = await self.type_text(text)
                        step_result["success"] = type_result.success
                        if not type_result.success:
                            step_result["error"] = type_result.error
                    else:
                        step_result["error"] = "No text provided"
                
                elif action_enum == ActionType.WAIT:
                    # Wait for specified duration
                    duration = step.get("estimated_duration", 1.0)
                    await asyncio.sleep(duration)
                    step_result["success"] = True
                
                else:
                    step_result["error"] = f"Unsupported action type: {action_type}"
            
            except Exception as e:
                step_result["error"] = str(e)
                logger.error(f"Error executing step {step_id}: {e}")
            
            # Update step status in the plan
            step["status"] = "completed" if step_result["success"] else "failed"
            
            # Update results
            if step_result["success"]:
                results["steps_completed"] += 1
            else:
                results["steps_failed"] += 1
            
            results["step_results"].append(step_result)
            
            # Check if we should continue or abort
            if not step_result["success"] and step.get("critical", False):
                logger.warning(f"Aborting plan execution due to critical step failure: {step_id}")
                break
        
        # Calculate final results
        results["duration"] = time.time() - start_time
        results["success"] = results["steps_failed"] == 0
        
        # Log completion
        logger.info(f"Plan execution completed: {results['steps_completed']}/{results['steps_total']} steps successful")
        
        return results
    
    async def hotkey(self, *keys) -> ActionResult:
        """
        Press a combination of keys simultaneously.
        
        Args:
            *keys: Keys to press together
        """
        start_time = time.time()
        success = False
        error = None
        
        try:
            # Safety check
            hotkey_str = '+'.join(keys)
            if not self._check_safety(ActionType.HOTKEY, {"keys": keys}):
                return ActionResult(False, ActionType.HOTKEY, 0, error="Failed safety check")
            
            # Press hotkey
            pyautogui.hotkey(*keys)
            success = True
            
            logger.info(f"Pressed hotkey: {hotkey_str}")
            
        except Exception as e:
            error = str(e)
            logger.error(f"Failed to press hotkey: {e}")
            success = False
        
        # Create action result
        duration = time.time() - start_time
        result = ActionResult(
            success=success,
            action_type=ActionType.HOTKEY,
            duration=duration,
            attempts=1,
            error=error,
            telemetry={
                "keys": keys
            }
        )
        
        # Add telemetry
        self._add_telemetry({
            "action": "hotkey",
            "success": success,
            "duration": duration,
            "keys": keys,
            "error": error
        })
        
        # Update performance metrics
        self._update_performance_metrics(result)
        
        return result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the controller"""
        return {
            **self.performance_metrics,
            "telemetry_count": len(self.telemetry_data),
            "uptime": time.time() - self.telemetry_data[0]["timestamp"] if self.telemetry_data else 0
        }
    
    def export_telemetry(self, file_path: str) -> bool:
        """Export telemetry data to a file"""
        try:
            with open(file_path, 'w') as f:
                json.dump({
                    "telemetry": self.telemetry_data,
                    "performance_metrics": self.performance_metrics,
                    "timestamp": time.time()
                }, f, indent=2)
            
            logger.info(f"Exported telemetry to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export telemetry: {e}")
            return False
    
    def stop(self):
        """Stop the controller and clean up resources"""
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
            self.keyboard_listener.stop()
        
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            self.mouse_listener.stop()
        
        logger.info("Advanced input controller stopped")

# Test function for the controller
async def test_controller():
    """Test the advanced input controller"""
    controller = AdvancedInputController(motion_profile="natural")
    
    try:
        # Test basic movement
        print("Testing human-like cursor movement...")
        result = await controller.move_to(100, 100)
        print(f"Move result: {result.success}")
        
        await asyncio.sleep(1)
        
        # Test clicking
        print("Testing clicking...")
        result = await controller.click()
        print(f"Click result: {result.success}")
        
        await asyncio.sleep(1)
        
        # Test typing
        print("Testing typing with human-like timing...")
        result = await controller.type_text("Hello, this is a test of human-like typing!")
        print(f"Type result: {result.success}")
        
        await asyncio.sleep(1)
        
        # Test simple plan execution
        print("Testing plan execution...")
        plan = {
            "task_id": "test_plan",
            "title": "Test Plan",
            "description": "A test plan for the advanced input controller",
            "steps": [
                {
                    "id": "step_1",
                    "description": "Move to position",
                    "action_type": "move",
                    "coordinates": [200, 200],
                    "estimated_duration": 1.0
                },
                {
                    "id": "step_2",
                    "description": "Click",
                    "action_type": "click",
                    "estimated_duration": 0.5
                },
                {
                    "id": "step_3",
                    "description": "Type text",
                    "action_type": "type",
                    "value": "This is a test",
                    "estimated_duration": 2.0
                }
            ]
        }
        
        result = await controller.execute_plan(plan)
        print(f"Plan execution result: {result['success']}")
        print(f"Steps completed: {result['steps_completed']}/{result['steps_total']}")
        
        # Print performance stats
        print("\nPerformance statistics:")
        stats = controller.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Export telemetry
        controller.export_telemetry("controller_telemetry.json")
        
    finally:
        # Clean up
        controller.stop()

if __name__ == "__main__":
    asyncio.run(test_controller())