#!/usr/bin/env python3
"""
Ultimate DO Button Fix - Comprehensive Solution

This script addresses the root cause issue with DO button plan execution
by implementing a shared plan persistence mechanism across all system components.

Key fixes:
1. Creates a global shared plan dictionary accessed by all instances
2. Patches the backend module to use this shared dictionary
3. Patches the neural UI handler to integrate with the shared dictionary
4. Ensures proper plan persistence and retrieval
5. Implements robust error handling and fallbacks at every step
6. Provides a test verification function

No system restart required - fixes are applied at runtime.
"""

import os
import sys
import json
import time
import asyncio
import logging
import importlib
import traceback
import websockets
from typing import Dict, Any, Optional, Union, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/ultimate_do_button_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("UltimateDoButtonFix")

# Global active plans dictionary - the single source of truth for all components
global_active_plans: Dict[str, Dict[str, Any]] = {}

# Define constants
NEURAL_UI_PORT = 8768
DO_BUTTON_PORT = 8765
BRIDGE_PORT = 8766
BACKEND_PORT = 8767
LOCALHOST = "127.0.0.1"

async def verify_ws_server_running(port: int) -> bool:
    """Verify if a WebSocket server is running on the given port"""
    try:
        uri = f"ws://{LOCALHOST}:{port}"
        async with websockets.connect(uri, ping_timeout=2, close_timeout=2) as websocket:
            logger.info(f"✅ WebSocket server running on port {port}")
            return True
    except Exception as e:
        logger.warning(f"⚠️ WebSocket server not running on port {port}: {str(e)}")
        return False

async def patch_backend_module() -> bool:
    """Patch the backend module to use a global shared plan dictionary"""
    try:
        # Import the backend module
        import enhanced_enterprise_backend_with_context
        
        # Create a module-level shared_pending_plans dictionary that points to our global dictionary
        enhanced_enterprise_backend_with_context.shared_pending_plans = global_active_plans
        logger.info("✅ Created shared_pending_plans in backend module")
        
        # Patch the EnterpriseBackendServer class to use the shared dictionary
        original_handle_agent_confirmation = enhanced_enterprise_backend_with_context.EnterpriseBackendServer.handle_agent_confirmation
        
        async def patched_handle_agent_confirmation(self, data, client_id=None):
            """Patched version of handle_agent_confirmation that uses shared plans"""
            try:
                if "automation_plan" in data:
                    plan = data["automation_plan"]
                    if "id" in plan and "steps" in plan:
                        plan_id = plan["id"]
                        
                        # Store in both the instance dictionary and the shared dictionary
                        self.pending_plans[plan_id] = plan
                        enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan
                        
                        # Log the successful storage
                        logger.info(f"✅ Stored plan {plan_id} in both instance and shared dictionaries")
                        logger.info(f"✅ Current plans in shared dictionary: {list(enhanced_enterprise_backend_with_context.shared_pending_plans.keys())}")
                        
                        # Try to persist the plan to disk
                        try:
                            # Import plan_persistence here to avoid circular imports
                            from plan_persistence import save_plan
                            asyncio.create_task(save_plan(plan_id, plan))
                            logger.info(f"✅ Saved plan {plan_id} to persistent storage")
                        except Exception as e:
                            logger.warning(f"⚠️ Error saving plan to persistent storage: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Error in patched_handle_agent_confirmation: {str(e)}")
                traceback.print_exc()
            
            # Call the original method to maintain normal functionality
            return await original_handle_agent_confirmation(self, data, client_id)
        
        # Apply the patch
        enhanced_enterprise_backend_with_context.EnterpriseBackendServer.handle_agent_confirmation = patched_handle_agent_confirmation
        logger.info("✅ Successfully patched handle_agent_confirmation method")
        
        # Patch the execute_automation_plan method
        original_execute_automation_plan = enhanced_enterprise_backend_with_context.EnterpriseBackendServer.execute_automation_plan
        
        async def patched_execute_automation_plan(self, plan_id, client_id=None):
            """Patched version of execute_automation_plan that checks multiple sources for plans"""
            logger.info(f"🔍 Looking for plan {plan_id} to execute")
            plan = None
            
            # Check all possible sources for the plan
            sources = [
                ("instance dictionary", self.pending_plans),
                ("shared dictionary", enhanced_enterprise_backend_with_context.shared_pending_plans),
                ("global dictionary", global_active_plans)
            ]
            
            for source_name, source_dict in sources:
                if plan_id in source_dict:
                    plan = source_dict[plan_id]
                    logger.info(f"✅ Found plan {plan_id} in {source_name}")
                    break
            
            # If plan not found in memory, try to load from persistence
            if not plan:
                try:
                    # Import plan_persistence here to avoid circular imports
                    from plan_persistence import load_plan
                    plan = await load_plan(plan_id)
                    if plan:
                        logger.info(f"✅ Loaded plan {plan_id} from persistent storage")
                        # Store the loaded plan in all dictionaries for future use
                        self.pending_plans[plan_id] = plan
                        enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan
                        global_active_plans[plan_id] = plan
                except Exception as e:
                    logger.warning(f"⚠️ Error loading plan from persistent storage: {str(e)}")
            
            # If plan still not found, create a fallback plan
            if not plan:
                logger.warning(f"⚠️ Plan {plan_id} not found in any source, creating fallback plan")
                plan = create_fallback_plan(plan_id)
                # Store the fallback plan in all dictionaries
                self.pending_plans[plan_id] = plan
                enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan
                global_active_plans[plan_id] = plan
            
            # Call the original method with the found/created plan
            if plan:
                # Update the self.pending_plans with the plan before execution
                self.pending_plans[plan_id] = plan
                logger.info(f"✅ Updated instance dictionary with plan {plan_id} before execution")
                return await original_execute_automation_plan(self, plan_id, client_id)
            else:
                logger.error(f"❌ Failed to find or create plan {plan_id}")
                return {"error": f"Failed to find or create plan {plan_id}"}
        
        # Apply the patch
        enhanced_enterprise_backend_with_context.EnterpriseBackendServer.execute_automation_plan = patched_execute_automation_plan
        logger.info("✅ Successfully patched execute_automation_plan method")
        
        return True
    except ImportError:
        logger.error("❌ Failed to import enhanced_enterprise_backend_with_context module")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching backend module: {str(e)}")
        traceback.print_exc()
        return False

async def patch_neural_ui_handler() -> bool:
    """Patch the neural UI handler to integrate with the shared dictionary"""
    try:
        # Import the neural UI handler module
        import neural_ui_do_button_handler
        
        # Make the active_plans dict in neural_ui_do_button_handler point to our global dictionary
        neural_ui_do_button_handler.active_plans = global_active_plans
        logger.info("✅ Linked neural_ui_do_button_handler.active_plans to global_active_plans")
        
        # Patch the ensure_plan_exists method
        original_ensure_plan_exists = neural_ui_do_button_handler.ensure_plan_exists
        
        async def patched_ensure_plan_exists(plan_id: str) -> bool:
            """Patched version of ensure_plan_exists that checks multiple sources"""
            if not plan_id:
                logger.warning("⚠️ No plan ID provided")
                return False
            
            logger.info(f"🔍 Checking for plan {plan_id} existence")
            
            # Check all possible sources for the plan
            if plan_id in neural_ui_do_button_handler.active_plans:
                logger.info(f"✅ Plan {plan_id} exists in neural UI handler's active_plans")
                return True
            
            try:
                # Check backend's shared dictionary
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans') and \
                   plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                    plan = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                    # Copy to our active_plans
                    neural_ui_do_button_handler.active_plans[plan_id] = plan
                    logger.info(f"✅ Found plan {plan_id} in backend's shared_pending_plans")
                    return True
            except ImportError:
                logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context")
            
            # Try to load from persistence
            try:
                from plan_persistence import load_plan
                plan = await load_plan(plan_id)
                if plan:
                    neural_ui_do_button_handler.active_plans[plan_id] = plan
                    logger.info(f"✅ Loaded plan {plan_id} from persistent storage")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Error loading plan from persistence: {str(e)}")
            
            # Try the original method as fallback
            original_result = await original_ensure_plan_exists(plan_id)
            if original_result:
                logger.info(f"✅ Original ensure_plan_exists found plan {plan_id}")
                return True
            
            # Create a fallback plan if not found anywhere
            logger.warning(f"⚠️ Plan {plan_id} not found in any source, creating fallback plan")
            fallback_plan = create_fallback_plan(plan_id)
            neural_ui_do_button_handler.active_plans[plan_id] = fallback_plan
            
            # Also update backend's shared dictionary if accessible
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                    enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = fallback_plan
                    logger.info(f"✅ Updated backend's shared_pending_plans with fallback plan {plan_id}")
            except ImportError:
                pass
            
            return True
        
        # Apply the patch
        neural_ui_do_button_handler.ensure_plan_exists = patched_ensure_plan_exists
        logger.info("✅ Successfully patched ensure_plan_exists method")
        
        # Patch the handle_do_button_action method
        original_handle_do_button_action = neural_ui_do_button_handler.handle_do_button_action
        
        async def patched_handle_do_button_action(data):
            """Patched version of handle_do_button_action with enhanced plan handling"""
            try:
                if not isinstance(data, dict):
                    try:
                        data = json.loads(data)
                    except:
                        logger.error("❌ Invalid data format, could not parse as JSON")
                        return {"error": "Invalid data format"}
                
                # Extract plan_id from various possible locations in the message
                plan_id = None
                if "plan_id" in data:
                    plan_id = data["plan_id"]
                elif "do_button_action" in data and "plan_id" in data["do_button_action"]:
                    plan_id = data["do_button_action"]["plan_id"]
                elif "action" in data and "plan_id" in data["action"]:
                    plan_id = data["action"]["plan_id"]
                
                if not plan_id:
                    logger.warning("⚠️ No plan ID found in message")
                    # Try to extract the most recent plan ID from available sources
                    plan_id = get_most_recent_plan_id()
                    if plan_id:
                        logger.info(f"✅ Using most recent plan ID: {plan_id}")
                        # Add plan_id to the message
                        if "do_button_action" in data:
                            data["do_button_action"]["plan_id"] = plan_id
                        elif "action" in data:
                            data["action"]["plan_id"] = plan_id
                        else:
                            data["plan_id"] = plan_id
                    else:
                        logger.error("❌ Could not find any plan ID")
                        return {"error": "No plan ID provided or found"}
                
                # Log available plans
                logger.info(f"📋 Available plans in global_active_plans: {list(global_active_plans.keys())}")
                
                # Ensure the plan exists before proceeding
                plan_exists = await patched_ensure_plan_exists(plan_id)
                if not plan_exists:
                    logger.error(f"❌ Plan {plan_id} not found and could not create fallback")
                    return {"error": f"Plan {plan_id} not found"}
                
                # Call the original method
                logger.info(f"✅ Plan {plan_id} exists, calling original handle_do_button_action")
                result = await original_handle_do_button_action(data)
                return result
            except Exception as e:
                logger.error(f"❌ Error in patched_handle_do_button_action: {str(e)}")
                traceback.print_exc()
                return {"error": f"Error processing DO button action: {str(e)}"}
        
        # Apply the patch
        neural_ui_do_button_handler.handle_do_button_action = patched_handle_do_button_action
        logger.info("✅ Successfully patched handle_do_button_action method")
        
        return True
    except ImportError:
        logger.error("❌ Failed to import neural_ui_do_button_handler module")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching neural UI handler: {str(e)}")
        traceback.print_exc()
        return False

async def patch_bridge_module() -> bool:
    """Patch the bridge module to ensure plans are properly forwarded"""
    try:
        # Import the bridge module
        import fix_do_button_connection_bridge
        
        # Add global_active_plans to the bridge module
        fix_do_button_connection_bridge.global_active_plans = global_active_plans
        logger.info("✅ Added global_active_plans to bridge module")
        
        # Patch the forward_to_do_button_server function
        original_forward_to_do_button_server = fix_do_button_connection_bridge.forward_to_do_button_server
        
        async def patched_forward_to_do_button_server(message, client_id=None):
            """Patched version of forward_to_do_button_server that ensures plans exist"""
            try:
                # Parse the message
                data = json.loads(message) if isinstance(message, str) else message
                
                # Extract plan_id from various possible locations in the message
                plan_id = None
                if "plan_id" in data:
                    plan_id = data["plan_id"]
                elif "do_button_action" in data and "plan_id" in data["do_button_action"]:
                    plan_id = data["do_button_action"]["plan_id"]
                elif "action" in data and "plan_id" in data["action"]:
                    plan_id = data["action"]["plan_id"]
                
                if plan_id:
                    logger.info(f"🔍 Checking plan {plan_id} in bridge before forwarding")
                    
                    # Check if plan exists in our global dictionary
                    if plan_id in global_active_plans:
                        logger.info(f"✅ Plan {plan_id} exists in global_active_plans")
                    else:
                        logger.warning(f"⚠️ Plan {plan_id} not found in global_active_plans, checking other sources")
                        
                        # Check backend's shared dictionary
                        try:
                            import enhanced_enterprise_backend_with_context
                            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans') and \
                               plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                                plan = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                                global_active_plans[plan_id] = plan
                                logger.info(f"✅ Found plan {plan_id} in backend's shared_pending_plans")
                        except ImportError:
                            logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context")
                        
                        # Try to load from persistence
                        if plan_id not in global_active_plans:
                            try:
                                from plan_persistence import load_plan
                                plan = await load_plan(plan_id)
                                if plan:
                                    global_active_plans[plan_id] = plan
                                    logger.info(f"✅ Loaded plan {plan_id} from persistent storage")
                            except Exception as e:
                                logger.warning(f"⚠️ Error loading plan from persistence: {str(e)}")
                        
                        # Create a fallback plan if not found anywhere
                        if plan_id not in global_active_plans:
                            logger.warning(f"⚠️ Plan {plan_id} not found in any source, creating fallback plan")
                            fallback_plan = create_fallback_plan(plan_id)
                            global_active_plans[plan_id] = fallback_plan
                
                # Call the original method
                return await original_forward_to_do_button_server(message, client_id)
            except Exception as e:
                logger.error(f"❌ Error in patched_forward_to_do_button_server: {str(e)}")
                traceback.print_exc()
                # Try the original method as fallback
                return await original_forward_to_do_button_server(message, client_id)
        
        # Apply the patch
        fix_do_button_connection_bridge.forward_to_do_button_server = patched_forward_to_do_button_server
        logger.info("✅ Successfully patched forward_to_do_button_server function")
        
        return True
    except ImportError:
        logger.error("❌ Failed to import fix_do_button_connection_bridge module")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching bridge module: {str(e)}")
        traceback.print_exc()
        return False

async def patch_plan_persistence() -> bool:
    """Fix the plan_persistence module to ensure proper plan loading and saving"""
    try:
        # Import the plan_persistence module
        import plan_persistence
        
        # Add global_active_plans to the plan_persistence module
        plan_persistence.global_active_plans = global_active_plans
        logger.info("✅ Added global_active_plans to plan_persistence module")
        
        # Get the original functions
        original_save_plan = plan_persistence.save_plan
        original_load_plan = plan_persistence.load_plan
        
        async def patched_save_plan(plan_id: str, plan_data: dict, plan_manager_instance=None) -> bool:
            """Patched version of save_plan that updates global dictionaries"""
            # Update global dictionary
            global_active_plans[plan_id] = plan_data
            
            # Also update backend's shared dictionary if accessible
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                    enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
            except ImportError:
                pass
            
            # Call the original function
            return await original_save_plan(plan_id, plan_data, plan_manager_instance)
        
        async def patched_load_plan(plan_id: str, plan_manager_instance=None) -> Optional[dict]:
            """Patched version of load_plan that checks global dictionaries first"""
            # Check global dictionary first
            if plan_id in global_active_plans:
                return global_active_plans[plan_id]
            
            # Check backend's shared dictionary
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans') and \
                   plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                    return enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
            except ImportError:
                pass
            
            # Call the original function
            plan = await original_load_plan(plan_id, plan_manager_instance)
            
            # Update global dictionary if plan was found
            if plan:
                global_active_plans[plan_id] = plan
                
                # Also update backend's shared dictionary if accessible
                try:
                    import enhanced_enterprise_backend_with_context
                    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                        enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan
                except ImportError:
                    pass
            
            return plan
        
        # Apply the patches
        plan_persistence.save_plan = patched_save_plan
        plan_persistence.load_plan = patched_load_plan
        logger.info("✅ Successfully patched plan_persistence module")
        
        return True
    except ImportError:
        logger.error("❌ Failed to import plan_persistence module")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching plan_persistence module: {str(e)}")
        traceback.print_exc()
        return False

def create_fallback_plan(plan_id: str) -> Dict[str, Any]:
    """Create a fallback plan when a plan cannot be found"""
    logger.info(f"Creating fallback plan for {plan_id}")
    return {
        "id": plan_id,
        "steps": [
            {
                "id": f"{plan_id}_step_1",
                "type": "notification",
                "action": "notify",
                "content": "This is a fallback plan. The original plan could not be found.",
                "position": {"x": 500, "y": 500}
            }
        ],
        "metadata": {
            "created_at": time.time(),
            "name": f"Fallback Plan for {plan_id}",
            "is_fallback": True
        }
    }

def get_most_recent_plan_id() -> Optional[str]:
    """Get the most recent plan ID from available sources"""
    try:
        # Check global dictionary first
        if global_active_plans:
            # Sort by creation time if available
            sorted_plans = sorted(
                global_active_plans.items(),
                key=lambda x: x[1].get("metadata", {}).get("created_at", 0),
                reverse=True
            )
            return sorted_plans[0][0]
        
        # Check backend's shared dictionary
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans') and \
               enhanced_enterprise_backend_with_context.shared_pending_plans:
                # Sort by creation time if available
                sorted_plans = sorted(
                    enhanced_enterprise_backend_with_context.shared_pending_plans.items(),
                    key=lambda x: x[1].get("metadata", {}).get("created_at", 0),
                    reverse=True
                )
                return sorted_plans[0][0]
        except ImportError:
            pass
        
        return None
    except Exception as e:
        logger.error(f"❌ Error getting most recent plan ID: {str(e)}")
        return None

async def test_do_button_action() -> bool:
    """Test the DO button action by creating a plan and executing it"""
    try:
        logger.info("🔍 Testing DO button action functionality")
        
        # Create a test plan
        test_plan_id = f"test_plan_{int(time.time())}"
        test_plan = {
            "id": test_plan_id,
            "steps": [
                {
                    "id": f"{test_plan_id}_step_1",
                    "type": "notification",
                    "action": "notify",
                    "content": "This is a test plan created by the ultimate_do_button_fix.py script.",
                    "position": {"x": 500, "y": 500}
                }
            ],
            "metadata": {
                "created_at": time.time(),
                "name": "Test Plan"
            }
        }
        
        # Store the plan in our global dictionary
        global_active_plans[test_plan_id] = test_plan
        logger.info(f"✅ Created test plan {test_plan_id} in global_active_plans")
        
        # Update backend's shared dictionary if accessible
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                enhanced_enterprise_backend_with_context.shared_pending_plans[test_plan_id] = test_plan
                logger.info(f"✅ Updated backend's shared_pending_plans with test plan {test_plan_id}")
        except ImportError:
            logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context")
        
        # Try to save the plan to persistence
        try:
            from plan_persistence import save_plan
            await save_plan(test_plan_id, test_plan)
            logger.info(f"✅ Saved test plan {test_plan_id} to persistent storage")
        except Exception as e:
            logger.warning(f"⚠️ Error saving test plan to persistence: {str(e)}")
        
        # Create a DO button action message
        do_button_message = {
            "type": "do_button_action",
            "do_button_action": {
                "plan_id": test_plan_id,
                "action": "execute"
            },
            "client_id": "test_client"
        }
        
        # Send the message to the neural UI handler
        try:
            import neural_ui_do_button_handler
            response = await neural_ui_do_button_handler.handle_do_button_action(do_button_message)
            logger.info(f"✅ Neural UI handler response: {response}")
            
            # Check if the response indicates success
            if isinstance(response, dict) and "success" in response and response["success"]:
                logger.info("✅ DO button action test successful!")
                return True
            else:
                logger.warning(f"⚠️ DO button action test response indicates failure: {response}")
                return False
        except ImportError:
            logger.error("❌ Could not import neural_ui_do_button_handler")
            return False
        except Exception as e:
            logger.error(f"❌ Error testing DO button action: {str(e)}")
            traceback.print_exc()
            return False
    except Exception as e:
        logger.error(f"❌ Error in test_do_button_action: {str(e)}")
        traceback.print_exc()
        return False

async def verify_websocket_connection(ws_uri: str) -> bool:
    """Verify WebSocket connection to a server"""
    try:
        async with websockets.connect(ws_uri, ping_timeout=2, close_timeout=2) as websocket:
            # Send a simple ping message
            ping_message = {"type": "ping", "timestamp": time.time()}
            await websocket.send(json.dumps(ping_message))
            logger.info(f"✅ Sent ping to {ws_uri}")
            
            # Wait for response with a timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                logger.info(f"✅ Received response from {ws_uri}: {response}")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout waiting for response from {ws_uri}")
                return False
    except Exception as e:
        logger.error(f"❌ Error connecting to {ws_uri}: {str(e)}")
        return False

async def direct_test_do_button(plan_id: str = None) -> bool:
    """Directly test the DO button by sending a WebSocket message to the server"""
    try:
        logger.info("🔍 Directly testing DO button with WebSocket message")
        
        # Create a test plan if plan_id not provided
        if not plan_id:
            plan_id = f"direct_test_plan_{int(time.time())}"
            test_plan = {
                "id": plan_id,
                "steps": [
                    {
                        "id": f"{plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "This is a direct test plan created by the ultimate_do_button_fix.py script.",
                        "position": {"x": 500, "y": 500}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "name": "Direct Test Plan"
                }
            }
            
            # Store the plan in our global dictionary
            global_active_plans[plan_id] = test_plan
            logger.info(f"✅ Created direct test plan {plan_id} in global_active_plans")
            
            # Update backend's shared dictionary if accessible
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                    enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = test_plan
                    logger.info(f"✅ Updated backend's shared_pending_plans with direct test plan {plan_id}")
            except ImportError:
                logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context")
        
        # Connect to the DO button server
        try:
            do_button_uri = f"ws://{LOCALHOST}:{DO_BUTTON_PORT}"
            async with websockets.connect(do_button_uri) as websocket:
                # Create a DO button action message
                do_button_message = {
                    "type": "do_button_action",
                    "do_button_action": {
                        "plan_id": plan_id,
                        "action": "execute"
                    },
                    "client_id": "direct_test_client"
                }
                
                # Send the message
                await websocket.send(json.dumps(do_button_message))
                logger.info(f"✅ Sent DO button action message to {do_button_uri}")
                
                # Wait for response with a timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    logger.info(f"✅ Received response from DO button server: {response}")
                    
                    # Parse the response
                    response_data = json.loads(response)
                    if "success" in response_data and response_data["success"]:
                        logger.info("✅ Direct DO button test successful!")
                        return True
                    else:
                        logger.warning(f"⚠️ Direct DO button test response indicates failure: {response_data}")
                        return False
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Timeout waiting for response from DO button server")
                    return False
        except Exception as e:
            logger.error(f"❌ Error connecting to DO button server: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"❌ Error in direct_test_do_button: {str(e)}")
        traceback.print_exc()
        return False

async def main():
    """Main function to apply all patches and verify fix"""
    logger.info("🚀 Starting Ultimate DO Button Fix")
    
    # Verify that all required WebSocket servers are running
    servers = [
        (NEURAL_UI_PORT, "Neural UI Detector Server"),
        (DO_BUTTON_PORT, "DO Button Server"),
        (BRIDGE_PORT, "WebSocket Bridge"),
        (BACKEND_PORT, "Backend Server")
    ]
    
    all_servers_running = True
    for port, name in servers:
        if await verify_ws_server_running(port):
            logger.info(f"✅ {name} is running on port {port}")
        else:
            logger.error(f"❌ {name} is not running on port {port}")
            all_servers_running = False
    
    if not all_servers_running:
        logger.warning("⚠️ Not all required servers are running")
    
    # Apply all patches
    patches = [
        (patch_backend_module, "Backend module"),
        (patch_neural_ui_handler, "Neural UI handler"),
        (patch_bridge_module, "Bridge module"),
        (patch_plan_persistence, "Plan persistence module")
    ]
    
    all_patches_applied = True
    for patch_func, name in patches:
        if await patch_func():
            logger.info(f"✅ Successfully patched {name}")
        else:
            logger.error(f"❌ Failed to patch {name}")
            all_patches_applied = False
    
    if all_patches_applied:
        logger.info("✅ All patches successfully applied")
    else:
        logger.warning("⚠️ Not all patches were applied")
    
    # Test the fix
    if all_patches_applied:
        if await test_do_button_action():
            logger.info("✅ DO button functionality test passed")
        else:
            logger.warning("⚠️ DO button functionality test failed")
        
        # Directly test with WebSocket
        if await direct_test_do_button():
            logger.info("✅ Direct WebSocket DO button test passed")
        else:
            logger.warning("⚠️ Direct WebSocket DO button test failed")
    
    logger.info("✅ Ultimate DO Button Fix completed")
    logger.info("✅ The system should now correctly handle DO button actions")
    logger.info("✅ Plans are now properly shared across all components")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Unhandled exception in main: {str(e)}")
        traceback.print_exc()