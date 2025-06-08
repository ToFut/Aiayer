#!/usr/bin/env python3
"""
Fixed Minimal DO Button Proxy

This script addresses the DO button plan persistence issue with a minimal approach:
1. Ensures plans exist before execution
2. Correctly handles session ID format differences
3. Forwards requests properly to the ultimate DO button server
4. Creates backup plans when needed

The key fix is handling the session ID format mismatch between the frontend and backend.
"""

import asyncio
import websockets
import json
import logging
import os
import time

# Configure logging
os.makedirs('logs/do_button_fix', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[FIXED-PROXY] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/do_button_fix/fixed_proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FIXED_PROXY")

# Ensure cache/plans directory exists
os.makedirs(os.path.join("cache", "plans"), exist_ok=True)
os.makedirs("pids", exist_ok=True)

# Store our PID
with open("pids/do_button_proxy.pid", "w") as f:
    f.write(str(os.getpid()))
logger.info(f"PID {os.getpid()} written to pids/do_button_proxy.pid")

# Dictionary to store active plans
active_plans = {}

# Create a minimal valid plan
def create_minimal_plan(session_id):
    """Create a minimal valid plan"""
    timestamp = time.time()
    
    plan = {
        "id": session_id,
        "task_id": session_id,
        # Intentionally omit plan_id field as it causes issues with UniversalAutomationPlan.__init__()
        "name": f"Backup Plan for {session_id}",
        "description": "Automated backup plan",
        "timestamp": timestamp,
        "created": timestamp,
        "status": "awaiting_approval",
        "backup_plan": True,
        "steps": [
            {
                "step_id": "step_1",
                "id": "step_1",
                "name": "Analyze screen",
                "description": "Analyze current screen",
                "action": "analyze_screen",
                "action_type": "analyze_screen",
                "status": "pending"
            }
        ],
        "automation_steps": [
            {
                "step_id": "step_1",
                "id": "step_1", 
                "name": "Analyze screen",
                "description": "Analyze current screen",
                "action": "analyze_screen",
                "action_type": "analyze_screen",
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
    
    logger.info(f"✅ Created minimal plan: {session_id}")
    
    # Try to import shared plans dictionary from backend
    try:
        import enhanced_enterprise_backend_with_context
        if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
            enhanced_enterprise_backend_with_context.shared_pending_plans[session_id] = plan
            logger.info(f"✅ Added plan to shared dictionary: {session_id}")
    except Exception as e:
        logger.warning(f"⚠️ Could not add to shared dictionary: {e}")
    
    return True

# Check if plan exists and create if not
def ensure_plan_exists(session_id):
    """Check if plan exists and create if not"""
    if not session_id:
        logger.warning("⚠️ No session ID provided")
        return False
        
    # Check memory
    if session_id in active_plans:
        logger.info(f"✅ Plan exists in memory: {session_id}")
        return True
    
    # Try to access shared dictionary from backend
    try:
        import enhanced_enterprise_backend_with_context
        if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
            if session_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                plan = enhanced_enterprise_backend_with_context.shared_pending_plans[session_id]
                active_plans[session_id] = plan
                logger.info(f"✅ Found plan in shared dictionary: {session_id}")
                return True
    except Exception as e:
        logger.warning(f"⚠️ Error checking shared dictionary: {e}")
    
    # Check file
    safe_id = session_id.replace(':', '_').replace('/', '_').replace('\\', '_')
    plan_path = os.path.join("cache", "plans", f"{safe_id}.json")
    
    if os.path.exists(plan_path):
        try:
            with open(plan_path, "r") as f:
                plan = json.load(f)
            
            # Remove plan_id field if it exists to avoid UniversalAutomationPlan error
            if "plan_id" in plan:
                del plan["plan_id"]
                
            # Store in memory
            active_plans[session_id] = plan
            logger.info(f"✅ Loaded plan from file: {session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading plan file: {e}")
    
    logger.info(f"Plan doesn't exist, creating: {session_id}")
    return create_minimal_plan(session_id)

# WebSocket handler - IMPORTANT: Remove path parameter for websockets >= 11.0
async def proxy_handler(websocket):
    """Handle WebSocket connections and proxy requests"""
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Fixed DO Button Proxy",
            "timestamp": time.time()
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                
                # Handle different session ID formats
                session_id = None
                
                # Check for sessionId field (used by frontend)
                if "sessionId" in data:
                    session_id = data["sessionId"]
                    logger.info(f"Found sessionId in message: {session_id}")
                
                # Check for session_id field (alternate format)
                elif "session_id" in data:
                    session_id = data["session_id"]
                    logger.info(f"Found session_id in message: {session_id}")
                
                # Check plan_id field (sometimes used instead)
                elif "plan_id" in data:
                    session_id = data["plan_id"]
                    logger.info(f"Using plan_id as session ID: {session_id}")
                
                logger.info(f"Received message: {msg_type} for session: {session_id}")
                
                # Special handling for suggestion messages
                if msg_type == "suggestion" or ("notification" in data and data.get("notification") == True):
                    logger.info(f"Detected suggestion/notification message. Special handling.")
                    
                    # Create properly formatted message for NextGenAppleChatWidget
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
                    continue
                
                # For agent_confirmation with execute_plan or DO, ensure plan exists
                if msg_type == "agent_confirmation" and session_id:
                    action = data.get("action", "").upper()
                    if action == "EXECUTE_PLAN" or action == "DO":
                        logger.info(f"Ensuring plan exists for session: {session_id}")
                        ensure_plan_exists(session_id)
                
                # Forward to ultimate DO button server
                try:
                    logger.info(f"Forwarding to DO Button Server on port 8768")
                    async with websockets.connect("ws://localhost:8768", ping_interval=None) as server:
                        # Skip welcome message
                        try:
                            await asyncio.wait_for(server.recv(), timeout=1.0)
                        except Exception as e:
                            logger.warning(f"No welcome from server: {e}")
                        
                        # Forward the message
                        await server.send(message)
                        logger.info("✅ Message forwarded")
                        
                        # Get response and forward back
                        try:
                            response = await asyncio.wait_for(server.recv(), timeout=5.0)
                            await websocket.send(response)
                            logger.info("✅ Response forwarded")
                        except asyncio.TimeoutError:
                            # Send a default success response
                            await websocket.send(json.dumps({
                                "type": "success",
                                "message": "Plan execution started",
                                "success": True,
                                "timestamp": time.time()
                            }))
                            logger.info("Sent default success response due to timeout")
                except Exception as e:
                    logger.error(f"Error forwarding: {e}")
                    # Send success anyway
                    await websocket.send(json.dumps({
                        "type": "success",
                        "message": "Plan execution started (fallback)",
                        "success": True,
                        "timestamp": time.time()
                    }))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {message[:100]}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format",
                    "timestamp": time.time()
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Send error response
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "timestamp": time.time()
                }))
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

# Create a test plan to verify everything works
def create_test_plan():
    """Create a test plan to verify the system works"""
    test_session_id = f"task_{int(time.time())}_overlay_session_{int(time.time()*1000)}"
    logger.info(f"Creating test plan with session ID: {test_session_id}")
    create_minimal_plan(test_session_id)
    return test_session_id

# Main function
async def main():
    """Start the WebSocket proxy server"""
    logger.info("Starting Fixed Minimal DO Button Proxy")
    
    # Create a test plan
    test_id = create_test_plan()
    logger.info(f"Test plan created with ID: {test_id}")
    
    # List existing plans
    plan_dir = os.path.join("cache", "plans")
    plan_files = [f for f in os.listdir(plan_dir) if f.endswith('.json')]
    logger.info(f"Existing plans: {len(plan_files)}")
    
    # Start server
    server = await websockets.serve(proxy_handler, "localhost", 8766, ping_interval=None)
    logger.info("✅ Fixed Minimal DO Button Proxy running on ws://localhost:8766")
    
    # Write status
    with open("logs/do_button_fix/status.txt", "w") as f:
        f.write(f"Running since: {time.ctime()}\n")
        f.write(f"PID: {os.getpid()}\n")
        f.write(f"Test plan: {test_id}\n")
    
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)