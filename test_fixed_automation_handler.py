#!/usr/bin/env python3
"""
Test script to directly test the fixed universal automation handler
"""

import asyncio
import json
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_automation_handler():
    """Test the fixed universal automation handler directly"""
    
    try:
        # Import the fixed universal automation handler
        from fixed_universal_automation_handler import fixed_handle_universal_automation
        logger.info("✅ Successfully imported fixed_handle_universal_automation")
        
        # Test query
        test_query = "search for cats on google"
        session_id = f"test_session_{int(time.time())}"
        logger.info(f"Testing automation handler with query: {test_query}")
        
        # Execute the handler
        start_time = time.time()
        result = await fixed_handle_universal_automation(test_query, session_id)
        processing_time = time.time() - start_time
        
        logger.info(f"Automation handler processing time: {processing_time:.2f}s")
        
        # Check the result
        if result.get("success", False):
            logger.info("✅ Automation handler returned success")
        else:
            logger.warning("⚠️ Automation handler returned failure")
            
        plan_id = result.get("plan_id")
        if plan_id:
            logger.info(f"✅ Plan ID: {plan_id}")
        else:
            logger.warning("⚠️ No plan ID in result")
            
        # Print summary
        print("\n" + "="*50)
        print("FIXED AUTOMATION HANDLER TEST")
        print("="*50)
        print(f"Query: {test_query}")
        print(f"Success: {'✅' if result.get('success', False) else '❌'}")
        print(f"Plan ID: {result.get('plan_id', 'none')}")
        print(f"Processing time: {processing_time:.2f}s")
        
        print("\nResponse preview (first 300 chars):")
        print("-"*50)
        response_text = result.get("response", "")
        print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
        print("-"*50)
        
        plan_mentions = "plan" in response_text.lower()
        automation_mentions = "automation" in response_text.lower()
        
        print(f"Response mentions plan: {'✅' if plan_mentions else '❌'}")
        print(f"Response mentions automation: {'✅' if automation_mentions else '❌'}")
        print(f"\nOverall test result: {'✅ PASSED' if result.get('success') and (plan_mentions or automation_mentions) else '❌ FAILED'}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        print(f"\n❌ TEST FAILED: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_automation_handler())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")