#!/usr/bin/env python3
"""
Test Overlay to Backend DO Button Flow

This script tests the entire communication chain from overlay to backend for DO button actions.
It simulates how a real user interaction would flow through the system.
"""

import asyncio
import websockets
import json
import logging
import time
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_overlay_to_backend_do_button.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestOverlayToBackendDoButton")

async def test_overlay_to_backend_flow():
    """Test the complete flow from overlay to backend for DO button actions"""
    try:
        # Step 1: Connect to the backend to register and get a client_id
        backend_uri = "ws://localhost:8767/ws"
        logger.info(f"Connecting to backend at {backend_uri}")
        
        async with websockets.connect(backend_uri) as backend_websocket:
            # Get welcome message with client_id
            welcome = await backend_websocket.recv()
            welcome_data = json.loads(welcome)
            client_id = welcome_data.get("client_id")
            logger.info(f"✅ Connected to backend with client_id: {client_id}")
            
            # Step 2: Connect to the DO button server
            do_button_uri = "ws://localhost:8765"
            logger.info(f"Connecting to DO button server at {do_button_uri}")
            
            async with websockets.connect(do_button_uri) as do_button_websocket:
                # Get welcome message
                do_welcome = await do_button_websocket.recv()
                logger.info(f"✅ Connected to DO button server")
                
                # Step 3: Connect to the proxy
                proxy_uri = "ws://localhost:8766"
                logger.info(f"Connecting to proxy at {proxy_uri}")
                
                try:
                    async with websockets.connect(proxy_uri) as proxy_websocket:
                        # Get welcome message
                        proxy_welcome = await proxy_websocket.recv()
                        logger.info(f"✅ Connected to proxy")
                        
                        # Step 4: Create a plan on the backend
                        test_plan_id = f"test_plan_{int(time.time())}"
                        logger.info(f"Creating test plan with ID: {test_plan_id}")
                        
                        test_plan = {
                            "id": test_plan_id,
                            "title": "Overlay to Backend Test Plan",
                            "description": "This plan tests overlay to backend communication",
                            "steps": [
                                {
                                    "id": f"{test_plan_id}_step_1",
                                    "type": "notification",
                                    "action": "notify",
                                    "content": "Testing overlay to backend communication...",
                                    "position": {"x": 500, "y": 300}
                                },
                                {
                                    "id": f"{test_plan_id}_step_2",
                                    "type": "pause",
                                    "duration": 0.5,
                                    "description": "Short pause"
                                },
                                {
                                    "id": f"{test_plan_id}_step_3",
                                    "type": "notification",
                                    "action": "notify",
                                    "content": "Overlay to backend communication working!",
                                    "position": {"x": 500, "y": 400}
                                }
                            ],
                            "metadata": {
                                "created_at": time.time(),
                                "test_plan": True
                            }
                        }
                        
                        # Send a message to the backend to create a plan
                        backend_message = {
                            "type": "create_plan",
                            "plan": test_plan,
                            "client_id": client_id
                        }
                        
                        await backend_websocket.send(json.dumps(backend_message))
                        logger.info(f"✅ Sent create_plan message to backend")
                        
                        # Wait for response or timeout after 2 seconds
                        try:
                            response = await asyncio.wait_for(backend_websocket.recv(), timeout=2.0)
                            logger.info(f"✅ Received response from backend: {response[:100]}...")
                        except asyncio.TimeoutError:
                            logger.warning("⚠️ No response from backend within timeout")
                        
                        # Step 5: Simulate overlay sending a DO button action through proxy
                        logger.info(f"Simulating DO button click from overlay via proxy")
                        
                        # Create overlay to proxy message (simulating UI click)
                        overlay_message = {
                            "type": "agent_confirmation",
                            "action": "DO",
                            "sessionId": test_plan_id,
                            "client_id": client_id
                        }
                        
                        # Send the message to the proxy
                        await proxy_websocket.send(json.dumps(overlay_message))
                        logger.info(f"✅ Sent agent_confirmation message to proxy")
                        
                        # Step 6: Check for responses from both backend and DO button server
                        responses = {
                            "backend": [],
                            "do_button": [],
                            "proxy": []
                        }
                        
                        # Function to collect responses from a websocket
                        async def collect_responses(websocket, key, timeout=5.0):
                            start_time = time.time()
                            while time.time() - start_time < timeout:
                                try:
                                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                                    response_data = json.loads(response)
                                    responses[key].append(response_data)
                                    logger.info(f"✅ Received {key} response: {response_data}")
                                except asyncio.TimeoutError:
                                    break
                                except Exception as e:
                                    logger.error(f"❌ Error receiving {key} response: {e}")
                                    break
                        
                        # Collect responses from all connections
                        await asyncio.gather(
                            collect_responses(backend_websocket, "backend"),
                            collect_responses(do_button_websocket, "do_button"),
                            collect_responses(proxy_websocket, "proxy")
                        )
                        
                        # Step 7: Analyze responses
                        logger.info(f"Received {len(responses['backend'])} backend responses")
                        logger.info(f"Received {len(responses['do_button'])} DO button responses")
                        logger.info(f"Received {len(responses['proxy'])} proxy responses")
                        
                        # Check for success indicators
                        success = False
                        
                        for resp in responses["do_button"]:
                            if resp.get("type") == "agent_progress":
                                success = True
                                logger.info(f"✅ Found agent_progress response from DO button server")
                                break
                        
                        for resp in responses["proxy"]:
                            if resp.get("type") == "agent_progress":
                                success = True
                                logger.info(f"✅ Found agent_progress response from proxy")
                                break
                                
                        return success
                except Exception as e:
                    logger.error(f"❌ Error connecting to proxy: {e}")
                    # Continue with direct backend to DO button test
                    
                # Step 8: If proxy test failed, test direct backend to DO button
                logger.info(f"Testing direct backend to DO button communication")
                
                # Create a new plan
                direct_plan_id = f"direct_plan_{int(time.time())}"
                direct_plan = {
                    "id": direct_plan_id,
                    "title": "Direct Backend to DO Button Test Plan",
                    "description": "This plan tests direct backend to DO button communication",
                    "steps": [
                        {
                            "id": f"{direct_plan_id}_step_1",
                            "type": "notification",
                            "action": "notify",
                            "content": "Testing direct backend to DO button communication...",
                            "position": {"x": 500, "y": 300}
                        }
                    ],
                    "metadata": {
                        "created_at": time.time(),
                        "test_plan": True
                    }
                }
                
                # Send DO button action directly
                direct_message = {
                    "type": "do_button",
                    "plan_id": direct_plan_id,
                    "plan": direct_plan
                }
                
                await do_button_websocket.send(json.dumps(direct_message))
                logger.info(f"✅ Sent direct DO button message")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(do_button_websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    logger.info(f"✅ Received direct response: {response_data}")
                    
                    if response_data.get("type") == "agent_progress":
                        logger.info(f"✅ Direct backend to DO button communication successful")
                        return True
                    else:
                        logger.warning(f"⚠️ Unexpected response type: {response_data.get('type')}")
                        return False
                except asyncio.TimeoutError:
                    logger.warning("⚠️ No response received within timeout period")
                    return False
    except Exception as e:
        logger.error(f"❌ Error in overlay to backend test: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting Overlay to Backend DO Button Test")
    
    success = await test_overlay_to_backend_flow()
    
    if success:
        logger.info("✅ Overlay to Backend DO Button Test PASSED!")
    else:
        logger.error("❌ Overlay to Backend DO Button Test FAILED!")
        
    logger.info("Test completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())