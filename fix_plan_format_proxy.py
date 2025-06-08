#!/usr/bin/env python3
"""
Fix Plan Format Proxy - WebSocket proxy that converts plan format between systems
Handles proper plan conversion between JSON and UniversalAutomationPlan objects
"""

import asyncio
import json
import logging
import os
import sys
import uuid
import websockets
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[PLAN-FORMAT-FIX] %(levelname)s:%(name)s:%(message)s',
)
logger = logging.getLogger(__name__)

# Define the same data structures as in universal_intelligent_automation_handler.py
@dataclass
class SmartAutomationStep:
    """Enhanced automation step with smart execution capabilities"""
    id: str
    description: str
    action_type: str  # 'open_app', 'navigate_url', 'click_element', 'type_text', 'hotkey', 'wait', 'analyze_screen'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"  # pending, approved, executing, completed, failed
    estimated_duration: float = 2.0
    retry_count: int = 0
    max_retries: int = 3
    fallback_action: Optional[str] = None
    context_hints: List[str] = None

@dataclass 
class UniversalAutomationPlan:
    """Universal automation plan that works with any request type"""
    task_id: str
    title: str
    description: str
    request_type: str  # 'web_search', 'flight_search', 'app_usage', 'research', 'shopping', etc.
    steps: List[SmartAutomationStep]
    estimated_duration: float
    complexity_score: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    success_probability: float = 0.8
    fallback_strategies: List[str] = None
    user_guidance_needed: bool = False

# Dictionary to store active client connections
client_connections = {}

# Dictionary to store active plans (in memory cache)
active_plans = {}

# Storage directory for plans
PLANS_DIR = os.path.join("cache", "plans")
os.makedirs(PLANS_DIR, exist_ok=True)

async def save_plan_to_disk(plan_id: str, plan_data: Dict[str, Any]) -> bool:
    """Save a plan to disk"""
    try:
        plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
        with open(plan_path, 'w') as f:
            json.dump(plan_data, f, indent=2)
        logger.info(f"Saved plan {plan_id} to disk")
        return True
    except Exception as e:
        logger.error(f"Error saving plan to disk: {e}")
        return False

async def load_plan_from_disk(plan_id: str) -> Optional[Dict[str, Any]]:
    """Load a plan from disk"""
    try:
        plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
        if not os.path.exists(plan_path):
            logger.warning(f"Plan file not found: {plan_path}")
            return None
        with open(plan_path, 'r') as f:
            plan_data = json.load(f)
        logger.info(f"Loaded plan {plan_id} from disk")
        return plan_data
    except Exception as e:
        logger.error(f"Error loading plan from disk: {e}")
        return None

async def convert_plan_dict_to_object(plan_data: Dict[str, Any]) -> Optional[UniversalAutomationPlan]:
    """Convert a plan dictionary to a UniversalAutomationPlan object"""
    if not isinstance(plan_data, dict):
        logger.error(f"Invalid plan data type: {type(plan_data)}")
        return None
    
    try:
        # Convert steps to SmartAutomationStep objects
        smart_steps = []
        for i, step_data in enumerate(plan_data.get("steps", [])):
            # Handle coordinates safely
            coordinates = None
            if step_data.get("coordinates"):
                try:
                    coords = step_data["coordinates"]
                    if isinstance(coords, list) and len(coords) >= 2:
                        coordinates = (int(coords[0]), int(coords[1]))
                except Exception as e:
                    logger.warning(f"Error parsing coordinates: {e}")
            
            step = SmartAutomationStep(
                id=step_data.get("id", f"step_{i+1}"),
                description=step_data.get("description", ""),
                action_type=step_data.get("action_type", "analyze_screen"),
                target=step_data.get("target"),
                value=step_data.get("value"),
                coordinates=coordinates,
                confidence=float(step_data.get("confidence", 0.8)),
                status=step_data.get("status", "pending"),
                estimated_duration=float(step_data.get("estimated_duration", 2.0)),
                retry_count=int(step_data.get("retry_count", 0)),
                max_retries=int(step_data.get("max_retries", 3)),
                fallback_action=step_data.get("fallback_action"),
                context_hints=step_data.get("context_hints", []) or []
            )
            smart_steps.append(step)
        
        # Create plan object
        plan = UniversalAutomationPlan(
            task_id=plan_data.get("task_id", "unknown"),
            title=plan_data.get("title", "Untitled Plan"),
            description=plan_data.get("description", ""),
            request_type=plan_data.get("request_type", "general"),
            steps=smart_steps,
            estimated_duration=float(plan_data.get("estimated_duration", 0.0)),
            complexity_score=float(plan_data.get("complexity_score", 0.5)),
            requires_approval=bool(plan_data.get("requires_approval", True)),
            status=plan_data.get("status", "awaiting_approval"),
            success_probability=float(plan_data.get("success_probability", 0.8)),
            fallback_strategies=plan_data.get("fallback_strategies", []) or [],
            user_guidance_needed=bool(plan_data.get("user_guidance_needed", False))
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error converting plan to object: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def ensure_plan_exists(plan_id: str) -> bool:
    """Ensure a plan exists in memory or on disk, creating a dummy if needed"""
    # Check if plan exists in memory
    if plan_id in active_plans:
        logger.info(f"Plan {plan_id} exists in memory")
        return True
    
    # Check if plan exists on disk
    plan_data = await load_plan_from_disk(plan_id)
    if plan_data:
        # Convert to plan object and store in memory
        plan_obj = await convert_plan_dict_to_object(plan_data)
        if plan_obj:
            active_plans[plan_id] = plan_obj
            logger.info(f"Loaded plan {plan_id} into memory")
            return True
    
    # Create a dummy plan if not found
    try:
        timestamp = int(datetime.now().timestamp())
        
        # Create a dummy step
        dummy_step = SmartAutomationStep(
            id="step_1",
            description="Dummy step for plan execution",
            action_type="analyze_screen",
            estimated_duration=1.0
        )
        
        # Create a dummy plan
        dummy_plan = UniversalAutomationPlan(
            task_id=plan_id,
            title=f"Dummy Plan {plan_id}",
            description="Automatically created dummy plan",
            request_type="general",
            steps=[dummy_step],
            estimated_duration=1.0,
            complexity_score=0.1,
            success_probability=0.9
        )
        
        # Store in memory
        active_plans[plan_id] = dummy_plan
        
        # Save to disk
        await save_plan_to_disk(plan_id, asdict(dummy_plan))
        
        logger.info(f"Created dummy plan for {plan_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating dummy plan: {e}")
        return False

async def process_agent_confirmation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process an agent confirmation message, ensuring plan exists in proper format"""
    try:
        # Extract plan ID and action
        session_id = data.get("sessionId") or data.get("session_id")
        action = data.get("action") or data.get("button")
        
        if not session_id:
            logger.warning("Missing session ID in agent confirmation")
            return data
        
        logger.info(f"🔄 Converting button_action to agent_confirmation: {action} for plan {session_id}")
        
        # Ensure plan exists
        if action and action.upper() in ["DO", "EXECUTE", "EXECUTE_PLAN"]:
            plan_exists = await ensure_plan_exists(session_id)
            if not plan_exists:
                logger.warning(f"Failed to ensure plan exists for {session_id}")
                return {
                    "type": "error",
                    "error": f"Plan {session_id} not found and could not be created",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
            # Add plan to message if present in memory
            if session_id in active_plans and "plan" not in data:
                plan_obj = active_plans[session_id]
                data["plan"] = asdict(plan_obj)
                logger.info(f"Added plan data to message for {session_id}")
        
        logger.info(f"🎯 Agent confirmation received: sessionId={session_id}, action={action}")
        
        # Standardize to agent_confirmation format
        return {
            "type": "agent_confirmation",
            "sessionId": session_id,
            "action": action,
            "plan": data.get("plan"),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing agent confirmation: {e}")
        return data

async def process_button_action(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a button action message, ensuring plan exists in proper format"""
    try:
        # Extract plan ID and action
        plan_id = data.get("plan_id")
        action = data.get("action")
        
        if not plan_id:
            logger.warning("Missing plan ID in button action")
            return data
        
        logger.info(f"🔄 Processing button action: {action} for plan {plan_id}")
        
        # Ensure plan exists
        if action and action.upper() in ["DO", "EXECUTE", "EXECUTE_PLAN"]:
            plan_exists = await ensure_plan_exists(plan_id)
            if not plan_exists:
                logger.warning(f"Failed to ensure plan exists for {plan_id}")
                return {
                    "type": "error",
                    "error": f"Plan {plan_id} not found and could not be created",
                    "plan_id": plan_id,
                    "timestamp": datetime.now().isoformat()
                }
                
            # Add plan to message if present in memory
            if plan_id in active_plans and "plan" not in data:
                plan_obj = active_plans[plan_id]
                data["plan"] = asdict(plan_obj)
                logger.info(f"Added plan data to message for {plan_id}")
        
        return data
    
    except Exception as e:
        logger.error(f"Error processing button action: {e}")
        return data

async def handle_client(websocket, path=None):
    """Handle client connection and message processing"""
    client_id = str(uuid.uuid4())
    client_connections[client_id] = websocket
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "message": "Connected to Plan Format Fix Proxy",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                logger.info(f"Received message type: {msg_type}")
                
                # Process message based on type
                if msg_type == "agent_confirmation":
                    data = await process_agent_confirmation(data)
                elif msg_type == "button_action":
                    data = await process_button_action(data)
                elif msg_type == "do_button":
                    # Treat do_button as button_action
                    data["type"] = "button_action"
                    data = await process_button_action(data)
                
                # Forward to target server (typically the DO button server)
                try:
                    target_server = data.get("target_server", "ws://localhost:8765")
                    async with websockets.connect(target_server) as server:
                        logger.info(f"Connected to target server: {target_server}")
                        await server.send(json.dumps(data))
                        response = await server.recv()
                        logger.info(f"Received response from target server")
                        await websocket.send(response)
                except Exception as e:
                    logger.error(f"Error forwarding to target server: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": f"Error forwarding to target server: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {message}")
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
    port = 8771  # Different port to avoid conflicts
    
    logger.info(f"Starting Plan Format Fix Proxy on port {port}")
    server = await websockets.serve(handle_client, "localhost", port)
    logger.info(f"✅ Plan Format Fix Proxy running on ws://localhost:{port}")
    
    # Save port to file
    with open("logs/plan_format_proxy_port.txt", "w") as f:
        f.write(str(port))
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Plan Format Fix Proxy stopped by user")
    except Exception as e:
        logger.error(f"Error running proxy: {e}")
        import traceback
        logger.error(traceback.format_exc())