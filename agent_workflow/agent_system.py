#!/usr/bin/env python3
"""
Agent System
Core module for contextual task tracking and assistance.
Provides an intelligent agent that integrates with the operating system
to track user tasks, understand context, and provide relevant assistance.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import websockets
from websockets.client import WebSocketClientProtocol

# Configure logging
os.makedirs('logs/agent', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent/agent_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentSystem:
    """
    Core agent system that provides contextual task tracking and assistance.
    Similar to Project Mariner, this system integrates with the OS to track
    user tasks, understand contextual information, and provide assistance.
    """
    
    def __init__(self, server_uri: str = "ws://127.0.0.1:8765"):
        self.server_uri = server_uri
        self.ws: Optional[WebSocketClientProtocol] = None
        self.client_id = str(uuid.uuid4())
        self.running = False
        self.reconnect_delay = 3
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        
        # Current user context
        self.current_context = {
            "active_app": None,
            "active_window": None,
            "active_apps": [],
            "screen_content": None,
            "timestamp": None,
            "tasks": [],
            "session_id": str(uuid.uuid4())
        }
        
        # Active task tracking
        self.active_tasks = []
        self.completed_tasks = []
        self.task_history = []
        
        # Task detection patterns
        self.task_patterns = [
            {"pattern": "email", "task_type": "communication", "apps": ["Mail", "Gmail", "Outlook"]},
            {"pattern": "document", "task_type": "productivity", "apps": ["Word", "Google Docs", "Pages"]},
            {"pattern": "meeting", "task_type": "communication", "apps": ["Zoom", "Teams", "Google Meet"]},
            {"pattern": "code", "task_type": "development", "apps": ["VS Code", "Xcode", "IntelliJ"]},
            {"pattern": "browse", "task_type": "research", "apps": ["Chrome", "Safari", "Firefox"]},
        ]
    
    async def start(self):
        """Start the agent system."""
        try:
            # Start WebSocket connection
            self.running = True
            await self._connect()
            return True
        except Exception as e:
            logger.error(f"Error starting agent system: {e}")
            return False
    
    async def stop(self):
        """Stop the agent system."""
        self.running = False
        if self.ws:
            await self.ws.close()
    
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
                    
                    # Handle messages
                    await self._handle_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            
            if self.running:
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
    
    async def _send_connection_message(self):
        """Send initial connection message to server."""
        try:
            await self.ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client_type": "agent",
                    "client_id": self.client_id,
                    "version": "1.0.0",
                    "capabilities": ["task_tracking", "context_awareness", "assistance"],
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent connection message")
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
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message."""
        try:
            msg_type = data.get('type')
            
            if msg_type == 'sensor_update':
                # Update context with sensor data
                await self._handle_sensor_update(data.get('data', {}))
            elif msg_type == 'task_request':
                # Handle task request
                await self._handle_task_request(data.get('data', {}))
            elif msg_type == 'context_request':
                # Send current context
                await self._send_context(data.get('data', {}))
            elif msg_type == 'user_instruction':
                # Process natural language instruction
                await self._handle_user_instruction(data.get('data', {}))
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_sensor_update(self, data: Dict[str, Any]):
        """
        Handle sensor update message.
        Updates the agent's understanding of the current context.
        """
        try:
            # Update current context
            if 'active_app' in data:
                self.current_context['active_app'] = data['active_app']
            if 'active_window' in data:
                self.current_context['active_window'] = data['active_window']
            if 'active_apps' in data:
                self.current_context['active_apps'] = data['active_apps']
            if 'screen_content' in data:
                self.current_context['screen_content'] = data['screen_content']
            
            # Update timestamp
            self.current_context['timestamp'] = datetime.now().isoformat()
            
            # Detect potential tasks based on context
            await self._detect_tasks()
            
            logger.info(f"Updated context with active app: {self.current_context.get('active_app')}")
        except Exception as e:
            logger.error(f"Error handling sensor update: {e}")
    
    async def _detect_tasks(self):
        """
        Detect potential tasks based on current context.
        This is a key feature of Mariner-like systems - understanding user tasks from context.
        """
        try:
            # Check active app against task patterns
            active_app = self.current_context.get('active_app')
            active_window = self.current_context.get('active_window', '')
            
            if not active_app:
                return
            
            # Look for task patterns in window title
            potential_tasks = []
            for pattern in self.task_patterns:
                if active_app in pattern.get('apps', []):
                    if pattern['pattern'].lower() in active_window.lower():
                        # Found a potential task
                        task = {
                            "id": str(uuid.uuid4()),
                            "task_type": pattern['task_type'],
                            "app": active_app,
                            "window": active_window,
                            "detected_at": datetime.now().isoformat(),
                            "status": "detected",
                            "confidence": 0.7  # Basic confidence score
                        }
                        potential_tasks.append(task)
            
            # Add new tasks if they don't exist yet
            for task in potential_tasks:
                if not any(t.get('window') == task['window'] for t in self.active_tasks):
                    self.active_tasks.append(task)
                    logger.info(f"Detected new task: {task['task_type']} in {task['app']}")
            
            # Update current context with tasks
            self.current_context['tasks'] = self.active_tasks
            
            # Send task update to interested clients
            await self._send_task_update()
            
        except Exception as e:
            logger.error(f"Error detecting tasks: {e}")
    
    async def _send_task_update(self):
        """Send task update to interested clients."""
        try:
            await self.ws.send(json.dumps({
                "type": "task_update",
                "data": {
                    "active_tasks": self.active_tasks,
                    "completed_tasks": self.completed_tasks,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info(f"Sent task update with {len(self.active_tasks)} active tasks")
        except Exception as e:
            logger.error(f"Error sending task update: {e}")
    
    async def _handle_task_request(self, data: Dict[str, Any]):
        """Handle task request from client."""
        try:
            request_type = data.get('request_type')
            
            if request_type == 'get_tasks':
                # Send current tasks
                await self._send_task_update()
            elif request_type == 'create_task':
                # Create new task
                task_data = data.get('task_data', {})
                new_task = {
                    "id": str(uuid.uuid4()),
                    "task_type": task_data.get('task_type', 'unknown'),
                    "app": task_data.get('app', self.current_context.get('active_app')),
                    "window": task_data.get('window', self.current_context.get('active_window')),
                    "description": task_data.get('description', ''),
                    "created_at": datetime.now().isoformat(),
                    "status": "active",
                    "confidence": 1.0  # User-created tasks have highest confidence
                }
                self.active_tasks.append(new_task)
                logger.info(f"Created new task: {new_task['task_type']}")
                
                # Send task update
                await self._send_task_update()
            elif request_type == 'update_task':
                # Update existing task
                task_id = data.get('task_id')
                updates = data.get('updates', {})
                
                # Find and update task
                for task in self.active_tasks:
                    if task.get('id') == task_id:
                        task.update(updates)
                        logger.info(f"Updated task: {task_id}")
                        break
                
                # Send task update
                await self._send_task_update()
            elif request_type == 'complete_task':
                # Complete task
                task_id = data.get('task_id')
                
                # Find task and mark as completed
                for i, task in enumerate(self.active_tasks):
                    if task.get('id') == task_id:
                        task['status'] = 'completed'
                        task['completed_at'] = datetime.now().isoformat()
                        self.completed_tasks.append(task)
                        self.active_tasks.pop(i)
                        self.task_history.append(task)
                        logger.info(f"Completed task: {task_id}")
                        break
                
                # Send task update
                await self._send_task_update()
        except Exception as e:
            logger.error(f"Error handling task request: {e}")
    
    async def _send_context(self, request: Dict[str, Any]):
        """Send current context to client."""
        try:
            await self.ws.send(json.dumps({
                "type": "context_update",
                "data": {
                    "context": self.current_context,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent context update")
        except Exception as e:
            logger.error(f"Error sending context: {e}")
    
    async def _handle_user_instruction(self, data: Dict[str, Any]):
        """
        Handle natural language instruction from user.
        This allows users to interact with the agent using natural language,
        similar to Project Mariner's capabilities.
        """
        try:
            instruction = data.get('instruction', '')
            if not instruction:
                return
            
            # Process instruction using LLM (in a real implementation)
            # For now, just log the instruction
            logger.info(f"Received user instruction: {instruction}")
            
            # Simple keyword-based processing
            if 'create task' in instruction.lower():
                # Create a new task based on instruction
                new_task = {
                    "id": str(uuid.uuid4()),
                    "task_type": "user_defined",
                    "description": instruction,
                    "app": self.current_context.get('active_app'),
                    "window": self.current_context.get('active_window'),
                    "created_at": datetime.now().isoformat(),
                    "status": "active",
                    "confidence": 1.0
                }
                self.active_tasks.append(new_task)
                
                # Send response to user
                await self._send_user_response(f"Created new task: {instruction}")
                
            elif 'list tasks' in instruction.lower():
                # List current tasks
                task_list = "\n".join([f"- {t.get('description', t.get('task_type'))} in {t.get('app')}" 
                                     for t in self.active_tasks])
                
                if not task_list:
                    task_list = "No active tasks"
                
                # Send response to user
                await self._send_user_response(f"Current tasks:\n{task_list}")
                
            elif 'help' in instruction.lower():
                # Send help information
                help_text = """
                I can help you manage your tasks and provide assistance based on what you're doing.
                
                Commands:
                - "create task [description]" - Create a new task
                - "list tasks" - List your current tasks
                - "complete task [task number or description]" - Mark a task as completed
                - "what am I working on?" - Get information about your current context
                """
                await self._send_user_response(help_text)
                
            else:
                # Generic response - would be handled by LLM in real implementation
                await self._send_user_response(f"I received your instruction: {instruction}")
            
        except Exception as e:
            logger.error(f"Error handling user instruction: {e}")
    
    async def _send_user_response(self, response: str):
        """Send response to user."""
        try:
            await self.ws.send(json.dumps({
                "type": "agent_response",
                "data": {
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info(f"Sent response to user")
        except Exception as e:
            logger.error(f"Error sending response to user: {e}")

async def main():
    """Main function to start the agent system."""
    agent = AgentSystem()
    if await agent.start():
        try:
            # Keep the service running
            await asyncio.Future()
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