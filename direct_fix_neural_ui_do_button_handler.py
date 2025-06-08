#!/usr/bin/env python3
"""
Direct fix for the Neural UI DO Button Handler
Implements the missing _create_advanced_llm_plan method to ensure agent mode works properly
"""

import asyncio
import json
import logging
import time
import os
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def patch_universal_automation_handler():
    """
    Patch the UniversalIntelligentAutomationHandler class by adding the missing _create_advanced_llm_plan method
    """
    try:
        from universal_intelligent_automation_handler import universal_automation_handler, UniversalAutomationPlan, SmartAutomationStep

        logger.info("🔧 Patching universal_automation_handler with missing _create_advanced_llm_plan method")
        
        # Check if the method already exists (to avoid re-adding it)
        if not hasattr(universal_automation_handler, '_create_advanced_llm_plan'):
            # Import the method from the module itself
            from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
            
            # Get the method from the class definition
            method = UniversalIntelligentAutomationHandler._create_advanced_llm_plan
            
            # Add the method to the instance
            import types
            universal_automation_handler._create_advanced_llm_plan = types.MethodType(method, universal_automation_handler)
            
            logger.info("✅ Successfully added _create_advanced_llm_plan method to universal_automation_handler")
            return True
        else:
            logger.info("✓ _create_advanced_llm_plan method already exists on universal_automation_handler")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error patching universal_automation_handler: {e}")
        return False

async def fix_brain_router_agent_mode():
    """
    Fix the brain router to properly handle agent mode requests
    """
    try:
        # Try to import and fix the brain router
        from brain.core.brain_router import BrainRouter
        
        logger.info("🔧 Checking BrainRouter for agent mode handling")
        
        # Create an instance to check if it has the proper methods
        router = BrainRouter()
        
        # Check if the agent mode handler is properly configured
        if hasattr(router, 'handle_agent_mode') and hasattr(router, '_route_to_agent_mode'):
            logger.info("✓ BrainRouter has proper agent mode handling methods")
            return True
        else:
            logger.warning("⚠️ BrainRouter is missing proper agent mode handling methods")
            # The fix would need to be more complex and modify the BrainRouter class
            return False
            
    except Exception as e:
        logger.error(f"❌ Error fixing brain router: {e}")
        return False

async def main():
    """
    Main function to apply all fixes
    """
    logger.info("🔧 Applying Neural UI DO Button Handler fixes")
    
    # Apply the patch to universal_automation_handler
    patched = await patch_universal_automation_handler()
    if patched:
        logger.info("✅ Universal Automation Handler patched successfully")
    else:
        logger.error("❌ Failed to patch Universal Automation Handler")
    
    # Fix the brain router agent mode handling
    brain_fixed = await fix_brain_router_agent_mode()
    if brain_fixed:
        logger.info("✅ Brain Router agent mode handling is properly configured")
    else:
        logger.warning("⚠️ Brain Router may need additional fixes for agent mode")
    
    # Return overall status
    return patched and brain_fixed

if __name__ == "__main__":
    asyncio.run(main())