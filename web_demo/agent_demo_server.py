#!/usr/bin/env python3
"""
Agent Demo Server - Real-time WebSocket server for testing agent capabilities.

Provides comprehensive testing interface for:
- Task execution and monitoring
- Agent state management
- Performance metrics
- Failure simulation
- Real-time updates
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# FastAPI and WebSocket imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from execution.core.task_orchestrator import TaskOrchestrator, TaskDefinition, TaskStep, TaskPriority
from execution.core.agent_base import AgentBase, AgentConfig, AgentCapability, AgentState
from execution.agents.suggestion_agent import SuggestionAgent
from execution.memory.agent_memory import AgentMemory, MemoryType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SensAI Agent Demo", version="1.0.0")

# Global state
orchestrator = TaskOrchestrator(max_concurrent_tasks=20)
connected_clients: List[WebSocket] = []
test_agents: Dict[str, AgentBase] = {}
demo_scenarios: Dict[str, Dict[str, Any]] = {}

# Mock Test Agents for demonstration
class MockScreenAnalysisAgent(AgentBase):
    """Mock agent for screen analysis testing."""
    
    async def initialize(self) -> None:
        await asyncio.sleep(0.1)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        action = task_data.get("action", "analyze")
        
        if action == "analyze_screen":
            # Simulate screen analysis with variable success
            await asyncio.sleep(2.0)
            success_rate = 0.85
            
            if hash(str(time.time())) % 100 < success_rate * 100:
                return {
                    "success": True,
                    "elements_found": 15,
                    "ui_components": ["button", "textfield", "dropdown"],
                    "confidence": 0.92,
                    "processing_time": 2.0
                }
            else:
                raise Exception("Screen capture failed - display not accessible")
        
        elif action == "simulate_failure":
            await asyncio.sleep(1.0)
            raise Exception("Simulated agent failure for testing")
        
        return {"action": action, "status": "completed"}
    
    async def cleanup(self) -> None:
        pass

class MockAutomationAgent(AgentBase):
    """Mock agent for automation testing."""
    
    async def initialize(self) -> None:
        await asyncio.sleep(0.1)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        action = task_data.get("action", "automate")
        
        if action == "click_element":
            await asyncio.sleep(1.5)
            return {
                "success": True,
                "element_clicked": task_data.get("element_id", "unknown"),
                "coordinates": [100, 200],
                "execution_time": 1.5
            }
        
        elif action == "type_text":
            text = task_data.get("text", "")
            await asyncio.sleep(len(text) * 0.05)  # Simulate typing speed
            return {
                "success": True,
                "text_typed": text,
                "characters": len(text),
                "execution_time": len(text) * 0.05
            }
        
        elif action == "complex_workflow":
            # Multi-step workflow simulation
            steps = ["analyze", "plan", "execute", "verify"]
            results = []
            
            for step in steps:
                await asyncio.sleep(1.0)
                # Simulate occasional step failures
                if step == "execute" and hash(str(time.time())) % 10 < 2:
                    raise Exception(f"Workflow step '{step}' failed")
                
                results.append({"step": step, "completed": True})
            
            return {
                "success": True,
                "workflow_steps": results,
                "total_duration": len(steps) * 1.0
            }
        
        return {"action": action, "status": "completed"}
    
    async def cleanup(self) -> None:
        pass

class MockLLMAgent(AgentBase):
    """Mock agent for LLM reasoning testing."""
    
    async def initialize(self) -> None:
        await asyncio.sleep(0.2)
    
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        query = task_data.get("query", "")
        complexity = task_data.get("complexity", "medium")
        
        # Simulate processing time based on complexity
        processing_times = {"simple": 1.0, "medium": 3.0, "complex": 8.0}
        processing_time = processing_times.get(complexity, 3.0)
        
        await asyncio.sleep(processing_time)
        
        # Simulate reasoning with potential failures
        if "impossible" in query.lower():
            raise Exception("Cannot process impossible request")
        
        return {
            "success": True,
            "response": f"Analyzed query: '{query}' with {complexity} complexity",
            "reasoning_steps": 5,
            "confidence": 0.87,
            "processing_time": processing_time,
            "tokens_processed": len(query.split()) * 4
        }
    
    async def cleanup(self) -> None:
        pass

# Initialize test agents
async def initialize_test_agents():
    """Initialize mock agents for testing."""
    global test_agents
    
    agents_config = [
        {
            "name": "screen_agent",
            "class": MockScreenAnalysisAgent,
            "capabilities": [AgentCapability.SCREEN_ANALYSIS, AgentCapability.VISUAL_PROCESSING]
        },
        {
            "name": "automation_agent",
            "class": MockAutomationAgent,
            "capabilities": [AgentCapability.TASK_AUTOMATION]
        },
        {
            "name": "llm_agent",
            "class": MockLLMAgent,
            "capabilities": [AgentCapability.LLM_REASONING, AgentCapability.CONTEXT_AWARENESS]
        }
    ]
    
    for config in agents_config:
        agent_config = AgentConfig(
            name=config["name"],
            capabilities=config["capabilities"],
            max_concurrent_tasks=3,
            enable_metrics=True
        )
        
        agent = config["class"](agent_config)
        await agent.start()
        
        test_agents[config["name"]] = agent
        orchestrator.register_agent(agent)
    
    logger.info(f"Initialized {len(test_agents)} test agents")

# Demo scenarios
def create_demo_scenarios():
    """Create predefined demo scenarios."""
    global demo_scenarios
    
    demo_scenarios = {
        "simple_success": {
            "name": "Simple Success Case",
            "description": "Basic screen analysis task that should succeed",
            "task_def": TaskDefinition(
                task_id=str(uuid.uuid4()),
                name="Simple Screen Analysis",
                description="Analyze current screen for UI elements",
                steps=[
                    TaskStep(
                        step_id="analyze",
                        agent_capability=AgentCapability.SCREEN_ANALYSIS,
                        action="analyze_screen",
                        parameters={"mode": "full", "confidence_threshold": 0.8}
                    )
                ],
                priority=TaskPriority.NORMAL
            )
        },
        
        "complex_workflow": {
            "name": "Complex Multi-Step Workflow",
            "description": "Multi-agent workflow with dependencies",
            "task_def": TaskDefinition(
                task_id=str(uuid.uuid4()),
                name="Complex Automation Workflow",
                description="Multi-step automation with screen analysis",
                steps=[
                    TaskStep(
                        step_id="screen_scan",
                        agent_capability=AgentCapability.SCREEN_ANALYSIS,
                        action="analyze_screen",
                        parameters={"detailed": True}
                    ),
                    TaskStep(
                        step_id="plan_automation",
                        agent_capability=AgentCapability.LLM_REASONING,
                        action="process_task",
                        parameters={"query": "Plan automation based on screen analysis", "complexity": "medium"},
                        dependencies=["screen_scan"]
                    ),
                    TaskStep(
                        step_id="execute_automation",
                        agent_capability=AgentCapability.TASK_AUTOMATION,
                        action="complex_workflow",
                        parameters={"workflow_type": "adaptive"},
                        dependencies=["plan_automation"]
                    )
                ],
                priority=TaskPriority.HIGH
            )
        },
        
        "failure_scenario": {
            "name": "Planned Failure Test",
            "description": "Test failure handling and recovery",
            "task_def": TaskDefinition(
                task_id=str(uuid.uuid4()),
                name="Failure Test",
                description="Test agent failure handling",
                steps=[
                    TaskStep(
                        step_id="fail_step",
                        agent_capability=AgentCapability.SCREEN_ANALYSIS,
                        action="simulate_failure",
                        parameters={"failure_type": "planned"},
                        max_retries=2
                    )
                ],
                priority=TaskPriority.LOW
            )
        },
        
        "stress_test": {
            "name": "High Load Stress Test",
            "description": "Test system under high concurrent load",
            "task_def": TaskDefinition(
                task_id=str(uuid.uuid4()),
                name="Stress Test",
                description="Concurrent task execution test",
                steps=[
                    TaskStep(
                        step_id=f"parallel_{i}",
                        agent_capability=AgentCapability.LLM_REASONING,
                        action="process_task",
                        parameters={"query": f"Process request {i}", "complexity": "simple"}
                    ) for i in range(10)
                ],
                priority=TaskPriority.NORMAL
            )
        }
    }

# WebSocket connection management
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected clients."""
    if connected_clients:
        message_str = json.dumps(message)
        disconnected = []
        
        for client in connected_clients:
            try:
                await client.send_text(message_str)
            except Exception:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            connected_clients.remove(client)

# Event handlers for real-time updates
class DemoEventHandler:
    """Event handler for demo real-time updates."""
    
    def on_state_change(self, agent_id: str, old_state: AgentState, new_state: AgentState):
        asyncio.create_task(broadcast_message({
            "type": "agent_state_change",
            "agent_id": agent_id,
            "old_state": old_state.value,
            "new_state": new_state.value,
            "timestamp": time.time()
        }))
    
    def on_task_start(self, agent_id: str, task_id: str, task_data: Dict[str, Any]):
        asyncio.create_task(broadcast_message({
            "type": "task_start",
            "agent_id": agent_id,
            "task_id": task_id,
            "task_data": task_data,
            "timestamp": time.time()
        }))
    
    def on_task_complete(self, agent_id: str, task_id: str, result: Any):
        asyncio.create_task(broadcast_message({
            "type": "task_complete",
            "agent_id": agent_id,
            "task_id": task_id,
            "result": result,
            "timestamp": time.time()
        }))
    
    def on_error(self, agent_id: str, error: Exception, context: Dict[str, Any]):
        asyncio.create_task(broadcast_message({
            "type": "agent_error",
            "agent_id": agent_id,
            "error": str(error),
            "context": context,
            "timestamp": time.time()
        }))

# Add event handler to all agents
demo_handler = DemoEventHandler()

# API Endpoints
@app.get("/")
async def index():
    """Serve the demo interface."""
    return HTMLResponse(open("/Users/segevbin/Desktop/SensAI/Aiayer/web_demo/index.html").read())

@app.get("/simple")
async def simple_interface():
    """Serve the simple demo interface."""
    return HTMLResponse(open("/Users/segevbin/Desktop/SensAI/Aiayer/web_demo/simple.html").read())

@app.get("/api/agents")
async def get_agents():
    """Get all registered agents and their status."""
    agents_info = []
    for agent_id, agent in test_agents.items():
        status = agent.get_status()
        agents_info.append({
            "id": agent_id,
            "name": agent.config.name,
            "status": status
        })
    
    return {"agents": agents_info}

@app.get("/api/scenarios")
async def get_scenarios():
    """Get available demo scenarios."""
    scenarios_info = []
    for scenario_id, scenario in demo_scenarios.items():
        scenarios_info.append({
            "id": scenario_id,
            "name": scenario["name"],
            "description": scenario["description"]
        })
    
    return {"scenarios": scenarios_info}

@app.post("/api/execute/{scenario_id}")
async def execute_scenario(scenario_id: str):
    """Execute a demo scenario."""
    if scenario_id not in demo_scenarios:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    scenario = demo_scenarios[scenario_id]
    task_def = scenario["task_def"]
    
    # Generate new task ID for each execution
    task_def.task_id = str(uuid.uuid4())
    
    # Submit task to orchestrator
    try:
        task_id = await orchestrator.submit_task(task_def)
        return {"success": True, "task_id": task_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/orchestrator/status")
async def get_orchestrator_status():
    """Get orchestrator status and statistics."""
    return orchestrator.get_orchestrator_status()

@app.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str):
    """Get detailed task status."""
    status = orchestrator.get_task_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "agents_count": len(test_agents),
            "scenarios_count": len(demo_scenarios),
            "timestamp": time.time()
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": time.time()}))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the demo environment."""
    logger.info("Starting Agent Demo Server...")
    
    # Initialize test agents
    await initialize_test_agents()
    
    # Add event handlers to agents
    for agent in test_agents.values():
        agent.add_event_handler(demo_handler)
    
    # Create demo scenarios
    create_demo_scenarios()
    
    # Start orchestrator
    await orchestrator.start()
    
    logger.info("Agent Demo Server ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Agent Demo Server...")
    
    # Stop orchestrator
    await orchestrator.stop()
    
    # Stop all agents
    for agent in test_agents.values():
        await agent.stop()
    
    logger.info("Agent Demo Server stopped.")

# Background task for periodic updates
async def periodic_status_updates():
    """Send periodic status updates to clients."""
    while True:
        try:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            if connected_clients:
                status_update = {
                    "type": "status_update",
                    "orchestrator": orchestrator.get_orchestrator_status(),
                    "agents": {agent_id: agent.get_status() for agent_id, agent in test_agents.items()},
                    "timestamp": time.time()
                }
                
                await broadcast_message(status_update)
                
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(1)

# Start periodic updates task
@app.on_event("startup")
async def start_periodic_updates():
    asyncio.create_task(periodic_status_updates())

if __name__ == "__main__":
    uvicorn.run(
        "agent_demo_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
