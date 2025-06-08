#!/usr/bin/env python3
"""
Direct Coordinate Automation System
Provides reliable automation through direct coordinate specification
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
import traceback
import base64
import io
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageGrab

# Configure logging
os.makedirs('logs/websocket', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/direct_coordinate_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('direct_coordinate_automation')

# Try to import input controller for real automation
try:
    from agent_workflow.input_controller import InputController
    try:
        input_controller = InputController(safety_level="medium")
        INPUT_CONTROLLER_AVAILABLE = True
        logger.info("✅ Input controller loaded successfully")
    except Exception as e:
        logger.error(f"⚠️ Input controller initialization failed: {e}")
        INPUT_CONTROLLER_AVAILABLE = False
        input_controller = None
except ImportError as e:
    logger.error(f"⚠️ Input controller module not available: {e}")
    INPUT_CONTROLLER_AVAILABLE = False
    input_controller = None

# Track connected clients and execution stats
connected_clients = set()
execution_count = 0
current_plan = None

async def execute_step(step, step_index):
    """Execute a single step with direct coordinate specifications"""
    global input_controller
    
    if not input_controller or not INPUT_CONTROLLER_AVAILABLE:
        logger.error("Cannot execute step - Input controller not available")
        return False
    
    try:
        # Get action type from the step
        action_type = step.get('type', '').lower()
        if not action_type:
            action_type = step.get('action_type', '').lower()
        
        description = step.get('description', f'Step {step_index + 1}')
        logger.info(f"Executing step {step_index + 1}: {action_type} - {description}")
        
        # Different handling based on action type
        if action_type == 'click' or action_type == 'click_element':
            # Get coordinates - DIRECT APPROACH
            coords = None
            
            # First try direct coordinates
            x = step.get('x')
            y = step.get('y')
            if x is not None and y is not None:
                coords = (int(float(x)), int(float(y)))
                logger.info(f"Using direct x,y coordinates: {coords}")
            
            # Next try coordinates array/object
            if not coords:
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
            
            # Default to screen center if needed
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
            
            # Type the text
            logger.info(f"Typing text: '{text}'")
            input_controller.type_text(text)
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
        
        elif action_type == 'move' or action_type == 'move_mouse':
            # Get coordinates - DIRECT APPROACH
            coords = None
            
            # First try direct coordinates
            x = step.get('x')
            y = step.get('y')
            if x is not None and y is not None:
                coords = (int(float(x)), int(float(y)))
                logger.info(f"Using direct x,y coordinates: {coords}")
            
            # Next try coordinates array/object
            if not coords:
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
            
            # Default to screen center if needed
            if not coords:
                screen_width, screen_height = input_controller.screen_width, input_controller.screen_height
                coords = (screen_width // 2, screen_height // 2)
                logger.warning(f"No coordinates found, using screen center: {coords}")
            
            # Move the mouse
            logger.info(f"Moving mouse to {coords}")
            input_controller.move_to(coords[0], coords[1])
            await asyncio.sleep(0.5)
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
    """Execute a plan using direct coordinate automation"""
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
            
            # Execute the step with direct coordinates
            success = await execute_step(step, i)
            
            if success:
                executed_steps += 1
                logger.info(f"✅ Step {i+1} executed successfully: {step_desc}")
            else:
                logger.warning(f"❌ Step {i+1} failed: {step_desc}")
                
                # Try again with a retry
                logger.info(f"Retrying step {i+1}...")
                await asyncio.sleep(1.0)  # Wait a bit before retry
                retry_success = await execute_step(step, i)
                
                if retry_success:
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

# Screen sharing variables
screen_sharing_clients = set()
screen_capture_active = False
screen_sharing_fps = 5
screen_sharing_quality = 70
last_screen_capture_time = 0

async def capture_and_send_screen():
    """Capture the screen and send it to all screen sharing clients"""
    global last_screen_capture_time
    
    # Check if any clients want screen sharing
    if not screen_sharing_clients:
        return
        
    try:
        # Get current time
        current_time = time.time()
        
        # Limit frame rate to avoid excessive CPU usage
        if current_time - last_screen_capture_time < 1.0 / screen_sharing_fps:
            return
            
        last_screen_capture_time = current_time
        
        # Capture the screen
        screenshot = ImageGrab.grab()
        width, height = screenshot.size
        
        # Convert RGBA to RGB (remove alpha channel) before saving as JPEG
        if screenshot.mode == 'RGBA':
            rgb_image = Image.new('RGB', screenshot.size, (255, 255, 255))
            rgb_image.paste(screenshot, mask=screenshot.split()[3])  # Use alpha channel as mask
            screenshot = rgb_image
        
        # Convert to JPEG
        img_byte_array = io.BytesIO()
        screenshot.save(img_byte_array, format='JPEG', quality=screen_sharing_quality)
        img_byte_array.seek(0)
        
        # Encode as base64
        img_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
        
        # Prepare frame data
        frame_data = {
            "type": "screen_frame",
            "width": width,
            "height": height,
            "format": "jpeg",
            "compression": screen_sharing_quality,
            "timestamp": current_time,
            "data": img_base64,
            "fps": screen_sharing_fps,
            "frame_id": int(current_time * 1000)
        }
        
        # Send to all screen sharing clients
        frame_json = json.dumps(frame_data)
        
        for client in screen_sharing_clients:
            try:
                await client.send(frame_json)
                logger.debug(f"Sent screen frame to client, size: {len(img_base64) // 1024}KB")
            except Exception as e:
                logger.error(f"Error sending screen frame to client: {e}")
                # Will be cleaned up in the heartbeat
                
    except Exception as e:
        logger.error(f"Error capturing screen: {e}")
        logger.error(traceback.format_exc())

async def websocket_handler(websocket, path=None):
    """WebSocket connection handler with correct function signature"""
    global connected_clients, current_plan, execution_count, screen_sharing_clients, screen_capture_active, screen_sharing_fps, screen_sharing_quality
    
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    is_screen_sharing = False
    
    try:
        # Log connection
        logger.info(f"Client {client_id} connected from {client_ip}")
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to direct coordinate automation server on port 8765",
            "server_time": datetime.now().isoformat(),
            "server_name": "Direct Coordinate Automation Server",
            "real_input": INPUT_CONTROLLER_AVAILABLE,
            "screen_sharing_supported": True
        }
        
        await websocket.send(json.dumps(welcome_message))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', '').lower()
                
                logger.info(f"Received message type: {msg_type}")
                
                # ---- SCREEN SHARING HANDLERS ----
                
                # Start screen sharing
                if msg_type in ['start_screen_sharing', 'screen_capture'] and data.get('action', '') != 'stop':
                    logger.info(f"Screen sharing requested by client {client_id}")
                    
                    # Add to screen sharing clients
                    screen_sharing_clients.add(websocket)
                    is_screen_sharing = True
                    
                    # Update capture settings
                    if 'fps' in data:
                        try:
                            requested_fps = float(data['fps'])
                            screen_sharing_fps = min(max(1, requested_fps), 30)  # Limit between 1-30 fps
                        except (ValueError, TypeError):
                            pass
                            
                    if 'compression' in data or 'quality' in data:
                        try:
                            quality = data.get('compression', data.get('quality', 70))
                            screen_sharing_quality = min(max(10, int(quality)), 95)  # Limit between 10-95%
                        except (ValueError, TypeError):
                            pass
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "screen_sharing_started",
                        "fps": screen_sharing_fps,
                        "quality": screen_sharing_quality,
                        "message": "Screen sharing started"
                    }))
                    
                    # Start screen capture if not already running
                    if not screen_capture_active:
                        screen_capture_active = True
                        logger.info("Screen capture activated")
                    
                    # Send initial screen immediately
                    await capture_and_send_screen()
                
                # Stop screen sharing
                elif (msg_type == 'stop_screen_sharing' or 
                      (msg_type == 'screen_capture' and data.get('action', '') == 'stop')):
                    logger.info(f"Screen sharing stop requested by client {client_id}")
                    
                    # Remove from screen sharing clients
                    if websocket in screen_sharing_clients:
                        screen_sharing_clients.remove(websocket)
                        is_screen_sharing = False
                    
                    # Stop screen capture if no clients left
                    if not screen_sharing_clients and screen_capture_active:
                        screen_capture_active = False
                        logger.info("Screen capture deactivated")
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "screen_sharing_stopped",
                        "message": "Screen sharing stopped"
                    }))
                
                # Get a single screenshot
                elif msg_type == 'get_screenshot':
                    logger.info(f"Screenshot requested by client {client_id}")
                    
                    try:
                        # Capture screen
                        screenshot = ImageGrab.grab()
                        width, height = screenshot.size
                        
                        # Convert to JPEG with requested quality
                        quality = min(max(10, int(data.get('quality', 70))), 95)
                        img_byte_array = io.BytesIO()
                        screenshot.save(img_byte_array, format='JPEG', quality=quality)
                        img_byte_array.seek(0)
                        
                        # Encode as base64
                        img_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
                        
                        # Send screenshot
                        await websocket.send(json.dumps({
                            "type": "screenshot",
                            "width": width,
                            "height": height,
                            "format": "jpeg",
                            "compression": quality,
                            "timestamp": time.time(),
                            "data": img_base64
                        }))
                        
                        logger.info(f"Screenshot sent to client {client_id}")
                    except Exception as e:
                        logger.error(f"Error capturing screenshot: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Failed to capture screenshot: {str(e)}"
                        }))
                
                # ---- AUTOMATION HANDLERS ----
                
                # Store plan if received
                elif msg_type == 'plan_created':
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
                
                # Direct mouse click at specific coordinates
                elif msg_type == 'direct_click':
                    x = data.get('x')
                    y = data.get('y')
                    
                    if x is not None and y is not None:
                        logger.info(f"Direct click requested at ({x}, {y})")
                        
                        if INPUT_CONTROLLER_AVAILABLE and input_controller:
                            # Create a simple plan for the click
                            direct_plan = {
                                'title': f'Direct Click at ({x}, {y})',
                                'steps': [
                                    {
                                        'type': 'click',
                                        'x': x,
                                        'y': y,
                                        'description': f'Click at ({x}, {y})'
                                    }
                                ]
                            }
                            
                            # Execute the plan
                            session_id = data.get('session_id', f'direct_{int(time.time())}')
                            await execute_plan(direct_plan, session_id, websocket)
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": "Input controller not available for direct clicking"
                            }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "Missing x, y coordinates for direct click"
                        }))
                
                # Direct text typing
                elif msg_type == 'direct_type':
                    text = data.get('text')
                    
                    if text:
                        logger.info(f"Direct typing requested: '{text}'")
                        
                        if INPUT_CONTROLLER_AVAILABLE and input_controller:
                            # Create a simple plan for typing
                            direct_plan = {
                                'title': 'Direct Text Input',
                                'steps': [
                                    {
                                        'type': 'type_text',
                                        'value': text,
                                        'description': f'Type text: {text}'
                                    }
                                ]
                            }
                            
                            # Execute the plan
                            session_id = data.get('session_id', f'direct_{int(time.time())}')
                            await execute_plan(direct_plan, session_id, websocket)
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": "Input controller not available for direct typing"
                            }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "Missing text for direct typing"
                        }))
                
                # Get screen size
                elif msg_type == 'get_screen_size':
                    if INPUT_CONTROLLER_AVAILABLE and input_controller:
                        screen_width, screen_height = input_controller.screen_width, input_controller.screen_height
                        await websocket.send(json.dumps({
                            "type": "screen_size",
                            "width": screen_width,
                            "height": screen_height
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "Input controller not available for screen size"
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
        
        # Clean up screen sharing
        if is_screen_sharing and websocket in screen_sharing_clients:
            screen_sharing_clients.remove(websocket)
            
            # Stop screen capture if no clients left
            if not screen_sharing_clients and screen_capture_active:
                screen_capture_active = False
                logger.info("Screen capture deactivated due to client disconnect")
                
        logger.info(f"Client {client_id} disconnected")

async def heartbeat():
    """Send periodic heartbeat to all connected clients and handle screen sharing"""
    global screen_capture_active, last_screen_capture_time
    
    while True:
        # Send heartbeat to clients
        if connected_clients:
            heartbeat_msg = json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "connected_clients": len(connected_clients),
                "executions": execution_count,
                "screen_sharing_active": screen_capture_active,
                "screen_sharing_clients": len(screen_sharing_clients)
            })
            
            for client in list(connected_clients):
                try:
                    await client.send(heartbeat_msg)
                except:
                    # Will be cleaned up in the handler
                    pass
        
        # Handle screen sharing if active
        if screen_capture_active and screen_sharing_clients:
            try:
                await capture_and_send_screen()
            except Exception as e:
                logger.error(f"Error in screen sharing heartbeat: {e}")
        
        await asyncio.sleep(1 if screen_capture_active else 30)

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
    
    # Start the server with correct parameters
    try:
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
        with open("pids/direct_coordinate_automation.pid", "w") as f:
            f.write(str(os.getpid()))
        
        # Start background tasks
        heartbeat_task = asyncio.create_task(heartbeat())
        status_task = asyncio.create_task(status_logger())
        
        logger.info(f"✅ Direct Coordinate Automation Server running on ws://{host}:{port}")
        if INPUT_CONTROLLER_AVAILABLE:
            logger.info("🎮 Physical automation ready - REAL mouse and keyboard actions enabled")
        else:
            logger.info("⚠️ Input controller not available - automation will be simulated")
        
        # Keep running
        await asyncio.Future()
    
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

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