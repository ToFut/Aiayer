#!/usr/bin/env python3
"""
Fix Plan Structure - Convert JSON plans to objects for universal_automation_handler
"""

import asyncio
import json
import logging
import os
import sys
import websockets
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[ENHANCED-SYSTEM] %(levelname)s:%(name)s:%(message)s',
)
logger = logging.getLogger(__name__)

@dataclass
class SmartAutomationStep:
    """Enhanced automation step with smart execution capabilities"""
    id: str
    description: str
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[tuple] = None
    confidence: float = 0.8
    status: str = "pending"
    estimated_duration: float = 2.0
    retry_count: int = 0
    max_retries: int = 3
    fallback_action: Optional[str] = None
    context_hints: list = field(default_factory=list)

@dataclass 
class UniversalAutomationPlan:
    """Universal automation plan that works with any request type"""
    task_id: str
    title: str
    description: str
    request_type: str
    steps: list
    estimated_duration: float
    complexity_score: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    success_probability: float = 0.8
    fallback_strategies: list = field(default_factory=list)
    user_guidance_needed: bool = False

async def convert_plan_to_object(data: Dict[str, Any]) -> Optional[UniversalAutomationPlan]:
    """Convert a plan dictionary to a UniversalAutomationPlan object"""
    if not isinstance(data, dict):
        logger.error(f"Invalid plan data: {type(data)}")
        return None
    
    try:
        # Convert steps to SmartAutomationStep objects
        smart_steps = []
        for i, step_data in enumerate(data.get("steps", [])):
            # Handle coordinates safely
            coordinates = None
            if step_data.get("coordinates"):
                try:
                    coords = step_data["coordinates"]
                    if isinstance(coords, list) and len(coords) >= 2:
                        coordinates = (int(coords[0]), int(coords[1]))
                except Exception as e:
                    logger.warning(f"Error parsing coordinates: {e}")
            
            # Create SmartAutomationStep
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
        
        # Create UniversalAutomationPlan
        plan = UniversalAutomationPlan(
            task_id=data.get("task_id", f"task_{int(datetime.now().timestamp())}"),
            title=data.get("title", "Automation Plan"),
            description=data.get("description", ""),
            request_type=data.get("request_type", "general"),
            steps=smart_steps,
            estimated_duration=float(data.get("estimated_duration", 0.0)),
            complexity_score=float(data.get("complexity_score", 0.5)),
            requires_approval=bool(data.get("requires_approval", True)),
            status=data.get("status", "awaiting_approval"),
            success_probability=float(data.get("success_probability", 0.8)),
            fallback_strategies=data.get("fallback_strategies", []) or [],
            user_guidance_needed=bool(data.get("user_guidance_needed", False))
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error converting plan to object: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def fix_websocket_message(websocket, path):
    """Fix websocket message to ensure plan objects are properly formatted"""
    client_id = str(hash(websocket))
    logger.info(f"Client {client_id} connected")
    
    try:
        # Handle incoming messages
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                logger.info(f"Received message type: {msg_type}")
                
                # Special handling for button_action or agent_confirmation
                if msg_type in ["button_action", "agent_confirmation", "do_button"]:
                    # Extract plan_id and action
                    plan_id = data.get("plan_id") or data.get("sessionId") or data.get("session_id")
                    action = data.get("action") or data.get("button")
                    
                    if plan_id and action and action.upper() in ["DO", "EXECUTE", "EXECUTE_PLAN"]:
                        logger.info(f"🔄 Converting {msg_type} to agent_confirmation: {action} for plan {plan_id}")
                        
                        # Prepare plan if included
                        if "plan" in data and isinstance(data["plan"], dict):
                            # Convert plan to proper object
                            plan_obj = await convert_plan_to_object(data["plan"])
                            if plan_obj:
                                # Store plan in memory (simulate universal_automation_handler.active_plans)
                                logger.info(f"🎯 Agent confirmation received: sessionId={plan_id}, action={action}")
                                # Check active plans (would be handled by handler)
                                logger.info(f"🔍 Available plans: {plan_obj}")
                                
                                # Modify message for handler
                                data = {
                                    "type": "agent_confirmation",
                                    "sessionId": plan_id,
                                    "action": action,
                                    "timestamp": datetime.now().isoformat()
                                }
                            else:
                                logger.warning(f"❌ Failed to convert plan to object")
                        else:
                            logger.info(f"🎯 Agent confirmation received: sessionId={plan_id}, action={action}")
                            logger.info(f"🔍 Available plans: None")
                
                # Send response (for testing)
                response = {
                    "type": "response",
                    "original_type": msg_type,
                    "message": "Message processed successfully",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
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

async def start_server():
    """Start the WebSocket server"""
    port = 8770  # Different port to avoid conflicts
    
    logger.info(f"Starting Plan Structure Fix server on port {port}")
    server = await websockets.serve(fix_websocket_message, "localhost", port)
    logger.info(f"✅ Plan Structure Fix server running on ws://localhost:{port}")
    
    await server.wait_closed()

async def test_convert_plan():
    """Test converting a plan dictionary to an object"""
    # Test plan data
    plan_data = {
        "task_id": f"test_task_{int(datetime.now().timestamp())}",
        "title": "Test Automation Plan",
        "description": "Test plan for conversion",
        "request_type": "web_search",
        "steps": [
            {
                "id": "step_1",
                "description": "Open Safari",
                "action_type": "open_app",
                "target": "Safari",
                "estimated_duration": 2.0
            },
            {
                "id": "step_2",
                "description": "Navigate to Google",
                "action_type": "navigate_url",
                "value": "https://www.google.com",
                "estimated_duration": 3.0
            }
        ],
        "estimated_duration": 5.0,
        "complexity_score": 0.3
    }
    
    # Convert plan
    plan_obj = await convert_plan_to_object(plan_data)
    
    if plan_obj:
        logger.info(f"Successfully converted plan to object")
        logger.info(f"Plan title: {plan_obj.title}")
        logger.info(f"Plan has {len(plan_obj.steps)} steps")
        
        # Test handling in universal_automation_handler
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
            logger.info("Successfully imported universal_automation_handler")
            
            # Store plan in handler
            universal_automation_handler.active_plans[plan_obj.task_id] = plan_obj
            
            # Try execution
            logger.info(f"Testing execution of plan {plan_obj.task_id}")
            result = await universal_automation_handler.handle_button_action("DO", plan_obj.task_id, plan_obj.task_id)
            logger.info(f"Execution result: {result}")
            
        except ImportError as e:
            logger.error(f"Failed to import universal_automation_handler: {e}")
        except Exception as e:
            logger.error(f"Error in test: {e}")
    else:
        logger.error("Failed to convert plan to object")

async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        await start_server()
    else:
        await test_convert_plan()

if __name__ == "__main__":
    asyncio.run(main())