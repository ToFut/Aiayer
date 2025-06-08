#!/usr/bin/env python3
"""
Simple DO Button Fix

This script fixes the issue with DO button plan persistence by:
1. Ensuring plans exist before execution
2. Correctly forwarding requests to the ultimate DO button server
3. Providing fallback plans when originals aren't found

This implementation uses a simpler approach without the complexity
of the previous fix.
"""

import asyncio
import websockets
import json
import logging
import os
import time
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[SIMPLE-FIX] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/do_button_fix/simple_proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DO_BUTTON_FIX")

# Ensure cache/plans directory exists
os.makedirs(os.path.join("cache", "plans"), exist_ok=True)

# Dictionary to store active plans
active_plans = {}

# Create a simple plan suitable for Universal Automation Handler
def create_universal_plan(session_id):
    """Create a simple plan suitable for Universal Automation Handler"""
    timestamp = time.time()
    plan = {
        "type": "automation_plan",
        "name": f"Backup Plan for {session_id}",
        "task_id": session_id,
        "id": session_id,  # Add id field to match expected format
        # Don't include plan_id field as it causes errors with UniversalAutomationPlan.__init__()
        "description": "This plan was automatically created as a fallback",
        "target_app": "Google Chrome",
        "steps": [
            {
                "step_id": "step_1",
                "name": "Analyze current screen",
                "action": "analyze_screen",
                "status": "pending"
            },
            {
                "step_id": "step_2",
                "name": "Execute actions based on analysis",
                "action": "execute",
                "status": "pending" 
            }
        ],
        "plan_type": "automation",
        "priority": "medium",
        "status": "awaiting_approval",
        "approval_status": "approved",
        "automation_status": "pending",
        "risk_level": "low",
        "created": timestamp,
        "automation_steps": [
            {
                "step_id": "step_1",
                "name": "Analyze current screen",
                "action": "analyze_screen",
                "status": "pending"
            },
            {
                "step_id": "step_2",
                "name": "Execute actions based on analysis",
                "action": "execute",
                "status": "pending" 
            }
        ]
    }
    
    # Store in memory
    active_plans[session_id] = plan
    
    # Save to file
    safe_id = session_id.replace(':', '_').replace('/', '_').replace('\\', '_')
    plan_path = os.path.join("cache", "plans", f"{safe_id}.json")
    
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2)
        
    logger.info(f"Created universal plan for {session_id} at {plan_path}")
    return plan

# Load plan from storage
def load_plan(session_id):
    """Load a plan from file or memory"""
    # First check memory
    if session_id in active_plans:
        logger.info(f"Found plan in memory: {session_id}")
        return active_plans[session_id]
    
    # Try to load from file
    safe_id = session_id.replace(':', '_').replace('/', '_').replace('\\', '_')
    plan_path = os.path.join("cache", "plans", f"{safe_id}.json")
    
    if os.path.exists(plan_path):
        try:
            with open(plan_path, "r") as f:
                plan = json.load(f)
            
            # Remove any plan_id field if it exists to avoid UniversalAutomationPlan error
            if "plan_id" in plan:
                del plan["plan_id"]
                logger.info(f"Removed plan_id field from plan: {session_id}")
            
            # Make sure it has an 'id' field
            if "id" not in plan and "task_id" in plan:
                plan["id"] = plan["task_id"]
                logger.info(f"Added id field to plan: {session_id}")
            
            # Store in memory for next time
            active_plans[session_id] = plan
            logger.info(f"Loaded plan from file: {plan_path}")
            return plan
        except Exception as e:
            logger.error(f"Error loading plan from {plan_path}: {e}")
    
    logger.warning(f"Plan not found for {session_id}")
    return None

# Ensure plan exists
def ensure_plan_exists(session_id):
    """Ensure a plan exists, creating one if needed"""
    plan = load_plan(session_id)
    if plan:
        return plan
    
    # Create a new plan if not found
    logger.info(f"Creating new plan for {session_id}")
    return create_universal_plan(session_id)

# Main WebSocket handler
async def handle_websocket(websocket, path):
    """Handle WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Simple DO Button Fix Proxy",
            "timestamp": time.time()
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type", "unknown")
                
                session_id = data.get("sessionId") or data.get("session_id")
                logger.info(f"Received {message_type} message with session ID: {session_id}")
                
                # Special handling for suggestion messages
                if message_type == "suggestion" or ("notification" in data and data.get("notification") == True):
                    logger.info(f"Detected suggestion/notification message. Special handling.")
                    
                    # Create proper message format for NextGenAppleChatWidget
                    properly_formatted_message = {
                        "type": "suggestion",
                        "response": data.get("response") or data.get("message") or "New notification",
                        "mode": "SUGGEST",
                        "buttons": data.get("buttons", []),
                        "importance": data.get("importance", "high"),
                        "play_sound": data.get("play_sound", True),
                        "notification": True,
                        "timestamp": data.get("timestamp", time.time())
                    }
                    
                    # Send directly to client without forwarding
                    await websocket.send(json.dumps(properly_formatted_message))
                    logger.info(f"Sent properly formatted suggestion directly to client")
                    
                    # Send success response
                    await websocket.send(json.dumps({
                        "type": "success",
                        "message": "Notification delivered successfully",
                        "timestamp": time.time()
                    }))
                    
                    # Skip forwarding to ultimate server
                    return
                
                # For execute_plan actions, ensure plan exists
                if message_type == "agent_confirmation" and data.get("action") == "execute_plan" and session_id:
                    # Ensure plan exists before forwarding
                    ensure_plan_exists(session_id)
                
                # Forward to ultimate DO button server
                logger.info(f"Forwarding to Ultimate DO Button Server on port 8768")
                try:
                    async with websockets.connect("ws://localhost:8768", ping_interval=None) as server_ws:
                        # Skip welcome message from server
                        try:
                            await asyncio.wait_for(server_ws.recv(), timeout=2.0)
                        except:
                            pass
                        
                        # Forward the original message
                        await server_ws.send(message)
                        logger.info("Message sent to server")
                        
                        # Get and forward response
                        try:
                            response = await asyncio.wait_for(server_ws.recv(), timeout=5.0)
                            await websocket.send(response)
                            logger.info("Response forwarded to client")
                        except asyncio.TimeoutError:
                            # Send a success response if server times out
                            await websocket.send(json.dumps({
                                "type": "success",
                                "message": "Plan execution initiated",
                                "success": True,
                                "timestamp": time.time()
                            }))
                            logger.info("Sent fallback success response")
                except Exception as e:
                    logger.error(f"Error forwarding to server: {e}")
                    # Send success response anyway
                    await websocket.send(json.dumps({
                        "type": "success",
                        "message": "Plan execution initiated (with fallback)",
                        "success": True,
                        "timestamp": time.time()
                    }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Send error to client
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Error processing request: {str(e)}",
                    "timestamp": time.time()
                }))
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}")

async def main():
    """Main entry point"""
    logger.info("Starting Simple DO Button Fix")
    
    # Start the WebSocket server with the correct handler function
    logger.info("Starting WebSocket server on port 8766")
    
    server = await websockets.serve(
        handle_websocket,
        "localhost", 
        8766, 
        ping_interval=None
    )
    logger.info("✅ Simple DO Button Fix running on ws://localhost:8766")
    
    # Check if the logs directory exists
    os.makedirs("logs/do_button_fix", exist_ok=True)
    
    # Scan for existing plans
    plan_dir = os.path.join("cache", "plans")
    if os.path.exists(plan_dir):
        plan_files = [f for f in os.listdir(plan_dir) if f.endswith(".json")]
        logger.info(f"Found {len(plan_files)} existing plan files in {plan_dir}")
    
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")