#!/usr/bin/env python3
"""
Test overlay plan execution with the fixed backend
"""

import asyncio
import websockets
import json
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_overlay_plan_execution():
    """Test the overlay plan execution workflow"""
    
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
                "client_id": "test_client",
                "session_id": "test_session"
            }
            
            logger.info("📤 Sending query to create plan...")
            await websocket.send(json.dumps(query_message))
            
            # Step 2: Wait for plan response (handle welcome message first)
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"📥 Received response type: {data.get('type')}")
            
            # If we got a welcome message, wait for the actual response
            if data.get('type') == 'welcome':
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"📥 Received actual response type: {data.get('type')}")
            
            if data.get('type') == 'plan_created':
                plan_id = data.get('payload', {}).get('plan_id')
                logger.info(f"✅ Plan created with ID: {plan_id}")
                
                # Step 3: Send execute command
                execute_message = {
                    "type": "query",
                    "payload": {
                        "message": f"/do_execute {plan_id}"
                    },
                    "client_id": "test_client",
                    "session_id": "test_session"
                }
                
                logger.info("📤 Sending execute command...")
                await websocket.send(json.dumps(execute_message))
                
                # Step 4: Wait for execution response
                execution_response = await websocket.recv()
                exec_data = json.loads(execution_response)
                logger.info(f"📥 Received execution response type: {exec_data.get('type')}")
                
                if exec_data.get('type') == 'execution_result':
                    logger.info("✅ Plan execution successful!")
                    logger.info(f"Result: {exec_data.get('result', {}).get('response', 'No response')}")
                else:
                    logger.error(f"❌ Execution failed: {exec_data}")
            else:
                logger.error(f"❌ Plan creation failed: {data}")
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_overlay_plan_execution()) 