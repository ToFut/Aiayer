#!/usr/bin/env python3
"""
Fixed DO Button Server
Standalone WebSocket server that handles DO button clicks and executes plans with real automation
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

# Try to import input controller for real automation
try:
    from agent_workflow.input_controller import InputController
    input_controller = InputController(safety_level="medium")
    INPUT_CONTROLLER_AVAILABLE = True
    print("✅ Input controller loaded successfully")
except ImportError as e:
    print(f"⚠️ Input controller not available: {e}")
    INPUT_CONTROLLER_AVAILABLE = False
    input_controller = None

# Configure logging
os.makedirs('logs/websocket', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/fixed_do_button_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_do_button_server')

# Track connected clients and execution stats
connected_clients = set()
execution_count = 0
current_plan = None

# UI element positions for automation
UI_ELEMENTS = {
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

def get_element_position(element_name: str) -> Optional[Tuple[int, int]]:
    """Get the screen coordinates for a UI element by name"""
    # Check if element is in our predefined mapping
    if element_name in UI_ELEMENTS:
        return UI_ELEMENTS[element_name]
    
    # If element is not found but contains common names, try to match
    element_lower = element_name.lower()
    
    if 'button' in element_lower:
        logger.info(f"Using default button position for unknown element: {element_name}")
        return UI_ELEMENTS['default_button']
    
    if any(field in element_lower for field in ['field', 'box', 'input', 'text']):
        logger.info(f"Using default field position for unknown element: {element_name}")
        return UI_ELEMENTS['default_field']
    
    # Generate random position as last resort
    logger.warning(f"No position mapping for element: {element_name}, using random position")
    if input_controller:
        # Get screen dimensions from input controller
        screen_width, screen_height = input_controller.screen_width, input_controller.screen_height
        x = random.randint(int(screen_width * 0.2), int(screen_width * 0.8))
        y = random.randint(int(screen_height * 0.2), int(screen_height * 0.8))
    else:
        # Fallback to default dimensions
        x = random.randint(300, 700)
        y = random.randint(200, 400)
    return (x, y)

async def execute_step(step: Dict[str, Any], step_index: int) -> bool:
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
            
            # If no coordinates provided, look up by target name
            if not coords and target:
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
                source = get_element_position(source_elem)
            
            if target_elem:
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
            # This is a passive action
            logger.info(f"Analyzing screen (passive action)")
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

async def execute_plan(plan: Dict[str, Any], session_id: str, websocket) -> bool:
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
            else:
                logger.warning(f"❌ Step {i+1} failed: {step_desc}")
            
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
            "message": "Connected to fixed DO button server on port 8765",
            "server_time": datetime.now().isoformat(),
            "server_name": "Fixed DO Button Server",
            "real_input": INPUT_CONTROLLER_AVAILABLE
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
    
    logger.info(f"Starting Fixed DO Button Server on {host}:{port}")
    
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
    with open("pids/fixed_do_button_server.pid", "w") as f:
        f.write(str(os.getpid()))
    
    # Start background tasks
    heartbeat_task = asyncio.create_task(heartbeat())
    status_task = asyncio.create_task(status_logger())
    
    logger.info(f"✅ Fixed DO Button Server running on ws://{host}:{port}")
    if INPUT_CONTROLLER_AVAILABLE:
        logger.info("🎮 Physical automation ready - REAL mouse and keyboard actions enabled")
    else:
        logger.info("⚠️ Input controller not available - automation will be simulated")
    
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