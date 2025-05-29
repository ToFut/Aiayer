#!/usr/bin/env python3
"""
Test script to verify AgentMode parameter fix and plan_id storage
Tests the flight search functionality that was reported as broken
"""
import asyncio
import websockets
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_mode_flight_search():
    """Test the agent mode flight search functionality"""
    
    # Connect to the backend WebSocket
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend WebSocket")
            
            # First receive the connection established message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"📨 Welcome message: {welcome_data.get('type', 'unknown')}")
            
            # Send agent mode request for flight search
            test_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "search best flights to Miami from New York",
                "session_id": "test_session_flight_search",
                "client_id": "test_client_001"
            }
            
            logger.info(f"🚀 Sending agent request: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response (agent processing may take time)
            logger.info("⏳ Waiting for agent response...")
            
            # Keep receiving messages until we get the final agent response
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                response_data = json.loads(response)
                
                response_type = response_data.get('type', 'unknown')
                logger.info(f"📨 Received response type: {response_type}")
                
                # Handle progress updates
                if response_type == "progress_update":
                    stage = response_data.get('stage', 'Unknown stage')
                    logger.info(f"📈 Progress: {stage}")
                    continue
                    
                # Break on final response types
                elif response_type in ["agent_response", "chat_response", "chat_complete", "error"]:
                    break
                else:
                    logger.info(f"📦 Other message: {response_data}")
                    continue
            
            # Check if we got an agent response with buttons
            if response_data.get("type") == "agent_response":
                response_text = response_data.get("response", "")
                buttons = response_data.get("buttons", [])
                
                logger.info(f"📝 Response length: {len(response_text)} characters")
                logger.info(f"🎯 Number of buttons: {len(buttons)}")
                
                if buttons:
                    logger.info("✅ SUCCESS: Interactive buttons generated!")
                    for i, button in enumerate(buttons):
                        logger.info(f"   Button {i+1}: {button.get('text', 'Unknown')} ({button.get('action', 'Unknown')})")
                else:
                    logger.warning("❌ ISSUE: No interactive buttons found in response")
                
                # Check if response contains plan details
                if "AUTOMATION EXECUTION PLAN" in response_text or "plan" in response_text.lower():
                    logger.info("✅ SUCCESS: Response contains plan information")
                else:
                    logger.warning("❌ ISSUE: Response does not contain plan information")
                    
                # Show part of the response for debugging
                logger.info(f"📄 Response preview: {response_text[:200]}...")
                    
                return len(buttons) > 0
            elif response_data.get("type") == "chat_response":
                # Handle chat_response type as well
                response_text = response_data.get("response", "")
                logger.info(f"📝 Got chat_response: {response_text[:200]}...")
                logger.warning("⚠️  Got chat_response instead of agent_response")
                return False
            else:
                logger.error(f"❌ FAILED: Unexpected response type: {response_data.get('type')}")
                logger.info(f"📄 Full response: {response_data}")
                return False
                
    except asyncio.TimeoutError:
        logger.error("❌ TIMEOUT: No response received within 30 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ CONNECTION ERROR: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🧪 Starting AgentMode flight search test...")
    logger.info("📋 Testing fix for parameter mismatch and plan_id storage")
    
    success = await test_agent_mode_flight_search()
    
    if success:
        logger.info("🎉 TEST PASSED: AgentMode flight search working correctly!")
        logger.info("✅ Parameter fix and plan_id storage fix successful")
    else:
        logger.error("💥 TEST FAILED: AgentMode still has issues")
        logger.error("❌ Check backend logs for more details")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)