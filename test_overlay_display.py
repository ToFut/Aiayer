#!/usr/bin/env python3
"""
Test overlay plan display and execute button functionality
"""

import asyncio
import websockets
import json
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_overlay_display():
    """Test the overlay plan display functionality"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Step 1: Send a query to create a plan
            query_message = {
                "type": "query",
                "payload": {
                    "message": "search segev in google"
                },
                "client_id": "overlay_test",
                "session_id": "overlay_session"
            }
            
            logger.info("📤 Sending query to create plan...")
            await websocket.send(json.dumps(query_message))
            
            # Step 2: Wait for plan response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"📥 Received response type: {data.get('type')}")
            
            # If we got a connection message, wait for the actual response
            if data.get('type') in ['connection_established', 'welcome']:
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"📥 Received actual response type: {data.get('type')}")
            
            if data.get('type') == 'response' and data.get('payload', {}).get('plan_id'):
                plan_id = data.get('payload', {}).get('plan_id')
                response_content = data.get('payload', {}).get('response', '')
                logger.info(f"✅ Plan created with ID: {plan_id}")
                logger.info(f"📋 Response content length: {len(response_content)} characters")
                
                # Check if the response contains the expected format
                if "🎯 **AUTOMATION EXECUTION PLAN**" in response_content:
                    logger.info("✅ Plan has proper formatting for overlay display")
                else:
                    logger.error("❌ Plan missing proper formatting")
                
                if "🆔 Plan ID:" in response_content:
                    logger.info("✅ Plan ID is included in response")
                else:
                    logger.error("❌ Plan ID missing from response")
                
                if "🚀 Automation Steps:" in response_content:
                    logger.info("✅ Automation steps are included")
                else:
                    logger.error("❌ Automation steps missing")
                
                # Step 3: Test execute command
                execute_message = {
                    "type": "query",
                    "payload": {
                        "message": f"/do_execute {plan_id}"
                    },
                    "client_id": "overlay_test",
                    "session_id": "overlay_session"
                }
                
                logger.info("📤 Sending execute command...")
                await websocket.send(json.dumps(execute_message))
                
                # Step 4: Wait for execution response
                execution_response = await websocket.recv()
                exec_data = json.loads(execution_response)
                logger.info(f"📥 Received execution response type: {exec_data.get('type')}")
                
                if exec_data.get('type') == 'plan_executed':
                    status = exec_data.get('payload', {}).get('status')
                    logger.info(f"✅ Plan execution completed with status: {status}")
                    
                    if status == 'failed':
                        failed_steps = exec_data.get('payload', {}).get('failed_steps', [])
                        logger.info(f"❌ Failed steps: {len(failed_steps)}")
                        for step in failed_steps:
                            logger.info(f"   - Error: {step.get('error', 'Unknown error')}")
                else:
                    logger.error(f"❌ Execution failed: {exec_data}")
            else:
                logger.error(f"❌ Plan creation failed: {data}")
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_overlay_display()) 