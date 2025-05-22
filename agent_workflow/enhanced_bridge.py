#!/usr/bin/env python3
"""
Enhanced Bridge for Agent Workflow
Extends the existing overlay bridge to support agent-based keyboard and cursor automation.
"""
import asyncio
import json
import logging
import os
import sys
import time
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
import websockets
from websockets.server import WebSocketServerProtocol

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the context-aware agent and input controller
from agent_workflow.context_aware_agent import ContextAwareAgent
from agent_workflow.input_controller import InputController

# Import from agent directory (existing overlay bridge)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agent'))
from agent.overlay_bridge import OverlayBridge

# Configure logging
os.makedirs('logs/agent', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent/enhanced_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedBridge(OverlayBridge):
    """
    Enhanced bridge that extends the existing overlay bridge with agent-based
    keyboard and cursor automation capabilities.
    """
    
    def __init__(self, host="localhost", port=8765, agent_safety_level="high"):
        """
        Initialize the enhanced bridge.
        
        Args:
            host: Host for WebSocket server
            port: Port for WebSocket server
            agent_safety_level: Safety level for the agent's input control
        """
        # Initialize the parent class (existing overlay bridge)
        super().__init__(host, port)
        
        # Create the context-aware agent
        self.agent = ContextAwareAgent(
            server_uri=f"ws://{host}:{port}",
            safety_level=agent_safety_level
        )
        
        # Create the input controller (shared with agent)
        self.input_controller = self.agent.input_controller
        
        # Store client types for routing
        self.client_types = {}  # Map client WebSocket to type
        
        # Register new message handlers for agent-related messages
        self.register_callback('cursor_action', self._handle_cursor_action)
        self.register_callback('keyboard_action', self._handle_keyboard_action)
        self.register_callback('automate_task', self._handle_automate_task)
        self.register_callback('suggestion_feedback', self._handle_suggestion_feedback)
        
        # Confirmation tracking for actions
        self.pending_confirmations = {}
        self.confirmation_timeout = 30  # Seconds
        
        # Agent-related state
        self.agent_started = False
        self.user_authorized_automation = False
        self.authorized_tasks = set()  # Tasks authorized by user
        
        # Context integration
        self.context_integration_enabled = True
        self.context_cache = {}
        
        logger.info("Enhanced bridge initialized")
    
    async def start(self):
        """Start the enhanced bridge and the context-aware agent."""
        # Start the agent first
        self.agent_started = await self.agent.start()
        
        if not self.agent_started:
            logger.error("Failed to start context-aware agent")
        else:
            logger.info("Context-aware agent started successfully")
        
        # Then start the bridge (parent implementation)
        await super().start()
    
    async def stop(self):
        """Stop the enhanced bridge and the context-aware agent."""
        # Stop the agent
        if self.agent_started:
            await self.agent.stop()
            self.agent_started = False
            logger.info("Stopped context-aware agent")
        
        # Stop the bridge (parent implementation)
        await super().stop()
    
    async def _process_message(self, websocket, data):
        """
        Process incoming WebSocket message with enhanced agent-related handling.
        Extends the parent implementation to add agent-related features.
        """
        try:
            message_type = data.get('type')
            payload = data.get('payload', {})
            
            # Identify the client type during connection
            if message_type == 'connection_established':
                client_type = payload.get('client_type', 'unknown')
                self.client_types[websocket] = client_type
                logger.info(f"Client connected as type: {client_type}")
            
            # Forward sensor data to the agent
            if message_type in ['screen_data', 'process_data']:
                # Convert to sensor_data format for agent
                agent_data = {
                    "type": "sensor_data",
                    "payload": {
                        "sensor_type": "screen" if message_type == "screen_data" else "process",
                        **payload
                    }
                }
                
                # Queue message for agent if it's running
                if self.agent_started:
                    await self.agent.ws.send(json.dumps(agent_data))
            
            # Forward LLM responses to agent for suggestion analysis
            if message_type in ['llm_response', 'query_response']:
                # Check if the agent should analyze this for automation
                if self.agent_started and self.context_integration_enabled:
                    # Forward to agent for analysis
                    agent_data = {
                        "type": "llm_suggestion", 
                        "payload": {
                            "suggestion": payload
                        }
                    }
                    
                    try:
                        await self.agent.ws.send(json.dumps(agent_data))
                    except Exception as e:
                        logger.error(f"Error forwarding LLM response to agent: {e}")
            
            # Forward agent-specific messages
            if message_type in ['cursor_action', 'keyboard_action', 'automate_task']:
                # Handle via our specialized methods
                if message_type == 'cursor_action':
                    await self._handle_cursor_action(payload)
                elif message_type == 'keyboard_action':
                    await self._handle_keyboard_action(payload)
                elif message_type == 'automate_task':
                    await self._handle_automate_task(payload)
            
            # Process message via parent handler for other message types
            await super()._process_message(websocket, data)
                
        except Exception as e:
            logger.error(f"Error processing message in enhanced bridge: {e}")
    
    async def _handle_cursor_action(self, payload: Dict[str, Any]):
        """
        Handle cursor action request.
        This can be direct or via the agent, and may require user confirmation.
        """
        try:
            action_type = payload.get('action')
            confirmation_required = payload.get('require_confirmation', True)
            action_source = payload.get('source', 'user')  # 'user', 'agent', or 'automation'
            
            logger.info(f"Handling cursor action: {action_type} from {action_source}")
            
            # Check if confirmation is required
            if confirmation_required and action_source != 'user':
                # Generate confirmation ID
                confirmation_id = str(uuid.uuid4())
                
                # Store pending confirmation
                self.pending_confirmations[confirmation_id] = {
                    "type": "cursor_action",
                    "payload": payload,
                    "expires_at": time.time() + self.confirmation_timeout,
                    "confirmed": False
                }
                
                # Request user confirmation
                await self._request_action_confirmation(
                    confirmation_id,
                    f"Confirm cursor {action_type} action",
                    f"Application wants to {action_type} the cursor. Allow this action?"
                )
                
                # Action will be executed when confirmation is received
                return
            
            # Execute cursor action directly or via agent
            if self.agent_started and action_source == 'agent':
                # Forward to agent
                await self.agent.ws.send(json.dumps({
                    "type": "cursor_action",
                    "payload": payload
                }))
            else:
                # Execute locally using the input controller
                if action_type == 'move':
                    x = payload.get('x')
                    y = payload.get('y')
                    duration = payload.get('duration')
                    human_like = payload.get('human_like', True)
                    self.input_controller.move_to(x, y, duration, human_like)
                    
                elif action_type == 'click':
                    x = payload.get('x')
                    y = payload.get('y')
                    button = payload.get('button', 'left')
                    clicks = payload.get('clicks', 1)
                    self.input_controller.click(x, y, button, clicks)
                    
                elif action_type == 'right_click':
                    x = payload.get('x')
                    y = payload.get('y')
                    self.input_controller.right_click(x, y)
                    
                elif action_type == 'double_click':
                    x = payload.get('x')
                    y = payload.get('y')
                    self.input_controller.double_click(x, y)
                    
                elif action_type == 'drag':
                    x = payload.get('x')
                    y = payload.get('y')
                    button = payload.get('button', 'left')
                    self.input_controller.drag_to(x, y, button)
                    
                elif action_type == 'scroll':
                    clicks = payload.get('clicks', 0)
                    self.input_controller.scroll(clicks)
            
            # Send response
            await self.send_message("action_result", {
                "action_type": action_type,
                "success": True,
                "source": action_source
            })
            
        except Exception as e:
            logger.error(f"Error handling cursor action: {e}")
            
            # Send failure response
            await self.send_message("action_result", {
                "action_type": payload.get('action', 'unknown'),
                "success": False,
                "error": str(e)
            })
    
    async def _handle_keyboard_action(self, payload: Dict[str, Any]):
        """
        Handle keyboard action request.
        This can be direct or via the agent, and may require user confirmation.
        """
        try:
            action_type = payload.get('action')
            confirmation_required = payload.get('require_confirmation', True)
            action_source = payload.get('source', 'user')
            
            logger.info(f"Handling keyboard action: {action_type} from {action_source}")
            
            # Check if confirmation is required
            if confirmation_required and action_source != 'user':
                # Generate confirmation ID
                confirmation_id = str(uuid.uuid4())
                
                # Store pending confirmation
                self.pending_confirmations[confirmation_id] = {
                    "type": "keyboard_action",
                    "payload": payload,
                    "expires_at": time.time() + self.confirmation_timeout,
                    "confirmed": False
                }
                
                # Request user confirmation
                action_description = f"{action_type}"
                if action_type == 'type':
                    action_description = f"type '{payload.get('text', '')}'"
                elif action_type == 'press':
                    action_description = f"press {payload.get('key', '')}"
                elif action_type == 'hotkey':
                    action_description = f"press {'+'.join(payload.get('keys', []))}"
                
                await self._request_action_confirmation(
                    confirmation_id,
                    f"Confirm keyboard action",
                    f"Application wants to {action_description}. Allow this action?"
                )
                
                # Action will be executed when confirmation is received
                return
            
            # Execute keyboard action directly or via agent
            if self.agent_started and action_source == 'agent':
                # Forward to agent
                await self.agent.ws.send(json.dumps({
                    "type": "keyboard_action",
                    "payload": payload
                }))
            else:
                # Execute locally using the input controller
                if action_type == 'type':
                    text = payload.get('text', '')
                    interval = payload.get('interval')
                    self.input_controller.type_text(text, interval)
                    
                elif action_type == 'press':
                    key = payload.get('key', '')
                    self.input_controller.press_key(key)
                    
                elif action_type == 'hotkey':
                    keys = payload.get('keys', [])
                    if keys:
                        self.input_controller.hotkey(*keys)
            
            # Send response
            await self.send_message("action_result", {
                "action_type": action_type,
                "success": True,
                "source": action_source
            })
            
        except Exception as e:
            logger.error(f"Error handling keyboard action: {e}")
            
            # Send failure response
            await self.send_message("action_result", {
                "action_type": payload.get('action', 'unknown'),
                "success": False,
                "error": str(e)
            })
    
    async def _handle_automate_task(self, payload: Dict[str, Any]):
        """
        Handle task automation request.
        Executes a sequence of actions to automate a task.
        """
        try:
            task_name = payload.get('task_name')
            task_id = payload.get('task_id', str(uuid.uuid4()))
            actions = payload.get('actions', [])
            
            logger.info(f"Handling automation task: {task_name} with {len(actions)} actions")
            
            # Check if this task is authorized
            if task_id not in self.authorized_tasks and not self.user_authorized_automation:
                # Request confirmation
                confirmation_id = str(uuid.uuid4())
                
                # Store pending confirmation
                self.pending_confirmations[confirmation_id] = {
                    "type": "automate_task",
                    "payload": payload,
                    "expires_at": time.time() + self.confirmation_timeout,
                    "confirmed": False,
                    "task_id": task_id
                }
                
                # Request user confirmation
                await self._request_action_confirmation(
                    confirmation_id,
                    f"Confirm task automation: {task_name}",
                    f"Agent wants to automate task: {task_name} with {len(actions)} actions. Allow this task?"
                )
                
                # Task will be executed when confirmation is received
                return
            
            # Execute the task directly or via agent
            if self.agent_started:
                # Forward to agent
                await self.agent.ws.send(json.dumps({
                    "type": "automate_task",
                    "payload": payload
                }))
            else:
                # Execute directly using the input controller
                success = self.input_controller.execute_action_sequence(actions)
                
                # Send result
                await self.send_message("automation_result", {
                    "task_id": task_id,
                    "task_name": task_name,
                    "success": success,
                    "message": "Task completed successfully" if success else "Task failed"
                })
            
        except Exception as e:
            logger.error(f"Error handling task automation: {e}")
            
            # Send failure response
            await self.send_message("automation_result", {
                "task_id": payload.get('task_id', 'unknown'),
                "task_name": payload.get('task_name', 'unknown'),
                "success": False,
                "error": str(e)
            })
    
    async def _handle_suggestion_feedback(self, payload: Dict[str, Any]):
        """
        Handle feedback on an LLM suggestion.
        If the user accepts a suggestion that can be automated, execute the automation.
        """
        try:
            suggestion_id = payload.get('suggestion_id')
            action = payload.get('action')  # 'accept', 'reject', 'modify'
            
            logger.info(f"Handling suggestion feedback: {action} for {suggestion_id}")
            
            if action == 'accept':
                # Check if this suggestion had automation potential
                task_id = payload.get('task_id')
                
                if task_id:
                    # This suggestion can be automated - authorize the task
                    self.authorized_tasks.add(task_id)
                    
                    # Send automate task request
                    await self.send_message("automate_task", {
                        "task_id": task_id,
                        "task_name": payload.get('task_name', 'Automated Suggestion'),
                        "actions": payload.get('actions', []),
                        "source": "suggestion",
                        "suggestion_id": suggestion_id
                    })
            
            # Forward the feedback to the agent
            if self.agent_started:
                await self.agent.ws.send(json.dumps({
                    "type": "suggestion_feedback",
                    "payload": payload
                }))
            
        except Exception as e:
            logger.error(f"Error handling suggestion feedback: {e}")
    
    async def _request_action_confirmation(self, confirmation_id: str, title: str, message: str):
        """Request confirmation from the user for an action."""
        try:
            await self.send_message("action_confirmation", {
                "confirmation_id": confirmation_id,
                "title": title,
                "message": message,
                "options": [
                    {"id": "confirm", "label": "Allow", "primary": True},
                    {"id": "deny", "label": "Deny", "primary": False},
                    {"id": "always", "label": "Always Allow", "primary": False}
                ],
                "expires_in": self.confirmation_timeout
            })
            
            logger.info(f"Requested confirmation: {title}")
            
        except Exception as e:
            logger.error(f"Error requesting confirmation: {e}")
    
    async def _handle_confirmation_response(self, payload: Dict[str, Any]):
        """Handle response to a confirmation request."""
        try:
            confirmation_id = payload.get('confirmation_id')
            response = payload.get('response')  # 'confirm', 'deny', 'always'
            
            if confirmation_id not in self.pending_confirmations:
                logger.warning(f"Received response for unknown confirmation: {confirmation_id}")
                return
            
            confirmation = self.pending_confirmations[confirmation_id]
            
            # Check if confirmation has expired
            if time.time() > confirmation["expires_at"]:
                logger.warning(f"Confirmation {confirmation_id} has expired")
                del self.pending_confirmations[confirmation_id]
                return
            
            if response == 'confirm' or response == 'always':
                # Mark as confirmed
                confirmation["confirmed"] = True
                
                # If "always", set global authorization
                if response == 'always':
                    self.user_authorized_automation = True
                    logger.info("User authorized all automations")
                
                # Handle confirmed action based on type
                action_type = confirmation.get("type")
                action_payload = confirmation.get("payload", {})
                
                if action_type == "cursor_action":
                    await self._handle_cursor_action(action_payload)
                elif action_type == "keyboard_action":
                    await self._handle_keyboard_action(action_payload)
                elif action_type == "automate_task":
                    # Add task to authorized tasks
                    task_id = confirmation.get("task_id")
                    if task_id:
                        self.authorized_tasks.add(task_id)
                    await self._handle_automate_task(action_payload)
            
            # Clean up the confirmation
            del self.pending_confirmations[confirmation_id]
            
        except Exception as e:
            logger.error(f"Error handling confirmation response: {e}")
    
    # Register the new handler during initialization
    def __post_init__(self):
        """Register additional handlers after parent initialization."""
        self.register_callback('confirmation_response', self._handle_confirmation_response)

async def run_enhanced_bridge():
    """Run the enhanced bridge server."""
    bridge = EnhancedBridge()
    await bridge.start()

if __name__ == "__main__":
    try:
        asyncio.run(run_enhanced_bridge())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)