#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ask_mode():
    """Test ASK mode with the fixed contextual system"""
    
    try:
        # Connect to the backend WebSocket
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to {uri}")
            
            # Send ASK mode request about open applications
            test_message = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "what apps are open on my computer right now?",
                "timestamp": "2025-01-25T20:00:00Z"
            }
            
            logger.info(f"Sending test message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for responses (might get connection message first)
            logger.info("Waiting for responses...")
            
            # Get first response (connection acknowledgment)
            response1 = await websocket.recv()
            conn_data = json.loads(response1)
            print(f"\nConnection Response: {conn_data.get('type', 'unknown')}")
            
            # Get actual chat response
            response2 = await websocket.recv()
            response_data = json.loads(response2)
            print(f"\n{'='*60}")
            print(f"ASK MODE TEST RESULT:")
            print(f"{'='*60}")
            print(f"Response: {response_data.get('response', 'No response')}")
            print(f"Type: {response_data.get('type', 'Unknown')}")
            print(f"Mode: {response_data.get('mode', 'Unknown')}")
            print(f"AI Powered: {response_data.get('ai_powered', 'Unknown')}")
            print(f"Brain Router Used: {response_data.get('brain_router_used', 'Unknown')}")
            print(f"Enhanced Memory Used: {response_data.get('enhanced_memory_used', 'Unknown')}")
            print(f"Semantic Search Used: {response_data.get('semantic_search_used', 'Unknown')}")
            print(f"{'='*60}\n")
            
            # Test suggest mode as well
            suggest_message = {
                "type": "chat_request",
                "mode": "Suggest", 
                "message": "I want to be more productive",
                "timestamp": "2025-01-25T20:01:00Z"
            }
            
            logger.info(f"Testing SUGGEST mode: {suggest_message}")
            await websocket.send(json.dumps(suggest_message))
            
            suggest_response = await websocket.recv()
            suggest_data = json.loads(suggest_response)
            print(f"SUGGEST MODE TEST RESULT:")
            print(f"{'='*60}")
            print(f"Response: {suggest_data.get('response', 'No response')}")
            print(f"Type: {suggest_data.get('type', 'Unknown')}")
            print(f"Mode: {suggest_data.get('mode', 'Unknown')}")
            print(f"AI Powered: {suggest_data.get('ai_powered', 'Unknown')}")
            print(f"Brain Router Used: {suggest_data.get('brain_router_used', 'Unknown')}")
            print(f"Memory Integrated: {suggest_data.get('memory_integrated', 'Unknown')}")
            print(f"{'='*60}\n")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_ask_mode())