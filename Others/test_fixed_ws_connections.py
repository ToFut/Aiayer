#!/usr/bin/env python3
"""
Test WebSocket Connections

This script tests connections to the bridge server and LLM service
to verify they are properly configured and running.
"""
import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_connections')

# Connection URLs to test
BRIDGE_URL = "ws://localhost:8768"
LLM_URL = "ws://localhost:8770"

async def test_connection(url):
    """Test connection to a WebSocket URL"""
    logger.info(f"Testing connection to: {url}")
    
    try:
        async with websockets.connect(url, ping_interval=None) as websocket:
            logger.info(f"✅ Connected to {url}")
            
            # Send a test message
            test_message = {
                "type": "test_connection",
                "timestamp": datetime.now().isoformat(),
                "client": "test_script"
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info(f"Message sent to {url}")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received response from {url}: {response[:200]}")
                return True
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout waiting for response from {url}")
                return False
                
    except ConnectionRefusedError:
        logger.error(f"❌ Connection refused at {url}. Server not running or port incorrect.")
        return False
    except Exception as e:
        logger.error(f"❌ Error connecting to {url}: {e}")
        return False

async def test_llm_request(url):
    """Test LLM request to a WebSocket URL"""
    logger.info(f"Testing LLM request to: {url}")
    
    try:
        async with websockets.connect(url, ping_interval=None) as websocket:
            logger.info(f"Connected to {url}")
            
            # Wait for initial welcome message
            try:
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received welcome message: {welcome[:200]}")
            except asyncio.TimeoutError:
                logger.warning("No welcome message received, continuing anyway")
            
            # Send a test LLM request
            test_message = {
                "type": "llm_request",
                "payload": {
                    "query": "Hello, this is a test. Please respond with a short greeting."
                }
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info(f"LLM request sent to {url}")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                response_data = json.loads(response)
                logger.info(f"Received LLM response from {url}:")
                logger.info(f"  Type: {response_data.get('type', 'unknown')}")
                content = response_data.get('content', '')
                logger.info(f"  Content: {content[:200]}")
                
                if content:
                    logger.info(f"✅ LLM request test successful!")
                    return True
                else:
                    logger.warning("⚠️ LLM response received but content is empty")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout waiting for LLM response from {url}")
                return False
                
    except ConnectionRefusedError:
        logger.error(f"❌ Connection refused at {url}. LLM server not running or port incorrect.")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing LLM request to {url}: {e}")
        return False

async def run_tests():
    """Run all connection tests"""
    logger.info("Starting WebSocket connection tests")
    
    # Test bridge server connection
    logger.info("===== Testing Bridge Server Connection =====")
    bridge_result = await test_connection(BRIDGE_URL)
    
    # Test LLM service connection
    logger.info("===== Testing LLM Service Connection =====")
    llm_connection_result = await test_connection(LLM_URL)
    
    # Test LLM request
    if llm_connection_result:
        logger.info("===== Testing LLM Request =====")
        llm_request_result = await test_llm_request(LLM_URL)
    else:
        llm_request_result = False
    
    # Print summary
    logger.info("===== Test Results =====")
    logger.info(f"Bridge Server Connection: {'✅ SUCCESS' if bridge_result else '❌ FAILED'}")
    logger.info(f"LLM Service Connection: {'✅ SUCCESS' if llm_connection_result else '❌ FAILED'}")
    logger.info(f"LLM Request: {'✅ SUCCESS' if llm_request_result else '❌ FAILED'}")
    
    if bridge_result and llm_connection_result and llm_request_result:
        logger.info("All tests passed successfully! The system is properly configured.")
        return True
    else:
        logger.error("Some tests failed. Please check the configuration and ensure all services are running.")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Tests stopped by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)