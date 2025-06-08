#!/usr/bin/env python3
"""
Neural UI DO Button Handler

This module bridges the gap between the Neural UI Detector setup and the DO button execution system.
It ensures plans are correctly synchronized between different components:
1. Neural UI detector (port 8768)
2. DO Button server (port 8765)
3. Backend server (port 8767)
4. WebSocket proxy (port 8766)
"""

import asyncio
import websockets
import json
import logging
import logging.config
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

# Configure logging
os.makedirs('logs', exist_ok=True)
try:
    logging.config.fileConfig('config/neural_ui_do_button_logging.conf')
    logger = logging.getLogger('neural_ui_do_button')
    logger.info("✅ Loaded logging configuration from config/neural_ui_do_button_logging.conf")
except Exception as e:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/neural_ui_do_button.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger('neural_ui_do_button')
    logger.warning(f"⚠️ Using fallback logging configuration: {e}")

# Connection info
BACKEND_WS_URL = "ws://localhost:8767/ws"
DO_BUTTON_WS_URL = "ws://localhost:8765"
NEURAL_UI_WS_URL = "ws://localhost:8768"

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
            return active_plans[plan_id]
        logger.warning(f"⚠️ Plan {plan_id} not found in memory (persistence not available)")
        return None
        
    async def delete_plan(plan_id):
        """Fallback implementation of delete_plan"""
        if plan_id in active_plans:
            del active_plans[plan_id]
            logger.info(f"🗑️ Plan {plan_id} deleted from memory (persistence not available)")
            return True
        return False
        
    PLAN_PERSISTENCE_AVAILABLE = False

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

class NeuralUIDOButtonHandler:
    """Handles the integration between Neural UI Detector and DO button execution"""
    def __init__(self):
        self.backend_ws = None
        self.do_button_ws = None
        self.neural_ui_ws = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to all required WebSocket servers"""
        try:
            # Connect to backend server
            self.backend_ws = await websockets.connect(BACKEND_WS_URL)
            welcome = await self.backend_ws.recv()
            logger.info(f"Connected to backend server: {welcome[:50]}...")
            
            # Connect to DO button server
            self.do_button_ws = await websockets.connect(DO_BUTTON_WS_URL)
            welcome = await self.do_button_ws.recv()
            logger.info(f"Connected to DO button server: {welcome[:50]}...")
            
            # Try to connect to Neural UI server (optional)
            try:
                self.neural_ui_ws = await websockets.connect(NEURAL_UI_WS_URL)
                welcome = await self.neural_ui_ws.recv()
                logger.info(f"Connected to Neural UI server: {welcome[:50]}...")
            except Exception as e:
                logger.warning(f"Could not connect to Neural UI server: {e}")
                self.neural_ui_ws = None
            
            self.connected = True
            logger.info("✅ Connected to all required servers")
            return True
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """Close all WebSocket connections"""
        if self.backend_ws:
            await self.backend_ws.close()
            self.backend_ws = None
            
        if self.do_button_ws:
            await self.do_button_ws.close()
            self.do_button_ws = None
            
        if self.neural_ui_ws:
            await self.neural_ui_ws.close()
            self.neural_ui_ws = None
            
        self.connected = False
        logger.info("Disconnected from all servers")
    
    async def ensure_plan_exists(self, plan_id: str) -> bool:
        """Ensure plan exists in all required systems"""
        if not plan_id:
            logger.warning("No plan ID provided")
            return False
            
        # Log the plan ID we're looking for
        logger.info(f"🔍 Looking for plan with ID: {plan_id}")
            
        # Check if plan exists in memory cache
        if plan_id in active_plans:
            logger.info(f"✅ Plan {plan_id} exists in memory")
            return True
            
        # Check shared plans dictionary from backend
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                if plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                    plan = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                    # Copy to our active_plans
                    active_plans[plan_id] = plan
                    logger.info(f"✅ Found plan in backend shared dictionary: {plan_id}")
                    return True
                # Log the keys that are in the shared dictionary
                logger.info(f"📋 Available plans in backend: {list(enhanced_enterprise_backend_with_context.shared_pending_plans.keys())}")
        except Exception as e:
            logger.warning(f"⚠️ Error checking backend shared dictionary: {e}")
            
        # Try to load from persistence
        if PLAN_PERSISTENCE_AVAILABLE:
            try:
                # Ensure the plans directory exists
                os.makedirs(os.path.join("cache", "plans"), exist_ok=True)
                
                # Try to load the plan
                plan = await load_plan(plan_id)
                if plan:
                    # Store in memory
                    active_plans[plan_id] = plan
                    
                    # Update backend if accessible
                    try:
                        import enhanced_enterprise_backend_with_context
                        if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                            enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan
                    except Exception:
                        pass
                        
                    logger.info(f"✅ Loaded plan from persistence: {plan_id}")
                    return True
                else:
                    # Check if any plans exist in the directory
                    plan_files = os.listdir(os.path.join("cache", "plans"))
                    logger.info(f"📋 Available plan files: {plan_files}")
            except Exception as e:
                logger.warning(f"⚠️ Error loading plan from persistence: {e}")
        
        # Create backup plan if not found
        logger.warning(f"⚠️ Plan {plan_id} not found, creating backup plan")
        return await self.create_backup_plan(plan_id)
    
    async def create_backup_plan(self, plan_id: str) -> bool:
        """Create a backup plan when a plan cannot be found"""
        timestamp = time.time()
        
        # Create a simple backup plan
        backup_plan = {
            "id": plan_id,
            "task_id": plan_id,  # Make sure task_id is set for execution
            "plan_id": plan_id,  # Add plan_id for compatibility
            "title": f"Backup Plan {plan_id[:8]}",
            "description": f"Backup plan created by Neural UI DO Button Handler for session {plan_id}",
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
            "backup_plan": True,
            "timestamp": timestamp,
            "created": timestamp
        }
        
        # Store in memory
        active_plans[plan_id] = backup_plan
        
        # Save to persistent storage if available
        if PLAN_PERSISTENCE_AVAILABLE:
            try:
                success = await save_plan(plan_id, backup_plan)
                logger.info(f"✅ Created and saved backup plan: {success}")
            except Exception as e:
                logger.warning(f"⚠️ Error saving backup plan: {e}")
                
        logger.info(f"✅ Created backup plan for {plan_id}")
        return True
    
    async def handle_do_button_action(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DO button action by ensuring the plan exists and forwarding to the DO button server"""
        # Extract the plan ID based on message type
        plan_id = None
        
        # Log the full message for debugging
        logger.info(f"🔄 Processing DO button action: {json.dumps(message_data, default=str)}")
        
        if message_data.get('type') == 'agent_confirmation':
            # Prioritize sessionId, then fall back to plan_id, and finally session_id
            plan_id = message_data.get('sessionId') or message_data.get('plan_id') or message_data.get('session_id')
            logger.info(f"🔄 Agent confirmation with plan_id: {plan_id}")
        elif message_data.get('type') == 'button_action':
            plan_id = message_data.get('plan_id')
            logger.info(f"🔄 Button action with plan_id: {plan_id}")
        elif message_data.get('type') == 'do_button':
            plan_id = message_data.get('plan_id')
            logger.info(f"🔄 DO button with plan_id: {plan_id}")
        elif message_data.get('type') == 'do_button_action' and message_data.get('do_button_action', {}).get('plan_id'):
            plan_id = message_data.get('do_button_action', {}).get('plan_id')
            logger.info(f"🔄 DO button action with plan_id: {plan_id}")
        
        if not plan_id:
            logger.error("❌ No plan ID found in message")
            return {
                "type": "error",
                "error": "No plan ID found in message"
            }
        
        # Ensure plan exists
        plan_exists = await self.ensure_plan_exists(plan_id)
        if not plan_exists:
            logger.error(f"❌ Failed to ensure plan exists: {plan_id}")
            return {
                "type": "error",
                "error": f"Plan {plan_id} not found and could not be created"
            }
            
        # If the message doesn't include the full plan, add it
        if 'plan' not in message_data and plan_id in active_plans:
            message_data['plan'] = active_plans[plan_id]
            logger.info(f"✅ Added plan data to message for {plan_id}")
        
        try:
            # Forward to DO button server
            if not self.do_button_ws or self.do_button_ws.closed:
                logger.info("Reconnecting to DO button server")
                self.do_button_ws = await websockets.connect(DO_BUTTON_WS_URL)
                welcome = await self.do_button_ws.recv()
                logger.info(f"Reconnected to DO button server: {welcome[:50]}...")
            
            await self.do_button_ws.send(json.dumps(message_data))
            logger.info(f"✅ Forwarded DO button action to server: {message_data.get('type')}")
            
            # Wait for response
            response = await self.do_button_ws.recv()
            try:
                response_data = json.loads(response)
                logger.info(f"✅ Received response from DO button server: {response_data.get('type', 'unknown')}")
                return response_data
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response from DO button server: {response[:100]}...")
                return {
                    "type": "success",
                    "message": "DO button action forwarded successfully"
                }
        except Exception as e:
            logger.error(f"❌ Error forwarding DO button action: {e}")
            return {
                "type": "error",
                "error": f"Error forwarding DO button action: {str(e)}"
            }
    
    async def listen_for_messages(self):
        """Listen for messages from all connected servers"""
        logger.info("Started listening for messages from all servers")
        
        # Create tasks for each server
        backend_task = asyncio.create_task(self._listen_to_backend())
        do_button_task = asyncio.create_task(self._listen_to_do_button())
        neural_ui_task = asyncio.create_task(self._listen_to_neural_ui()) if self.neural_ui_ws else None
        
        # Create a set of tasks to wait for
        pending = {backend_task, do_button_task}
        if neural_ui_task:
            pending.add(neural_ui_task)
            
        # Wait for tasks to complete
        while pending:
            done, pending = await asyncio.wait(
                pending, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=60
            )
            
            for task in done:
                try:
                    result = task.result()
                    logger.info(f"Task completed with result: {result}")
                except Exception as e:
                    logger.error(f"Task failed with error: {e}")
                    # Reconnect and restart the task
                    await self.disconnect()
                    await asyncio.sleep(2)  # Give servers time to clean up
                    success = await self.connect()
                    if success:
                        if task == backend_task:
                            backend_task = asyncio.create_task(self._listen_to_backend())
                            pending.add(backend_task)
                        elif task == do_button_task:
                            do_button_task = asyncio.create_task(self._listen_to_do_button())
                            pending.add(do_button_task)
                        elif self.neural_ui_ws and task == neural_ui_task:
                            neural_ui_task = asyncio.create_task(self._listen_to_neural_ui())
                            pending.add(neural_ui_task)
    
    async def _listen_to_backend(self):
        """Listen for messages from the backend server"""
        logger.info("Started listening to backend server")
        try:
            async for message in self.backend_ws:
                try:
                    data = json.loads(message)
                    logger.info(f"Received message from backend: {data.get('type', 'unknown')}")
                    
                    # Handle plan updates from backend
                    if data.get('type') == 'plan_created' or data.get('type') == 'plan_updated':
                        plan_id = data.get('plan_id')
                        plan_data = data.get('plan')
                        if plan_id and plan_data:
                            active_plans[plan_id] = plan_data
                            logger.info(f"✅ Updated plan in memory: {plan_id}")
                            
                            # Save to persistence
                            if PLAN_PERSISTENCE_AVAILABLE:
                                try:
                                    await save_plan(plan_id, plan_data)
                                    logger.info(f"✅ Saved updated plan to persistence: {plan_id}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Error saving updated plan: {e}")
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from backend: {message[:100]}...")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Backend connection closed")
            raise
            
        except Exception as e:
            logger.error(f"Error in backend listener: {e}")
            raise
            
        return "Backend listener stopped"
    
    async def _listen_to_do_button(self):
        """Listen for messages from the DO button server"""
        logger.info("Started listening to DO button server")
        try:
            async for message in self.do_button_ws:
                try:
                    data = json.loads(message)
                    logger.info(f"Received message from DO button server: {data.get('type', 'unknown')}")
                    
                    # Handle plan updates from DO button server
                    if data.get('type') == 'plan_executed':
                        plan_id = data.get('plan_id')
                        if plan_id and plan_id in active_plans:
                            # Update plan status
                            active_plans[plan_id]['status'] = 'executed'
                            logger.info(f"✅ Updated plan status to executed: {plan_id}")
                            
                            # Save to persistence
                            if PLAN_PERSISTENCE_AVAILABLE:
                                try:
                                    await save_plan(plan_id, active_plans[plan_id])
                                    logger.info(f"✅ Saved executed plan to persistence: {plan_id}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Error saving executed plan: {e}")
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from DO button server: {message[:100]}...")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("DO button server connection closed")
            raise
            
        except Exception as e:
            logger.error(f"Error in DO button listener: {e}")
            raise
            
        return "DO button listener stopped"
    
    async def _listen_to_neural_ui(self):
        """Listen for messages from the Neural UI server"""
        if not self.neural_ui_ws:
            return "Neural UI listener not started (no connection)"
            
        logger.info("Started listening to Neural UI server")
        try:
            async for message in self.neural_ui_ws:
                try:
                    data = json.loads(message)
                    logger.info(f"Received message from Neural UI server: {data.get('type', 'unknown')}")
                    
                    # Handle plan creation from Neural UI
                    if data.get('type') == 'create_plan':
                        plan_data = data.get('plan')
                        if plan_data and 'id' in plan_data:
                            plan_id = plan_data['id']
                            active_plans[plan_id] = plan_data
                            logger.info(f"✅ Created plan from Neural UI: {plan_id}")
                            
                            # Save to persistence
                            if PLAN_PERSISTENCE_AVAILABLE:
                                try:
                                    await save_plan(plan_id, plan_data)
                                    logger.info(f"✅ Saved plan from Neural UI to persistence: {plan_id}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Error saving plan from Neural UI: {e}")
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from Neural UI server: {message[:100]}...")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Neural UI server connection closed")
            raise
            
        except Exception as e:
            logger.error(f"Error in Neural UI listener: {e}")
            raise
            
        return "Neural UI listener stopped"
    
    async def send_ping(self):
        """Send ping messages to keep connections alive"""
        while self.connected:
            try:
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }
                
                if self.backend_ws and not self.backend_ws.closed:
                    await self.backend_ws.send(json.dumps(ping_message))
                    
                if self.do_button_ws and not self.do_button_ws.closed:
                    await self.do_button_ws.send(json.dumps(ping_message))
                    
                if self.neural_ui_ws and not self.neural_ui_ws.closed:
                    await self.neural_ui_ws.send(json.dumps(ping_message))
                    
                logger.debug("Sent ping to all servers")
                
            except Exception as e:
                logger.warning(f"Error sending ping: {e}")
                # Try to reconnect
                await self.disconnect()
                await self.connect()
                
            await asyncio.sleep(30)  # Send ping every 30 seconds

# Create handler instance
handler = NeuralUIDOButtonHandler()

async def start():
    """Start the Neural UI DO Button Handler"""
    logger.info("Starting Neural UI DO Button Handler")
    
    # Connect to all servers
    success = await handler.connect()
    if not success:
        logger.error("Failed to connect to servers, exiting")
        return
    
    # Start ping task to keep connections alive
    ping_task = asyncio.create_task(handler.send_ping())
    
    # Start listening for messages
    await handler.listen_for_messages()
    
    # Cancel ping task when done
    ping_task.cancel()
    try:
        await ping_task
    except asyncio.CancelledError:
        pass
        
    await handler.disconnect()

async def handle_proxy_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle message from the WebSocket proxy"""
    # Make sure we're connected
    if not handler.connected:
        success = await handler.connect()
        if not success:
            return {
                "type": "error",
                "error": "Failed to connect to servers"
            }
    
    # Handle different message types
    message_type = message_data.get('type', 'unknown')
    
    if message_type in ['agent_confirmation', 'button_action', 'do_button', 'do_button_action']:
        return await handler.handle_do_button_action(message_data)
    else:
        logger.warning(f"Unsupported message type: {message_type}")
        return {
            "type": "error",
            "error": f"Unsupported message type: {message_type}"
        }

if __name__ == "__main__":
    try:
        # Run the handler
        asyncio.run(start())
    except KeyboardInterrupt:
        logger.info("Neural UI DO Button Handler stopped by user")
    except Exception as e:
        logger.error(f"Neural UI DO Button Handler error: {e}")