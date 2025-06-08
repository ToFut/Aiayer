#!/usr/bin/env python3
"""
Mode Tester for Aiayer System

This script tests each chat mode (agent, ask, suggest) separately to determine 
which ones are working properly. It sends a single query in each mode.
"""

import asyncio
import json
import logging
import time
import websockets
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_WS_URL = "ws://localhost:8767"
TIMEOUT = 90  # seconds

# Simple test queries for each mode
TEST_QUERIES = {
    "agent": "show me what time it is",  # Simple task that should be fast
    "ask": "what's the current date?",   # Simple system information query
    "suggest": "I need to write some notes",  # Simple suggestion request
    "general": "hello, are you working?"  # Simple general query
}

async def test_mode(websocket, mode: str, message: str, session_id: str):
    """Test a specific mode with a query"""
    logger.info(f"Testing '{mode}' mode with message: '{message}'")
    
    # Send the request
    request = {
        "type": "chat_request",
        "mode": mode,
        "message": message,
        "session_id": session_id
    }
    await websocket.send(json.dumps(request))
    
    # Wait for response with timeout
    start_time = time.time()
    response_parts = []
    final_response = None
    response_received = False
    
    try:
        async with asyncio.timeout(TIMEOUT):
            while True:
                response = await websocket.recv()
                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON: {response[:100]}...")
                    continue
                
                # Log the response type
                msg_type = data.get("type", "unknown")
                logger.info(f"Received message type: {msg_type}")
                
                # Handle different response types
                if msg_type == "response":
                    response_content = data.get("response", "")
                    response_parts.append(response_content)
                    final_response = data
                    
                    if not data.get("streaming", False):
                        response_received = True
                        break
                        
                elif msg_type == "final_response":
                    response_content = data.get("response", "")
                    response_parts.append(response_content)
                    final_response = data
                    response_received = True
                    break
                        
                elif msg_type == "agent_response":
                    final_response = data
                    response_received = True
                    break
                    
                elif msg_type == "stream_end":
                    response_received = True
                    break
                    
                elif msg_type == "error":
                    error_msg = data.get("message", "Unknown error")
                    logger.error(f"Error from backend: {error_msg}")
                    final_response = data
                    response_received = True
                    break
    
    except asyncio.TimeoutError:
        logger.error(f"Response timeout after {TIMEOUT} seconds")
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Combine response parts if we have them
    combined_response = "".join(response_parts)
    
    if response_received:
        logger.info(f"Mode '{mode}' responded in {response_time:.2f}s")
        
        if combined_response:
            logger.info(f"Response preview: {combined_response[:100]}...")
        elif final_response:
            logger.info(f"Final response: {json.dumps(final_response)[:100]}...")
        else:
            logger.warning("Received empty response")
        
        return {
            "mode": mode,
            "success": True,
            "response_time": response_time,
            "response": combined_response if combined_response else final_response
        }
    else:
        logger.error(f"No response received for mode '{mode}'")
        return {
            "mode": mode,
            "success": False,
            "response_time": response_time,
            "response": None
        }

async def main():
    """Main function to test all modes"""
    parser = argparse.ArgumentParser(description='Test different modes of the Aiayer system')
    parser.add_argument('--backend_url', type=str, default=DEFAULT_WS_URL,
                        help=f'WebSocket URL of the backend (default: {DEFAULT_WS_URL})')
    parser.add_argument('--mode', type=str, choices=["all", "agent", "ask", "suggest", "general"],
                        default="all", help='Specific mode to test (default: all)')
    args = parser.parse_args()
    
    # Determine which modes to test
    if args.mode == "all":
        modes_to_test = ["agent", "ask", "suggest", "general"]
    else:
        modes_to_test = [args.mode]
    
    try:
        # Connect to the backend
        logger.info(f"Connecting to backend at {args.backend_url}")
        websocket = await websockets.connect(args.backend_url)
        
        # Wait for the connection established message
        connection_message = await websocket.recv()
        data = json.loads(connection_message)
        if data.get("type") == "connection_established":
            client_id = data.get("client_id", "unknown")
            logger.info(f"Successfully connected with client ID: {client_id}")
        else:
            logger.warning(f"Unexpected connection message: {data}")
            return
        
        # Create session ID
        session_id = f"mode_test_{int(time.time())}"
        
        # Test each mode
        results = {}
        for mode in modes_to_test:
            message = TEST_QUERIES[mode]
            result = await test_mode(websocket, mode, message, session_id)
            results[mode] = result
            
            # Wait between tests
            if mode != modes_to_test[-1]:
                await asyncio.sleep(2)
        
        # Close connection
        await websocket.close()
        
        # Print summary
        print("\n" + "=" * 60)
        print("MODE TEST RESULTS")
        print("=" * 60)
        
        for mode, result in results.items():
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            print(f"{mode.upper()} MODE: {status} - Response time: {result['response_time']:.2f}s")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())