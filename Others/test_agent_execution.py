#!/usr/bin/env python3
"""
Agent Mode Execution Test
Tests Agent mode with real task execution vs just planning
"""

import asyncio
import websockets
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_execution():
    """Test Agent mode with executable tasks"""
    
    # Test queries that should trigger real execution
    execution_tests = [
        "Help me organize my files on the desktop",
        "Clean up temporary files on my system", 
        "Check my system performance and resources",
        "Create a backup of important files",
        "Analyze my system status"
    ]
    
    # Test queries that should fall back to planning
    planning_tests = [
        "Help me become a better programmer",
        "Plan my career development",
        "Suggest ways to improve my workflow"
    ]
    
    ws_url = "ws://localhost:8767"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info(f"🔗 Connected to {ws_url}")
            
            logger.info("\n" + "="*60)
            logger.info("🤖 TESTING AGENT MODE WITH REAL EXECUTION")
            logger.info("="*60)
            
            # Test executable tasks
            logger.info("\n📋 Testing EXECUTABLE Tasks:")
            for i, query in enumerate(execution_tests, 1):
                logger.info(f"\n{i}. Testing: '{query}'")
                result = await test_single_query(websocket, query, "Agent")
                
                # Check if it actually executed or just planned
                if result.get("success"):
                    metadata = result.get("metadata", {})
                    real_execution = metadata.get("real_execution", False)
                    execution_attempted = metadata.get("execution_attempted", False)
                    
                    if real_execution:
                        logger.info("✅ REAL EXECUTION PERFORMED")
                        logger.info(f"   Steps: {metadata.get('steps_completed', 0)}/{metadata.get('total_steps', 0)}")
                        logger.info(f"   Workflow ID: {metadata.get('workflow_id', 'N/A')}")
                    elif execution_attempted:
                        logger.info("⚠️ EXECUTION ATTEMPTED, FELL BACK TO PLANNING")
                        logger.info(f"   Fallback reason: {metadata.get('fallback_to_planning', 'Unknown')}")
                    else:
                        logger.info("📝 PLANNING ONLY (NO EXECUTION ATTEMPTED)")
                        
                    # Show sample response
                    response_preview = result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", "")
                    logger.info(f"   Response: {response_preview}")
                else:
                    logger.info(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
                await asyncio.sleep(2)  # Wait between tests
            
            # Test planning-only tasks
            logger.info(f"\n📝 Testing PLANNING-ONLY Tasks:")
            for i, query in enumerate(planning_tests, 1):
                logger.info(f"\n{i}. Testing: '{query}'")
                result = await test_single_query(websocket, query, "Agent")
                
                if result.get("success"):
                    metadata = result.get("metadata", {})
                    real_execution = metadata.get("real_execution", False)
                    
                    if real_execution:
                        logger.info("⚠️ UNEXPECTED: Real execution for planning task")
                    else:
                        logger.info("✅ CORRECTLY HANDLED AS PLANNING TASK")
                else:
                    logger.info(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
                await asyncio.sleep(2)
            
            logger.info("\n" + "="*60)
            logger.info("🎯 AGENT MODE EXECUTION TEST COMPLETE")
            logger.info("="*60)
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    
    return True

async def test_single_query(websocket, query, mode):
    """Test a single query and return detailed results"""
    try:
        # Send message
        message = {
            "type": "chat_request",
            "mode": mode,
            "query": query,
            "user_id": f"test_user_{int(time.time())}",
            "session_id": f"test_session_{int(time.time())}",
            "timestamp": time.time()
        }
        
        start_time = time.time()
        await websocket.send(json.dumps(message))
        
        # Wait for response
        response_raw = await asyncio.wait_for(websocket.recv(), timeout=60.0)
        response = json.loads(response_raw)
        
        processing_time = time.time() - start_time
        
        if response.get("type") == "chat_response":
            payload = response.get("payload", {})
            return {
                "success": True,
                "response": payload.get("response", ""),
                "confidence": payload.get("confidence", 0.0),
                "resources_used": payload.get("resources_used", []),
                "metadata": payload.get("metadata", {}),
                "processing_time": processing_time
            }
        else:
            return {
                "success": False,
                "error": f"Invalid response type: {response.get('type')}",
                "processing_time": processing_time
            }
            
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Timeout waiting for response",
            "processing_time": time.time() - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time
        }

if __name__ == "__main__":
    asyncio.run(test_agent_execution())