#!/usr/bin/env python3
"""
Agent Workflow Integration Module

Connects the agent workflow system to the existing sensor and memory architecture.
This module enables:
1. Contextual task detection from user activity
2. Keyboard and cursor automation based on detected tasks
3. Integration with the existing memory system for contextual awareness
"""
import asyncio
import json
import logging
import os
import sys
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from agent_workflow
from agent_workflow.context_aware_agent import ContextAwareAgent
from agent_workflow.input_controller import InputController
from agent_workflow.enhanced_bridge import EnhancedBridge

# Configure logging
os.makedirs('logs/agent', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent/agent_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentWorkflowIntegration:
    """
    Integrates agent workflow with existing sensor and memory architecture.
    Provides bidirectional connection between the agent system and the memory system.
    """
    
    def __init__(self, 
                 memory_file: str = "memory/memory_state.json",
                 context_file: str = "memory/last_context.json",
                 enhanced_bridge: Optional[EnhancedBridge] = None,
                 integration_mode: str = "direct"):
        """
        Initialize the integration module.
        
        Args:
            memory_file: Path to memory state file
            context_file: Path to context file
            enhanced_bridge: Existing EnhancedBridge instance or None to create new
            integration_mode: Integration method ("direct" or "bridge")
        """
        self.memory_file = memory_file
        self.context_file = context_file
        self.integration_mode = integration_mode
        self.running = False
        self.update_interval = 2.0  # Seconds
        
        # Create or use bridge
        self.bridge = enhanced_bridge or EnhancedBridge()
        
        # Create agent (when not using the bridge's agent)
        if integration_mode == "direct":
            self.agent = ContextAwareAgent()
        else:
            self.agent = self.bridge.agent
        
        # Memory cache
        self.memory_cache = {}
        self.context_cache = {}
        self.last_memory_update = 0
        self.last_context_update = 0
        
        # Action queue for tasks that should be executed
        self.action_queue = asyncio.Queue()
        self.executor_task = None
        
        logger.info(f"Agent workflow integration initialized in {integration_mode} mode")
    
    async def start(self):
        """Start the integration module."""
        try:
            self.running = True
            
            # Start the bridge if in bridge mode
            if self.integration_mode == "bridge":
                logger.info("Starting enhanced bridge...")
                asyncio.create_task(self.bridge.start())
                await asyncio.sleep(1)  # Give bridge time to start
            
            # Start agent if in direct mode
            if self.integration_mode == "direct":
                logger.info("Starting context-aware agent...")
                await self.agent.start()
            
            # Start action executor
            self.executor_task = asyncio.create_task(self._action_executor())
            
            # Start main loop
            await self._main_loop()
            
            return True
        except Exception as e:
            logger.error(f"Error starting agent integration: {e}")
            return False
    
    async def stop(self):
        """Stop the integration module."""
        self.running = False
        
        # Stop agent if in direct mode
        if self.integration_mode == "direct":
            await self.agent.stop()
        
        # Stop bridge if in bridge mode
        if self.integration_mode == "bridge":
            await self.bridge.stop()
        
        # Cancel executor task
        if self.executor_task:
            self.executor_task.cancel()
            
        logger.info("Agent workflow integration stopped")
    
    async def _load_memory_state(self) -> Dict[str, Any]:
        """Load memory state from file."""
        try:
            if os.path.exists(self.memory_file):
                last_modified = os.path.getmtime(self.memory_file)
                
                # Use cached version if not modified
                if last_modified <= self.last_memory_update:
                    return self.memory_cache
                
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.memory_cache = data
                    self.last_memory_update = last_modified
                    return data
            return {}
        except Exception as e:
            logger.error(f"Error loading memory state: {e}")
            return {}
    
    async def _load_context(self) -> Dict[str, Any]:
        """Load context from file."""
        try:
            if os.path.exists(self.context_file):
                last_modified = os.path.getmtime(self.context_file)
                
                # Use cached version if not modified
                if last_modified <= self.last_context_update:
                    return self.context_cache
                
                with open(self.context_file, 'r') as f:
                    data = json.load(f)
                    self.context_cache = data
                    self.last_context_update = last_modified
                    return data
            return {}
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return {}
    
    async def _update_agent_context(self):
        """Update agent with latest context from memory system."""
        try:
            # Load context from file
            context = await self._load_context()
            
            if not context:
                return
            
            # Create sensor data update for the agent
            process_data = {
                "type": "sensor_data",
                "payload": {
                    "sensor_type": "process",
                    "active_window": context.get("active_window", ""),
                    "active_app": context.get("active_app", ""),
                    "active_apps": context.get("active_apps", []),
                    "window_history": context.get("window_history", []),
                    "timestamp": context.get("timestamp", int(time.time()))
                }
            }
            
            # Create screen data update for the agent
            screen_data = {
                "type": "sensor_data",
                "payload": {
                    "sensor_type": "screen",
                    "text": context.get("screen_text", ""),
                    "visual_context": context.get("visual_context", ""),
                    "timestamp": context.get("timestamp", int(time.time()))
                }
            }
            
            # Send updates to agent via WebSocket
            if self.agent and self.agent.ws:
                # Send process data
                await self.agent.ws.send(json.dumps(process_data))
                
                # Send screen data
                await self.agent.ws.send(json.dumps(screen_data))
                
                logger.debug("Updated agent with latest context")
        except Exception as e:
            logger.error(f"Error updating agent context: {e}")
    
    async def _check_for_task_opportunities(self):
        """
        Check memory and context for task automation opportunities.
        Detects potential tasks that could be automated based on user activity.
        """
        try:
            # Load memory and context
            memory = await self._load_memory_state()
            context = await self._load_context()
            
            if not memory or not context:
                return
            
            # Check active window and app
            active_window = context.get("active_window", "")
            active_app = context.get("active_app", "")
            
            if not active_window or not active_app:
                return
            
            # Analyze for repetitive patterns (simplified)
            # In a real implementation, this would use more sophisticated pattern detection
            
            # Check for repeated window switches that might indicate a task
            window_history = context.get("window_history", [])
            if len(window_history) >= 3:
                # Check for back-and-forth pattern (A -> B -> A)
                if window_history[0] == window_history[2] and window_history[0] != window_history[1]:
                    # Potential task: switching between two windows
                    logger.info(f"Detected potential task: Switching between {window_history[0]} and {window_history[1]}")
                    
                    # Create a potential automation task
                    task = {
                        "task_type": "window_switching",
                        "description": f"Switch between {window_history[0]} and {window_history[1]}",
                        "windows": [window_history[0], window_history[1]],
                        "confidence": 0.7
                    }
                    
                    # Queue for potential automation
                    await self._suggest_task_automation(task)
            
            # Check for repeated text entry (simplified)
            # In a real implementation, this would track text entry patterns
            
            logger.debug("Checked for task opportunities")
            
        except Exception as e:
            logger.error(f"Error checking for task opportunities: {e}")
    
    async def _suggest_task_automation(self, task: Dict[str, Any]):
        """Suggest task automation to the user."""
        try:
            # Create suggestion
            suggestion = {
                "type": "suggestion",
                "payload": {
                    "title": f"Automate: {task.get('description', 'Task')}",
                    "content": f"I noticed you're repeatedly {task.get('description')}. Would you like me to automate this?",
                    "task_data": task,
                    "confidence": task.get("confidence", 0.5),
                    "actions": [
                        {"id": "automate", "label": "Automate", "primary": True},
                        {"id": "dismiss", "label": "No Thanks", "primary": False},
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Send via bridge if available
            if self.bridge and hasattr(self.bridge, "send_message"):
                await self.bridge.send_message("agent_suggestion", suggestion["payload"])
            elif self.agent and self.agent.ws:
                # Send directly to agent
                await self.agent.ws.send(json.dumps(suggestion))
                
            logger.info(f"Suggested task automation: {task.get('description')}")
            
        except Exception as e:
            logger.error(f"Error suggesting task automation: {e}")
    
    async def _main_loop(self):
        """Main loop for the integration module."""
        try:
            logger.info("Starting main integration loop")
            
            while self.running:
                # Update agent with latest context
                await self._update_agent_context()
                
                # Check for task opportunities
                await self._check_for_task_opportunities()
                
                # Wait before next iteration
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
    
    async def _action_executor(self):
        """Execute queued actions."""
        try:
            logger.info("Starting action executor")
            
            while self.running:
                # Get next action from queue
                try:
                    action = await asyncio.wait_for(self.action_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Execute the action
                action_type = action.get("type")
                
                if action_type == "cursor":
                    # Execute cursor action
                    await self._execute_cursor_action(action)
                elif action_type == "keyboard":
                    # Execute keyboard action
                    await self._execute_keyboard_action(action)
                elif action_type == "task":
                    # Execute task sequence
                    await self._execute_task_sequence(action)
                
                # Mark task as done
                self.action_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("Action executor cancelled")
        except Exception as e:
            logger.error(f"Error in action executor: {e}")
    
    async def _execute_cursor_action(self, action: Dict[str, Any]):
        """Execute a cursor action."""
        try:
            # Get parameters
            action_name = action.get("action", "move")
            x = action.get("x")
            y = action.get("y")
            
            # Execute via agent's input controller
            input_controller = self.agent.input_controller
            
            if action_name == "move":
                input_controller.move_to(x, y)
            elif action_name == "click":
                input_controller.click(x, y)
            elif action_name == "right_click":
                input_controller.right_click(x, y)
            elif action_name == "double_click":
                input_controller.double_click(x, y)
            elif action_name == "drag":
                end_x = action.get("end_x")
                end_y = action.get("end_y")
                input_controller.drag_to(end_x, end_y)
            
            logger.info(f"Executed cursor action: {action_name}")
            
        except Exception as e:
            logger.error(f"Error executing cursor action: {e}")
    
    async def _execute_keyboard_action(self, action: Dict[str, Any]):
        """Execute a keyboard action."""
        try:
            # Get parameters
            action_name = action.get("action", "type")
            
            # Execute via agent's input controller
            input_controller = self.agent.input_controller
            
            if action_name == "type":
                text = action.get("text", "")
                input_controller.type_text(text)
            elif action_name == "press":
                key = action.get("key", "")
                input_controller.press_key(key)
            elif action_name == "hotkey":
                keys = action.get("keys", [])
                input_controller.hotkey(*keys)
            
            logger.info(f"Executed keyboard action: {action_name}")
            
        except Exception as e:
            logger.error(f"Error executing keyboard action: {e}")
    
    async def _execute_task_sequence(self, action: Dict[str, Any]):
        """Execute a sequence of actions as a task."""
        try:
            # Get parameters
            task_name = action.get("name", "Unnamed Task")
            actions = action.get("actions", [])
            
            if not actions:
                logger.warning(f"Task {task_name} has no actions to execute")
                return
            
            # Execute via agent's input controller
            input_controller = self.agent.input_controller
            
            # Execute action sequence
            success = input_controller.execute_action_sequence(actions)
            
            if success:
                logger.info(f"Successfully executed task sequence: {task_name}")
            else:
                logger.error(f"Failed to execute task sequence: {task_name}")
            
        except Exception as e:
            logger.error(f"Error executing task sequence: {e}")

async def run_direct_integration():
    """Run the agent workflow integration in direct mode."""
    integration = AgentWorkflowIntegration(integration_mode="direct")
    
    if await integration.start():
        try:
            # Keep the integration running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Integration stopped by user")
        finally:
            await integration.stop()
    else:
        logger.error("Failed to start integration")
        sys.exit(1)

async def run_bridge_integration():
    """Run the agent workflow integration in bridge mode."""
    # Create bridge
    bridge = EnhancedBridge()
    
    # Create integration with the bridge
    integration = AgentWorkflowIntegration(
        integration_mode="bridge",
        enhanced_bridge=bridge
    )
    
    if await integration.start():
        try:
            # Keep the integration running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Integration stopped by user")
        finally:
            await integration.stop()
    else:
        logger.error("Failed to start integration")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check if mode is specified
        mode = "direct"
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
        
        if mode == "bridge":
            asyncio.run(run_bridge_integration())
        else:
            asyncio.run(run_direct_integration())
    except KeyboardInterrupt:
        logger.info("Integration stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)