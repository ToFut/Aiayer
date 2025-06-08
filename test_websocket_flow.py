#!/usr/bin/env python3
"""
Websocket flow tester for debugging
"""
import asyncio
import websockets
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_ws_flow(port):
    """Test the websocket flow to diagnose issues"""
    try:
        uri = f"ws://localhost:{port}"
        logger.info(f"Connecting to {uri}...")
        
        async with websockets.connect(uri, close_timeout=5) as ws:
            logger.info(f"Connected to {uri}")
            
            # 1. Wait for welcome message
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2)
                logger.info(f"Welcome message: {welcome[:100]}...")
            except asyncio.TimeoutError:
                logger.warning(f"No welcome message received from {uri}")
            
            # 2. Send registration
            registration = {
                "type": "register",
                "payload": {
                    "client_type": "test_client",
                    "client_id": f"test_client_{port}",
                    "version": "1.0",
                    "capabilities": ["text"]
                }
            }
            logger.info(f"Sending registration to {uri}...")
            await ws.send(json.dumps(registration))
            
            # 3. Wait for registration confirmation
            try:
                reg_response = await asyncio.wait_for(ws.recv(), timeout=2)
                logger.info(f"Registration response: {reg_response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning(f"No registration response from {uri}")
            
            # 4. Send test query
            test_query = {
                "type": "llm_request",
                "payload": {
                    "query": "This is a test query from debugging script",
                    "mode": "ask",
                    "session_id": "test_session",
                    "user_id": "test_user"
                }
            }
            logger.info(f"Sending test query to {uri}...")
            await ws.send(json.dumps(test_query))
            
            # 5. Wait for response with extended timeout
            try:
                start_response = await asyncio.wait_for(ws.recv(), timeout=5)
                logger.info(f"Initial response: {start_response[:100]}...")
                
                # Check if it's a final response or if we need to wait for more
                try:
                    response_data = json.loads(start_response)
                    if response_data.get("type") in ["typing_start", "thinking", "processing"]:
                        logger.info("Received intermediate response, waiting for final response...")
                        final_response = await asyncio.wait_for(ws.recv(), timeout=20)
                        logger.info(f"Final response: {final_response[:100]}...")
                except Exception as e:
                    logger.error(f"Error parsing response: {e}")
            except asyncio.TimeoutError:
                logger.warning(f"No response received from {uri} after test query")
            
            logger.info(f"Test completed for {uri}")
    
    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
        logger.error(f"Connection error for {uri}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error for {uri}: {e}")

async def test_all_ports():
    """Test all relevant ports"""
    ports = [8765, 8766, 8767]
    results = {}
    
    for port in ports:
        logger.info(f"===== Testing port {port} =====")
        await test_ws_flow(port)
        logger.info(f"===== Completed testing port {port} =====\n")

if __name__ == "__main__":
    logger.info("Starting WebSocket flow test...")
    asyncio.run(test_all_ports())
    logger.info("WebSocket flow test completed")