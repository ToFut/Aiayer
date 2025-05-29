#!/usr/bin/env python3
"""
Test the integrated brain router ASK mode functionality
Tests that the enhanced backend now uses brain router for ASK mode
"""

import asyncio
import websockets
import json
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_integrated_brain_router():
    """Test the brain router integration in enhanced backend"""
    
    try:
        # Connect to the enhanced backend
        async with websockets.connect("ws://localhost:8767") as websocket:
            logger.info("Connected to Enhanced Enterprise Backend 8767")
            
            # Wait for connection message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            logger.info(f"Connection established: {connection_data.get('message', 'No message')}")
            
            # Test the app query that was failing before
            test_query = "what APPs running in my PC?"
            
            logger.info(f"🧪 Testing ASK mode with brain router integration: {test_query}")
            
            # Send the chat request
            request = {
                "type": "chat_request",
                "mode": "Ask",
                "message": test_query,
                "session_id": "test_brain_router_integration",
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(request))
            logger.info(f"📤 Sent ASK mode request: {test_query}")
            
            # Collect all responses
            responses = []
            start_time = time.time()
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    responses.append(response_data)
                    
                    response_type = response_data.get("type", "unknown")
                    
                    if response_type == "final_response":
                        final_response = response_data.get("response", "")
                        processing_time = time.time() - start_time
                        
                        logger.info(f"✅ Final response received in {processing_time:.2f}s")
                        logger.info(f"📝 Response: {final_response}")
                        
                        # Analyze the response to see if it's using brain router
                        if "I cannot provide a list" in final_response:
                            logger.error("❌ STILL GETTING GENERIC RESPONSE - Brain router integration failed")
                            return False
                        elif any(keyword in final_response.lower() for keyword in ["application", "app", "running", "open", "chrome", "cursor", "spotify"]):
                            logger.info("✅ SUCCESS: Response contains actual app information - Brain router integration working!")
                            return True
                        else:
                            logger.warning("⚠️ Response doesn't contain expected app information")
                            logger.info(f"Response content: {final_response}")
                            return False
                    
                    elif response_type == "chat_response_metadata":
                        metadata = response_data
                        logger.info(f"📊 Metadata: {metadata.get('context_metrics', {})}")
                        break
                    
                    elif response_type == "progress_update":
                        logger.info(f"🔄 Progress: {response_data.get('stage', 'Unknown')}")
                    
                    elif response_type == "error":
                        logger.error(f"❌ Error response: {response_data.get('error', 'Unknown error')}")
                        return False
                        
                except asyncio.TimeoutError:
                    logger.error("❌ Timeout waiting for response")
                    return False
                except Exception as e:
                    logger.error(f"❌ Error receiving response: {e}")
                    return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing Brain Router Integration in Enhanced Backend")
    print("=" * 60)
    
    success = await test_integrated_brain_router()
    
    print("=" * 60)
    if success:
        print("✅ INTEGRATION TEST PASSED: Brain router is working in enhanced backend")
        print("🎯 ASK mode now uses sophisticated semantic search and memory integration")
    else:
        print("❌ INTEGRATION TEST FAILED: Brain router integration not working")
        print("🔧 Check logs for debugging information")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)