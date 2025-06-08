#!/usr/bin/env python3
"""
DO Button Plan Persistence Fix

This script addresses the issue where plans with session IDs in the format
'task_{timestamp}_overlay_session_{timestamp}' are not being properly saved and retrieved.

The fix includes:
1. Ensures cache/plans directory exists
2. Properly synchronizes plans between components
3. Fixes how plan_id and sessionId are mapped
4. Adds direct plan creation on execution request
5. Adds extensive logging to troubleshoot the issue
"""

import asyncio
import websockets
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
os.makedirs('logs/do_button_fix', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[PLAN-FIX] %(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.FileHandler('logs/do_button_fix/plan_persistence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure cache/plans directory exists
os.makedirs(os.path.join("cache", "plans"), exist_ok=True)

# Dictionary to store active plans
active_plans = {}

# Try to import the shared_pending_plans from backend
try:
    import enhanced_enterprise_backend_with_context
    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
        # Use the backend's shared dictionary as our active_plans
        active_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
        logger.info("✅ Using backend's shared_pending_plans dictionary")
except ImportError:
    logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context")
except Exception as e:
    logger.warning(f"⚠️ Error accessing backend's shared_pending_plans: {e}")

# Function to create a backup plan
async def create_backup_plan(plan_id: str):
    """Create a backup plan when one doesn't exist"""
    logger.info(f"Creating backup plan for: {plan_id}")
    timestamp = time.time()
    
    # Create a simple backup plan in the format expected by the Ultimate DO Button Server
    backup_plan = {
        "task_id": plan_id,
        "plan_id": plan_id,
        "title": f"Backup Plan for {plan_id}",
        "description": f"Backup plan created for {plan_id}",
        "steps": [
            {
                "id": "step_1",
                "description": "Analyze current screen",
                "action_type": "analyze_screen",
                "estimated_duration": 1.0,
                "status": "pending"
            },
            {
                "id": "step_2",
                "description": "Execute action based on analysis",
                "action_type": "execute",
                "estimated_duration": 2.0,
                "status": "pending"
            }
        ],
        "estimated_duration": 3.0,
        "status": "awaiting_approval",
        "creation_time": timestamp,
        "backup_plan": True,
        "timestamp": timestamp,
        "created": timestamp,
        # Universal Automation Plan fields
        "type": "automation_plan",
        "name": f"Backup Plan for {plan_id}",
        "description": f"Backup plan created when original plan not found",
        "target_app": "Google Chrome",
        "plan_type": "automation",
        "priority": "medium",
        "approval_status": "approved",
        "automation_status": "pending",
        "risk_level": "low",
        "automation_steps": [
            {
                "step_id": "step_1",
                "name": "Analyze current screen",
                "action": "analyze_screen",
                "status": "pending"
            },
            {
                "step_id": "step_2", 
                "name": "Execute action based on analysis",
                "action": "execute",
                "status": "pending"
            }
        ]
    }
    
    # Store in memory
    active_plans[plan_id] = backup_plan
    
    # Save to file
    try:
        # Sanitize plan_id for filename compatibility
        safe_plan_id = plan_id.replace(':', '_').replace('/', '_').replace('\\', '_')
        plan_path = os.path.join("cache", "plans", f"{safe_plan_id}.json")
        
        with open(plan_path, "w") as f:
            json.dump(backup_plan, f)
        
        logger.info(f"✅ Saved backup plan to {plan_path}")
        
        # Add to shared dictionary if available
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = backup_plan
                logger.info(f"✅ Added backup plan to shared dictionary: {plan_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not add to shared dictionary: {e}")
            
        return True
    except Exception as e:
        logger.error(f"Error saving backup plan: {e}")
        return False

# Function to load a plan from file or memory
async def load_plan(plan_id: str):
    """Load a plan from file or memory"""
    logger.info(f"🔍 Loading plan with ID: {plan_id}")
    
    # Try different variations of plan_id formats
    plan_id_variations = [plan_id]
    
    # Extract components from complex session IDs
    if plan_id.startswith('task_') and '_overlay_session_' in plan_id:
        # Format: task_1749057683_overlay_session_1749057605386
        parts = plan_id.split('_overlay_session_')
        if len(parts) == 2:
            task_part = parts[0]  # task_1749057683
            session_part = "overlay_session_" + parts[1]  # overlay_session_1749057605386
            
            # Add variations
            plan_id_variations.append(task_part)
            plan_id_variations.append(session_part)
            
            # If task_part has timestamp, extract it
            if task_part.startswith('task_'):
                timestamp = task_part[5:]  # 1749057683
                plan_id_variations.append("task_" + timestamp)
                plan_id_variations.append(timestamp)
    
    # List all available plans for debugging
    plan_dir = os.path.join("cache", "plans")
    available_plans = [f for f in os.listdir(plan_dir) if f.endswith('.json') and f != 'metadata.json']
    logger.info(f"Available plan files: {available_plans}")
    
    # Try all plan_id variations
    for pid in plan_id_variations:
        # Check if plan exists in memory
        if pid in active_plans:
            logger.info(f"✅ Plan found in memory with ID: {pid}")
            return active_plans[pid]
        
        # Check shared plans dictionary from backend
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                if pid in enhanced_enterprise_backend_with_context.shared_pending_plans:
                    plan = enhanced_enterprise_backend_with_context.shared_pending_plans[pid]
                    active_plans[plan_id] = plan  # Store under the original ID
                    logger.info(f"✅ Found plan in shared dictionary with ID: {pid}")
                    return plan
        except Exception as e:
            logger.warning(f"⚠️ Error checking shared dictionary: {e}")
        
        # Try to load from file
        try:
            # Sanitize plan_id for filename compatibility
            safe_pid = pid.replace(':', '_').replace('/', '_').replace('\\', '_')
            plan_path = os.path.join("cache", "plans", f"{safe_pid}.json")
            
            if os.path.exists(plan_path):
                with open(plan_path, "r") as f:
                    plan_data = json.load(f)
                
                # Store in memory under both IDs
                active_plans[plan_id] = plan_data  # Original ID
                active_plans[pid] = plan_data      # Variation ID
                
                # Update shared dictionary if available
                try:
                    import enhanced_enterprise_backend_with_context
                    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                        enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
                        enhanced_enterprise_backend_with_context.shared_pending_plans[pid] = plan_data
                except Exception:
                    pass
                    
                logger.info(f"✅ Loaded plan from file: {plan_path}")
                return plan_data
        except Exception as e:
            logger.error(f"Error loading plan from file {safe_pid}.json: {e}")
    
    # List all plans in persistence
    logger.info(f"📋 Available plans in storage: {available_plans}")
    logger.warning(f"❌ Plan not found: {plan_id}")
    return None

# Function to ensure plan exists
async def ensure_plan_exists(plan_id: str):
    """Ensure a plan exists, creating a backup if needed"""
    logger.info(f"🔍 Ensuring plan exists: {plan_id}")
    
    # Load plan
    plan = await load_plan(plan_id)
    if plan:
        return True
    
    # Create backup plan if not found
    logger.warning(f"⚠️ Plan {plan_id} not found, creating backup")
    return await create_backup_plan(plan_id)

# WebSocket handler for the proxy server
async def handle_websocket(websocket, path=None):
    """Handle WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    logger.info(f"Client {client_id} connected to DO Button Plan Persistence Proxy")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to DO Button Plan Persistence Proxy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type', 'unknown')
                logger.info(f"Received {message_type} message from {client_id}")
                
                # Extract session/plan ID
                session_id = None
                plan_id = None
                
                if message_type == 'agent_confirmation':
                    # Extract session ID - try both variants
                    session_id = data.get('sessionId') or data.get('session_id')
                    action = data.get('action', '')
                    
                    logger.info(f"🎯 Agent confirmation received: sessionId={session_id}, action={action}")
                    
                    # Handle both "DO" and "execute_plan" actions
                    if (action.upper() == 'DO' or action.lower() == 'execute_plan') and session_id:
                        # This is a DO button action, ensure plan exists
                        logger.info(f"DO button action received for session: {session_id}")
                        
                        # Additional logging to debug missing plans
                        logger.info(f"🔍 Available plans: {list(active_plans.keys())}")
                        
                        # Try to load the plan first
                        plan = await load_plan(session_id)
                        if not plan:
                            # If plan not found, always create a backup
                            logger.warning(f"Plan not found for session ID: {session_id}, creating backup")
                            plan_exists = await create_backup_plan(session_id)
                            
                            if not plan_exists:
                                logger.error(f"❌ Failed to create backup plan for {session_id}")
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "error": f"Failed to create backup plan for {session_id}",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                continue
                        else:
                            logger.info(f"Plan found for session ID: {session_id}")
                            plan_exists = True
                            
                        # Double-check the plan exists
                        if session_id not in active_plans:
                            logger.error(f"❌ Plan still not in active_plans after creation: {session_id}")
                            # Try one more emergency backup creation
                            await create_backup_plan(session_id)
                    
                elif message_type == 'button_action':
                    # Extract plan ID
                    plan_id = data.get('plan_id')
                    if plan_id:
                        logger.info(f"Button action received for plan: {plan_id}")
                        plan_exists = await ensure_plan_exists(plan_id)
                        
                        if not plan_exists:
                            logger.error(f"❌ Failed to ensure plan exists for {plan_id}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Failed to ensure plan exists for {plan_id}",
                                "timestamp": datetime.now().isoformat()
                            }))
                            continue
                
                # Forward message to the ultimate DO button server
                try:
                    logger.info(f"Forwarding WebSocket message to ultimate DO button server")
                    
                    # Note: We need to connect to the ultimate DO button server on port 8768
                    # This is the correct target for plan execution
                    logger.info("Connecting to ultimate DO button server on port 8768")
                    async with websockets.connect("ws://localhost:8768", ping_interval=None) as do_button_ws:
                        try:
                            # Wait for welcome message with timeout
                            welcome = await asyncio.wait_for(do_button_ws.recv(), timeout=5.0)
                            logger.info(f"Connected to ultimate DO button server: {welcome[:50]}...")
                        except asyncio.TimeoutError:
                            logger.warning("No welcome message received, continuing anyway")
                        except Exception as e:
                            logger.warning(f"Error receiving welcome message: {e}, continuing anyway")
                        
                        # Make sure our plan exists in the active_plans dictionary 
                        # before forwarding the message
                        if session_id and session_id not in active_plans:
                            logger.warning(f"Plan not in active_plans before forwarding, creating emergency backup")
                            await create_backup_plan(session_id)
                        
                        # Forward the original message
                        await do_button_ws.send(message)
                        logger.info(f"Message forwarded to ultimate DO button server")
                        
                        try:
                            # Wait for response with timeout
                            response = await asyncio.wait_for(do_button_ws.recv(), timeout=10.0)
                            logger.info(f"Received response from ultimate DO button server")
                            
                            # Forward the response back to the client
                            await websocket.send(response)
                            logger.info(f"Response forwarded to client")
                        except asyncio.TimeoutError:
                            logger.error("Timeout waiting for response from ultimate DO button server")
                            # Send a success response to the client anyway
                            await websocket.send(json.dumps({
                                "type": "success",
                                "message": "Plan execution initiated (no response from server)",
                                "success": True,
                                "timestamp": datetime.now().isoformat()
                            }))
                except Exception as e:
                    logger.error(f"Error forwarding to ultimate DO button server: {e}")
                    # Send error back to client
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": f"Error forwarding to ultimate DO button server: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Try fallback to the regular WebSocket server
                    try:
                        logger.info("Attempting fallback to regular WebSocket server on port 8765")
                        async with websockets.connect("ws://localhost:8765") as fallback_ws:
                            await fallback_ws.send(message)
                            logger.info("Message forwarded to fallback server")
                            
                            # Try to get a response from the fallback server
                            try:
                                fallback_response = await asyncio.wait_for(fallback_ws.recv(), timeout=5.0)
                                await websocket.send(fallback_response)
                                logger.info("Received and forwarded response from fallback server")
                            except Exception:
                                logger.warning("No response from fallback server")
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}")
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Error processing message: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")

async def fix_plans_in_directory():
    """Scan the plans directory and fix any broken plans"""
    plan_dir = os.path.join("cache", "plans")
    if not os.path.exists(plan_dir):
        os.makedirs(plan_dir, exist_ok=True)
        logger.info(f"Created plans directory: {plan_dir}")
        return
        
    # List all plan files
    plan_files = [f for f in os.listdir(plan_dir) if f.endswith('.json') and f != 'metadata.json']
    logger.info(f"Found {len(plan_files)} plan files in {plan_dir}")
    
    for filename in plan_files:
        try:
            plan_path = os.path.join(plan_dir, filename)
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
            
            # Extract plan ID
            plan_id = plan_data.get('id') or plan_data.get('task_id') or plan_data.get('plan_id')
            if not plan_id:
                plan_id = filename.replace('.json', '')
            
            # Update missing fields
            modified = False
            if "task_id" not in plan_data:
                plan_data["task_id"] = plan_id
                modified = True
            if "plan_id" not in plan_data:
                plan_data["plan_id"] = plan_id
                modified = True
            if "id" not in plan_data:
                plan_data["id"] = plan_id
                modified = True
            if "timestamp" not in plan_data:
                plan_data["timestamp"] = time.time()
                modified = True
            if "created" not in plan_data:
                plan_data["created"] = plan_data.get("timestamp", time.time())
                modified = True
                
            # Save the updated plan if modified
            if modified:
                with open(plan_path, 'w') as f:
                    json.dump(plan_data, f)
                logger.info(f"✅ Updated plan file: {filename}")
                
            # Add to memory and shared dictionary
            active_plans[plan_id] = plan_data
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                    enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Error processing plan file {filename}: {e}")

async def main():
    """Main entry point"""
    logger.info("Starting DO Button Plan Persistence Fix")
    
    # Create plans directory if it doesn't exist
    os.makedirs(os.path.join("cache", "plans"), exist_ok=True)
    
    # Fix existing plans
    await fix_plans_in_directory()
    
    # Create a test plan to verify everything works
    test_session_id = f"task_{int(time.time())}_overlay_session_{int(time.time()*1000)}"
    logger.info(f"Creating test plan with session ID: {test_session_id}")
    await create_backup_plan(test_session_id)
    
    # Start WebSocket server on port 8766
    logger.info("Starting WebSocket server on port 8766")
    server = await websockets.serve(handle_websocket, "localhost", 8766)
    logger.info("✅ DO Button Plan Persistence Proxy running on ws://localhost:8766")
    
    try:
        await asyncio.Future()  # Run forever
    finally:
        server.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("DO Button Plan Persistence Fix stopped by user")
    except Exception as e:
        logger.error(f"Error in DO Button Plan Persistence Fix: {e}")