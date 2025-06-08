#\!/usr/bin/env python3
"""
Test script to verify Agent mode handling in the brain router
"""

import asyncio
import sys
import os
import logging
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("agent_mode_test")

async def test_agent_mode():
    """Test the brain router Agent mode handling"""
    try:
        logger.info("Adding project root to Python path...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(script_dir)
        logger.info("Python path: %s", sys.path)
        
        # Import the brain router
        logger.info("Importing brain router...")
        from brain.core.brain_router import (
            ChatRequest, ChatMode, BrainResponse, 
            get_brain_router, process_chat_request
        )
        
        # Wait for brain router to initialize
        logger.info("Getting brain router instance...")
        brain_router = await get_brain_router()
        logger.info("Brain router instance created")
        
        # Create a test request for Agent mode
        test_request = ChatRequest(
            mode=ChatMode.AGENT,
            query="search Segev in Notepad",
            user_id="test_user",
            session_id=f"test_session_{int(time.time())}",
            timestamp=time.time(),
            context={}
        )
        
        # Process the request
        logger.info("Processing Agent mode request: %s", test_request.query)
        logger.info("Testing direct brain router method first...")
        
        # First try direct brain router method
        response = await brain_router._handle_agent_mode(test_request)
        
        logger.info("Direct agent mode response: %s", response)
        logger.info("Response type: %s", type(response))
        logger.info("Response content: %s", response.response)
        logger.info("Resources used: %s", response.resources_used)
        
        # Check if the response looks like it's from the real_agent_automation_handler or the fixed_universal_automation_handler
        if "AUTOMATION EXECUTION PLAN" in response.response:
            logger.info("✅ Response appears to be from fixed_universal_automation_handler")
        elif "Process Request" in response.response:
            logger.error("❌ Response appears to be from real_agent_automation_handler")
        else:
            logger.warning("⚠️ Cannot determine the source of the response")
        
        return True
    except Exception as e:
        logger.error("Error testing Agent mode: %s", str(e), exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent_mode())
    print("Agent mode test result:", "SUCCESS" if success else "FAILED")
