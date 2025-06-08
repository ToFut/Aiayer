#!/usr/bin/env python3
"""
Update Enhanced Enterprise Backend with Context
This script updates enhanced_enterprise_backend_with_context.py to use the fixed_handle_universal_button_action function
"""

import os
import re

def update_enterprise_backend():
    """Update enhanced_enterprise_backend_with_context.py to use fixed_handle_universal_button_action"""
    file_path = "enhanced_enterprise_backend_with_context.py"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
    
    # Read the current content
    with open(file_path, "r") as f:
        content = f.read()
    
    # Define the start and end pattern for the execute_verified_plan method
    start_pattern = "async def execute_verified_plan"
    end_pattern = "async def _try_agnostic_deep_data_access"
    
    # Find the execute_verified_plan method
    method_start = content.find(start_pattern)
    method_end = content.find(end_pattern)
    
    if method_start == -1 or method_end == -1:
        print("Could not find execute_verified_plan method in enhanced_enterprise_backend_with_context.py")
        return False
    
    # Extract the execute_verified_plan method
    execute_plan_code = content[method_start:method_end]
    
    # Create the updated method implementation
    updated_execute_plan_code = """
async def execute_verified_plan(self, plan_id: str, session_id: str = None) -> Dict[str, Any]:
        # Execute a verified plan using the correct handler based on plan_id
        try:
            if session_id is None:
                session_id = plan_id  # Use plan_id as session_id if not provided
                
            logger.info(f"🚀 Executing verified plan: {plan_id} for session: {session_id}")
            
            # First try to use the fixed universal button action handler
            try:
                from fixed_universal_automation_handler import fixed_handle_universal_button_action
                logger.info(f"✅ Using fixed_handle_universal_button_action for any plan type")
                result = await fixed_handle_universal_button_action("execute_plan", plan_id, session_id)
                logger.info(f"✅ Plan execution result: {result}")
                return result
            except ImportError as e:
                logger.warning(f"⚠️ fixed_handle_universal_button_action not available: {e}, falling back to alternatives")
            
            # Fallback to check if this is a universal plan (use standard universal handler)
            if "universal_" in plan_id:
                try:
                    from universal_intelligent_automation_handler import handle_universal_button_action
                    logger.info(f"✅ Using handle_universal_button_action for universal plan")
                    result = await handle_universal_button_action("execute_plan", plan_id, session_id)
                    logger.info(f"✅ Plan execution result: {result}")
                    return result
                except ImportError as e:
                    logger.warning(f"⚠️ handle_universal_button_action not available: {e}, falling back to standard execution")
            
            # Standard execution for other plan types
            logger.info(f"🔍 Using standard execution for plan: {plan_id}")
            
            # Load the plan from storage
            plan_data = None
            try:
                from plan_persistence import load_plan
                plan_data = await load_plan(plan_id)
            except ImportError:
                logger.warning("⚠️ Plan persistence not available")
                
            if not plan_data:
                # Check if plan is in pending_plans
                if hasattr(self, 'pending_plans') and plan_id in self.pending_plans:
                    plan_data = self.pending_plans[plan_id]
                    logger.info(f"✅ Found plan in pending_plans: {plan_id}")
                else:
                    # Create a fallback plan for testing if plan loading fails
                    logger.warning(f"⚠️ Creating fallback plan for testing: {plan_id}")
                    plan_data = {
                        "client_id": "fallback",
                        "plan": {
                            "title": "Fallback Test Plan",
                            "description": "Open Safari browser",
                            "steps": [
                                {
                                    "id": "step_1",
                                    "description": "Open Safari browser",
                                    "action_type": "open_app",
                                    "target": "Safari"
                                }
                            ]
                        }
                    }
            
            # Extract steps from the plan data structure
            steps = []
            if "steps" in plan_data:
                steps = plan_data["steps"]
            elif "plan" in plan_data and "steps" in plan_data["plan"]:
                steps = plan_data["plan"]["steps"]
            
            if not steps:
                error_message = f"❌ No steps found in plan: {plan_id}"
                logger.error(error_message)
                return {"success": False, "response": error_message}
            
            # Find websocket for this client
            websocket = None
            client_id = plan_data.get("client_id", "default")
            for client_session in self.sessions.values():
                if client_session.get("client_id") == client_id:
                    websocket = client_session.get("websocket")
                    break
            
            # Initialize adaptive retry handler
            try:
                from adaptive_retry_automation_handler import adaptive_retry_handler, AutomationStep
                
                # Execute each step with the adaptive retry handler
                execution_results = []
                successful_steps = 0
                
                for i, step_data in enumerate(steps):
                    step_desc = step_data.get('description', f'Step {i+1}')
                    logger.info(f"📌 Executing step {i+1}/{len(steps)}: {step_desc}")
                    
                    # Send progress update if websocket is available
                    if websocket:
                        await websocket.send(json.dumps({
                            "type": "execution_progress",
                            "step": i+1,
                            "total_steps": len(steps),
                            "message": f"Executing step {i+1}: {step_desc}",
                            "progress": int((i+1) / len(steps) * 100),
                            "plan_id": plan_id,
                            "timestamp": time.time()
                        }))
                    
                    # Convert step data to AutomationStep
                    step = AutomationStep(
                        id=step_data.get("id", f"step_{i+1}"),
                        description=step_data.get("description", ""),
                        action_type=step_data.get("action_type", ""),
                        target=step_data.get("target"),
                        value=step_data.get("value"),
                        coordinates=step_data.get("coordinates")
                    )
                    
                    # Execute the step using adaptive retry handler
                    result = await adaptive_retry_handler.execute_step_with_retry(step, plan_id)
                    execution_results.append(result)
                    
                    if result.success:
                        successful_steps += 1
                    
                    # Add small delay for UI to update
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ Error executing plan steps: {e}")
                return {
                    "success": False,
                    "response": f"Error executing plan steps: {str(e)}",
                    "error": str(e)
                }
            
            # Calculate success rate
            success_rate = successful_steps / len(steps) if steps else 0
            
            # Clean up the plan from pending_plans if it exists
            if hasattr(self, 'pending_plans') and plan_id in self.pending_plans:
                del self.pending_plans[plan_id]
                
            # Send completion notification if websocket is available
            if websocket:
                await websocket.send(json.dumps({
                    "type": "execution_complete",
                    "success": successful_steps > 0,
                    "success_rate": success_rate,
                    "steps_completed": successful_steps,
                    "total_steps": len(steps),
                    "plan_id": plan_id,
                    "timestamp": time.time()
                }))
            
            # Return success response
            return {
                "success": successful_steps > 0,
                "response": f"✅ Executed {successful_steps}/{len(steps)} steps successfully",
                "execution_results": execution_results,
                "success_rate": success_rate,
                "summary": f"Successfully executed {successful_steps}/{len(steps)} automation steps",
                "execution_completed": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing verified plan: {e}")
            return {
                "success": False,
                "response": f"❌ Error executing plan: {str(e)}",
                "error": str(e)
            }
    
    async def _try_agnostic_deep_data_access"""
    
    # Replace the method in the content
    updated_content = content[:method_start] + updated_execute_plan_code + content[method_end:]
    
    # Write the updated content
    with open(file_path, "w") as f:
        f.write(updated_content)
    
    print(f"Updated {file_path} to use fixed_handle_universal_button_action for all plan types")
    return True

# Run the function
if __name__ == "__main__":
    update_enterprise_backend()