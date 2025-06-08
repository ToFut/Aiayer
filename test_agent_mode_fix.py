#!/usr/bin/env python3
"""
Test script for verifying Agent Mode is working correctly

This script tests the fixes applied to:
1. universal_intelligent_automation_handler.py
2. brain_router.py 
3. WebSocket interface

It directly tests the Agent Mode functionality through:
- Direct handler invocation to test fixes without system restart
- WebSocket interface to test end-to-end functionality
"""

import asyncio
import json
import websockets
import time
import logging
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_universal_automation_handler():
    """Test the universal_intelligent_automation_handler directly"""
    logger.info("🧪 Testing universal_intelligent_automation_handler directly...")
    
    try:
        # Import the handler we fixed
        from universal_intelligent_automation_handler import handle_universal_automation
        
        # Test with a simple query
        simple_query = "How can I automate searching for images of cats on Google?"
        logger.info(f"🔍 Testing with query: {simple_query}")
        
        # Call the handler
        session_id = f"test_session_{int(time.time())}"
        result = await handle_universal_automation(simple_query, session_id)
        
        # Log the result
        logger.info(f"✅ Result success: {result.get('success', False)}")
        logger.info(f"📋 Has execution plan: {'Yes' if result.get('execution_plan') else 'No'}")
        
        # Check if the response looks like a template or real LLM response
        response_text = result.get('response', '')
        is_template = "🎯 AUTOMATION EXECUTION PLAN" in response_text and "Step 1:" in response_text
        
        if is_template:
            logger.warning("⚠️ Response appears to be a template rather than real LLM content")
        else:
            logger.info("✨ Response appears to be real LLM-generated content")
            
        logger.info(f"💬 Response preview: {response_text[:100]}...")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Error testing universal_automation_handler: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def test_brain_router():
    """Test the brain_router with Agent Mode"""
    logger.info("🧪 Testing brain_router with Agent Mode...")
    
    try:
        # Import the brain router
        from brain.core.brain_router import BrainRouter, BrainRequest
        
        # Create a brain router instance
        router = BrainRouter()
        
        # Create a test request
        test_request = BrainRequest(
            query="How do I automate searching for vacation destinations?",
            mode="agent",
            session_id=f"test_session_{int(time.time())}",
            metadata={"test": True}
        )
        
        logger.info(f"📤 Sending request to brain router: {test_request.query}")
        
        # Process the request
        response = await router.process_request(test_request)
        
        # Log the result
        logger.info(f"✅ Response success: {response.success}")
        logger.info(f"🔠 Mode used: {response.mode_used}")
        logger.info(f"⏱️ Processing time: {response.processing_time:.2f} seconds")
        logger.info(f"🔧 Resources used: {response.resources_used}")
        
        # Check if the response has an execution plan
        if hasattr(response, 'execution_plan') and response.execution_plan:
            logger.info("📝 Response includes an execution plan")
            if isinstance(response.execution_plan, dict):
                logger.info(f"🔢 Plan has {len(response.execution_plan.get('steps', []))} steps")
        else:
            logger.warning("⚠️ Response does not include an execution plan")
        
        # Check if the response looks like a template
        is_template = "🎯 AUTOMATION EXECUTION PLAN" in response.response and "Step 1:" in response.response
        
        if is_template:
            logger.warning("⚠️ Response appears to be a template rather than real LLM content")
        else:
            logger.info("✨ Response appears to be real LLM-generated content")
            
        logger.info(f"💬 Response preview: {response.response[:100]}...")
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Error testing brain_router: {e}")
        logger.error(traceback.format_exc())
        return None

async def test_with_different_queries():
    """Test with different types of queries to ensure robustness"""
    logger.info("🧪 Testing with different query types...")
    
    queries = [
        "How do I automate opening my email and sending a message?",
        "Can you help me automate checking the weather?",
        "I want to automate searching for recipes",
        "Help me automate a Google search for local restaurants",
        "Create a plan to automate checking my calendar"
    ]
    
    try:
        # Import the handler we fixed
        from universal_intelligent_automation_handler import handle_universal_automation
        
        results = []
        for query in queries:
            logger.info(f"🔍 Testing with query: {query}")
            
            # Call the handler
            result = await handle_universal_automation(query, f"test_session_{int(time.time())}")
            
            # Log basic info
            success = result.get('success', False)
            has_plan = bool(result.get('execution_plan'))
            logger.info(f"✓ Query: '{query}' - Success: {success}, Has Plan: {has_plan}")
            
            results.append({
                "query": query,
                "success": success,
                "has_plan": has_plan
            })
        
        # Summarize results
        success_count = sum(1 for r in results if r["success"])
        plan_count = sum(1 for r in results if r["has_plan"])
        
        logger.info(f"📊 Test summary: {success_count}/{len(results)} successful, {plan_count}/{len(results)} have plans")
        return results
    
    except Exception as e:
        logger.error(f"❌ Error in multi-query test: {e}")
        logger.error(traceback.format_exc())
        return []

async def test_agent_mode_websocket():
    """Test Agent mode functionality via WebSocket"""
    logger.info("🧪 Starting Agent mode WebSocket test...")
    
    try:
        # Connect to the backend server
        uri = "ws://localhost:8767"
        logger.info(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend server")
            
            # Wait for connection established message
            initial_response = await websocket.recv()
            logger.info(f"👋 Received connection message: {initial_response[:100]}...")
            
            # Generate a unique session ID
            session_id = f"test_{int(time.time())}"
            
            # Send Agent mode request
            test_message = "Open Safari and search for 'python websockets library'"
            
            request = {
                "type": "chat_request",
                "mode": "Agent",  # Important: this is the Agent mode
                "message": test_message,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📤 Sending Agent mode request: {test_message}")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            logger.info(f"📥 Received response: {response[:200]}...")
            
            # Analyze response
            if response_data.get("type") == "agent_automation_plan":
                logger.info("✅ SUCCESS! Received proper Agent mode automation plan!")
                logger.info(f"🎯 Plan details: {json.dumps(response_data, indent=2)}")
                
                # Check if it looks like a template
                plan_text = response_data.get("payload", {}).get("plan_text", "")
                is_template = "🎯 AUTOMATION EXECUTION PLAN" in plan_text and "Step 1:" in plan_text
                
                if is_template:
                    logger.warning("⚠️ Plan appears to be a template rather than real LLM content")
                else:
                    logger.info("✨ Plan appears to be real LLM-generated content")
                
                return True
            else:
                logger.error(f"❌ ERROR! Did not receive an agent_automation_plan message")
                logger.error(f"📋 Response type: {response_data.get('type')}")
                logger.error(f"📋 Response payload: {response_data.get('payload')}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Agent mode: {e}")
        logger.error(traceback.format_exc())
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Agent Mode fix tests")
    
    test_results = {}
    
    # Test the universal automation handler directly
    logger.info("\n==== 🧪 TESTING UNIVERSAL AUTOMATION HANDLER ====")
    handler_result = await test_universal_automation_handler()
    test_results["universal_handler"] = handler_result.get("success", False) if handler_result else False
    
    # Test the brain router with Agent Mode
    logger.info("\n==== 🧪 TESTING BRAIN ROUTER ====")
    router_result = await test_brain_router()
    test_results["brain_router"] = router_result.success if router_result else False
    
    # Test with different queries
    logger.info("\n==== 🧪 TESTING WITH DIFFERENT QUERIES ====")
    query_results = await test_with_different_queries()
    test_results["different_queries"] = sum(1 for r in query_results if r["success"]) > 0
    
    # Test via WebSocket interface
    logger.info("\n==== 🧪 TESTING WEBSOCKET INTERFACE ====")
    websocket_result = await test_agent_mode_websocket()
    test_results["websocket"] = websocket_result
    
    # Print summary
    logger.info("\n==== 📊 TEST SUMMARY ====")
    for test_name, result in test_results.items():
        logger.info(f"{'✅' if result else '❌'} {test_name}: {'PASS' if result else 'FAIL'}")
    
    overall_success = all(test_results.values())
    logger.info(f"\n{'🎉 ALL TESTS PASSED!' if overall_success else '⚠️ SOME TESTS FAILED!'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)