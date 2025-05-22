#!/usr/bin/env python3
"""
Context-Aware Agent
Intelligent agent that understands user context and can automate tasks
using keyboard and cursor interactions.

This agent is inspired by Project Mariner's approach to contextual task automation.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import websockets
from websockets.client import WebSocketClientProtocol

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from agent_workflow
from agent_workflow.input_controller import InputController

# Configure logging
os.makedirs('logs/agent', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent/context_aware_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContextAwareAgent:
    """
    Agent that understands user context and automates tasks using keyboard and cursor.
    Integrates with existing screen sensor, process sensor, and memory systems.
    """
    
    def __init__(self, server_uri: str = "ws://127.0.0.1:8765", safety_level: str = "high"):
        """
        Initialize the context-aware agent.
        
        Args:
            server_uri: URI of the WebSocket server for communication
            safety_level: Safety level for input controller ("low", "medium", "high")
        """
        self.server_uri = server_uri
        self.ws: Optional[WebSocketClientProtocol] = None
        self.client_id = str(uuid.uuid4())
        self.running = False
        self.reconnect_delay = 3
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        
        # Initialize the input controller
        self.input_controller = InputController(safety_level=safety_level)
        logger.info(f"Input controller initialized with safety level: {safety_level}")
        logger.info("🚨 Emergency shutdown: Press Ctrl+1 to stop agent immediately")
        
        # Current context data
        self.current_context = {
            "active_app": None,
            "active_window": None,
            "active_apps": [],
            "screen_content": None,
            "visual_context": None,
            "timestamp": None,
            "session_id": str(uuid.uuid4()),
            "ui_elements": []  # Detected UI elements
        }
        
        # Task management
        self.current_tasks = []
        self.task_history = []
        self.automated_actions = []
        
        # UI element detection patterns
        self.ui_element_patterns = [
            {"type": "button", "patterns": ["btn", "button", "submit", "cancel", "ok", "apply"]},
            {"type": "input", "patterns": ["input", "text", "field", "entry", "form"]},
            {"type": "menu", "patterns": ["menu", "dropdown", "select", "option"]},
            {"type": "tab", "patterns": ["tab", "page", "view", "panel"]},
            {"type": "link", "patterns": ["link", "href", "url", "navigate"]}
        ]
        
        # Common task patterns
        self.task_patterns = [
            {
                "name": "text_entry",
                "description": "Enter text into a field",
                "triggers": ["type", "enter", "input", "write"],
                "apps": ["*"]  # All apps
            },
            {
                "name": "navigation",
                "description": "Navigate between pages/views",
                "triggers": ["navigate", "go to", "open", "visit"],
                "apps": ["Safari", "Chrome", "Firefox"]
            },
            {
                "name": "document_edit",
                "description": "Edit document content",
                "triggers": ["edit", "change", "modify", "update"],
                "apps": ["Pages", "Word", "Google Docs", "TextEdit"]
            },
            {
                "name": "file_management",
                "description": "Manage files and folders",
                "triggers": ["save", "open", "create", "delete", "rename"],
                "apps": ["Finder", "Explorer"]
            }
        ]
        
        # Cached screen data for element detection
        self.screen_data = None
        self.screen_elements = []
        
        # Initialize listeners
        self.llm_listener_active = False
        self.llm_listener_thread = None
    
    async def start(self):
        """Start the agent and connect to the WebSocket server."""
        try:
            self.running = True
            
            # Start WebSocket connection
            await self._connect()
            
            return True
        except Exception as e:
            logger.error(f"Error starting context-aware agent: {e}")
            return False
    
    async def stop(self):
        """Stop the agent and clean up resources."""
        self.running = False
        
        # Stop the input controller
        self.input_controller.stop()
        
        # Close WebSocket connection
        if self.ws:
            await self.ws.close()
            
        logger.info("Context-aware agent stopped")
    
    async def _connect(self):
        """Connect to the WebSocket server."""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to {self.server_uri}")
                
                async with websockets.connect(self.server_uri) as websocket:
                    self.ws = websocket
                    self.reconnect_attempts = 0
                    
                    # Send connection message
                    await self._send_connection_message()
                    
                    # Start handling messages
                    await self._handle_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"Connection error: {e}")
                logger.error(f"Stack trace: {sys.exc_info()}")
            
            if self.running:
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
    
    async def _send_connection_message(self):
        """Send initial connection message to server."""
        try:
            await self.ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client_type": "context_agent",
                    "client_id": self.client_id,
                    "version": "1.0.0",
                    "capabilities": ["cursor_automation", "keyboard_automation", "context_awareness", "task_automation"],
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent connection message to server")
        except Exception as e:
            logger.error(f"Error sending connection message: {e}")
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON message received")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    logger.error(f"Stack trace: {sys.exc_info()}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            logger.error(f"Stack trace: {sys.exc_info()}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message."""
        try:
            msg_type = data.get('type')
            payload = data.get('payload', {})
            
            if msg_type == 'sensor_data':
                # Update context with sensor data
                await self._handle_sensor_data(payload)
            elif msg_type == 'automate_task':
                # Handle task automation request
                await self._handle_task_automation(payload)
            elif msg_type == 'cursor_action':
                # Handle cursor action request
                await self._handle_cursor_action(payload)
            elif msg_type == 'keyboard_action':
                # Handle keyboard action request
                await self._handle_keyboard_action(payload)
            elif msg_type == 'llm_suggestion':
                # Handle LLM suggestion with potential automation
                await self._handle_llm_suggestion(payload)
            elif msg_type == 'context_request':
                # Send current context data
                await self._send_context_data()
            else:
                logger.debug(f"Unhandled message type: {msg_type}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Stack trace: {sys.exc_info()}")
    
    async def _handle_sensor_data(self, data: Dict[str, Any]):
        """
        Handle sensor data from screen and process sensors.
        Updates the agent's understanding of the current context.
        """
        try:
            sensor_type = data.get('sensor_type')
            
            if sensor_type == 'screen':
                # Handle screen sensor data
                self.screen_data = data
                
                # Update context with screen data
                self.current_context.update({
                    "screen_content": data.get('text'),
                    "visual_context": data.get('llava_analysis', {}).get('description')
                })
                
                # Detect UI elements from screen data
                await self._detect_ui_elements(data)
                
            elif sensor_type == 'process':
                # Handle process sensor data
                self.current_context.update({
                    "active_app": data.get('active_app'),
                    "active_window": data.get('active_window'),
                    "active_apps": data.get('active_apps', [])
                })
            
            # Update timestamp
            self.current_context["timestamp"] = datetime.now().isoformat()
            
            logger.debug(f"Updated context with {sensor_type} sensor data")
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    async def _detect_ui_elements(self, screen_data: Dict[str, Any]):
        """
        Detect UI elements from screen data.
        Uses LLaVA analysis and text content to identify interactive elements.
        """
        try:
            ui_elements = []
            
            # Extract potential UI elements from LLaVA analysis
            llava_analysis = screen_data.get('llava_analysis', {})
            
            # Check if LLaVA identified UI elements
            if 'ui_elements' in llava_analysis:
                ui_elements.extend(llava_analysis['ui_elements'])
            
            # Use text content to detect potential UI elements
            text_content = screen_data.get('text', '')
            if text_content:
                # Look for common UI element patterns in text
                for pattern in self.ui_element_patterns:
                    for trigger in pattern['patterns']:
                        if trigger.lower() in text_content.lower():
                            # Add as potential UI element
                            ui_elements.append({
                                "type": pattern['type'],
                                "text": trigger,
                                "confidence": 0.7,  # Default confidence
                                "source": "text_detection"
                            })
            
            # Update current context with detected UI elements
            self.current_context['ui_elements'] = ui_elements
            self.screen_elements = ui_elements
            
            logger.info(f"Detected {len(ui_elements)} UI elements from screen data")
            
        except Exception as e:
            logger.error(f"Error detecting UI elements: {e}")
    
    async def _handle_task_automation(self, data: Dict[str, Any]):
        """
        Handle task automation request.
        Executes a sequence of input actions to automate a task.
        """
        try:
            task_name = data.get('task_name')
            task_description = data.get('description', '')
            actions = data.get('actions', [])
            
            logger.info(f"Automating task: {task_name} - {task_description}")
            
            # Execute the action sequence
            success = self.input_controller.execute_action_sequence(actions)
            
            if success:
                logger.info(f"Successfully automated task: {task_name}")
                
                # Record the automated task
                task_record = {
                    "task_id": str(uuid.uuid4()),
                    "name": task_name,
                    "description": task_description,
                    "actions": actions,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                self.automated_actions.append(task_record)
                
                # Send success message
                await self._send_automation_result(task_name, True, "Task completed successfully")
            else:
                logger.error(f"Failed to automate task: {task_name}")
                
                # Send failure message
                await self._send_automation_result(task_name, False, "Task automation failed")
            
        except Exception as e:
            logger.error(f"Error handling task automation: {e}")
            
            # Send failure message
            await self._send_automation_result(
                data.get('task_name', 'unknown'), 
                False, 
                f"Error: {str(e)}"
            )
    
    async def _handle_cursor_action(self, data: Dict[str, Any]):
        """
        Handle cursor action request.
        Executes a specific cursor action like click, drag, etc.
        """
        try:
            action_type = data.get('action')
            
            if action_type == 'move':
                x = data.get('x')
                y = data.get('y')
                duration = data.get('duration')
                human_like = data.get('human_like', True)
                
                success = self.input_controller.move_to(x, y, duration, human_like)
                
            elif action_type == 'click':
                x = data.get('x')
                y = data.get('y')
                button = data.get('button', 'left')
                clicks = data.get('clicks', 1)
                
                success = self.input_controller.click(x, y, button, clicks)
                
            elif action_type == 'right_click':
                x = data.get('x')
                y = data.get('y')
                
                success = self.input_controller.right_click(x, y)
                
            elif action_type == 'double_click':
                x = data.get('x')
                y = data.get('y')
                
                success = self.input_controller.double_click(x, y)
                
            elif action_type == 'drag':
                x = data.get('x')
                y = data.get('y')
                button = data.get('button', 'left')
                
                success = self.input_controller.drag_to(x, y, button)
                
            elif action_type == 'scroll':
                clicks = data.get('clicks', 0)
                
                success = self.input_controller.scroll(clicks)
                
            else:
                logger.warning(f"Unknown cursor action type: {action_type}")
                success = False
            
            # Send result
            await self._send_action_result(action_type, success)
            
        except Exception as e:
            logger.error(f"Error handling cursor action: {e}")
            
            # Send failure result
            await self._send_action_result(
                data.get('action', 'unknown'), 
                False, 
                f"Error: {str(e)}"
            )
    
    async def _handle_keyboard_action(self, data: Dict[str, Any]):
        """
        Handle keyboard action request.
        Executes a specific keyboard action like typing, pressing a key, etc.
        """
        try:
            action_type = data.get('action')
            
            if action_type == 'type':
                text = data.get('text', '')
                interval = data.get('interval')
                
                success = self.input_controller.type_text(text, interval)
                
            elif action_type == 'press':
                key = data.get('key', '')
                
                success = self.input_controller.press_key(key)
                
            elif action_type == 'hotkey':
                keys = data.get('keys', [])
                
                success = self.input_controller.hotkey(*keys)
                
            else:
                logger.warning(f"Unknown keyboard action type: {action_type}")
                success = False
            
            # Send result
            await self._send_action_result(action_type, success)
            
        except Exception as e:
            logger.error(f"Error handling keyboard action: {e}")
            
            # Send failure result
            await self._send_action_result(
                data.get('action', 'unknown'), 
                False, 
                f"Error: {str(e)}"
            )
    
    async def _handle_llm_suggestion(self, data: Dict[str, Any]):
        """
        Handle LLM suggestion with potential automation.
        Analyzes if the suggestion can be automated using cursor/keyboard actions.
        """
        try:
            suggestion = data.get('suggestion', {})
            suggestion_text = suggestion.get('content', '')
            suggestion_title = suggestion.get('title', '')
            
            logger.info(f"Handling LLM suggestion: {suggestion_title}")
            
            # Analyze suggestion for automation potential
            automation_actions = await self._analyze_suggestion_for_automation(suggestion_text)
            
            if automation_actions:
                # Suggestion can be automated
                logger.info(f"Suggestion can be automated with {len(automation_actions)} actions")
                
                # Create task for automation
                task = {
                    "task_id": str(uuid.uuid4()),
                    "name": f"Auto: {suggestion_title}",
                    "description": suggestion_text,
                    "actions": automation_actions,
                    "source": "llm_suggestion",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add task to current tasks
                self.current_tasks.append(task)
                
                # Send response with automation potential
                await self.ws.send(json.dumps({
                    "type": "suggestion_response",
                    "payload": {
                        "suggestion_id": suggestion.get('id'),
                        "can_automate": True,
                        "task_id": task["task_id"],
                        "actions_count": len(automation_actions),
                        "message": "This suggestion can be automated",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
            else:
                # Suggestion cannot be automated
                logger.info("Suggestion cannot be automated")
                
                # Send response
                await self.ws.send(json.dumps({
                    "type": "suggestion_response",
                    "payload": {
                        "suggestion_id": suggestion.get('id'),
                        "can_automate": False,
                        "message": "This suggestion cannot be automated",
                        "timestamp": datetime.now().isoformat()
                    }
                }))
            
        except Exception as e:
            logger.error(f"Error handling LLM suggestion: {e}")
    
    async def _analyze_suggestion_for_automation(self, suggestion_text: str) -> List[Dict[str, Any]]:
        """
        Analyze a suggestion text to determine if it can be automated.
        Returns a list of actions if automation is possible, or empty list if not.
        
        This is a simplified version - in a real implementation, this would use
        more sophisticated NLP or LLM analysis to understand the suggestion.
        """
        # Simplified analysis based on keyword matching
        actions = []
        
        # Look for common actions in the suggestion text
        suggestion_lower = suggestion_text.lower()
        
        # Check for click actions
        click_triggers = ["click", "select", "choose", "press"]
        if any(trigger in suggestion_lower for trigger in click_triggers):
            # In a real implementation, we would analyze the suggestion text
            # to determine what to click on using NLP/LLM and UI element detection
            
            # For now, just look for UI elements that match keywords in the suggestion
            for element in self.screen_elements:
                element_text = element.get('text', '').lower()
                if element_text and element_text in suggestion_lower:
                    # Found a UI element mentioned in the suggestion
                    actions.append({
                        "action": "click",
                        "x": element.get('position', {}).get('x', 500),  # Default position
                        "y": element.get('position', {}).get('y', 500),  # Default position
                        "button": "left"
                    })
                    break
        
        # Check for type actions
        type_triggers = ["type", "enter", "input", "write"]
        if any(trigger in suggestion_lower for trigger in type_triggers):
            # Extract what to type (simplified)
            start_markers = ['"', "'", "type ", "enter ", "input "]
            end_markers = ['"', "'", " in", " into"]
            
            text_to_type = ""
            for start in start_markers:
                if start in suggestion_lower:
                    start_idx = suggestion_lower.find(start) + len(start)
                    for end in end_markers:
                        if end in suggestion_lower[start_idx:]:
                            end_idx = suggestion_lower[start_idx:].find(end)
                            text_to_type = suggestion_lower[start_idx:start_idx + end_idx]
                            break
                    if text_to_type:
                        break
            
            if text_to_type:
                actions.append({
                    "action": "type",
                    "text": text_to_type
                })
        
        # Check for navigation actions
        nav_triggers = ["go to", "navigate to", "open"]
        if any(trigger in suggestion_lower for trigger in nav_triggers):
            # In a real implementation, we would extract the target location
            # and determine how to navigate there based on current context
            
            # For now, just identify this as a potential navigation action
            if actions:  # If we already have other actions, this is probably automated
                actions.append({
                    "action": "press",
                    "key": "enter"  # Often navigation is completed with Enter
                })
        
        return actions
    
    async def _send_context_data(self):
        """Send current context data to the server."""
        try:
            await self.ws.send(json.dumps({
                "type": "agent_context",
                "payload": {
                    "context": self.current_context,
                    "tasks": self.current_tasks,
                    "ui_elements": self.screen_elements,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.debug("Sent current context data")
        except Exception as e:
            logger.error(f"Error sending context data: {e}")
    
    async def _send_automation_result(self, task_name: str, success: bool, message: str = ""):
        """Send automation result to the server."""
        try:
            await self.ws.send(json.dumps({
                "type": "automation_result",
                "payload": {
                    "task_name": task_name,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info(f"Sent automation result: {success}")
        except Exception as e:
            logger.error(f"Error sending automation result: {e}")
    
    async def _send_action_result(self, action_type: str, success: bool, message: str = ""):
        """Send action result to the server."""
        try:
            await self.ws.send(json.dumps({
                "type": "action_result",
                "payload": {
                    "action_type": action_type,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.debug(f"Sent action result: {success}")
        except Exception as e:
            logger.error(f"Error sending action result: {e}")
    
    def start_llm_listener(self):
        """
        Start a thread to listen for LLM suggestions.
        This thread monitors for LLM output and analyzes it for potential automation.
        """
        if self.llm_listener_active:
            return
        
        self.llm_listener_active = True
        self.llm_listener_thread = threading.Thread(
            target=self._llm_listener_thread,
            daemon=True
        )
        self.llm_listener_thread.start()
        logger.info("Started LLM listener thread")
    
    def _llm_listener_thread(self):
        """
        Thread function to listen for LLM output.
        Analyzes LLM responses for potential automation opportunities.
        """
        while self.llm_listener_active:
            try:
                # Check for new LLM output (this would interface with your existing LLM system)
                # For now, just sleep and wait
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in LLM listener thread: {e}")
                time.sleep(5)  # Wait before retrying

async def main():
    """Main function to run the context-aware agent."""
    agent = ContextAwareAgent()
    
    if await agent.start():
        try:
            # Keep the agent running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
        finally:
            await agent.stop()
    else:
        logger.error("Failed to start agent")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)