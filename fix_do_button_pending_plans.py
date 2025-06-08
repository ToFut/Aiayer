#!/usr/bin/env python3
"""
Fix DO Button Pending Plans

This script provides a runtime fix for the DO button issue by ensuring plans
are properly shared across all backend instances. It also sets up a listener
that creates backup plans on-the-fly when needed.
"""

import asyncio
import websockets
import json
import logging
import os
import time
import importlib
import sys
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/fix_do_button_pending_plans.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FixDoButtonPendingPlans")

# Global shared dictionary for plans across all instances
global_pending_plans = {}

def import_and_update_backend():
    """Import the backend module and update its shared_pending_plans"""
    try:
        # Import the backend module
        import enhanced_enterprise_backend_with_context
        
        # Store a reference to shared_pending_plans
        global global_pending_plans
        global_pending_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
        
        logger.info(f"✅ Successfully imported backend module and obtained shared_pending_plans reference")
        logger.info(f"✅ Current plans in shared_pending_plans: {list(global_pending_plans.keys())}")
        
        return True
    except ImportError:
        logger.error("❌ Failed to import enhanced_enterprise_backend_with_context module")
        return False
    except Exception as e:
        logger.error(f"❌ Error importing backend module: {e}")
        return False

async def check_and_load_plans_from_persistence():
    """Check and load plans from persistence if available"""
    try:
        # Import plan_persistence
        import plan_persistence
        
        # Get all plan metadata
        all_metadata = await plan_persistence.get_all_plan_metadata()
        logger.info(f"✅ Found {len(all_metadata)} plans in persistence")
        
        # Load each plan
        for metadata in all_metadata:
            plan_id = metadata.get("plan_id")
            if plan_id and plan_id not in global_pending_plans:
                plan = await plan_persistence.load_plan(plan_id)
                if plan:
                    global_pending_plans[plan_id] = plan
                    logger.info(f"✅ Loaded plan {plan_id} from persistence")
        
        logger.info(f"✅ Now {len(global_pending_plans)} plans in shared_pending_plans")
        return True
    except ImportError:
        logger.error("❌ Failed to import plan_persistence module")
        return False
    except Exception as e:
        logger.error(f"❌ Error loading plans from persistence: {e}")
        return False

async def create_backup_plan_if_needed(plan_id: str):
    """Create a backup plan if it doesn't exist"""
    if not plan_id:
        logger.error("❌ No plan ID provided")
        return False
        
    # Check if plan already exists
    if plan_id in global_pending_plans:
        logger.info(f"✅ Plan {plan_id} already exists in shared_pending_plans")
        return True
        
    # Create a backup plan
    try:
        timestamp = time.time()
        backup_plan = {
            "id": plan_id,
            "title": f"Backup Plan for {plan_id[:8]}",
            "description": "This is a backup plan created to fix the DO button issue",
            "steps": [
                {
                    "id": f"{plan_id[:8]}_step_1",
                    "type": "notification",
                    "action": "notify",
                    "content": "This is a backup plan. The original plan could not be found.",
                    "position": {"x": 500, "y": 500}
                }
            ],
            "metadata": {
                "created_at": timestamp,
                "backup_plan": True
            }
        }
        
        # Add to global_pending_plans
        global_pending_plans[plan_id] = backup_plan
        logger.info(f"✅ Created backup plan for {plan_id}")
        
        # Save to persistence if available
        try:
            import plan_persistence
            await plan_persistence.save_plan(plan_id, backup_plan)
            logger.info(f"✅ Saved backup plan {plan_id} to persistence")
        except Exception as e:
            logger.warning(f"⚠️ Could not save backup plan to persistence: {e}")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error creating backup plan: {e}")
        return False

async def listen_for_do_button_events():
    """Listen for DO button events on WebSocket server"""
    try:
        # Connect to DO button server
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to DO button server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message from server")
            
            # Listen for messages
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    # Check for agent_confirmation or button_action
                    if message_type in ["agent_confirmation", "button_action", "do_button", "do_button_action"]:
                        # Extract plan ID
                        plan_id = None
                        if message_type == "agent_confirmation":
                            plan_id = data.get("sessionId") or data.get("session_id")
                        elif message_type == "button_action":
                            plan_id = data.get("plan_id")
                        elif message_type == "do_button":
                            plan_id = data.get("plan_id")
                        elif message_type == "do_button_action" and "do_button_action" in data:
                            plan_id = data["do_button_action"].get("plan_id")
                            
                        if plan_id:
                            logger.info(f"🔍 Detected {message_type} message with plan_id: {plan_id}")
                            
                            # Check if plan exists
                            if plan_id in global_pending_plans:
                                logger.info(f"✅ Plan {plan_id} exists in shared_pending_plans")
                            else:
                                logger.warning(f"⚠️ Plan {plan_id} not found in shared_pending_plans")
                                
                                # Create a backup plan
                                await create_backup_plan_if_needed(plan_id)
                                
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Received non-JSON message: {message[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
    except websockets.exceptions.ConnectionClosed:
        logger.warning("⚠️ Connection to DO button server closed")
    except Exception as e:
        logger.error(f"❌ Error connecting to DO button server: {e}")

async def update_backend_module():
    """Patch the backend module's handle_agent_confirmation method at runtime"""
    try:
        import enhanced_enterprise_backend_with_context
        import inspect
        import types
        
        # Find the class that contains handle_agent_confirmation
        for name, obj in inspect.getmembers(enhanced_enterprise_backend_with_context):
            if inspect.isclass(obj) and hasattr(obj, 'handle_agent_confirmation'):
                backend_class = obj
                original_method = obj.handle_agent_confirmation
                
                async def patched_handle_agent_confirmation(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
                    """Patched version of handle_agent_confirmation"""
                    try:
                        # Handle both sessionId (frontend) and session_id (backend) formats
                        session_id = data.get("sessionId") or data.get("session_id")
                        action = data.get("action", "").upper()
                        
                        logger.info(f"🎯 Agent confirmation received: sessionId={session_id}, action={action}")
                        
                        # Check if we need to create a backup plan
                        if session_id and (not hasattr(self, 'pending_plans') or session_id not in self.pending_plans):
                            # Try shared dictionary first
                            if session_id in global_pending_plans:
                                if hasattr(self, 'pending_plans'):
                                    self.pending_plans[session_id] = global_pending_plans[session_id]
                                    logger.info(f"✅ Copied plan {session_id} from global dictionary to instance")
                            else:
                                # Try to create a backup plan
                                await create_backup_plan_if_needed(session_id)
                                
                                # Copy to instance
                                if hasattr(self, 'pending_plans') and session_id in global_pending_plans:
                                    self.pending_plans[session_id] = global_pending_plans[session_id]
                                    logger.info(f"✅ Copied backup plan {session_id} to instance")
                    except Exception as e:
                        logger.error(f"❌ Error in patched handle_agent_confirmation: {e}")
                    
                    # Call the original method
                    return await original_method(self, data, client_id)
                
                # Apply the patch
                backend_class.handle_agent_confirmation = patched_handle_agent_confirmation
                logger.info(f"✅ Successfully patched handle_agent_confirmation method in {backend_class.__name__}")
                break
        else:
            logger.warning("⚠️ Could not find handle_agent_confirmation method to patch")
            
        return True
    except ImportError:
        logger.error("❌ Failed to import enhanced_enterprise_backend_with_context module")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching backend module: {e}")
        return False

async def monitor_websocket_proxy():
    """Monitor the WebSocket proxy server for DO button messages"""
    try:
        # Connect to proxy server
        uri = "ws://localhost:8766"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to WebSocket proxy at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message from proxy")
            
            # Listen for messages
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    # Check for relevant message types
                    if message_type in ["agent_confirmation", "button_action", "do_button", "do_button_action"]:
                        # Extract plan ID
                        plan_id = None
                        if message_type == "agent_confirmation":
                            plan_id = data.get("sessionId") or data.get("session_id")
                        elif message_type == "button_action":
                            plan_id = data.get("plan_id")
                        elif message_type == "do_button":
                            plan_id = data.get("plan_id")
                        elif message_type == "do_button_action" and "do_button_action" in data:
                            plan_id = data["do_button_action"].get("plan_id")
                            
                        if plan_id:
                            logger.info(f"🔍 Detected {message_type} message with plan_id: {plan_id} via proxy")
                            
                            # Ensure plan exists
                            if plan_id not in global_pending_plans:
                                await create_backup_plan_if_needed(plan_id)
                                
                            # Check if plan is in message and missing from global plans
                            if 'plan' in data and isinstance(data['plan'], dict) and plan_id not in global_pending_plans:
                                global_pending_plans[plan_id] = data['plan']
                                logger.info(f"✅ Extracted plan from message and added to global dictionary: {plan_id}")
                                
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Received non-JSON message from proxy: {message[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Error processing message from proxy: {e}")
    except websockets.exceptions.ConnectionClosed:
        logger.warning("⚠️ Connection to proxy server closed")
    except Exception as e:
        logger.error(f"❌ Error connecting to proxy server: {e}")

async def main():
    """Main function that runs the fix"""
    logger.info("🚀 Starting DO Button Pending Plans Fix")
    
    # Step 1: Import and update backend
    if not import_and_update_backend():
        logger.error("❌ Failed to import and update backend module.")
        logger.info("Continuing with other fixes...")
        
    # Step 2: Update backend module
    await update_backend_module()
    
    # Step 3: Check and load plans from persistence
    await check_and_load_plans_from_persistence()
    
    # Step 4: Start listeners
    logger.info("🔍 Starting listeners for DO button events...")
    
    # Create tasks for both listeners
    do_button_listener = asyncio.create_task(listen_for_do_button_events())
    proxy_listener = asyncio.create_task(monitor_websocket_proxy())
    
    # Wait for both listeners
    try:
        await asyncio.gather(do_button_listener, proxy_listener)
    except asyncio.CancelledError:
        logger.info("Listeners cancelled")
    finally:
        # Cancel tasks if they're still running
        if not do_button_listener.done():
            do_button_listener.cancel()
        if not proxy_listener.done():
            proxy_listener.cancel()

if __name__ == "__main__":
    try:
        logger.info("DO Button Pending Plans Fix - Press Ctrl+C to stop")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("DO Button Pending Plans Fix stopped by user")
    except Exception as e:
        logger.error(f"Error in DO Button Pending Plans Fix: {e}")
        import traceback
        logger.error(traceback.format_exc())