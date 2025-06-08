#!/usr/bin/env python3
"""
Test script for the real DO button executor
Simulates a DO button click and verifies that the plan is properly executed
"""
import asyncio
import websockets
import json
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_real_do_button')

async def test_do_button_execution():
    """Test the real DO button executor"""
    uri = "ws://localhost:8765"
    logger.info(f"Connecting to WebSocket server at {uri}...")
    
    try:
        async with websockets.connect(uri, ping_timeout=10) as ws:
            # Get welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            welcome_data = json.loads(welcome)
            logger.info(f"Received welcome message: {welcome_data.get('message', '')}")
            
            # Try to find the newest plan ID (if plan_persistence is available)
            newest_plan_id = None
            try:
                from plan_persistence import plan_manager
                plans = await plan_manager.get_all_plan_metadata()
                if plans:
                    # Sort by timestamp (newest first)
                    sorted_plans = sorted(plans, key=lambda x: x.get("timestamp", 0), reverse=True)
                    newest_plan_id = sorted_plans[0].get("plan_id")
                    logger.info(f"Found newest plan: {newest_plan_id}")
            except ImportError:
                logger.warning("Plan persistence not available, using default test plan ID")
            
            # Create agent_confirmation message with DO action
            session_id = newest_plan_id or "test_session_123"
            message = {
                "type": "agent_confirmation",
                "session_id": session_id,
                "action": "DO",
                "timestamp": int(time.time() * 1000)
            }
            
            logger.info(f"Sending DO button request for session {session_id}...")
            await ws.send(json.dumps(message))
            
            # Process responses
            execution_success = False
            progress_updates = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=10)
                    response_data = json.loads(response)
                    
                    response_type = response_data.get("type", "")
                    
                    if response_type == "agent_progress":
                        progress = response_data.get("progress", 0)
                        step_msg = response_data.get("message", "")
                        logger.info(f"Progress update: {progress}% - {step_msg}")
                        progress_updates += 1
                        
                    elif response_type == "agent_execution_success":
                        success = response_data.get("result", {}).get("success", False)
                        steps_executed = response_data.get("result", {}).get("steps_executed", 0)
                        summary = response_data.get("summary", "")
                        
                        logger.info(f"Execution complete - Success: {success}")
                        logger.info(f"Steps executed: {steps_executed}")
                        logger.info(f"Summary: {summary}")
                        
                        execution_success = success
                        break
                        
                    elif response_type == "error":
                        error = response_data.get("error", "Unknown error")
                        logger.error(f"Error received: {error}")
                        break
                        
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for response from server")
                    break
            
            # Return test results
            return {
                "success": execution_success,
                "progress_updates": progress_updates,
                "session_id": session_id
            }
            
    except ConnectionRefusedError:
        logger.error(f"Connection refused to {uri}. Is the server running?")
        return {"success": False, "error": "Connection refused"}
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Run the test and show results"""
    print("Testing real DO button executor...")
    print("This will simulate a DO button click and verify that plans are executed")
    print("----------------------------------------------------------------------")
    
    result = await test_do_button_execution()
    
    if result.get("success", False):
        print("\n✅ TEST PASSED: DO button execution successful!")
        print(f"✅ Received {result.get('progress_updates', 0)} progress updates")
        print(f"✅ Session ID: {result.get('session_id', 'unknown')}")
    else:
        print("\n❌ TEST FAILED: DO button execution failed!")
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        print("❌ Make sure the real_do_button_executor.py is running on port 8765")
    
    print("\nTo start the real DO button executor, run:")
    print("  ./start_real_do_button_executor.sh")

if __name__ == "__main__":
    asyncio.run(main())