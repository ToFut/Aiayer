#!/usr/bin/env python3
"""
Test Context Integration with LLM

This script tests if the context from sensors is properly being integrated into LLM responses.
It sends a test query to the LLM service via WebSocket and checks if context is included in the response.
"""
import json
import asyncio
import websockets
import os
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_context_integration')

async def test_llm_query(query="What am I seeing?"):
    """Send a test query to the LLM service and display the response"""
    llm_service_uri = "ws://localhost:8770"
    
    try:
        logger.info(f"Connecting to LLM service at {llm_service_uri}")
        async with websockets.connect(llm_service_uri) as websocket:
            logger.info(f"Connected to LLM service")
            
            # Prepare request with the test query
            request = {
                "type": "llm_request",
                "query": query,
                "include_context": True,  # Request context inclusion
                "request_id": f"test_{int(time.time())}"
            }
            
            # First, let's check what's in the context
            context_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'memory', 'last_context.json')
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    try:
                        context = json.load(f)
                        logger.info(f"Current context from last_context.json:")
                        print(json.dumps(context, indent=2))
                    except json.JSONDecodeError:
                        logger.warning(f"Could not decode context file: {context_file}")
            else:
                logger.warning(f"Context file not found: {context_file}")
            
            # Send the request
            logger.info(f"Sending query: '{query}'")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            logger.info(f"Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # Display response
            logger.info(f"Received response:")
            print("\n" + "-"*80)
            print(f"QUERY: {query}")
            print("-"*80)
            
            if "error" in response_data:
                print(f"ERROR: {response_data['error']}")
            else:
                # Check if context was used
                context_used = "context_used" in response_data and response_data["context_used"]
                print(f"CONTEXT USED: {'Yes' if context_used else 'No'}")
                
                # Print full response
                print("\nRESPONSE:")
                print(response_data.get("response", "No response content"))
            
            print("-"*80 + "\n")
            
            return response_data
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"Connection closed: {e}")
        return {"error": f"Connection closed: {e}"}
    except Exception as e:
        logger.error(f"Error testing LLM: {e}")
        return {"error": str(e)}

async def run_tests():
    """Run a series of test queries to check context integration"""
    # Test basic context query
    await test_llm_query("What am I seeing?")
    
    # Test application context
    await test_llm_query("What application am I using?")
    
    # Test general context awareness
    await test_llm_query("Summarize my current context")
    
    # Test memory integration
    await test_llm_query("What have I been doing recently?")

if __name__ == "__main__":
    logger.info("Starting context integration test")
    asyncio.run(run_tests())
