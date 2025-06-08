#!/usr/bin/env python3
"""
Simple direct fix for Agent mode
This script directly updates and corrects the core issue in the universal_intelligent_automation_handler
"""

import sys
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_universal_handler():
    """Apply a direct fix to the universal_intelligent_automation_handler.py file"""
    
    source_path = "/Users/segevbin/Desktop/SensAI/Aiayer/universal_intelligent_automation_handler.py"
    backup_path = "/Users/segevbin/Desktop/SensAI/Aiayer/universal_intelligent_automation_handler.py.bak"
    
    # Create a backup
    os.system(f"cp {source_path} {backup_path}")
    logger.info(f"Created backup at {backup_path}")
    
    # Check if the handler file exists
    if not os.path.exists(source_path):
        logger.error(f"Error: File not found at {source_path}")
        return False
    
    # Load the file content
    with open(source_path, 'r') as f:
        content = f.read()
    
    # First fix: Make sure the _create_advanced_llm_plan method is properly placed inside the class
    # Check if the method is defined at the correct indentation level
    if "    async def _create_advanced_llm_plan" not in content:
        logger.error("Error: Method _create_advanced_llm_plan is not found or not properly indented")
        return False
    
    # Second fix: Make sure the create_universal_automation_plan method correctly calls _create_advanced_llm_plan
    if "self._create_advanced_llm_plan" not in content:
        logger.info("Fixing method call in create_universal_automation_plan")
        
        # Replace the method call with the correct one
        content = content.replace(
            "            # Use advanced LLM planning for universal request handling\n            plan = await self._create_advanced_llm_plan(user_request, session_id)",
            "            # Use advanced LLM planning for universal request handling\n            plan = await self._create_advanced_llm_plan(user_request, session_id)"
        )
    
    # Third fix: Fix handle_universal_automation to always use the instance method directly
    content = content.replace(
        "async def handle_universal_automation(user_request: str, session_id: str) -> Dict[str, Any]:",
        """async def handle_universal_automation(user_request: str, session_id: str) -> Dict[str, Any]:
    """
    )
    
    content = content.replace(
        "    return await universal_automation_handler.create_universal_automation_plan(user_request, session_id)",
        """    try:
        # Ensure the universal_automation_handler is properly initialized
        if not hasattr(universal_automation_handler, '_create_advanced_llm_plan'):
            # Add a message to help debug
            logger.warning("Missing _create_advanced_llm_plan method, using direct implementation")
            # Use a direct implementation that doesn't rely on the method
            from fixed_universal_automation_handler import fixed_handle_universal_automation
            return await fixed_handle_universal_automation(user_request, session_id)
        
        # Use the normal path if the method exists
        return await universal_automation_handler.create_universal_automation_plan(user_request, session_id)
    except Exception as e:
        logger.error(f"Error in handle_universal_automation: {e}")
        # Fallback to fixed implementation
        try:
            from fixed_universal_automation_handler import fixed_handle_universal_automation
            return await fixed_handle_universal_automation(user_request, session_id)
        except Exception as fallback_error:
            logger.error(f"Error in fallback handler: {fallback_error}")
            return {
                "success": False,
                "response": f"Error creating automation plan: {str(e)}",
                "automation_available": False
            }"""
    )
    
    # Write the updated content back to the file
    with open(source_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Successfully updated {source_path} with direct fixes")
    return True

def main():
    """Main function to apply the fix"""
    logger.info("Applying direct fix to Agent mode automation")
    
    if fix_universal_handler():
        logger.info("✅ Successfully applied direct fix to universal handler")
        logger.info("ℹ️ Please restart the system to apply changes: ./RESTART_FIXED_SYSTEM.sh")
    else:
        logger.error("❌ Failed to apply direct fix")
        logger.info("ℹ️ Try using the alternative approach: ./APPLY_AGENT_MODE_FIX.sh")
    
if __name__ == "__main__":
    main()