#!/usr/bin/env python3
"""
Fixed WebSocket Server for port 8765
This version properly binds to port 8765 to match the overlay's expectations
and properly handles agent_confirmation messages for the DO button
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_ws_server_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_ws_server_8765')

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

# Track connected clients
connected_clients = set()

# Handler for WebSocket connections
async def handler(websocket, path=None):
    """WebSocket connection handler
    Supports both old and new websockets library signatures
    """
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message with a default session_id for connection
        connection_session_id = f"connection_{int(datetime.now().timestamp())}"
        await websocket.send(json.dumps({
            "type": "connection_established",
            "server_version": "1.0.0",
            "capabilities": ["context_tracking", "agent_automation", "semantic_search"],
            "timestamp": datetime.now().isoformat(),
            "session_id": connection_session_id
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type}")
                
                # Handle agent_confirmation (DO button)
                if msg_type == 'agent_confirmation':
                    logger.info(f"Agent confirmation received: {data}")
                    session_id = data.get('session_id', '')
                    action = data.get('action', '').upper()
                    
                    try:
                        # Initialize the real automation handler
                        from real_agent_automation_handler import RealAgentAutomationHandler
                        handler = RealAgentAutomationHandler()
                        
                        # Map button actions to handler actions
                        action_map = {
                            'DO': 'execute_plan',
                            'DISMISS': 'cancel_plan',
                            'ADJUST': 'modify_plan'
                        }
                        
                        # Get the corresponding handler action
                        handler_action = action_map.get(action, action.lower())
                        
                        # Handle the action
                        result = await handler.handle_button_action(handler_action, session_id, session_id)
                        
                        if result.get('success'):
                            # Send the result
                            await websocket.send(json.dumps({
                                "type": "execution_complete",
                                "result": result,
                                "session_id": session_id
                            }))
                        else:
                            # Send error response
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": result.get('response', 'Unknown error'),
                                "session_id": session_id
                            }))
                            
                    except Exception as e:
                        logger.error(f"Error handling button action: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Error processing action: {str(e)}",
                            "session_id": session_id
                        }))
                
                # Handle chat_request messages
                elif msg_type == 'chat_request':
                    mode = data.get('mode', '').lower()
                    message = data.get('message', '').lower()
                    session_id = data.get('session_id', f'session_{int(datetime.now().timestamp())}')
                    
                    if mode == 'agent':
                        try:
                            # Initialize the real automation handler
                            from real_agent_automation_handler import RealAgentAutomationHandler
                            handler = RealAgentAutomationHandler()
                            
                            # Create LLM-based automation plan for any request
                            result = await handler.handle_agent_request(message, session_id)
                            
                            if result.get('success'):
                                # Send the LLM-generated plan
                                await websocket.send(json.dumps({
                                    "success": True,
                                    "response": result['response'],
                                    "mode": "agent",
                                    "interactive": True,
                                    "buttons": ["DO", "DISMISS", "ADJUST"],
                                    "plan_id": result.get('plan_id'),
                                    "requires_approval": True,
                                    "executionPlan": result.get('execution_plan', {}),
                                    "estimatedDuration": result.get('execution_plan', {}).get('total_steps', 0) * 2,
                                    "confidence": result.get('confidence_score', 0.8),
                                    "riskLevel": "low",
                                    "session_id": session_id
                                }))
                            else:
                                # Fallback to generic response if LLM planning fails
                                await websocket.send(json.dumps({
                                    "success": False,
                                    "response": "I apologize, but I couldn't create an automation plan for that request.",
                                    "mode": "agent",
                                    "session_id": session_id
                                }))
                                
                        except Exception as e:
                            logger.error(f"Error in LLM planning: {e}")
                            # Fallback to generic response
                            await websocket.send(json.dumps({
                                "success": False,
                                "response": "I apologize, but I encountered an error while planning the automation.",
                                "mode": "agent",
                                "session_id": session_id
                            }))
                
                # Handle ping messages
                elif msg_type == 'ping':
                    # Extract session_id from ping or use a default one
                    ping_session_id = data.get('session_id', f"ping_{int(datetime.now().timestamp())}")
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                        "session_id": ping_session_id
                    }))
                
                # Handle button_action messages
                elif msg_type == 'button_action':
                    logger.info(f"Button action received: {data}")
                    action = data.get('action', '').lower()
                    plan_id = data.get('plan_id', '')
                    session_id = data.get('session_id', plan_id)
                    
                    try:
                        # Initialize the real automation handler
                        from real_agent_automation_handler import RealAgentAutomationHandler
                        handler = RealAgentAutomationHandler()
                        
                        # Map button actions to handler actions
                        action_map = {
                            'do': 'execute_plan',
                            'dismiss': 'cancel_plan',
                            'adjust': 'modify_plan'
                        }
                        
                        # Get the corresponding handler action
                        handler_action = action_map.get(action, action)
                        
                        # Handle the action
                        result = await handler.handle_button_action(handler_action, plan_id, session_id)
                        
                        if result.get('success'):
                            # Send the result
                            await websocket.send(json.dumps({
                                "type": "execution_complete",
                                "result": result,
                                "session_id": session_id
                            }))
                        else:
                            # Send error response
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": result.get('response', 'Unknown error'),
                                "session_id": session_id
                            }))
                            
                    except Exception as e:
                        logger.error(f"Error handling button action: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Error processing action: {str(e)}",
                            "session_id": session_id
                        }))
                
                # Handle suggestion/notification messages (additional check)
                elif "notification" in data or "suggestion" in data or msg_type in ["notification", "suggestion"]:
                    logger.info(f"Handling notification/suggestion message: {msg_type}")
                    
                    # Check if this is an Epiphany mode suggestion format
                    if "suggestion_id" in data and ("title" in data or "message" in data):
                        logger.info(f"Detected Epiphany mode suggestion format")
                        # Pass through the original message for Epiphany mode
                        await websocket.send(message)
                        logger.info(f"Forwarded original Epiphany mode suggestion to client {client_id}")
                    else:
                        # Create properly formatted message for NextGenAppleChatWidget
                        # Extract session_id from original data or create new one
                        suggestion_session_id = data.get("session_id", f"suggestion_{int(datetime.now().timestamp())}")
                        properly_formatted_message = {
                            "type": "suggestion",
                            "response": data.get("response") or data.get("message") or data.get("content") or "New notification",
                            "mode": "SUGGEST",
                            "buttons": data.get("buttons", [
                                {"text": "✅ Got it", "value": "understood", "style": "success"},
                                {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
                            ]),
                            "importance": data.get("importance", "high"),
                            "play_sound": data.get("play_sound", True),
                            "notification": True,
                            "timestamp": data.get("timestamp", datetime.now().isoformat()),
                            "session_id": suggestion_session_id
                        }
                        
                        await websocket.send(json.dumps(properly_formatted_message))
                        logger.info(f"Sent properly formatted suggestion to client {client_id}")
                
                # Handle client registration for Epiphany mode
                elif msg_type == 'register':
                    client_type = data.get('client_type', '')
                    logger.info(f"Client registration received: {client_type}")
                    
                    if 'epiphany' in client_type.lower():
                        logger.info(f"✅ Epiphany mode client registered: {client_type}")
                        # Send a registration confirmation
                        # Extract or create session_id
                        reg_session_id = data.get("session_id", f"registration_{int(datetime.now().timestamp())}")
                        await websocket.send(json.dumps({
                            "type": "registration_success",
                            "client_type": client_type,
                            "server_time": datetime.now().isoformat(),
                            "message": f"Successfully registered as {client_type}",
                            "session_id": reg_session_id
                        }))
                    else:
                        # Standard registration confirmation
                        # Extract or create session_id
                        reg_session_id = data.get("session_id", f"registration_{int(datetime.now().timestamp())}")
                        await websocket.send(json.dumps({
                            "type": "registration_success",
                            "client_type": client_type,
                            "timestamp": datetime.now().isoformat(),
                            "session_id": reg_session_id
                        }))
                
                # Handle suggestion responses from Epiphany mode
                elif msg_type == 'suggestion_response':
                    suggestion_id = data.get('suggestion_id', '')
                    approved = data.get('approved', False)
                    logger.info(f"Suggestion response received for {suggestion_id}: approved={approved}")
                    
                    # Extract or use suggestion_id as session_id
                    suggestion_session_id = data.get('session_id', suggestion_id)
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "type": "suggestion_response_received",
                        "suggestion_id": suggestion_id,
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                        "session_id": suggestion_session_id
                    }))
                    
                    # If approved, simulate execution updates
                    if approved:
                        logger.info(f"Starting execution for approved suggestion {suggestion_id}")
                        
                        # Send initial progress
                        await websocket.send(json.dumps({
                            "type": "execution_update",
                            "suggestion_id": suggestion_id,
                            "progress": 25,
                            "message": "Starting execution...",
                            "session_id": suggestion_session_id
                        }))
                        
                        # Wait a bit
                        await asyncio.sleep(1.5)
                        
                        # Send more progress
                        await websocket.send(json.dumps({
                            "type": "execution_update",
                            "suggestion_id": suggestion_id,
                            "progress": 60,
                            "message": "Processing...",
                            "session_id": suggestion_session_id
                        }))
                        
                        # Wait a bit more
                        await asyncio.sleep(1.5)
                        
                        # Send completion
                        await websocket.send(json.dumps({
                            "type": "execution_complete",
                            "suggestion_id": suggestion_id,
                            "result": {
                                "success": True,
                                "message": "Task completed successfully!"
                            },
                            "session_id": suggestion_session_id
                        }))
                
                # Handle all other messages with a simple echo
                else:
                    # Extract session_id or use message type as fallback
                    other_session_id = data.get('session_id', f"{msg_type}_{int(datetime.now().timestamp())}")
                    await websocket.send(json.dumps({
                        "type": "response",
                        "message": f"Received {msg_type} message",
                        "timestamp": datetime.now().isoformat(),
                        "session_id": other_session_id
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                error_session_id = f"error_{int(datetime.now().timestamp())}"
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format",
                    "session_id": error_session_id
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def heartbeat():
    """Send periodic heartbeat to clients"""
    while True:
        if connected_clients:
            # Create heartbeat message with a heartbeat-specific session_id
            heartbeat_session_id = f"heartbeat_{int(datetime.now().timestamp())}"
            heartbeat_msg = json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "connected_clients": len(connected_clients),
                "session_id": heartbeat_session_id
            })
            
            # Send to all clients
            for websocket in list(connected_clients):
                try:
                    await websocket.send(heartbeat_msg)
                except websockets.exceptions.ConnectionClosed:
                    # Will be cleaned up in the handler
                    pass
                    
        # Wait for next heartbeat
        await asyncio.sleep(30)

async def main():
    # Ensure port 8765 is available
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', 8765))
        test_socket.close()
        logger.info("Port 8765 is available")
    except OSError:
        logger.error("Port 8765 is already in use. Please stop any existing WebSocket servers.")
        sys.exit(1)
    
    # IMPORTANT: Fixed port to 8765 to match overlay's expectations
    port = 8765  # Fixed from 8768 to 8765
    host = "localhost"
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Start server with proper WebSocket configuration
    server = await websockets.serve(
        handler,
        host,
        port,
        ping_interval=30,
        ping_timeout=60,
        close_timeout=30,
        max_size=10 * 1024 * 1024,
        max_queue=32
    )
    
    # Save PID
    os.makedirs("pids", exist_ok=True)
    with open('pids/fixed_ws_server_8765.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat())
    
    logger.info(f"✅ Fixed WebSocket server running on ws://{host}:{port}")
    logger.info(f"🎯 Ready to handle agent_confirmation messages (DO button)")
    
    # Keep running indefinitely
    await asyncio.Future()

if __name__ == "__main__":
    try:
        # Kill any existing processes on port 8765
        import subprocess
        subprocess.run("lsof -ti:8765 | xargs kill -9 2>/dev/null || true", shell=True)
        logger.info("Killed any existing processes on port 8765")
        # Give some time for port to be released
        asyncio.run(asyncio.sleep(1))
        
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)