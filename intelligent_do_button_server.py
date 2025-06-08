#!/usr/bin/env python3
"""
Intelligent DO Button Server
Provides real mouse/keyboard automation with intelligent UI element detection
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
import random
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
import threading
import pyautogui

# Configure logging
os.makedirs('logs/websocket', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/intelligent_do_button_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('intelligent_do_button_server')

# Try to import input controller for real automation
try:
    from agent_workflow.input_controller import InputController
    input_controller = InputController(safety_level="medium")
    INPUT_CONTROLLER_AVAILABLE = True
    logger.info("✅ Input controller loaded successfully")
except ImportError as e:
    logger.error(f"⚠️ Input controller not available: {e}")
    INPUT_CONTROLLER_AVAILABLE = False
    input_controller = None

# Try to import UI detection systems if available
try:
    from universal_ui_element_detector import detect_ui_elements, find_element_by_description
    UI_DETECTOR_AVAILABLE = True
    logger.info("✅ Universal UI element detector loaded")
except ImportError:
    UI_DETECTOR_AVAILABLE = False
    logger.warning("⚠️ Universal UI element detector not available")

try:
    from intelligent_ui_detector import IntelligentUIDetector
    intelligent_detector = IntelligentUIDetector()
    INTELLIGENT_UI_AVAILABLE = True
    logger.info("✅ Intelligent UI detector loaded")
except ImportError:
    INTELLIGENT_UI_AVAILABLE = False
    intelligent_detector = None
    logger.warning("⚠️ Intelligent UI detector not available")

# Track connected clients and execution stats
connected_clients = set()
execution_count = 0
current_plan = None

# Default UI element positions for automation
DEFAULT_UI_ELEMENTS = {
    # Browser search scenario
    "search_box": (400, 200),
    "search_button": (600, 200),
    
    # Email composition scenario
    "compose_button": (100, 150),
    "to_field": (400, 200),
    "subject_field": (400, 250),
    "body_field": (400, 300),
    "send_button": (500, 450),
    
    # Default fallback positions
    "default_button": (500, 300),
    "default_field": (400, 250)
}

# Cache for UI element detection results
ui_element_cache = {}
ui_element_cache_lock = threading.Lock()
CACHE_TIMEOUT = 30  # Seconds before cache expires

class UIElement:
    """Represents a detected UI element with position and metadata"""
    def __init__(self, element_type, x, y, width, height, confidence=0.0, text="", attributes=None):
        self.element_type = element_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.text = text
        self.attributes = attributes or {}
        self.center_x = x + (width // 2)
        self.center_y = y + (height // 2)
    
    @property
    def center(self):
        return (self.center_x, self.center_y)
    
    @property
    def bounds(self):
        return (self.x, self.y, self.width, self.height)
    
    def to_dict(self):
        return {
            "type": self.element_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "confidence": self.confidence,
            "text": self.text,
            "attributes": self.attributes
        }

def take_screenshot():
    """Take a screenshot of the current screen"""
    try:
        return pyautogui.screenshot()
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return None

async def detect_elements_on_screen():
    """Detect UI elements on the current screen"""
    global ui_element_cache, ui_element_cache_lock
    
    # Check if we have a recent cache
    with ui_element_cache_lock:
        if 'last_update' in ui_element_cache and time.time() - ui_element_cache['last_update'] < CACHE_TIMEOUT:
            logger.info("Using cached UI elements")
            return ui_element_cache.get('elements', [])
    
    # Take a screenshot
    screenshot = take_screenshot()
    if not screenshot:
        logger.error("Failed to take screenshot for UI detection")
        return []
    
    elements = []
    
    # Try different detection methods based on what's available
    if INTELLIGENT_UI_AVAILABLE and intelligent_detector:
        try:
            logger.info("Using intelligent UI detector")
            detection_result = await asyncio.to_thread(intelligent_detector.detect_elements, screenshot)
            
            if detection_result and 'elements' in detection_result:
                for elem in detection_result['elements']:
                    elements.append(UIElement(
                        element_type=elem.get('type', 'unknown'),
                        x=elem.get('x', 0),
                        y=elem.get('y', 0),
                        width=elem.get('width', 50),
                        height=elem.get('height', 30),
                        confidence=elem.get('confidence', 0.0),
                        text=elem.get('text', ''),
                        attributes=elem.get('attributes', {})
                    ))
        except Exception as e:
            logger.error(f"Error using intelligent UI detector: {e}")
    
    # Try universal detector if available and we don't have enough elements
    if UI_DETECTOR_AVAILABLE and len(elements) < 5:
        try:
            logger.info("Using universal UI element detector")
            detection_result = await asyncio.to_thread(detect_ui_elements, screenshot)
            
            if detection_result and isinstance(detection_result, list):
                for elem in detection_result:
                    elements.append(UIElement(
                        element_type=elem.get('type', 'unknown'),
                        x=elem.get('x', 0),
                        y=elem.get('y', 0),
                        width=elem.get('width', 50),
                        height=elem.get('height', 30),
                        confidence=elem.get('confidence', 0.0),
                        text=elem.get('text', ''),
                        attributes=elem.get('attributes', {})
                    ))
        except Exception as e:
            logger.error(f"Error using universal UI detector: {e}")
    
    # Fallback to basic element detection using PyAutoGUI
    if len(elements) < 3:
        try:
            logger.info("Using basic PyAutoGUI element detection")
            # PyAutoGUI has limited UI detection - mostly for images
            # Here we would implement a basic detection for common elements
            
            # For demonstration, add a few dummy elements around the mouse position
            mouse_x, mouse_y = pyautogui.position()
            
            elements.append(UIElement(
                element_type="button",
                x=mouse_x - 50,
                y=mouse_y + 50,
                width=100,
                height=30,
                confidence=0.7,
                text="Button near mouse"
            ))
            
            elements.append(UIElement(
                element_type="text_field",
                x=mouse_x - 100,
                y=mouse_y - 50,
                width=200,
                height=30,
                confidence=0.7,
                text=""
            ))
        except Exception as e:
            logger.error(f"Error with basic element detection: {e}")
    
    # Update cache
    with ui_element_cache_lock:
        ui_element_cache = {
            'elements': elements,
            'last_update': time.time()
        }
    
    logger.info(f"Detected {len(elements)} UI elements on screen")
    return elements

async def find_element_by_name(element_name, fuzzy_match=True):
    """Find a UI element by name or description"""
    elements = await detect_elements_on_screen()
    
    if not elements:
        logger.warning(f"No UI elements detected to find '{element_name}'")
        return None
    
    # Try exact match first
    for element in elements:
        if element.text.lower() == element_name.lower() or element.element_type.lower() == element_name.lower():
            logger.info(f"Found exact match for '{element_name}': {element.center}")
            return element
    
    # Try attribute match
    for element in elements:
        attrs = element.attributes
        if attrs and any(element_name.lower() in str(v).lower() for v in attrs.values()):
            logger.info(f"Found attribute match for '{element_name}': {element.center}")
            return element
    
    # Try fuzzy matching if enabled
    if fuzzy_match:
        best_match = None
        best_score = 0
        
        for element in elements:
            # Simple fuzzy matching based on substring
            element_text = element.text.lower()
            if element_name.lower() in element_text or element_text in element_name.lower():
                score = len(element_text) / max(len(element_text), len(element_name))
                if score > best_score:
                    best_score = score
                    best_match = element
            
            # Check element type too
            element_type = element.element_type.lower()
            if element_name.lower() in element_type or element_type in element_name.lower():
                score = len(element_type) / max(len(element_type), len(element_name)) * 0.8  # Lower weight for type match
                if score > best_score:
                    best_score = score
                    best_match = element
        
        if best_match and best_score > 0.3:  # Threshold
            logger.info(f"Found fuzzy match for '{element_name}': {best_match.center} (score: {best_score:.2f})")
            return best_match
    
    logger.warning(f"No matching element found for '{element_name}'")
    return None

def get_element_position(element_name, default_fallback=True):
    """Get the position of a UI element by name, with intelligent detection"""
    # Fast path for common elements
    if element_name in DEFAULT_UI_ELEMENTS:
        return DEFAULT_UI_ELEMENTS[element_name]
    
    # Use ThreadPoolExecutor to run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Create a new event loop if we're not in an async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    element = loop.run_until_complete(find_element_by_name(element_name))
    
    if element:
        logger.info(f"Found position for '{element_name}': {element.center}")
        return element.center
    
    # Apply default fallbacks if requested
    if default_fallback:
        element_lower = element_name.lower()
        
        if 'button' in element_lower:
            logger.info(f"Using default button position for '{element_name}'")
            return DEFAULT_UI_ELEMENTS['default_button']
        
        if any(field in element_lower for field in ['field', 'box', 'input', 'text']):
            logger.info(f"Using default field position for '{element_name}'")
            return DEFAULT_UI_ELEMENTS['default_field']
        
        # Generate a position based on screen size
        if input_controller:
            screen_width, screen_height = input_controller.screen_width, input_controller.screen_height
            x = random.randint(int(screen_width * 0.2), int(screen_width * 0.8))
            y = random.randint(int(screen_height * 0.2), int(screen_height * 0.8))
            logger.warning(f"Using random position for '{element_name}': ({x}, {y})")
            return (x, y)
    
    # Default to center of screen
    if input_controller:
        screen_width, screen_height = input_controller.screen_width, input_controller.screen_height
        return (screen_width // 2, screen_height // 2)
    else:
        return (500, 500)  # Fallback default

async def execute_step(step, step_index):
    """Execute a single step in the plan using real automation"""
    global input_controller
    
    if not input_controller:
        logger.error("Cannot execute step - Input controller not available")
        return False
    
    try:
        # Get action type from the step
        action_type = step.get('type', '').lower()
        if not action_type:
            action_type = step.get('action_type', '').lower()
        
        target = step.get('target', '')
        description = step.get('description', f'Step {step_index + 1}')
        
        logger.info(f"Executing step {step_index + 1}: {action_type} - {description}")
        
        # Different handling based on action type
        if action_type == 'click' or action_type == 'click_element':
            # Find target coordinates
            coords = None
            
            # Check if coordinates are directly provided
            coordinates = step.get('coordinates')
            if coordinates:
                try:
                    if isinstance(coordinates, list) and len(coordinates) >= 2:
                        coords = (int(float(coordinates[0])), int(float(coordinates[1])))
                    elif isinstance(coordinates, dict) and 'x' in coordinates and 'y' in coordinates:
                        coords = (int(float(coordinates['x'])), int(float(coordinates['y'])))
                    elif isinstance(coordinates, str):
                        coords_str = coordinates.strip('[]()').replace(' ', '').split(',')
                        if len(coords_str) >= 2:
                            coords = (int(float(coords_str[0])), int(float(coords_str[1])))
                except Exception as e:
                    logger.warning(f"Error parsing coordinates: {e}")
            
            # If no coordinates provided, try to find the element on screen
            if not coords and target:
                # First try intelligent element detection
                element = await find_element_by_name(target)
                if element:
                    coords = element.center
                else:
                    # Fall back to predefined positions
                    coords = get_element_position(target)
            
            # If still no coordinates, use screen center
            if not coords:
                screen_width, screen_height = input_controller.screen_width, input_controller.screen_height
                coords = (screen_width // 2, screen_height // 2)
                logger.warning(f"No coordinates found, using screen center: {coords}")
            
            # Perform the click
            logger.info(f"Clicking at {coords}")
            input_controller.click(coords[0], coords[1])
            await asyncio.sleep(0.5)
            return True
        
        elif action_type == 'text' or action_type == 'type_text':
            # Get text to type
            text = step.get('text', '')
            if not text:
                text = step.get('value', '')
            
            if not text:
                logger.error("No text provided for typing action")
                return False
            
            # Find target field coordinates if needed
            if target:
                # Try intelligent element detection
                element = await find_element_by_name(target)
                if element:
                    coords = element.center
                else:
                    # Fall back to predefined positions
                    coords = get_element_position(target)
                
                # Click on the field first
                logger.info(f"Clicking on field at {coords}")
                input_controller.click(coords[0], coords[1])
                await asyncio.sleep(0.5)
            
            # Type the text
            logger.info(f"Typing text: '{text}'")
            input_controller.type_text(text)
            await asyncio.sleep(0.5)
            return True
        
        elif action_type == 'hotkey':
            # Get keys to press
            keys = step.get('keys', [])
            if not keys:
                key = step.get('key', '')
                if key and '+' in key:
                    keys = key.split('+')
            
            if not keys:
                logger.error("No keys provided for hotkey action")
                return False
            
            # Press the hotkey
            logger.info(f"Pressing hotkey: {'+'.join(keys) if isinstance(keys, list) else keys}")
            if isinstance(keys, list):
                input_controller.hotkey(*keys)
            else:
                # Handle combined hotkeys (e.g., "command+a")
                if '+' in keys:
                    key_combo = keys.split('+')
                    input_controller.hotkey(*key_combo)
                else:
                    input_controller.press_key(keys)
            
            await asyncio.sleep(0.5)
            return True
        
        elif action_type == 'press' or action_type == 'press_key':
            # Get key to press
            key = step.get('key', '')
            if not key:
                logger.error("No key provided for press action")
                return False
            
            # Press the key
            logger.info(f"Pressing key: {key}")
            input_controller.press_key(key)
            await asyncio.sleep(0.5)
            return True
        
        elif action_type == 'scroll':
            # Get scroll amount
            clicks = int(step.get('clicks', 0))
            
            # Perform scrolling
            logger.info(f"Scrolling {clicks} clicks")
            input_controller.scroll(clicks)
            await asyncio.sleep(0.5)
            return True
        
        elif action_type == 'drag':
            # Get target coordinates
            source = None
            target = None
            
            source_elem = step.get('source', '')
            target_elem = step.get('target', '')
            
            if source_elem:
                # Try intelligent element detection
                element = await find_element_by_name(source_elem)
                if element:
                    source = element.center
                else:
                    # Fall back to predefined positions
                    source = get_element_position(source_elem)
            
            if target_elem:
                # Try intelligent element detection
                element = await find_element_by_name(target_elem)
                if element:
                    target = element.center
                else:
                    # Fall back to predefined positions
                    target = get_element_position(target_elem)
            
            if not source or not target:
                logger.error(f"Cannot find coordinates for drag operation")
                return False
            
            # Move to source
            logger.info(f"Moving to {source}")
            input_controller.move_to(source[0], source[1])
            await asyncio.sleep(0.5)
            
            # Perform drag
            logger.info(f"Dragging from {source} to {target}")
            input_controller.drag_to(target[0], target[1])
            await asyncio.sleep(0.5)
            return True
        
        elif action_type == 'wait':
            # Get wait duration, default to 1 second
            wait_time = float(step.get('duration', 1.0))
            if not wait_time:
                wait_time = float(step.get('estimated_duration', 1.0))
            
            # Cap wait time at 5 seconds for safety
            wait_time = min(wait_time, 5.0)
            
            logger.info(f"Waiting for {wait_time} seconds")
            await asyncio.sleep(wait_time)
            return True
        
        elif action_type == 'open_app' or action_type == 'launch_app':
            app_name = step.get('target', '')
            if not app_name:
                app_name = step.get('app_name', '')
                
            if not app_name:
                logger.error("No app name provided for open_app action")
                return False
            
            # Use Spotlight to open the app (Cmd+Space)
            logger.info(f"Opening app: {app_name}")
            input_controller.hotkey('command', 'space')
            await asyncio.sleep(1.0)
            
            # Type the app name
            input_controller.type_text(app_name)
            await asyncio.sleep(0.5)
            
            # Press Enter to launch
            input_controller.press_key('enter')
            await asyncio.sleep(2.0)
            return True
        
        elif action_type == 'navigate_url' or action_type == 'navigate_to':
            url = step.get('url', '')
            if not url:
                url = step.get('value', '')
            
            if not url:
                logger.error("No URL provided for navigate_url action")
                return False
            
            # Focus address bar (Cmd+L)
            logger.info(f"Navigating to URL: {url}")
            input_controller.hotkey('command', 'l')
            await asyncio.sleep(0.5)
            
            # Type the URL
            input_controller.type_text(url)
            await asyncio.sleep(0.5)
            
            # Press Enter to navigate
            input_controller.press_key('enter')
            await asyncio.sleep(2.0)
            return True
        
        elif action_type == 'analyze_screen' or action_type == 'observe':
            # Actively analyze the screen to update UI element cache
            logger.info(f"Analyzing screen for UI elements")
            elements = await detect_elements_on_screen()
            logger.info(f"Found {len(elements)} UI elements")
            await asyncio.sleep(0.5)
            return True
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
            await asyncio.sleep(0.5)
            # Return true for unknown actions to continue execution
            return True
    
    except Exception as e:
        logger.error(f"Error executing step {step_index}: {e}")
        logger.error(traceback.format_exc())
        return False

async def execute_plan(plan, session_id, websocket):
    """Execute a plan using real automation"""
    global execution_count
    
    try:
        start_time = time.time()
        plan_title = plan.get('title', 'Unknown Plan')
        
        # Check if steps exist in the plan
        steps = None
        
        # Handle different plan formats
        if isinstance(plan, dict):
            steps = plan.get('steps', [])
            if not steps and 'execution_plan' in plan:
                # Handle nested execution_plan format
                execution_plan = plan.get('execution_plan', {})
                if isinstance(execution_plan, dict):
                    steps = execution_plan.get('steps', [])
        
        if not steps:
            logger.warning(f"No steps found in plan {plan_title}")
            await websocket.send(json.dumps({
                "type": "agent_progress",
                "session_id": session_id,
                "step": 1,
                "progress": 50,
                "message": "⚠️ Plan has no steps to execute"
            }))
            
            await asyncio.sleep(0.5)
            
            await websocket.send(json.dumps({
                "type": "agent_execution_success",
                "session_id": session_id,
                "result": {
                    "success": False,
                    "steps_executed": 0,
                    "execution_time": time.time() - start_time
                },
                "summary": "⚠️ Could not execute plan: No steps found",
                "execution_completed": True
            }))
            return False
        
        # Initial UI analysis to populate element cache
        logger.info("Analyzing current screen before execution")
        await detect_elements_on_screen()
        
        # Send initial progress
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 1,
            "progress": 10,
            "message": f"🚀 Starting execution: {plan_title}"
        }))
        
        executed_steps = 0
        total_steps = len(steps)
        
        # Execute each step
        for i, step in enumerate(steps):
            step_desc = step.get('description', f'Step {i+1}')
            progress = int(((i + 1) / total_steps) * 100)
            
            # Send progress update
            await websocket.send(json.dumps({
                "type": "agent_progress",
                "session_id": session_id,
                "step": i + 1,
                "progress": progress,
                "message": f"⚡ Executing: {step_desc}"
            }))
            
            # Execute the step with real input
            success = await execute_step(step, i)
            
            if success:
                executed_steps += 1
                logger.info(f"✅ Step {i+1} executed successfully: {step_desc}")
                
                # Analyze screen after every few steps to update UI element cache
                if (i + 1) % 3 == 0 or i == 0:
                    logger.info("Refreshing UI element detection")
                    await detect_elements_on_screen()
            else:
                logger.warning(f"❌ Step {i+1} failed: {step_desc}")
                
                # Try one more time with fresh UI element detection
                logger.info("Retrying with fresh UI element detection")
                await detect_elements_on_screen()
                success = await execute_step(step, i)
                
                if success:
                    executed_steps += 1
                    logger.info(f"✅ Step {i+1} executed successfully on retry: {step_desc}")
            
            # Small delay between steps
            await asyncio.sleep(0.5)
        
        # Send completion message
        execution_time = time.time() - start_time
        execution_count += 1
        
        success_rate = (executed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        # Format success message based on execution results
        if executed_steps == total_steps:
            summary = f"✅ EXECUTION SUCCESSFUL: All {total_steps} steps completed"
            success = True
        elif executed_steps > 0:
            summary = f"⚠️ PARTIAL EXECUTION: {executed_steps}/{total_steps} steps completed ({success_rate:.0f}%)"
            success = True  # Still consider it a success if some steps worked
        else:
            summary = "❌ EXECUTION FAILED: No steps could be executed"
            success = False
        
        # Send final success message
        await websocket.send(json.dumps({
            "type": "agent_execution_success",
            "session_id": session_id,
            "result": {
                "success": success,
                "steps_executed": executed_steps,
                "total_steps": total_steps,
                "execution_time": execution_time,
                "success_rate": success_rate
            },
            "summary": summary,
            "execution_completed": True
        }))
        
        logger.info(f"Plan execution completed: {executed_steps}/{total_steps} steps, {execution_time:.2f}s")
        return True
    
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        logger.error(traceback.format_exc())
        
        # Send error message
        await websocket.send(json.dumps({
            "type": "agent_execution_success",
            "session_id": session_id,
            "result": {
                "success": False,
                "steps_executed": 0,
                "execution_time": time.time() - start_time,
                "error": str(e)
            },
            "summary": f"❌ EXECUTION ERROR: {str(e)}",
            "execution_completed": True
        }))
        return False

async def websocket_handler(websocket, path=None):
    """WebSocket connection handler with correct function signature"""
    global connected_clients, current_plan, execution_count
    
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    
    try:
        # Log connection
        logger.info(f"Client {client_id} connected from {client_ip}")
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to intelligent DO button server on port 8765",
            "server_time": datetime.now().isoformat(),
            "server_name": "Intelligent DO Button Server",
            "real_input": INPUT_CONTROLLER_AVAILABLE,
            "intelligent_ui": UI_DETECTOR_AVAILABLE or INTELLIGENT_UI_AVAILABLE
        }
        
        await websocket.send(json.dumps(welcome_message))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', '').lower()
                
                logger.info(f"Received message type: {msg_type}")
                
                # Store plan if received
                if msg_type == 'plan_created':
                    current_plan = data.get('plan')
                    session_id = data.get('session_id', '')
                    logger.info(f"Stored plan for session {session_id}: {current_plan.get('title', 'Untitled Plan')}")
                
                # Execute plan on DO button click
                elif (msg_type == 'agent_confirmation' and data.get('action', '').upper() in ['DO', 'EXECUTE']):
                    session_id = data.get('session_id', '')
                    
                    if current_plan:
                        logger.info(f"Executing plan for session {session_id}")
                        await execute_plan(current_plan, session_id, websocket)
                    else:
                        logger.error(f"No plan available for execution")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "No plan available for execution",
                            "session_id": session_id
                        }))
                
                # Also support button_action format
                elif (msg_type == 'button_action' and data.get('action', '').upper() in ['EXECUTE_PLAN', 'DO']):
                    plan_id = data.get('plan_id', '')
                    
                    if current_plan:
                        logger.info(f"Executing plan for {plan_id}")
                        await execute_plan(current_plan, plan_id, websocket)
                    else:
                        logger.error(f"No plan available for execution")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "No plan available for execution",
                            "plan_id": plan_id
                        }))
                
                # Command to analyze the screen
                elif msg_type == 'analyze_screen':
                    logger.info("Analyzing screen on demand")
                    elements = await detect_elements_on_screen()
                    
                    # Send analysis results
                    await websocket.send(json.dumps({
                        "type": "screen_analysis",
                        "elements": [elem.to_dict() for elem in elements],
                        "count": len(elements),
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Command to locate an element
                elif msg_type == 'find_element':
                    element_name = data.get('element_name', '')
                    fuzzy = data.get('fuzzy_match', True)
                    
                    if element_name:
                        logger.info(f"Finding element: {element_name}")
                        element = await find_element_by_name(element_name, fuzzy)
                        
                        if element:
                            await websocket.send(json.dumps({
                                "type": "element_found",
                                "element_name": element_name,
                                "element": element.to_dict(),
                                "success": True
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "type": "element_found",
                                "element_name": element_name,
                                "success": False,
                                "error": "Element not found"
                            }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "No element name provided"
                        }))
                
                # Echo response for other message types
                else:
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "original_type": msg_type,
                        "message": f"Received {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(traceback.format_exc())
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e)
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def heartbeat():
    """Send periodic heartbeat to all connected clients"""
    while True:
        if connected_clients:
            heartbeat_msg = json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "connected_clients": len(connected_clients),
                "executions": execution_count
            })
            
            for client in list(connected_clients):
                try:
                    await client.send(heartbeat_msg)
                except:
                    # Will be cleaned up in the handler
                    pass
        
        await asyncio.sleep(30)

async def status_logger():
    """Log periodic status updates"""
    while True:
        logger.info(f"Server status: {len(connected_clients)} clients connected, {execution_count} executions completed")
        await asyncio.sleep(60)

def free_port(port):
    """Force close any process using the specified port"""
    if sys.platform == "win32":
        os.system(f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port}\') do taskkill /F /PID %a')
    else:  # Unix-like
        os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null || true")

async def main():
    # Ensure port is available
    port = 8765
    host = "0.0.0.0"  # Listen on all interfaces
    
    # Free the port
    free_port(port)
    await asyncio.sleep(1)
    
    logger.info(f"Starting Intelligent DO Button Server on {host}:{port}")
    
    # Start the server with correct parameters
    server = await websockets.serve(
        websocket_handler,
        host,
        port,
        ping_interval=30,
        ping_timeout=60,
        close_timeout=30
    )
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open("pids/intelligent_do_button_server.pid", "w") as f:
        f.write(str(os.getpid()))
    
    # Start background tasks
    heartbeat_task = asyncio.create_task(heartbeat())
    status_task = asyncio.create_task(status_logger())
    
    logger.info(f"✅ Intelligent DO Button Server running on ws://{host}:{port}")
    if INPUT_CONTROLLER_AVAILABLE:
        logger.info("🎮 Physical automation ready - REAL mouse and keyboard actions enabled")
    else:
        logger.info("⚠️ Input controller not available - automation will be simulated")
    
    if UI_DETECTOR_AVAILABLE or INTELLIGENT_UI_AVAILABLE:
        logger.info("🔍 Intelligent UI detection active - automatic element recognition enabled")
    else:
        logger.info("⚠️ UI detection partially available - using fallback methods")
    
    # Keep running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        if "--debug" in sys.argv:
            logger.setLevel(logging.DEBUG)
            
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        # Clean up
        if input_controller:
            input_controller.stop()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)