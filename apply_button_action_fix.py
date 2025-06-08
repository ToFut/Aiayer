#!/usr/bin/env python3
"""
Simple script to apply the fix for the DO button action in the overlay chat.
This addresses the issue where clicking DO doesn't trigger the automation execution.
"""

import sys

def apply_fix():
    """Apply the fix to the enhanced_enterprise_backend_with_context.py file"""
    try:
        # Path to the file
        file_path = "/Users/segevbin/Desktop/SensAI/Aiayer/enhanced_enterprise_backend_with_context.py"
        
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Define the pattern to search for and the replacement
        old_code = """                # Execute the stored plan using appropriate handler
                # Check if this is a fast automation plan
                if plan_data.get("fast"):
                    # Use fast automation handler for execution
                    logger.info("⚡ Executing with Fast Automation Handler")
                    plan_id = plan_data.get("plan_id", session_id)
                    automation_result = await fast_universal_automation_handler.handle_button_action(
                        "execute_plan", plan_id, session_id
                    )
                else:
                    # Use regular automation handler
                    logger.info("🔧 Executing with Legacy Automation Handler")
                    execution_context = plan_data["context"].copy()
                    execution_context["stored_plan"] = plan_data["plan"]
                    
                    automation_result = await self.automation_handler.handle_user_instruction(
                        plan_data["context"]["user_prompt"], 
                        execution_context
                    )"""

        new_code = """                # Execute the stored plan using appropriate handler
                # First, check if this is a universal automation plan
                if "universal_" in session_id and UNIVERSAL_AVAILABLE:
                    # Use Universal Intelligent Automation Handler
                    logger.info("🧠 Executing with Universal Intelligent Automation Handler")
                    plan_id = plan_data.get("plan_id", session_id)
                    automation_result = await universal_automation_handler.handle_button_action(
                        "execute_plan", plan_id, session_id
                    )
                # Next, check if this is a fast automation plan
                elif plan_data.get("fast"):
                    # Use fast automation handler for execution
                    logger.info("⚡ Executing with Fast Automation Handler")
                    plan_id = plan_data.get("plan_id", session_id)
                    automation_result = await fast_universal_automation_handler.handle_button_action(
                        "execute_plan", plan_id, session_id
                    )
                else:
                    # Use regular automation handler
                    logger.info("🔧 Executing with Legacy Automation Handler")
                    execution_context = plan_data["context"].copy()
                    execution_context["stored_plan"] = plan_data["plan"]
                    
                    automation_result = await self.automation_handler.handle_user_instruction(
                        plan_data["context"]["user_prompt"], 
                        execution_context
                    )"""
        
        # Replace the code
        if old_code in content:
            new_content = content.replace(old_code, new_code)
            
            # Write the modified content back to the file
            with open(file_path, 'w') as file:
                file.write(new_content)
            
            print("✅ Fix applied successfully!")
            print("The overlay chat's DO button should now work correctly with universal automation plans.")
            return True
        else:
            print("⚠️ Could not find the code to replace. The file may have been modified.")
            return False
    
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False

if __name__ == "__main__":
    success = apply_fix()
    sys.exit(0 if success else 1)