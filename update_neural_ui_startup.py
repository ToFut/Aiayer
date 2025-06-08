#!/usr/bin/env python3
"""
Update START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh to integrate the agent mode fixes
This script modifies the startup script to apply the agent mode fixes before starting the backend.
"""

import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_startup_script():
    """Update the startup script to include agent mode fixes"""
    
    # Read the original startup script
    with open("START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh", "r") as f:
        content = f.read()
    
    # Find the section where the backend is started
    backend_start_section = "# Start the enhanced enterprise backend"
    backend_start_index = content.find(backend_start_section)
    
    if backend_start_index == -1:
        logger.error("❌ Could not find backend start section in the script")
        return False
    
    # Find the line where python3 enhanced_enterprise_backend_with_context.py is called
    python_line_index = content.find("python3 enhanced_enterprise_backend_with_context.py", backend_start_index)
    
    if python_line_index == -1:
        logger.error("❌ Could not find the backend startup command")
        return False
    
    # Find the start of that line
    line_start = content.rfind("\n", 0, python_line_index) + 1
    
    # Extract the line
    line_end = content.find("\n", python_line_index)
    original_line = content[line_start:line_end]
    
    logger.info(f"Found backend start command: {original_line}")
    
    # Add our fix command before starting the backend
    fix_command = "    # Apply Agent Mode LLM and Execution Fix\n    echo \" Applying Agent Mode LLM and Execution Fix...\"\n    python3 fix_agent_mode_llm_and_execution.py || echo \" ⚠️ Warning: Agent Mode fix failed, continuing anyway\"\n    echo \" Agent Mode fixes applied!\"\n    "
    
    # Insert the fix command before the backend start command
    updated_content = content[:line_start] + fix_command + content[line_start:]
    
    # Make sure we run fix_agent_mode_llm_and_execution.py as a command
    
    # Write the updated content back to the file
    with open("START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh", "w") as f:
        f.write(updated_content)
    
    logger.info("✅ Successfully updated START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh to apply Agent Mode fixes")
    
    # Also update STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh to stop the agent mode fixed processes
    try:
        with open("STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh", "r") as f:
            stop_content = f.read()
        
        # Find the section where processes are killed
        kill_section = "# Cleanup any remaining processes"
        kill_section_index = stop_content.find(kill_section)
        
        if kill_section_index == -1:
            logger.warning("⚠️ Could not find kill section in stop script")
        else:
            # Add our agent mode fixed process kill commands
            additional_kill = "pkill -f test_agent_mode_fixed 2>/dev/null || true\n"
            
            # Insert after the kill section
            kill_section_end = stop_content.find("\n", kill_section_index) + 1
            updated_stop_content = stop_content[:kill_section_end] + additional_kill + stop_content[kill_section_end:]
            
            # Write the updated content back to the file
            with open("STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh", "w") as f:
                f.write(updated_stop_content)
            
            logger.info("✅ Successfully updated STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh")
    except Exception as e:
        logger.warning(f"⚠️ Could not update stop script: {e}")
    
    return True

def create_integration_doc():
    """Create documentation for the integration"""
    doc_content = """# Agent Mode LLM and Execution Fix Integration

This document explains how the Agent Mode fixes have been integrated into the enhanced system startup script.

## Overview

The Agent Mode fixes address two main issues:
1. Agent Mode not providing real LLM plans to the overlay chat
2. DO button not executing plans after clicking the execute button

## Integration Details

The fixes have been integrated into the system startup script in the following ways:

1. The `START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh` script now runs `fix_agent_mode_llm_and_execution.py` before starting the enhanced enterprise backend. This ensures that the fixes are applied each time the system starts.

2. The fixes modify:
   - `enhanced_enterprise_backend_with_context.py` - To prioritize using the universal_intelligent_automation_handler which provides real LLM plans
   - `universal_intelligent_automation_handler.py` - To fix LLM initialization with proper async handling
   - The execute_verified_plan method - To properly handle plan loading and execution

## Testing the Integration

To verify that the integration is working:

1. Start the system using `./START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh`
2. Once the system is running, use the Agent Mode in the overlay chat
3. Enter a command like "search for python tutorials on Google"
4. Verify that a real LLM plan is displayed (it should be detailed and AI-generated)
5. Click the "Execute" button
6. Verify that the plan executes correctly

## Troubleshooting

If the Agent Mode still doesn't work correctly:

1. Check the logs for errors:
   ```
   tail -f logs/backend/enhanced_enterprise_8767.log
   ```

2. Run the test script to verify the specific components:
   ```
   python3 test_agent_mode_fixed.py
   ```

3. Try running the fix script manually:
   ```
   python3 fix_agent_mode_llm_and_execution.py
   ```

4. Restart the backend:
   ```
   ./restart_agent_mode_fixed.sh
   ```

If issues persist, please contact the development team for further assistance.
"""
    
    try:
        with open("AGENT_MODE_NEURAL_UI_INTEGRATION.md", "w") as f:
            f.write(doc_content)
        
        logger.info("✅ Created integration documentation: AGENT_MODE_NEURAL_UI_INTEGRATION.md")
    except Exception as e:
        logger.error(f"❌ Error creating integration documentation: {e}")
        return False
    
    return True

def main():
    """Main function to update startup script and create documentation"""
    logger.info("🔧 Updating startup script to integrate Agent Mode fixes")
    
    # Update the startup script
    if update_startup_script():
        logger.info("✅ Startup script updated successfully")
    else:
        logger.error("❌ Failed to update startup script")
    
    # Create integration documentation
    if create_integration_doc():
        logger.info("✅ Integration documentation created successfully")
    else:
        logger.error("❌ Failed to create integration documentation")
    
    logger.info("\n📋 Next Steps:")
    logger.info("1. Run './START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh' to start the system with Agent Mode fixes")
    logger.info("2. Test Agent Mode in the overlay chat")
    logger.info("3. If issues persist, run 'python3 test_agent_mode_fixed.py' for detailed testing")
    
    logger.info("\n✅ Integration completed!")

if __name__ == "__main__":
    main()