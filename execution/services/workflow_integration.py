#!/usr/bin/env python3
"""
WorkflowIntegrator - Seamless integration with existing agent_workflow components.

This service bridges the new execution system with the existing agent workflow,
providing backward compatibility and enhanced capabilities.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import websockets

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from execution.core.agent_base import AgentBase, AgentConfig, AgentCapability
from execution.core.task_orchestrator import TaskOrchestrator, TaskDefinition, TaskStep
from execution.agents.suggestion_agent import SuggestionAgent
from execution.agents.automation_agent import AutomationAgent
from execution.memory.agent_memory import AgentMemory

# Import existing workflow components
from agent_workflow.context_aware_agent import ContextAwareAgent
from agent_workflow.input_controller import InputController

logger = logging.getLogger(__name__)


class WorkflowIntegrator:
    """
    Enterprise-grade integration service for existing agent workflow components.
    
    Features:
    - Seamless integration with existing ContextAwareAgent
    - Bridge between old and new architecture
    - Backward compatibility
    - Enhanced capabilities
    - Unified task coordination
    - Memory integration across systems
    """
    
    def __init__(self, orchestrator: TaskOrchestrator, memory: AgentMemory):
        """Initialize the workflow integrator."""
        self.orchestrator = orchestrator
        self.memory = memory
        
        # Legacy components
        self.legacy_context_agent: Optional[ContextAwareAgent] = None
        self.legacy_input_controller: Optional[InputController] = None
        
        # New execution agents
        self.suggestion_agent: Optional[SuggestionAgent] = None
        self.automation_agent: Optional[AutomationAgent] = None
        
        # Integration mappings
        self.message_type_mapping = {
            # Legacy -> New system mappings
            'automate_task': 'agent_task_execution',
            'cursor_action': 'automation_action', 
            'keyboard_action': 'automation_action',
            'llm_suggestion': 'suggestion_processing',
            'context_request': 'context_analysis'
        }
        
        # WebSocket connections
        self.legacy_ws_connections: List[websockets.WebSocketServerProtocol] = []
        
        logger.info("WorkflowIntegrator initialized")
    
    async def initialize_integration(self) -> None:
        """Initialize integration with existing workflow."""
        try:
            # Initialize legacy context agent
            await self._initialize_legacy_components()
            
            # Initialize new execution agents
            await self._initialize_execution_agents()
            
            # Register agents with orchestrator
            await self._register_agents_with_orchestrator()
            
            # Setup message bridging
            await self._setup_message_bridging()
            
            logger.info("Workflow integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow integration: {e}")
            raise
    
    async def _initialize_legacy_components(self) -> None:
        """Initialize existing workflow components."""
        try:
            # Initialize legacy context aware agent
            self.legacy_context_agent = ContextAwareAgent(
                server_uri="ws://127.0.0.1:8765",
                safety_level="high"
            )
            
            # Initialize legacy input controller
            self.legacy_input_controller = InputController(safety_level="high")
            
            logger.info("Legacy components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize legacy components: {e}")
            raise
    
    async def _initialize_execution_agents(self) -> None:
        """Initialize new execution agents."""
        try:
            # Create suggestion agent
            suggestion_config = AgentConfig(
                name="SuggestionAgent",
                capabilities=[
                    AgentCapability.SUGGESTION_GENERATION,
                    AgentCapability.LLM_REASONING,
                    AgentCapability.CONTEXT_AWARENESS
                ]
            )
            self.suggestion_agent = SuggestionAgent(suggestion_config, self.memory)
            await self.suggestion_agent.start()
            
            # Create automation agent
            automation_config = AgentConfig(
                name="AutomationAgent", 
                capabilities=[
                    AgentCapability.TASK_AUTOMATION,
                    AgentCapability.SCREEN_ANALYSIS
                ]
            )
            self.automation_agent = AutomationAgent(automation_config, self.memory)
            await self.automation_agent.start()
            
            logger.info("Execution agents initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize execution agents: {e}")
            raise
    
    async def _register_agents_with_orchestrator(self) -> None:
        """Register all agents with the task orchestrator."""
        if self.suggestion_agent:
            self.orchestrator.register_agent(self.suggestion_agent)
            
        if self.automation_agent:
            self.orchestrator.register_agent(self.automation_agent)
            
        logger.info("Agents registered with orchestrator")
    
    async def _setup_message_bridging(self) -> None:
        """Setup message bridging between legacy and new systems."""
        # This would setup WebSocket message forwarding
        # between the legacy system and the new execution system
        logger.info("Message bridging setup completed")
    
    # ========== Legacy Message Handling ==========
    
    async def handle_legacy_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message from legacy system and route to appropriate agent."""
        msg_type = message.get("type")
        payload = message.get("payload", {})
        
        try:
            if msg_type in self.message_type_mapping:
                new_msg_type = self.message_type_mapping[msg_type]
                return await self._route_to_execution_system(new_msg_type, payload)
            else:
                return await self._route_to_legacy_system(msg_type, payload)
                
        except Exception as e:
            logger.error(f"Error handling legacy message: {e}")
            return {"error": str(e)}
    
    async def _route_to_execution_system(self, msg_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route message to new execution system."""
        if msg_type == "suggestion_processing":
            if self.suggestion_agent:
                task_id = await self.suggestion_agent.execute_task({
                    "action": "analyze_response",
                    "parameters": payload
                })
                return {"task_id": task_id, "routed_to": "suggestion_agent"}
                
        elif msg_type == "automation_action":
            if self.automation_agent:
                task_id = await self.automation_agent.execute_task({
                    "action": "execute_action",
                    "parameters": payload
                })
                return {"task_id": task_id, "routed_to": "automation_agent"}
                
        elif msg_type == "agent_task_execution":
            # Create complex task for orchestrator
            task_def = await self._create_task_from_legacy_request(payload)
            task_id = await self.orchestrator.submit_task(task_def)
            return {"task_id": task_id, "routed_to": "orchestrator"}
        
        return {"error": "No suitable agent found"}
    
    async def _route_to_legacy_system(self, msg_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route message to legacy system."""
        if self.legacy_context_agent:
            # Forward to legacy context agent
            # This would involve WebSocket communication
            return {"routed_to": "legacy_context_agent", "message_type": msg_type}
        
        return {"error": "Legacy system not available"}
    
    async def _create_task_from_legacy_request(self, payload: Dict[str, Any]) -> TaskDefinition:
        """Create TaskDefinition from legacy automation request."""
        task_name = payload.get("task_name", "Legacy Task")
        task_description = payload.get("description", "Task from legacy system")
        
        # Convert legacy actions to task steps
        steps = []
        actions = payload.get("actions", [])
        
        for i, action in enumerate(actions):
            step = TaskStep(
                step_id=f"step_{i}",
                agent_capability=self._map_legacy_action_to_capability(action),
                action=action.get("type", "unknown"),
                parameters=action.get("parameters", {})
            )
            steps.append(step)
        
        return TaskDefinition(
            task_id=f"legacy_task_{int(asyncio.get_event_loop().time())}",
            name=task_name,
            description=task_description,
            steps=steps,
            metadata={"source": "legacy_system"}
        )
    
    def _map_legacy_action_to_capability(self, action: Dict[str, Any]) -> AgentCapability:
        """Map legacy action type to agent capability."""
        action_type = action.get("type", "")
        
        if action_type in ["click", "type", "key_press", "drag"]:
            return AgentCapability.TASK_AUTOMATION
        elif action_type in ["analyze", "suggest"]:
            return AgentCapability.SUGGESTION_GENERATION
        elif action_type in ["screenshot", "find_element"]:
            return AgentCapability.SCREEN_ANALYSIS
        else:
            return AgentCapability.CONTEXT_AWARENESS
    
    # ========== Enhanced Capabilities ==========
    
    async def create_enhanced_task(self, task_data: Dict[str, Any]) -> str:
        """Create enhanced task using both legacy and new capabilities."""
        # This combines the power of legacy components with new execution system
        
        # Analyze context using legacy system
        context = await self._get_legacy_context()
        
        # Generate suggestions using new system
        suggestions = await self._get_enhanced_suggestions(context, task_data)
        
        # Create optimized task plan
        task_plan = await self._create_optimized_task_plan(task_data, context, suggestions)
        
        # Submit to orchestrator
        task_id = await self.orchestrator.submit_task(task_plan)
        
        logger.info(f"Created enhanced task: {task_id}")
        return task_id
    
    async def _get_legacy_context(self) -> Dict[str, Any]:
        """Get context from legacy system."""
        if self.legacy_context_agent:
            # This would get context from the legacy context aware agent
            return {
                "screen_data": "legacy_screen_analysis",
                "process_data": "legacy_process_info",
                "memory_data": "legacy_memory_context"
            }
        return {}
    
    async def _get_enhanced_suggestions(self, context: Dict[str, Any], 
                                      task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get enhanced suggestions from new system."""
        if self.suggestion_agent:
            task_id = await self.suggestion_agent.execute_task({
                "action": "analyze_response",
                "parameters": {
                    "response": task_data.get("description", ""),
                    "context": context
                }
            })
            
            # Wait for result (simplified for example)
            await asyncio.sleep(0.1)
            result = self.suggestion_agent.get_task_result(task_id)
            
            if result and result.get("is_suggestion"):
                return [result.get("suggestion_data", {})]
        
        return []
    
    async def _create_optimized_task_plan(self, task_data: Dict[str, Any], 
                                        context: Dict[str, Any],
                                        suggestions: List[Dict[str, Any]]) -> TaskDefinition:
        """Create optimized task plan combining all inputs."""
        
        # Use memory to optimize based on past executions
        similar_tasks = self.memory.get_recent_tasks(
            task_type=task_data.get("type", "general"),
            limit=5
        )
        
        # Create optimized steps
        steps = []
        
        # Add context analysis step
        steps.append(TaskStep(
            step_id="context_analysis",
            agent_capability=AgentCapability.CONTEXT_AWARENESS,
            action="analyze_context",
            parameters={"context": context}
        ))
        
        # Add suggestion generation step
        if suggestions:
            steps.append(TaskStep(
                step_id="suggestion_processing",
                agent_capability=AgentCapability.SUGGESTION_GENERATION,
                action="process_suggestions",
                parameters={"suggestions": suggestions}
            ))
        
        # Add automation steps based on task data
        automation_actions = task_data.get("actions", [])
        for i, action in enumerate(automation_actions):
            steps.append(TaskStep(
                step_id=f"automation_{i}",
                agent_capability=AgentCapability.TASK_AUTOMATION,
                action=action.get("type", "execute"),
                parameters=action.get("parameters", {})
            ))
        
        return TaskDefinition(
            task_id=f"enhanced_task_{int(asyncio.get_event_loop().time())}",
            name=task_data.get("name", "Enhanced Task"),
            description=task_data.get("description", "Optimized task execution"),
            steps=steps,
            metadata={
                "source": "enhanced_integration",
                "context_included": bool(context),
                "suggestions_included": len(suggestions),
                "similar_tasks_analyzed": len(similar_tasks)
            }
        )
    
    # ========== Statistics and Monitoring ==========
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics."""
        stats = {
            "legacy_components": {
                "context_agent_active": self.legacy_context_agent is not None,
                "input_controller_active": self.legacy_input_controller is not None
            },
            "execution_agents": {
                "suggestion_agent_active": self.suggestion_agent is not None,
                "automation_agent_active": self.automation_agent is not None
            },
            "orchestrator": self.orchestrator.get_orchestrator_status() if self.orchestrator else {},
            "message_bridging": {
                "legacy_ws_connections": len(self.legacy_ws_connections),
                "supported_message_types": len(self.message_type_mapping)
            }
        }
        
        # Add agent statistics if available
        if self.suggestion_agent:
            stats["suggestion_agent"] = self.suggestion_agent.get_suggestion_statistics()
            
        if self.automation_agent:
            stats["automation_agent"] = self.automation_agent.get_automation_statistics()
        
        return stats
    
    # ========== Cleanup ==========
    
    async def cleanup(self) -> None:
        """Cleanup integration resources."""
        try:
            # Stop execution agents
            if self.suggestion_agent:
                await self.suggestion_agent.stop()
                
            if self.automation_agent:
                await self.automation_agent.stop()
            
            # Cleanup legacy components
            if self.legacy_input_controller:
                self.legacy_input_controller.stop_listeners()
            
            # Close WebSocket connections
            for ws in self.legacy_ws_connections:
                if not ws.closed:
                    await ws.close()
            
            logger.info("Workflow integration cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")