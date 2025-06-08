#!/usr/bin/env python3
"""
Direct plan execution script - bypasses LLM for testing execution flow.
"""

import asyncio
import logging
import json
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Import direct execution function
        from universal_intelligent_automation_handler import direct_execute_plan
        
        # Create a test plan ID
        plan_id = "universal_test_safari_plan"
        session_id = "test_session"
        
        # Execute the plan directly
        logger.info(f"🚀 Executing plan directly: {plan_id}")
        result = await direct_execute_plan(plan_id, session_id)
        
        logger.info(f"Result: {json.dumps(result, indent=2)[:500]}...")
        return result.get("success", False)
    except Exception as e:
        logger.error(f"Error in direct execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing direct plan execution...\n")
    
    # Run test
    success = asyncio.run(main())
    
    print(f"\n{'✅' if success else '❌'} Direct execution test: {'PASSED' if success else 'FAILED'}\n")
    
    if success:
        print("🎉 Test passed! The direct execution flow is working correctly.")
        print("This confirms that the execution path works when properly called.")
        print("Your WebSocket handler should be able to call this function successfully.")
        print("\nTo trigger this in the overlay, try clicking DO with the same plan ID structure.")
    else:
        print("⚠️ Test failed. The execution flow still has issues that need to be fixed.")
    
    sys.exit(0 if success else 1)
