#!/usr/bin/env python3
"""
Direct test script for the Agent mode in the enhanced enterprise backend
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("direct_agent_test")

async def run_direct_agent_test():
    """Run a direct test of the Agent mode"""
    try:
        # Import the enhanced_enterprise_backend_with_context module
        from enhanced_enterprise_backend_with_context import handle_request
        
        # Test parameters
        session_id = f"test_session_{int(datetime.now().timestamp())}"
        
        # Create a test request
        test_request = {
            "mode": "Agent",
            "query": "search for Segev in Notepad",
            "session_id": session_id
        }
        
        # Send the request
        logger.info(f"Sending direct Agent mode request: {test_request}")
        response = await handle_request(test_request)
        
        # Log and analyze the response
        logger.info(f"Received response: {json.dumps(response, indent=2)}")
        
        # Check if the response looks like it's from the real_agent_automation_handler or the fixed_universal_automation_handler
        response_text = response.get("response", "")
        
        if "AUTOMATION EXECUTION PLAN" in response_text:
            logger.info("✅ Response appears to be from fixed_universal_automation_handler")
        elif "Process Request" in response_text:
            logger.error("❌ Response appears to be from real_agent_automation_handler")
        else:
            logger.warning("⚠️ Cannot determine the source of the response")
        
        # Return success
        return True
    except Exception as e:
        logger.error(f"Error in direct agent test: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(run_direct_agent_test())
    print(f"Direct agent test result: {'SUCCESS' if success else 'FAILED'}")