#!/usr/bin/env python3
"""
Add Universal Button Action Handler
This script adds a helper function to fixed_universal_automation_handler.py to handle button actions for any inquiry type
"""

import os
import re

def add_helper_function():
    """Add helper function to fixed_universal_automation_handler.py"""
    file_path = "fixed_universal_automation_handler.py"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
    
    # Read the current content
    with open(file_path, "r") as f:
        content = f.read()
    
    # Check if helper function already exists
    if "fixed_handle_universal_button_action" in content:
        print("Helper function already exists, skipping")
        return True
    
    # Find a good place to add the helper function (end of file)
    insert_point = content.rfind("# Monkey patch the original function")
    if insert_point == -1:
        insert_point = len(content)  # Append to end of file
    
    # Helper function to add
    helper_function = """

async def fixed_handle_universal_button_action(action: str, plan_id: str, session_id: str) -> dict:
    # Universal helper function to handle button actions for ANY inquiry type
    try:
        logger.info(f"🔘 Fixed universal button action handler: {action} for plan: {plan_id}")
        
        # Try to use the original handler first
        try:
            from universal_intelligent_automation_handler import handle_universal_button_action
            result = await handle_universal_button_action(action, plan_id, session_id)
            logger.info(f"✅ Successfully called original handle_universal_button_action")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Original handle_universal_button_action failed: {e}")
            # Fall through to our implementation
        
        # Fall back to direct implementation with plan persistence
        try:
            from plan_persistence import load_plan, save_plan
            
            # Load the plan from persistence
            plan_data = await load_plan(plan_id)
            
            if not plan_data:
                logger.error(f"❌ Plan not found: {plan_id}")
                return {
                    "success": False,
                    "response": f"❌ Plan not found: {plan_id}",
                    "interactive": False
                }
            
            # Handle different actions
            if action == "execute_plan" or action == "DO":
                logger.info(f"🚀 Executing plan: {plan_id}")
                
                # Try to use adaptive retry handler for execution
                try:
                    from adaptive_retry_automation_handler import adaptive_retry_handler, AutomationStep
                    
                    # Extract steps from the plan
                    steps = []
                    if "steps" in plan_data:
                        steps = plan_data["steps"]
                    elif "plan" in plan_data and "steps" in plan_data["plan"]:
                        steps = plan_data["plan"]["steps"]
                    
                    # Execute each step
                    execution_results = []
                    successful_steps = 0
                    
                    for i, step_data in enumerate(steps):
                        logger.info(f"📌 Executing step {i+1}/{len(steps)}: {step_data.get('description', '')}")
                        
                        # Convert to AutomationStep
                        step = AutomationStep(
                            id=step_data.get("id", f"step_{i+1}"),
                            description=step_data.get("description", ""),
                            action_type=step_data.get("action_type", ""),
                            target=step_data.get("target", ""),
                            value=step_data.get("value", ""),
                            coordinates=step_data.get("coordinates", None)
                        )
                        
                        # Execute with retry
                        result = await adaptive_retry_handler.execute_step_with_retry(step, plan_id)
                        execution_results.append(result)
                        
                        if result.success:
                            successful_steps += 1
                    
                    # Format response
                    success_rate = successful_steps / len(steps) if steps else 0
                    
                    return {
                        "success": successful_steps > 0,
                        "response": f"✅ Executed {successful_steps}/{len(steps)} steps successfully",
                        "interactive": False,
                        "execution_results": execution_results,
                        "success_rate": success_rate
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error executing plan: {e}")
                    return {
                        "success": False,
                        "response": f"❌ Error executing plan: {str(e)}",
                        "interactive": False
                    }
                    
            elif action == "cancel_plan" or action == "DISMISS":
                logger.info(f"🛑 Cancelling plan: {plan_id}")
                return {
                    "success": True,
                    "response": f"🚫 Plan {plan_id} cancelled",
                    "interactive": False
                }
                
            elif action == "modify_plan" or action == "ADJUST":
                logger.info(f"✏️ Modify plan request: {plan_id}")
                return {
                    "success": True,
                    "response": f"✏️ To modify this plan, please send a new request with your adjustments",
                    "interactive": False
                }
                
            elif action == "simulate_plan" or action == "SIMULATE":
                logger.info(f"🔍 Simulating plan: {plan_id}")
                
                # Extract steps for simulation
                steps = []
                if "steps" in plan_data:
                    steps = plan_data["steps"]
                elif "plan" in plan_data and "steps" in plan_data["plan"]:
                    steps = plan_data["plan"]["steps"]
                
                # Format simulation response
                response = f"🔍 **Simulation of Plan {plan_id}**\\n\\n"
                
                for i, step in enumerate(steps, 1):
                    response += f"{i}. ✅ Would execute: {step.get('description', 'Unknown step')}\\n"
                
                return {
                    "success": True,
                    "response": response,
                    "interactive": False,
                    "simulation": True
                }
                
            else:
                logger.warning(f"❓ Unknown action: {action}")
                return {
                    "success": False,
                    "response": f"❓ Unknown action: {action}",
                    "interactive": False
                }
                
        except Exception as e:
            logger.error(f"❌ Error in fixed_handle_universal_button_action: {e}")
            return {
                "success": False,
                "response": f"❌ Error: {str(e)}",
                "interactive": False
            }
            
    except Exception as e:
        logger.error(f"❌ Critical error in fixed_handle_universal_button_action: {e}")
        return {
            "success": False,
            "response": f"❌ Critical error: {str(e)}",
            "interactive": False
        }
"""
    
    # Add the helper function to the file
    new_content = content[:insert_point] + helper_function + content[insert_point:]
    
    # Write the updated content
    with open(file_path, "w") as f:
        f.write(new_content)
    
    print(f"Added helper function to {file_path}")
    return True

# Run the function
if __name__ == "__main__":
    add_helper_function()