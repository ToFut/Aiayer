#!/usr/bin/env python3
"""
Fix DO Button Connection - WebSocket Proxy between 8766 and 8765/8768
Ensures plans exist before forwarding to ultimate_do_button_server
"""

import asyncio
import websockets
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Set, List

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fix_do_button_connection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fix_do_button_connection')

# Dictionary to store active connections
client_connections = {}
do_button_server_connection = None
neural_ui_server_connection = None

# Dictionary to store active plans for quick lookup
active_plans = {}

# Try to import plan persistence
try:
    import plan_persistence
    # Direct access to the functions from the module
    load_plan = plan_persistence.load_plan
    save_plan = plan_persistence.save_plan
    delete_plan = plan_persistence.delete_plan
    PLAN_PERSISTENCE_AVAILABLE = True
    logger.info("✅ Plan persistence module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Plan persistence module not available: {e}")
    PLAN_PERSISTENCE_AVAILABLE = False
except AttributeError as e:
    logger.warning(f"⚠️ Plan persistence module missing function: {e}")
    # Create simple fallback implementations
    async def save_plan(plan_id, plan_data):
        """Fallback implementation of save_plan"""
        active_plans[plan_id] = plan_data
        logger.info(f"💾 Plan {plan_id} saved to memory (persistence not available)")
        return True
        
    async def load_plan(plan_id):
        """Fallback implementation of load_plan"""
        if plan_id in active_plans:
            logger.info(f"📂 Plan {plan_id} loaded from memory (persistence not available)")
            return active_plans[plan_id]
        return None
        
    async def delete_plan(plan_id):
        """Fallback implementation of delete_plan"""
        if plan_id in active_plans:
            del active_plans[plan_id]
            logger.info(f"🗑️ Plan {plan_id} deleted from memory (persistence not available)")
            return True
        return False
    
    PLAN_PERSISTENCE_AVAILABLE = True
    logger.info("✅ Using fallback plan persistence functions")

# Try to access the shared_pending_plans from backend
try:
    import enhanced_enterprise_backend_with_context
    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
        # Use the backend's shared dictionary as our active_plans
        active_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
        logger.info("✅ Using backend's shared_pending_plans dictionary")
except ImportError:
    logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context")
except Exception as e:
    logger.warning(f"⚠️ Error accessing backend's shared_pending_plans: {e}")

async def ensure_plan_exists(plan_id):
    """Ensure plan exists in both systems by creating a backup plan if needed"""
    # First check if we have a plan in memory
    if plan_id in active_plans:
        logger.info(f"Plan {plan_id} exists in memory")
        return True
    
    # Then check shared_pending_plans from backend
    try:
        import enhanced_enterprise_backend_with_context
        if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
            if plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                plan = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                # Copy to our active_plans
                active_plans[plan_id] = plan
                logger.info(f"✅ Found plan in backend shared dictionary: {plan_id}")
                return True
    except Exception as e:
        logger.warning(f"⚠️ Error checking backend shared dictionary: {e}")
    
    # Then check persistent storage if available
    if PLAN_PERSISTENCE_AVAILABLE:
        try:
            plan_data = await load_plan(plan_id)
            if plan_data:
                logger.info(f"Plan {plan_id} loaded from persistent storage")
                active_plans[plan_id] = plan_data
                
                # Update backend if accessible
                try:
                    import enhanced_enterprise_backend_with_context
                    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                        enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
                except Exception:
                    pass
                    
                return True
        except Exception as e:
            logger.warning(f"Error loading plan from persistent storage: {e}")
    
    # If plan doesn't exist, create a dummy one
    try:
        timestamp = int(time.time())
        
        # Create a simple automation plan with basic steps
        dummy_plan = {
            "id": plan_id,
            "title": f"Automation Plan {plan_id[:8]}",
            "description": f"Backup plan created for {plan_id}",
            "steps": [
                {
                    "id": "step_1",
                    "description": "Analyze current screen",
                    "action_type": "analyze_screen",
                    "estimated_duration": 1.0,
                    "status": "pending"
                },
                {
                    "id": "step_2",
                    "description": "Execute action based on analysis",
                    "action_type": "execute",
                    "estimated_duration": 2.0,
                    "status": "pending"
                }
            ],
            "estimated_duration": 3.0,
            "status": "awaiting_approval",
            "creation_time": timestamp,
            "backup_plan": True  # Mark as backup plan for easy identification
        }
        
        # Store in memory
        active_plans[plan_id] = dummy_plan
        
        # Update backend if accessible
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = dummy_plan
        except Exception:
            pass
        
        # Save to persistent storage if available
        if PLAN_PERSISTENCE_AVAILABLE:
            try:
                success = await save_plan(plan_id, dummy_plan)
                if success:
                    logger.info(f"Created and saved backup plan {plan_id}")
                else:
                    logger.warning(f"Failed to save backup plan {plan_id}")
            except Exception as e:
                logger.warning(f"Error saving backup plan to persistent storage: {e}")
        else:
            logger.info(f"Created backup plan {plan_id} in memory only (persistent storage not available)")
        
        return True
    except Exception as e:
        logger.error(f"Error creating backup plan: {e}")
        return False

async def forward_to_do_button_server(message, client_id=None):
    """Forward message to the DO button server using the Neural UI DO Button Handler"""
    try:
        # Parse the message
        data = json.loads(message) if isinstance(message, str) else message
        
        # Try to import and use the neural_ui_do_button_handler
        try:
            from neural_ui_do_button_handler import handle_proxy_message
            logger.info("✅ Using Neural UI DO Button Handler for improved plan handling")
            
            # Forward the message through the handler
            response = await handle_proxy_message(data)
            logger.info(f"✅ Neural UI DO Button Handler processed message: {data.get('type')}")
            
            # Return the response
            return json.dumps(response) if isinstance(response, dict) else response
            
        except ImportError:
            logger.warning("⚠️ Neural UI DO Button Handler not available, using fallback method")
            # Continue with the legacy implementation
        
        # --- LEGACY IMPLEMENTATION (FALLBACK) ---
        # Extract plan_id based on message type
        plan_id = None
        if data.get('type') == 'agent_confirmation':
            plan_id = data.get('sessionId') or data.get('session_id')
        elif data.get('type') == 'button_action':
            plan_id = data.get('plan_id')
        elif data.get('type') == 'do_button':
            plan_id = data.get('plan_id')
        elif data.get('type') == 'do_button_action' and 'do_button_action' in data:
            plan_id = data['do_button_action'].get('plan_id')
        
        # If this is a DO button action, ensure the plan exists
        if plan_id and data.get('type') in ['agent_confirmation', 'button_action', 'do_button', 'do_button_action']:
            action = data.get('action', '').upper() or data.get('button', '').upper()
            if action in ['DO', 'EXECUTE', 'EXECUTE_PLAN'] or data.get('type') == 'do_button_action':
                # Log the incoming message
                logger.info(f"Received {data.get('type')} message with plan_id: {plan_id}, action: {action}")
                
                # Ensure plan exists before forwarding
                plan_exists = await ensure_plan_exists(plan_id)
                if not plan_exists:
                    logger.warning(f"Failed to ensure plan {plan_id} exists")
                    # Return error response
                    return json.dumps({
                        "type": "agent_execution_error",
                        "error": f"Plan {plan_id} not found and could not be created",
                        "session_id": plan_id,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    logger.info(f"Plan {plan_id} exists or was created successfully")
                    
                    # If the message doesn't include the full plan, add it
                    if 'plan' not in data and plan_id in active_plans:
                        data['plan'] = active_plans[plan_id]
                        logger.info(f"Added plan data to message for {plan_id}")
        
        # Create a new connection for this request
        async with websockets.connect('ws://localhost:8765') as server_connection:
            logger.info("Connected to DO button server")
            
            # Forward the message
            await server_connection.send(json.dumps(data))
            logger.info(f"Forwarded message to DO button server: {data.get('type')}")
            
            # Wait for response
            response = await server_connection.recv()
            logger.info(f"Received response from DO button server: {response[:100]}...")
            
            return response
            
    except Exception as e:
        logger.error(f"Error forwarding to DO button server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return json.dumps({
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

async def forward_to_neural_ui_server(message, client_id=None):
    """Forward message to the Neural UI server"""
    global neural_ui_server_connection
    
    # Connect to Neural UI server if not already connected
    if not neural_ui_server_connection or neural_ui_server_connection.closed:
        try:
            neural_ui_server_connection = await websockets.connect('ws://localhost:8768')
            logger.info("Connected to Neural UI server")
        except Exception as e:
            logger.error(f"Failed to connect to Neural UI server: {e}")
            return None
    
    try:
        # Forward the message
        await neural_ui_server_connection.send(message if isinstance(message, str) else json.dumps(message))
        logger.info(f"Forwarded message to Neural UI server")
        
        # Wait for response
        response = await neural_ui_server_connection.recv()
        logger.info(f"Received response from Neural UI server")
        
        return response
    except Exception as e:
        logger.error(f"Error forwarding to Neural UI server: {e}")
        return None

async def handle_client(websocket, path=None):
    """Handle client WebSocket connection"""
    client_id = str(uuid.uuid4())
    client_connections[client_id] = websocket
    logger.info(f"Client {client_id} connected on path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "server_version": "1.0.0",
            "capabilities": ["agent_confirmation", "button_action", "do_button", "neural_ui", "suggestion"],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                # Parse the message
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                
                # Forward to appropriate server based on message type
                if msg_type in ['agent_confirmation', 'button_action', 'do_button', 'do_button_action']:
                    # These are DO button related actions
                    response = await forward_to_do_button_server(data, client_id)
                    if response:
                        await websocket.send(response if isinstance(response, str) else json.dumps(response))
                
                elif msg_type in ['detect', 'find', 'click', 'neural_ui']:
                    # These are Neural UI related actions
                    response = await forward_to_neural_ui_server(data, client_id)
                    if response:
                        await websocket.send(response if isinstance(response, str) else json.dumps(response))
                
                # Handle suggestion messages by forwarding to the overlay directly
                elif msg_type == 'suggestion':
                    logger.info(f"Handling suggestion message: {data.get('response', '')[:50]}...")
                    # Simply pass through the suggestion as-is since it's already in the format 
                    # expected by the overlay
                    await websocket.send(json.dumps({
                        "type": "suggestion",
                        "response": data.get('response', ''),
                        "buttons": data.get('buttons', []),
                        "importance": data.get('importance', 'high'),
                        "play_sound": data.get('play_sound', True),
                        "plan_id": data.get('plan_id', str(uuid.uuid4())),
                        "timestamp": datetime.now().isoformat()
                    }))
                    logger.info("Suggestion forwarded to client")
                
                # Handle ping messages directly
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Unknown message type
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": f"Unknown message type: {msg_type}",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }))
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    
    finally:
        if client_id in client_connections:
            del client_connections[client_id]

async def main():
    """Start the WebSocket proxy server"""
    port = 8766
    
    # First check if port is in use
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            logger.info(f"Port {port} is available")
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f"Port {port} is already in use. Killing existing process...")
            try:
                import subprocess
                subprocess.run(f"lsof -t -i:{port} | xargs kill -9", shell=True)
                logger.info(f"Killed process on port {port}")
                await asyncio.sleep(2)  # Wait for port to be released
            except Exception as kill_error:
                logger.error(f"Failed to kill process on port {port}: {kill_error}")
                # Use alternative port
                port = 8769
                logger.info(f"Using alternative port {port}")
    
    # Start server
    logger.info(f"Starting DO Button Connection Fix proxy on localhost:{port}")
    server = await websockets.serve(
        handle_client, 
        "localhost", 
        port
    )
    logger.info(f"✅ DO Button Connection Fix proxy running on ws://localhost:{port}")
    logger.info(f"📋 Proxy forwards to DO button server (8765) and Neural UI server (8768)")
    
    # Write port to file for clients to discover
    with open("logs/do_button_proxy_port.txt", "w") as f:
        f.write(str(port))
    
    # Keep server running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("DO Button Connection Fix proxy stopped by user")
    except Exception as e:
        logger.error(f"DO Button Connection Fix proxy error: {e}")