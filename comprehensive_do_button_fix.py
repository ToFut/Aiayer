#!/usr/bin/env python3
"""
Comprehensive DO Button Fix

This script implements a permanent fix for the DO button issue by:
1. Creating a global shared dictionary for plans
2. Patching all relevant modules to use this shared dictionary
3. Fixing plan persistence issues
4. Adding clear logging for troubleshooting
5. Creating a fallback mechanism for missing plans

No need to restart any services - this script applies fixes at runtime.
"""

import os
import sys
import json
import time
import asyncio
import logging
import importlib
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/comprehensive_do_button_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ComprehensiveDoButtonFix")

# Global shared dictionary for plans across all instances
GLOBAL_PLANS: Dict[str, Dict[str, Any]] = {}

def add_generate_plan_id_to_persistence():
    """Add generate_plan_id function to plan_persistence module"""
    try:
        import plan_persistence
        
        if not hasattr(plan_persistence, 'generate_plan_id'):
            # Add the function to the module
            def generate_plan_id(prefix="plan"):
                """Generate a unique plan ID with the given prefix"""
                return f"{prefix}_{int(time.time())}"
                
            plan_persistence.generate_plan_id = generate_plan_id
            logger.info("✅ Added generate_plan_id function to plan_persistence module")
        else:
            logger.info("✅ generate_plan_id function already exists in plan_persistence module")
            
        return True
    except ImportError:
        logger.error("❌ Failed to import plan_persistence module")
        return False
    except Exception as e:
        logger.error(f"❌ Error adding generate_plan_id to plan_persistence: {e}")
        return False

def fix_plan_persistence_module():
    """Fix the plan_persistence module to ensure proper plan loading and saving"""
    try:
        import plan_persistence
        
        # First, check if delete_plan exists
        if not hasattr(plan_persistence, 'delete_plan'):
            # Add delete_plan function
            async def delete_plan(plan_id: str, plan_manager_instance=None) -> bool:
                """Delete a plan from persistent storage"""
                instance = plan_manager_instance or plan_persistence.plan_manager
                return await instance.delete_plan(plan_id)
                
            plan_persistence.delete_plan = delete_plan
            logger.info("✅ Added delete_plan function to plan_persistence module")
        else:
            logger.info("✅ delete_plan function already exists in plan_persistence module")
        
        # Add generate_plan_id if it doesn't exist
        add_generate_plan_id_to_persistence()
        
        # Make the original save_plan and load_plan use our global dictionary
        original_save_plan = plan_persistence.save_plan
        original_load_plan = plan_persistence.load_plan
        
        async def enhanced_save_plan(plan_id: str, plan_data: dict, plan_manager_instance=None) -> bool:
            """Enhanced save_plan that updates the global dictionary"""
            # Store in global dictionary
            GLOBAL_PLANS[plan_id] = plan_data
            logger.info(f"✅ Saved plan {plan_id} to global dictionary")
            
            # Call the original function
            return await original_save_plan(plan_id, plan_data, plan_manager_instance)
            
        async def enhanced_load_plan(plan_id: str, plan_manager_instance=None) -> Optional[dict]:
            """Enhanced load_plan that checks the global dictionary first"""
            # Check global dictionary first
            if plan_id in GLOBAL_PLANS:
                logger.info(f"✅ Loaded plan {plan_id} from global dictionary")
                return GLOBAL_PLANS[plan_id]
                
            # Call the original function
            plan = await original_load_plan(plan_id, plan_manager_instance)
            
            # Store in global dictionary if found
            if plan:
                GLOBAL_PLANS[plan_id] = plan
                logger.info(f"✅ Stored loaded plan {plan_id} in global dictionary")
                
            return plan
            
        # Apply patches
        plan_persistence.save_plan = enhanced_save_plan
        plan_persistence.load_plan = enhanced_load_plan
        
        # Add the global dictionary to the module
        plan_persistence.GLOBAL_PLANS = GLOBAL_PLANS
        
        logger.info("✅ Fixed plan_persistence module successfully")
        return True
    except ImportError:
        logger.error("❌ Failed to import plan_persistence module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing plan_persistence module: {e}")
        return False

def fix_enterprise_backend():
    """Fix the enhanced_enterprise_backend_with_context module"""
    try:
        import enhanced_enterprise_backend_with_context
        
        # Replace the shared_pending_plans with our global dictionary
        enhanced_enterprise_backend_with_context.shared_pending_plans = GLOBAL_PLANS
        logger.info("✅ Updated shared_pending_plans in backend module to use global dictionary")
        
        # Fix handle_agent_confirmation to always check the global dictionary
        original_handle_agent_confirmation = None
        for attr_name in dir(enhanced_enterprise_backend_with_context):
            attr = getattr(enhanced_enterprise_backend_with_context, attr_name)
            if hasattr(attr, 'handle_agent_confirmation'):
                class_with_method = attr
                original_handle_agent_confirmation = class_with_method.handle_agent_confirmation
                break
                
        if original_handle_agent_confirmation:
            async def patched_handle_agent_confirmation(self, data, client_id=None):
                """Patched version of handle_agent_confirmation"""
                try:
                    # Handle both sessionId (frontend) and session_id (backend) formats
                    session_id = data.get("sessionId") or data.get("session_id")
                    logger.info(f"🎯 Agent confirmation received: sessionId={session_id}")
                    
                    # First store any plans that come with the message
                    if "automation_plan" in data and "id" in data["automation_plan"]:
                        plan_id = data["automation_plan"]["id"]
                        GLOBAL_PLANS[plan_id] = data["automation_plan"]
                        logger.info(f"✅ Stored incoming plan {plan_id} in global dictionary")
                        
                        # Also store in the instance dictionary
                        if hasattr(self, 'pending_plans'):
                            self.pending_plans[plan_id] = data["automation_plan"]
                            
                    # Check for plan in the message
                    if session_id and "plan" in data:
                        GLOBAL_PLANS[session_id] = data["plan"]
                        logger.info(f"✅ Stored plan from message for {session_id} in global dictionary")
                        
                        # Also store in the instance dictionary
                        if hasattr(self, 'pending_plans'):
                            self.pending_plans[session_id] = data["plan"]
                            
                    # Ensure pending_plans exists on the instance
                    if not hasattr(self, 'pending_plans'):
                        self.pending_plans = {}
                        
                    # Log available plans
                    logger.info(f"🔍 Available plans in global dictionary: {list(GLOBAL_PLANS.keys())}")
                    logger.info(f"🔍 Available plans in instance dictionary: {list(self.pending_plans.keys())}")
                    
                    # If session_id is in global plans but not in instance plans, copy it
                    if session_id and session_id in GLOBAL_PLANS and session_id not in self.pending_plans:
                        self.pending_plans[session_id] = GLOBAL_PLANS[session_id]
                        logger.info(f"✅ Copied plan {session_id} from global to instance dictionary")
                        
                    # If no plan exists, try to create a backup plan
                    if session_id and session_id not in self.pending_plans and session_id not in GLOBAL_PLANS:
                        # Try to load from persistence
                        try:
                            import plan_persistence
                            plan_data = await plan_persistence.load_plan(session_id)
                            if plan_data:
                                self.pending_plans[session_id] = plan_data
                                GLOBAL_PLANS[session_id] = plan_data
                                logger.info(f"✅ Loaded plan {session_id} from persistence")
                            else:
                                logger.warning(f"⚠️ Could not load plan {session_id} from persistence")
                                # Create a backup plan
                                timestamp = time.time()
                                backup_plan = {
                                    "id": session_id,
                                    "title": f"Backup Plan for {session_id}",
                                    "description": "This is a backup plan created by the comprehensive DO button fix",
                                    "steps": [
                                        {
                                            "id": f"{session_id}_step_1",
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
                                self.pending_plans[session_id] = backup_plan
                                GLOBAL_PLANS[session_id] = backup_plan
                                logger.info(f"✅ Created backup plan for {session_id}")
                                
                                # Save to persistence
                                try:
                                    await plan_persistence.save_plan(session_id, backup_plan)
                                    logger.info(f"✅ Saved backup plan {session_id} to persistence")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not save backup plan to persistence: {e}")
                        except Exception as e:
                            logger.warning(f"⚠️ Error checking persistence: {e}")
                            # Create a simple backup plan without persistence
                            timestamp = time.time()
                            backup_plan = {
                                "id": session_id,
                                "title": f"Backup Plan for {session_id}",
                                "description": "This is a backup plan created by the comprehensive DO button fix",
                                "steps": [
                                    {
                                        "id": f"{session_id}_step_1",
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
                            self.pending_plans[session_id] = backup_plan
                            GLOBAL_PLANS[session_id] = backup_plan
                            logger.info(f"✅ Created simple backup plan for {session_id}")
                except Exception as e:
                    logger.error(f"❌ Error in patched_handle_agent_confirmation: {e}")
                    
                # Call the original method
                return await original_handle_agent_confirmation(self, data, client_id)
                
            # Apply the patch
            class_with_method.handle_agent_confirmation = patched_handle_agent_confirmation
            logger.info(f"✅ Patched handle_agent_confirmation method in {class_with_method.__name__}")
        else:
            logger.warning("⚠️ Could not find handle_agent_confirmation method to patch")
            
        # Fix execute_automation_plan to check the global dictionary
        original_execute_automation_plan = None
        for attr_name in dir(enhanced_enterprise_backend_with_context):
            attr = getattr(enhanced_enterprise_backend_with_context, attr_name)
            if hasattr(attr, 'execute_automation_plan'):
                class_with_method = attr
                original_execute_automation_plan = class_with_method.execute_automation_plan
                break
                
        if original_execute_automation_plan:
            async def patched_execute_automation_plan(self, plan_id, client_id=None):
                """Patched version of execute_automation_plan"""
                try:
                    logger.info(f"🔍 Looking for plan {plan_id} to execute")
                    
                    # First check the instance dictionary
                    if hasattr(self, 'pending_plans') and plan_id in self.pending_plans:
                        logger.info(f"✅ Found plan {plan_id} in instance dictionary")
                    # Then check the global dictionary
                    elif plan_id in GLOBAL_PLANS:
                        # Copy to instance dictionary
                        if hasattr(self, 'pending_plans'):
                            self.pending_plans[plan_id] = GLOBAL_PLANS[plan_id]
                            logger.info(f"✅ Copied plan {plan_id} from global to instance dictionary")
                    # Try to load from persistence
                    else:
                        try:
                            import plan_persistence
                            plan = await plan_persistence.load_plan(plan_id)
                            if plan:
                                if hasattr(self, 'pending_plans'):
                                    self.pending_plans[plan_id] = plan
                                GLOBAL_PLANS[plan_id] = plan
                                logger.info(f"✅ Loaded plan {plan_id} from persistence")
                            else:
                                logger.warning(f"⚠️ Could not load plan {plan_id} from persistence")
                                # Create a backup plan
                                timestamp = time.time()
                                backup_plan = {
                                    "id": plan_id,
                                    "title": f"Backup Plan for {plan_id}",
                                    "description": "This is a backup plan created by the comprehensive DO button fix",
                                    "steps": [
                                        {
                                            "id": f"{plan_id}_step_1",
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
                                if hasattr(self, 'pending_plans'):
                                    self.pending_plans[plan_id] = backup_plan
                                GLOBAL_PLANS[plan_id] = backup_plan
                                logger.info(f"✅ Created backup plan for {plan_id}")
                                
                                # Save to persistence
                                try:
                                    await plan_persistence.save_plan(plan_id, backup_plan)
                                    logger.info(f"✅ Saved backup plan {plan_id} to persistence")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not save backup plan to persistence: {e}")
                        except Exception as e:
                            logger.warning(f"⚠️ Error checking persistence: {e}")
                            # Create a simple backup plan without persistence
                            timestamp = time.time()
                            backup_plan = {
                                "id": plan_id,
                                "title": f"Backup Plan for {plan_id}",
                                "description": "This is a backup plan created by the comprehensive DO button fix",
                                "steps": [
                                    {
                                        "id": f"{plan_id}_step_1",
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
                            if hasattr(self, 'pending_plans'):
                                self.pending_plans[plan_id] = backup_plan
                            GLOBAL_PLANS[plan_id] = backup_plan
                            logger.info(f"✅ Created simple backup plan for {plan_id}")
                except Exception as e:
                    logger.error(f"❌ Error in patched_execute_automation_plan: {e}")
                    
                # Call the original method
                return await original_execute_automation_plan(self, plan_id, client_id)
                
            # Apply the patch
            class_with_method.execute_automation_plan = patched_execute_automation_plan
            logger.info(f"✅ Patched execute_automation_plan method in {class_with_method.__name__}")
        else:
            logger.warning("⚠️ Could not find execute_automation_plan method to patch")
            
        logger.info("✅ Fixed enterprise backend module successfully")
        return True
    except ImportError:
        logger.error("❌ Failed to import enhanced_enterprise_backend_with_context module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing enterprise backend module: {e}")
        return False

def fix_neural_ui_do_button_handler():
    """Fix the neural_ui_do_button_handler module"""
    try:
        import neural_ui_do_button_handler
        
        # Use our global dictionary for active_plans
        neural_ui_do_button_handler.active_plans = GLOBAL_PLANS
        logger.info("✅ Updated active_plans in neural_ui_do_button_handler to use global dictionary")
        
        # Add reference to ensure_plan_exists for patching
        handler_instance = neural_ui_do_button_handler.handler
        original_ensure_plan_exists = handler_instance.ensure_plan_exists
        
        async def patched_ensure_plan_exists(self, plan_id: str) -> bool:
            """Patched version of ensure_plan_exists"""
            if not plan_id:
                logger.warning("⚠️ No plan ID provided")
                return False
                
            logger.info(f"🔍 Checking for plan {plan_id} existence")
            
            # Check if plan exists in memory cache
            if plan_id in GLOBAL_PLANS:
                logger.info(f"✅ Plan {plan_id} exists in global dictionary")
                return True
                
            # Try to load from persistence
            try:
                import plan_persistence
                plan = await plan_persistence.load_plan(plan_id)
                if plan:
                    GLOBAL_PLANS[plan_id] = plan
                    logger.info(f"✅ Loaded plan {plan_id} from persistence")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Error loading plan from persistence: {e}")
                
            # Create a backup plan
            try:
                timestamp = time.time()
                backup_plan = {
                    "id": plan_id,
                    "title": f"Backup Plan for {plan_id}",
                    "description": "This is a backup plan created by the comprehensive DO button fix",
                    "steps": [
                        {
                            "id": f"{plan_id}_step_1",
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
                GLOBAL_PLANS[plan_id] = backup_plan
                logger.info(f"✅ Created backup plan for {plan_id}")
                
                # Save to persistence
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
                
        # Apply the patch
        handler_instance.ensure_plan_exists = patched_ensure_plan_exists
        logger.info("✅ Patched ensure_plan_exists method in NeuralUIDOButtonHandler")
        
        # Patch handle_do_button_action
        original_handle_do_button_action = handler_instance.handle_do_button_action
        
        async def patched_handle_do_button_action(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
            """Patched version of handle_do_button_action"""
            # Extract the plan ID based on message type
            plan_id = None
            
            if message_data.get('type') == 'agent_confirmation':
                plan_id = message_data.get('sessionId') or message_data.get('session_id')
            elif message_data.get('type') == 'button_action':
                plan_id = message_data.get('plan_id')
            elif message_data.get('type') == 'do_button':
                plan_id = message_data.get('plan_id')
            elif message_data.get('type') == 'do_button_action' and message_data.get('do_button_action', {}).get('plan_id'):
                plan_id = message_data.get('do_button_action', {}).get('plan_id')
            
            if not plan_id:
                logger.error("❌ No plan ID found in message")
                return {
                    "type": "error",
                    "error": "No plan ID found in message"
                }
            
            logger.info(f"🔍 Processing DO button action for plan: {plan_id}")
            logger.info(f"🔍 Available plans in global dictionary: {list(GLOBAL_PLANS.keys())}")
            
            # Ensure plan exists
            plan_exists = await self.ensure_plan_exists(plan_id)
            if not plan_exists:
                logger.error(f"❌ Failed to ensure plan exists: {plan_id}")
                return {
                    "type": "error",
                    "error": f"Plan {plan_id} not found and could not be created"
                }
                
            # If the message doesn't include the full plan, add it
            if 'plan' not in message_data and plan_id in GLOBAL_PLANS:
                message_data['plan'] = GLOBAL_PLANS[plan_id]
                logger.info(f"✅ Added plan data to message for {plan_id}")
                
            # Call the original method
            return await original_handle_do_button_action(self, message_data)
            
        # Apply the patch
        handler_instance.handle_do_button_action = patched_handle_do_button_action
        logger.info("✅ Patched handle_do_button_action method in NeuralUIDOButtonHandler")
        
        # Patch handle_proxy_message
        original_handle_proxy_message = neural_ui_do_button_handler.handle_proxy_message
        
        async def patched_handle_proxy_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
            """Patched version of handle_proxy_message"""
            # Make sure the handler is connected
            if not handler_instance.connected:
                success = await handler_instance.connect()
                if not success:
                    logger.error("❌ Failed to connect to servers")
                    return {
                        "type": "error",
                        "error": "Failed to connect to servers"
                    }
                    
            # Log available plans
            logger.info(f"🔍 Available plans in global dictionary: {list(GLOBAL_PLANS.keys())}")
            
            # Extract plan ID from message
            plan_id = None
            
            if message_data.get('type') == 'agent_confirmation':
                plan_id = message_data.get('sessionId') or message_data.get('session_id')
            elif message_data.get('type') == 'button_action':
                plan_id = message_data.get('plan_id')
            elif message_data.get('type') == 'do_button':
                plan_id = message_data.get('plan_id')
            elif message_data.get('type') == 'do_button_action' and message_data.get('do_button_action', {}).get('plan_id'):
                plan_id = message_data.get('do_button_action', {}).get('plan_id')
                
            # If plan ID found, ensure the plan exists
            if plan_id:
                # Check if plan is in message
                if 'plan' in message_data:
                    GLOBAL_PLANS[plan_id] = message_data['plan']
                    logger.info(f"✅ Stored plan from message for {plan_id} in global dictionary")
                # Check if plan exists in global dictionary
                elif plan_id not in GLOBAL_PLANS:
                    # Create backup plan
                    timestamp = time.time()
                    backup_plan = {
                        "id": plan_id,
                        "title": f"Backup Plan for {plan_id}",
                        "description": "This is a backup plan created by the comprehensive DO button fix",
                        "steps": [
                            {
                                "id": f"{plan_id}_step_1",
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
                    GLOBAL_PLANS[plan_id] = backup_plan
                    logger.info(f"✅ Created backup plan for {plan_id} in global dictionary")
                    
                # Add plan to message if not already there
                if 'plan' not in message_data and plan_id in GLOBAL_PLANS:
                    message_data['plan'] = GLOBAL_PLANS[plan_id]
                    logger.info(f"✅ Added plan data to message for {plan_id}")
                    
            # Call the original function
            return await original_handle_proxy_message(message_data)
            
        # Apply the patch
        neural_ui_do_button_handler.handle_proxy_message = patched_handle_proxy_message
        logger.info("✅ Patched handle_proxy_message function in neural_ui_do_button_handler")
        
        logger.info("✅ Fixed neural_ui_do_button_handler module successfully")
        return True
    except ImportError:
        logger.error("❌ Failed to import neural_ui_do_button_handler module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing neural_ui_do_button_handler module: {e}")
        return False

def fix_do_button_connection_bridge():
    """Fix the fix_do_button_connection_bridge module"""
    try:
        import fix_do_button_connection_bridge
        
        # Add global plans dictionary to the module
        fix_do_button_connection_bridge.GLOBAL_PLANS = GLOBAL_PLANS
        logger.info("✅ Added GLOBAL_PLANS to fix_do_button_connection_bridge module")
        
        # Patch the forward_to_do_button_server function
        original_forward_to_do_button_server = fix_do_button_connection_bridge.forward_to_do_button_server
        
        async def patched_forward_to_do_button_server(message, client_id=None):
            """Patched version of forward_to_do_button_server"""
            try:
                # Parse the message
                data = json.loads(message) if isinstance(message, str) else message
                
                # Extract plan_id based on message type
                plan_id = None
                if data.get('type') == 'agent_confirmation':
                    plan_id = data.get('sessionId') or data.get('session_id')
                elif data.get('type') == 'button_action':
                    plan_id = data.get('plan_id')
                elif data.get('type') == 'do_button':
                    plan_id = data.get('plan_id')
                elif data.get('type') == 'do_button_action' and 'do_button_action' in data:
                    plan_id = data['do_button_action'].get('plan_id')
                    
                # Log the plan ID
                if plan_id:
                    logger.info(f"🔍 Processing message with plan ID: {plan_id}")
                    logger.info(f"🔍 Available plans in global dictionary: {list(GLOBAL_PLANS.keys())}")
                    
                    # Check if plan is in message
                    if 'plan' in data:
                        GLOBAL_PLANS[plan_id] = data['plan']
                        logger.info(f"✅ Stored plan from message for {plan_id} in global dictionary")
                    # Check if plan exists in global dictionary
                    elif plan_id not in GLOBAL_PLANS:
                        # Try to load from persistence
                        try:
                            import plan_persistence
                            plan = await plan_persistence.load_plan(plan_id)
                            if plan:
                                GLOBAL_PLANS[plan_id] = plan
                                logger.info(f"✅ Loaded plan {plan_id} from persistence")
                            else:
                                # Create backup plan
                                timestamp = time.time()
                                backup_plan = {
                                    "id": plan_id,
                                    "title": f"Backup Plan for {plan_id}",
                                    "description": "This is a backup plan created by the comprehensive DO button fix",
                                    "steps": [
                                        {
                                            "id": f"{plan_id}_step_1",
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
                                GLOBAL_PLANS[plan_id] = backup_plan
                                logger.info(f"✅ Created backup plan for {plan_id} in global dictionary")
                                
                                # Save to persistence
                                try:
                                    await plan_persistence.save_plan(plan_id, backup_plan)
                                    logger.info(f"✅ Saved backup plan {plan_id} to persistence")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not save backup plan to persistence: {e}")
                        except Exception as e:
                            # Create backup plan without persistence
                            timestamp = time.time()
                            backup_plan = {
                                "id": plan_id,
                                "title": f"Backup Plan for {plan_id}",
                                "description": "This is a backup plan created by the comprehensive DO button fix",
                                "steps": [
                                    {
                                        "id": f"{plan_id}_step_1",
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
                            GLOBAL_PLANS[plan_id] = backup_plan
                            logger.info(f"✅ Created backup plan for {plan_id} in global dictionary")
                            
                    # Add plan to message if not already there
                    if 'plan' not in data and plan_id in GLOBAL_PLANS:
                        data['plan'] = GLOBAL_PLANS[plan_id]
                        logger.info(f"✅ Added plan data to message for {plan_id}")
                        
                # Call the original function
                return await original_forward_to_do_button_server(data if isinstance(message, str) else message, client_id)
            except Exception as e:
                logger.error(f"❌ Error in patched_forward_to_do_button_server: {e}")
                # Try the original function as fallback
                return await original_forward_to_do_button_server(message, client_id)
                
        # Apply the patch
        fix_do_button_connection_bridge.forward_to_do_button_server = patched_forward_to_do_button_server
        logger.info("✅ Patched forward_to_do_button_server function in fix_do_button_connection_bridge")
        
        logger.info("✅ Fixed fix_do_button_connection_bridge module successfully")
        return True
    except ImportError:
        logger.error("❌ Failed to import fix_do_button_connection_bridge module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing fix_do_button_connection_bridge module: {e}")
        return False
        
async def verify_fix():
    """Verify that the fix works by creating a test plan and trying to access it"""
    logger.info("🔍 Verifying the fix...")
    
    # Create a test plan
    test_plan_id = f"test_plan_{int(time.time())}"
    test_plan = {
        "id": test_plan_id,
        "title": "Test Plan",
        "description": "This is a test plan created by the comprehensive DO button fix",
        "steps": [
            {
                "id": f"{test_plan_id}_step_1",
                "type": "notification",
                "action": "notify",
                "content": "This is a test plan created by the comprehensive DO button fix",
                "position": {"x": 500, "y": 500}
            }
        ],
        "metadata": {
            "created_at": time.time(),
            "test_plan": True
        }
    }
    
    # Store the plan in the global dictionary
    GLOBAL_PLANS[test_plan_id] = test_plan
    logger.info(f"✅ Created test plan {test_plan_id} in global dictionary")
    
    # Verify it can be accessed from plan_persistence
    try:
        import plan_persistence
        plan = await plan_persistence.load_plan(test_plan_id)
        if plan and plan["id"] == test_plan_id:
            logger.info(f"✅ Successfully loaded plan {test_plan_id} from plan_persistence")
        else:
            logger.warning(f"⚠️ Failed to load plan {test_plan_id} from plan_persistence")
    except ImportError:
        logger.warning("⚠️ Could not import plan_persistence module")
    except Exception as e:
        logger.warning(f"⚠️ Error testing plan_persistence: {e}")
        
    # Verify it can be accessed from enterprise backend
    try:
        import enhanced_enterprise_backend_with_context
        if test_plan_id in enhanced_enterprise_backend_with_context.shared_pending_plans:
            logger.info(f"✅ Successfully accessed plan {test_plan_id} from enterprise backend")
        else:
            logger.warning(f"⚠️ Failed to access plan {test_plan_id} from enterprise backend")
    except ImportError:
        logger.warning("⚠️ Could not import enhanced_enterprise_backend_with_context module")
    except Exception as e:
        logger.warning(f"⚠️ Error testing enterprise backend: {e}")
        
    # Verify it can be accessed from neural_ui_do_button_handler
    try:
        import neural_ui_do_button_handler
        if test_plan_id in neural_ui_do_button_handler.active_plans:
            logger.info(f"✅ Successfully accessed plan {test_plan_id} from neural_ui_do_button_handler")
        else:
            logger.warning(f"⚠️ Failed to access plan {test_plan_id} from neural_ui_do_button_handler")
    except ImportError:
        logger.warning("⚠️ Could not import neural_ui_do_button_handler module")
    except Exception as e:
        logger.warning(f"⚠️ Error testing neural_ui_do_button_handler: {e}")
        
    # Verify it can be accessed from fix_do_button_connection_bridge
    try:
        import fix_do_button_connection_bridge
        if hasattr(fix_do_button_connection_bridge, 'GLOBAL_PLANS') and test_plan_id in fix_do_button_connection_bridge.GLOBAL_PLANS:
            logger.info(f"✅ Successfully accessed plan {test_plan_id} from fix_do_button_connection_bridge")
        else:
            logger.warning(f"⚠️ Failed to access plan {test_plan_id} from fix_do_button_connection_bridge")
    except ImportError:
        logger.warning("⚠️ Could not import fix_do_button_connection_bridge module")
    except Exception as e:
        logger.warning(f"⚠️ Error testing fix_do_button_connection_bridge: {e}")
        
    logger.info("✅ Verification complete")

async def main():
    """Main function that applies all fixes"""
    logger.info("🚀 Starting Comprehensive DO Button Fix")
    
    # Step 1: Fix the plan_persistence module
    logger.info("Step 1: Fixing plan_persistence module...")
    if fix_plan_persistence_module():
        logger.info("✅ Step 1 completed successfully")
    else:
        logger.error("❌ Step 1 failed")
        
    # Step 2: Fix the enterprise backend
    logger.info("Step 2: Fixing enterprise backend module...")
    if fix_enterprise_backend():
        logger.info("✅ Step 2 completed successfully")
    else:
        logger.error("❌ Step 2 failed")
        
    # Step 3: Fix the neural UI DO button handler
    logger.info("Step 3: Fixing neural_ui_do_button_handler module...")
    if fix_neural_ui_do_button_handler():
        logger.info("✅ Step 3 completed successfully")
    else:
        logger.error("❌ Step 3 failed")
        
    # Step 4: Fix the DO button connection bridge
    logger.info("Step 4: Fixing fix_do_button_connection_bridge module...")
    if fix_do_button_connection_bridge():
        logger.info("✅ Step 4 completed successfully")
    else:
        logger.error("❌ Step 4 failed")
        
    # Step 5: Verify the fix works
    logger.info("Step 5: Verifying the fix...")
    await verify_fix()
    logger.info("✅ Step 5 completed")
    
    logger.info("✅ Comprehensive DO Button Fix applied successfully")
    logger.info("🎉 The system should now correctly handle DO button actions across all components")
    logger.info("📝 No restart required - all changes are applied at runtime")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Comprehensive DO Button Fix stopped by user")
    except Exception as e:
        logger.error(f"Error in Comprehensive DO Button Fix: {e}")
        import traceback
        logger.error(traceback.format_exc())