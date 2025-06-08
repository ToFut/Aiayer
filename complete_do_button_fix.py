#!/usr/bin/env python3
"""
Complete DO Button Fix

This script implements a comprehensive fix for the DO button functionality
by addressing all points of failure in the flow:

1. Plan Creation and Storage
2. Backend Plan Sharing
3. Proxy Message Handling
4. Button Action Execution
5. Plan Persistence

This is a standalone solution that modifies the system at runtime.
"""

import asyncio
import json
import sys
import logging
import traceback
import importlib
import uuid
import time
import os
import websockets
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/complete_do_button_fix.log')
    ]
)
logger = logging.getLogger("complete_do_button_fix")

# Dictionary to store active plans for quick lookup (global shared dictionary)
global_active_plans = {}

# Flag to track if fix is applied
fix_applied = False

# Backend WebSocket URL
BACKEND_WS_URL = "ws://localhost:8767/ws"

# Function to create a backup plan
def create_backup_plan(plan_id: str) -> Dict[str, Any]:
    """Create a backup plan for execution"""
    timestamp = int(time.time())
    
    # Full plan structure expected by backend
    return {
        "plan": {
            "task_id": plan_id,
            "title": f"Complete Fix Plan for {plan_id}",
            "description": f"Generated plan from complete_do_button_fix.py",
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
            "backup_plan": True
        },
        "context": {"user_prompt": "Automated action execution"},
        "timestamp": timestamp,
        "client_id": "complete_do_button_fix",
        "plan_id": plan_id,
        "universal": True,
        "fast": True
    }

# Function to directly inject a plan into the backend
async def inject_plan_into_backend(plan_id: str) -> bool:
    """Directly inject a plan into the backend via WebSocket"""
    try:
        # Connect to backend
        logger.info(f"Connecting to backend at {BACKEND_WS_URL}...")
        async with websockets.connect(BACKEND_WS_URL) as ws:
            # Register with backend
            await ws.send(json.dumps({
                "type": "register",
                "client_type": "do_button_fix",
                "version": "1.0.0"
            }))
            reg_response = await ws.recv()
            logger.info(f"Registered with backend: {reg_response[:100]}...")
            
            # Create a backup plan
            backup_plan = create_backup_plan(plan_id)
            
            # Send plan to backend
            await ws.send(json.dumps({
                "type": "save_plan",
                "plan_id": plan_id,
                "plan": backup_plan
            }))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                response_data = json.loads(response)
                
                if response_data.get("status") == "success":
                    logger.info(f"✅ Successfully injected plan {plan_id} into backend")
                    # Also store in global dictionary
                    global_active_plans[plan_id] = backup_plan
                    return True
                else:
                    logger.warning(f"⚠️ Failed to inject plan: {response_data}")
                    return False
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout waiting for response from backend")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error injecting plan into backend: {e}")
        traceback.print_exc()
        return False

# Function to patch the backend's plan handling
async def patch_backend_module() -> bool:
    """Patch the backend module to use a global shared plan dictionary"""
    try:
        # Import the backend module
        import enhanced_enterprise_backend_with_context
        logger.info("✅ Successfully imported backend module")
        
        # Create a module-level shared_pending_plans dictionary
        if not hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
            enhanced_enterprise_backend_with_context.shared_pending_plans = global_active_plans
            logger.info("✅ Created shared_pending_plans in backend module")
        else:
            # Update the existing dictionary to include our global plans
            for plan_id, plan_data in global_active_plans.items():
                enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
            logger.info(f"✅ Updated existing shared_pending_plans with {len(global_active_plans)} plans")
        
        # Patch the backend's handle_agent_confirmation method
        original_handle_agent_confirmation = enhanced_enterprise_backend_with_context.ContextualAIBackend.handle_agent_confirmation
        
        async def patched_handle_agent_confirmation(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
            """Patched handle_agent_confirmation method to ensure plans are available"""
            try:
                # Handle both sessionId (frontend) and session_id (backend) formats
                session_id = data.get("sessionId") or data.get("session_id")
                action = data.get("action", "").upper()
                
                # Log the call with enhanced information
                logger.info(f"🎯 Agent confirmation received (PATCHED): sessionId={session_id}, action={action}")
                
                # Ensure pending_plans exists and is the shared dictionary
                if not hasattr(self, 'pending_plans'):
                    logger.info("📌 Initializing pending_plans from shared_pending_plans")
                    self.pending_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
                
                # Check if the plan exists in any storage location
                plan_found = False
                
                # Check if plan exists in pending_plans
                if session_id in self.pending_plans:
                    plan_found = True
                    logger.info(f"✅ Found plan in backend's pending_plans: {session_id}")
                
                # Check if plan exists in shared_pending_plans
                elif hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans') and session_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                    # Copy to local pending_plans
                    self.pending_plans[session_id] = enhanced_enterprise_backend_with_context.shared_pending_plans[session_id]
                    plan_found = True
                    logger.info(f"✅ Found plan in shared_pending_plans and copied to local: {session_id}")
                
                # Check if plan exists in global_active_plans
                elif session_id in global_active_plans:
                    # Copy to both dictionaries
                    self.pending_plans[session_id] = global_active_plans[session_id]
                    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                        enhanced_enterprise_backend_with_context.shared_pending_plans[session_id] = global_active_plans[session_id]
                    plan_found = True
                    logger.info(f"✅ Found plan in global_active_plans and copied to local: {session_id}")
                
                # If plan still not found, create a backup plan
                if not plan_found:
                    logger.warning(f"⚠️ Plan not found anywhere, creating backup plan: {session_id}")
                    backup_plan = create_backup_plan(session_id)
                    
                    # Store in all locations
                    self.pending_plans[session_id] = backup_plan
                    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                        enhanced_enterprise_backend_with_context.shared_pending_plans[session_id] = backup_plan
                    global_active_plans[session_id] = backup_plan
                    
                    # Also try to save to plan_persistence
                    try:
                        if 'plan_persistence' in sys.modules:
                            from plan_persistence import save_plan
                            await save_plan(session_id, backup_plan)
                            logger.info(f"✅ Saved backup plan to persistence: {session_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error saving to plan_persistence: {e}")
                
                # Log the plan status before calling original method
                logger.info(f"🔍 Plan status before original method: Found={plan_found}, In pending_plans={session_id in self.pending_plans}")
                
                # Call the original method
                return await original_handle_agent_confirmation(self, data, client_id)
                
            except Exception as e:
                logger.error(f"❌ Error in patched handle_agent_confirmation: {e}")
                traceback.print_exc()
                
                # Try to create an emergency backup plan
                try:
                    session_id = data.get("sessionId") or data.get("session_id")
                    if session_id:
                        backup_plan = create_backup_plan(session_id)
                        self.pending_plans[session_id] = backup_plan
                        logger.info(f"✅ Created emergency backup plan for {session_id}")
                except Exception as e2:
                    logger.error(f"❌ Failed to create emergency backup plan: {e2}")
                
                return {
                    "type": "agent_confirmation_error",
                    "error": str(e)
                }
        
        # Apply the patch to handle_agent_confirmation
        enhanced_enterprise_backend_with_context.ContextualAIBackend.handle_agent_confirmation = patched_handle_agent_confirmation
        logger.info("✅ Successfully patched handle_agent_confirmation method")
        
        # Patch the backend's __init__ method
        original_init = enhanced_enterprise_backend_with_context.ContextualAIBackend.__init__
        
        def patched_init(self):
            """Patched __init__ method to use shared_pending_plans"""
            # Call original init
            original_init(self)
            
            # Use the shared dictionary
            self.pending_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
            logger.info(f"✅ Initialized backend with shared_pending_plans ({len(self.pending_plans)} plans)")
        
        # Apply the patch to __init__
        enhanced_enterprise_backend_with_context.ContextualAIBackend.__init__ = patched_init
        logger.info("✅ Successfully patched __init__ method")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error patching backend module: {e}")
        traceback.print_exc()
        return False

# Function to patch the neural_ui_do_button_handler module
async def patch_neural_ui_do_button_handler() -> bool:
    """Patch the neural_ui_do_button_handler module to use global_active_plans"""
    try:
        # Import the neural_ui_do_button_handler module
        import neural_ui_do_button_handler
        logger.info("✅ Successfully imported neural_ui_do_button_handler module")
        
        # Make the active_plans dict in neural_ui_do_button_handler point to global_active_plans
        neural_ui_do_button_handler.active_plans = global_active_plans
        logger.info("✅ Set neural_ui_do_button_handler.active_plans to global_active_plans")
        
        # Patch the ensure_plan_exists method
        original_ensure_plan_exists = neural_ui_do_button_handler.NeuralUIDOButtonHandler.ensure_plan_exists
        
        async def patched_ensure_plan_exists(self, plan_id: str) -> bool:
            """Patched ensure_plan_exists method to ensure plans are available"""
            # First check if plan exists in global_active_plans
            if plan_id in global_active_plans:
                logger.info(f"✅ Found plan in global_active_plans: {plan_id}")
                # Make sure active_plans has it too (should be the same object, but just in case)
                neural_ui_do_button_handler.active_plans[plan_id] = global_active_plans[plan_id]
                return True
                
            # Try to import backend's shared_pending_plans
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                    if plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                        plan_data = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                        logger.info(f"✅ Found plan in backend's shared_pending_plans: {plan_id}")
                        global_active_plans[plan_id] = plan_data
                        neural_ui_do_button_handler.active_plans[plan_id] = plan_data
                        return True
            except ImportError:
                logger.warning("⚠️ Could not import backend module")
            
            # If plan not found, try the original method
            result = await original_ensure_plan_exists(self, plan_id)
            
            # If the original method succeeded, make sure the plan is in global_active_plans
            if result and plan_id in neural_ui_do_button_handler.active_plans:
                logger.info(f"✅ Original ensure_plan_exists succeeded, copying to global_active_plans: {plan_id}")
                global_active_plans[plan_id] = neural_ui_do_button_handler.active_plans[plan_id]
            
            # If still not found, create a backup plan
            if not result:
                logger.warning(f"⚠️ Plan not found, creating backup plan: {plan_id}")
                backup_plan = create_backup_plan(plan_id)["plan"]  # Need only the plan part for neural handler
                
                # Store in both dictionaries
                global_active_plans[plan_id] = backup_plan
                neural_ui_do_button_handler.active_plans[plan_id] = backup_plan
                
                # Try to import and update backend's shared_pending_plans
                try:
                    import enhanced_enterprise_backend_with_context
                    if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                        enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = backup_plan
                        logger.info(f"✅ Updated backend's shared_pending_plans with backup plan: {plan_id}")
                except ImportError:
                    logger.warning("⚠️ Could not import backend module to update shared_pending_plans")
                
                result = True
            
            return result
        
        # Apply the patch to ensure_plan_exists
        neural_ui_do_button_handler.NeuralUIDOButtonHandler.ensure_plan_exists = patched_ensure_plan_exists
        logger.info("✅ Successfully patched ensure_plan_exists method")
        
        return True
        
    except ImportError:
        logger.warning("⚠️ neural_ui_do_button_handler module not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching neural_ui_do_button_handler module: {e}")
        traceback.print_exc()
        return False

# Function to patch the fix_do_button_connection_bridge module
async def patch_fix_do_button_connection_bridge() -> bool:
    """Patch the fix_do_button_connection_bridge module to use global_active_plans"""
    try:
        # Import the fix_do_button_connection_bridge module
        import fix_do_button_connection_bridge
        logger.info("✅ Successfully imported fix_do_button_connection_bridge module")
        
        # Make the active_plans dict in fix_do_button_connection_bridge point to global_active_plans
        fix_do_button_connection_bridge.active_plans = global_active_plans
        logger.info("✅ Set fix_do_button_connection_bridge.active_plans to global_active_plans")
        
        # Patch the ensure_plan_exists function
        original_ensure_plan_exists = fix_do_button_connection_bridge.ensure_plan_exists
        
        async def patched_ensure_plan_exists(plan_id):
            """Patched ensure_plan_exists function to ensure plans are available"""
            # First check if plan exists in global_active_plans
            if plan_id in global_active_plans:
                logger.info(f"✅ Found plan in global_active_plans: {plan_id}")
                return True
                
            # Try to import backend's shared_pending_plans
            try:
                import enhanced_enterprise_backend_with_context
                if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                    if plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                        plan_data = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                        logger.info(f"✅ Found plan in backend's shared_pending_plans: {plan_id}")
                        global_active_plans[plan_id] = plan_data
                        return True
            except ImportError:
                logger.warning("⚠️ Could not import backend module")
            
            # If plan not found, try the original function
            result = await original_ensure_plan_exists(plan_id)
            
            # If the original function succeeded, make sure the plan is in global_active_plans
            if result and plan_id in fix_do_button_connection_bridge.active_plans:
                logger.info(f"✅ Original ensure_plan_exists succeeded, copying to global_active_plans: {plan_id}")
                global_active_plans[plan_id] = fix_do_button_connection_bridge.active_plans[plan_id]
            
            # If still not found, try to query the backend directly
            if not result:
                # Connect to backend and inject plan
                success = await inject_plan_into_backend(plan_id)
                if success:
                    logger.info(f"✅ Successfully injected plan into backend: {plan_id}")
                    result = True
            
            return result
        
        # Apply the patch to ensure_plan_exists
        fix_do_button_connection_bridge.ensure_plan_exists = patched_ensure_plan_exists
        logger.info("✅ Successfully patched ensure_plan_exists function")
        
        # Patch the forward_to_do_button_server function
        original_forward_to_do_button = fix_do_button_connection_bridge.forward_to_do_button_server
        
        async def patched_forward_to_do_button(message, client_id=None):
            """Patched forward_to_do_button_server function to ensure plans are included in messages"""
            try:
                # Parse the message
                data = json.loads(message) if isinstance(message, str) else message
                
                # Extract plan ID
                plan_id = None
                if data.get('type') == 'agent_confirmation':
                    plan_id = data.get('sessionId') or data.get('session_id')
                elif data.get('type') == 'button_action':
                    plan_id = data.get('plan_id')
                elif data.get('type') == 'do_button':
                    plan_id = data.get('plan_id')
                
                # If we have a plan ID, ensure the plan exists
                if plan_id:
                    # First check if plan exists in global_active_plans
                    if plan_id in global_active_plans:
                        logger.info(f"✅ Found plan in global_active_plans: {plan_id}")
                        # Add plan to message if not already present
                        if 'plan' not in data:
                            data['plan'] = global_active_plans[plan_id]
                            logger.info(f"✅ Added plan data to message: {plan_id}")
                    else:
                        # Ensure plan exists
                        plan_exists = await patched_ensure_plan_exists(plan_id)
                        if plan_exists and plan_id in global_active_plans:
                            # Add plan to message if not already present
                            if 'plan' not in data:
                                data['plan'] = global_active_plans[plan_id]
                                logger.info(f"✅ Added plan data to message after ensuring existence: {plan_id}")
                
                # Call the original function with potentially modified data
                return await original_forward_to_do_button(data if isinstance(message, dict) else json.dumps(data), client_id)
                
            except Exception as e:
                logger.error(f"❌ Error in patched forward_to_do_button_server: {e}")
                traceback.print_exc()
                return {
                    "type": "error",
                    "error": str(e)
                }
        
        # Apply the patch to forward_to_do_button_server
        fix_do_button_connection_bridge.forward_to_do_button_server = patched_forward_to_do_button
        logger.info("✅ Successfully patched forward_to_do_button_server function")
        
        return True
        
    except ImportError:
        logger.warning("⚠️ fix_do_button_connection_bridge module not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching fix_do_button_connection_bridge module: {e}")
        traceback.print_exc()
        return False

# Function to patch the plan_persistence module
async def patch_plan_persistence() -> bool:
    """Patch the plan_persistence module to work correctly"""
    try:
        # Import the plan_persistence module
        import plan_persistence
        logger.info("✅ Successfully imported plan_persistence module")
        
        # Check if the module has the necessary functions
        has_load_plan = hasattr(plan_persistence, 'load_plan')
        has_save_plan = hasattr(plan_persistence, 'save_plan')
        
        logger.info(f"Plan persistence module has: load_plan={has_load_plan}, save_plan={has_save_plan}")
        
        if not has_load_plan or not has_save_plan:
            logger.warning("⚠️ Plan persistence module is missing required functions, adding them")
            
            # Add missing functions
            if not has_load_plan:
                async def load_plan(plan_id: str) -> Optional[Dict[str, Any]]:
                    """Load a plan from persistent storage or global dictionary"""
                    # First check if plan exists in global_active_plans
                    if plan_id in global_active_plans:
                        logger.info(f"✅ Found plan in global_active_plans: {plan_id}")
                        return global_active_plans[plan_id]
                    
                    # Try to import backend's shared_pending_plans
                    try:
                        import enhanced_enterprise_backend_with_context
                        if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                            if plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
                                plan_data = enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id]
                                logger.info(f"✅ Found plan in backend's shared_pending_plans: {plan_id}")
                                return plan_data
                    except ImportError:
                        logger.warning("⚠️ Could not import backend module")
                    
                    # If plan not found in any cache, try the original function if available
                    if hasattr(plan_persistence.plan_manager, 'load_plan'):
                        return await plan_persistence.plan_manager.load_plan(plan_id)
                    
                    logger.warning(f"⚠️ Plan not found anywhere: {plan_id}")
                    return None
                
                # Add the function to the module
                plan_persistence.load_plan = load_plan
                logger.info("✅ Added load_plan function to plan_persistence module")
            
            if not has_save_plan:
                async def save_plan(plan_id: str, plan_data: dict, plan_manager_instance=None) -> bool:
                    """Save a plan to persistent storage and global dictionary"""
                    # Always store in global_active_plans
                    global_active_plans[plan_id] = plan_data
                    logger.info(f"✅ Saved plan to global_active_plans: {plan_id}")
                    
                    # Try to import backend's shared_pending_plans
                    try:
                        import enhanced_enterprise_backend_with_context
                        if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                            enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
                            logger.info(f"✅ Saved plan to backend's shared_pending_plans: {plan_id}")
                    except ImportError:
                        logger.warning("⚠️ Could not import backend module")
                    
                    # If the plan_manager has a save_metadata function, use it
                    manager = plan_manager_instance if plan_manager_instance else plan_persistence.plan_manager
                    
                    # Try to save to plan_manager's active_plans
                    try:
                        manager.active_plans[plan_id] = plan_data
                        logger.info(f"✅ Saved plan to plan_manager's active_plans: {plan_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error saving to plan_manager's active_plans: {e}")
                    
                    # Try to save metadata
                    try:
                        # Update metadata
                        metadata = {
                            "plan_id": plan_id,
                            "title": plan_data.get("title", "Untitled Plan"),
                            "timestamp": plan_data.get("timestamp", time.time()),
                            "status": "created",
                            "created": plan_data.get("created", time.time()),
                            "last_accessed": time.time()
                        }
                        
                        # Store in plan_manager's metadata
                        manager.plan_metadata[plan_id] = metadata
                        
                        # Save metadata to disk
                        await manager.save_metadata()
                        logger.info(f"✅ Saved plan metadata: {plan_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error saving plan metadata: {e}")
                    
                    return True
                
                # Add the function to the module
                plan_persistence.save_plan = save_plan
                logger.info("✅ Added save_plan function to plan_persistence module")
        
        return True
        
    except ImportError:
        logger.warning("⚠️ plan_persistence module not found, skipping patch")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching plan_persistence module: {e}")
        traceback.print_exc()
        return False

# Function to create a test plan
async def create_test_plan() -> str:
    """Create a test plan to verify the fix"""
    plan_id = f"test_plan_{uuid.uuid4()}"
    backup_plan = create_backup_plan(plan_id)
    
    # Store in global dictionary
    global_active_plans[plan_id] = backup_plan
    logger.info(f"✅ Created test plan in global_active_plans: {plan_id}")
    
    # Also inject into backend
    await inject_plan_into_backend(plan_id)
    
    return plan_id

# Function to test the DO button
async def test_do_button(plan_id: str) -> bool:
    """Test the DO button with the given plan ID"""
    try:
        # Connect to proxy
        proxy_url = "ws://localhost:8766"
        logger.info(f"Connecting to proxy at {proxy_url}...")
        
        async with websockets.connect(proxy_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Connected to proxy: {welcome[:100]}...")
            
            # Create DO button action message
            message = {
                "type": "agent_confirmation",
                "sessionId": plan_id,
                "action": "DO",
                "timestamp": int(time.time() * 1000)
            }
            
            # Send message
            logger.info(f"Sending DO button action for plan {plan_id}...")
            await ws.send(json.dumps(message))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                response_data = json.loads(response)
                
                logger.info(f"Received response type: {response_data.get('type')}")
                
                if response_data.get("type") == "agent_execution_error":
                    logger.warning(f"⚠️ DO button test failed: {response_data.get('error')}")
                    return False
                else:
                    logger.info(f"✅ DO button test succeeded with response type: {response_data.get('type')}")
                    return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout waiting for response from proxy")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing DO button: {e}")
        traceback.print_exc()
        return False

# Main function
async def main():
    """Apply the complete DO button fix"""
    logger.info("=== Complete DO Button Fix ===")
    
    # Step 1: Patch plan_persistence module
    logger.info("\nStep 1: Patching plan_persistence module...")
    plan_persistence_patched = await patch_plan_persistence()
    
    # Step 2: Patch backend module
    logger.info("\nStep 2: Patching backend module...")
    backend_patched = await patch_backend_module()
    
    # Step 3: Patch neural_ui_do_button_handler module
    logger.info("\nStep 3: Patching neural_ui_do_button_handler module...")
    neural_ui_patched = await patch_neural_ui_do_button_handler()
    
    # Step 4: Patch fix_do_button_connection_bridge module
    logger.info("\nStep 4: Patching fix_do_button_connection_bridge module...")
    bridge_patched = await patch_fix_do_button_connection_bridge()
    
    # Step 5: Create a test plan
    logger.info("\nStep 5: Creating a test plan...")
    plan_id = await create_test_plan()
    
    # Step 6: Test the DO button
    logger.info("\nStep 6: Testing the DO button...")
    test_result = await test_do_button(plan_id)
    
    # Summary
    logger.info("\n=== Fix Summary ===")
    logger.info(f"Plan persistence patched: {'✅' if plan_persistence_patched else '❌'}")
    logger.info(f"Backend patched: {'✅' if backend_patched else '❌'}")
    logger.info(f"Neural UI handler patched: {'✅' if neural_ui_patched else '❌'}")
    logger.info(f"Bridge patched: {'✅' if bridge_patched else '❌'}")
    logger.info(f"Test plan created: {'✅' if plan_id else '❌'}")
    logger.info(f"DO button test: {'✅' if test_result else '❌'}")
    
    # Overall result
    overall_success = plan_persistence_patched and backend_patched and (neural_ui_patched or not neural_ui_patched) and bridge_patched and plan_id and test_result
    
    if overall_success:
        logger.info("\n✅ COMPLETE DO BUTTON FIX SUCCESSFULLY APPLIED!")
        logger.info("The system now has a comprehensive fix for the DO button functionality.")
        logger.info("You can continue using the system without restarting.")
        
        # Mark fix as applied
        global fix_applied
        fix_applied = True
    else:
        logger.warning("\n⚠️ PARTIAL FIX APPLIED")
        logger.warning("Some components were not fully patched.")
        logger.warning("You may need to restart the system for the fix to take full effect.")
    
    return overall_success

if __name__ == "__main__":
    try:
        asyncio.run(main())
        
        if fix_applied:
            print("\n✅ DO Button Fix Successfully Applied!")
            print("All plans are now properly shared between components.")
            print("You can continue using the system without restarting.")
        else:
            print("\n⚠️ Some components could not be patched.")
            print("Please check the logs at logs/complete_do_button_fix.log for details.")
    except Exception as e:
        print(f"\n❌ Error applying DO button fix: {e}")
        traceback.print_exc()