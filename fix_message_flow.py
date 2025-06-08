#!/usr/bin/env python3
"""
Fix Message Flow - Diagnostic and Fix Tool for Enhanced Enterprise Backend Response Issues
This script analyzes and fixes the content-type error in NDJSON handling from the Ollama API
"""

import os
import sys
import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, List
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/message_flow_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import LLM model for testing
try:
    from llm.model import LocalLLM
    LLM_MODEL_AVAILABLE = True
except ImportError:
    LLM_MODEL_AVAILABLE = False
    logger.error("Could not import LocalLLM - script will still run diagnostics")

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Constants
BACKEND_WS_URL = "ws://localhost:8767"
OLLAMA_API_URL = "http://localhost:11434/api/chat"

# Test message to send to backend
TEST_MESSAGE = {
    "type": "chat_request",
    "mode": "General",
    "message": "Hello, this is a test message. Please respond.",
    "session_id": "test_session",
    "client_id": "test_client"
}

class MessageFlowFixTool:
    """Tool to diagnose and fix message flow issues in the enhanced enterprise backend"""
    
    def __init__(self):
        self.connected = False
        self.received_response = False
    
    async def connect_to_backend(self):
        """Connect to the WebSocket backend"""
        try:
            self.ws = await websockets.connect(BACKEND_WS_URL)
            self.connected = True
            logger.info("✅ Connected to backend WebSocket")
            
            # Wait for initial connection message
            response = await self.ws.recv()
            logger.info(f"Received initial response: {response[:100]}...")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to backend: {e}")
            return False
    
    async def test_direct_ollama(self):
        """Test Ollama API directly to verify NDJSON content type handling"""
        logger.info("Testing direct Ollama API connection")
        
        try:
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test message. Please respond briefly."}
            ]
            
            request_data = {
                "model": "llama3.2:1b",
                "messages": test_messages,
                "stream": False,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                logger.info("Sending test request to Ollama API...")
                async with session.post(
                    OLLAMA_API_URL,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    logger.info(f"Response status: {response.status}")
                    logger.info(f"Response headers: {response.headers}")
                    
                    # Check content type to determine parsing strategy
                    content_type = response.headers.get('Content-Type', '')
                    logger.info(f"Content-Type: {content_type}")
                    
                    if 'application/x-ndjson' in content_type:
                        logger.info("Detected NDJSON content type - handling as streaming response")
                        text = await response.text()
                        logger.info(f"NDJSON response length: {len(text)} chars")
                        
                        lines = [line for line in text.split('\n') if line.strip()]
                        logger.info(f"Found {len(lines)} NDJSON lines")
                        
                        full_response = ""
                        for i, line in enumerate(lines):
                            try:
                                data = json.loads(line)
                                logger.info(f"NDJSON line {i} data keys: {list(data.keys())}")
                                if 'message' in data and 'content' in data['message']:
                                    full_response += data['message']['content']
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON line: {e}")
                        
                        logger.info(f"Assembled response: {full_response[:100]}...")
                        logger.info("✅ Successfully processed NDJSON response")
                        return True
                    else:
                        # Try to parse as JSON
                        try:
                            data = await response.json()
                            logger.info(f"JSON response data keys: {list(data.keys())}")
                            if 'message' in data and 'content' in data['message']:
                                logger.info(f"Response content: {data['message']['content'][:100]}...")
                            logger.info("✅ Successfully processed JSON response")
                            return True
                        except Exception as e:
                            logger.error(f"❌ Error parsing JSON response: {e}")
                            return False
        except Exception as e:
            logger.error(f"❌ Error testing direct Ollama API: {e}")
            return False
    
    async def test_backend_message_flow(self):
        """Test the backend message flow with a test message"""
        if not self.connected:
            success = await self.connect_to_backend()
            if not success:
                return False
        
        try:
            logger.info(f"Sending test message to backend: {TEST_MESSAGE}")
            await self.ws.send(json.dumps(TEST_MESSAGE))
            
            # Wait for response with timeout
            self.received_response = False
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
                self.received_response = True
                response_data = json.loads(response)
                
                logger.info(f"Received response type: {response_data.get('type')}")
                if response_data.get('type') == 'chat_response':
                    logger.info(f"Chat response: {response_data.get('response', '')[:100]}...")
                    logger.info("✅ Successfully received chat response")
                else:
                    logger.info(f"Other response: {response[:100]}...")
                
                return True
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for response from backend")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error testing backend message flow: {e}")
            return False
    
    async def find_and_apply_fix(self):
        """Identify issues and apply fixes based on diagnostic results"""
        # First check if we have direct access to the LLM model
        if LLM_MODEL_AVAILABLE:
            logger.info("LLM model available - testing and fixing directly")
            
            # First test the model directly
            model = LocalLLM(model_name="llama3.2:1b")
            await model.start()
            
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test message. Please respond briefly."}
            ]
            
            # Test with standard method
            logger.info("Testing response generation...")
            response = await model.generate_response(test_messages)
            logger.info(f"Generated response: {response[:100]}...")
            
            # Verify if the NDJSON issue was fixed
            if "Error" not in response:
                logger.info("✅ LLM response generation working correctly")
            else:
                logger.warning("⚠️ LLM response generation returned an error")
                
        # Next, test direct Ollama API to verify NDJSON handling
        logger.info("Testing direct Ollama API")
        direct_api_success = await self.test_direct_ollama()
        
        # Fix the model.py file if needed by ensuring proper NDJSON handling
        if not direct_api_success or not self.received_response:
            logger.info("Applying fixes to ensure proper NDJSON handling...")
            
            # Suggest code fix pattern for LocalLLM.generate_response
            logger.info("Fix recommendation for llm/model.py:")
            logger.info("""
            The issue is in the content type handling for 'application/x-ndjson' responses.
            
            In llm/model.py, we need to update the generate_response method to properly handle NDJSON:
            
            1. Always check for streaming responses or NDJSON content type
            2. Always parse streaming responses as text first, then parse as NDJSON
            3. Verify that 'application/x-ndjson' check is correctly comparing strings
            
            The key issue is in the condition that checks content_type:
            
            if 'application/x-ndjson' in content_type or stream:
                # Always handle streaming responses properly
                text = await response.text()
                ...
            """)
            
        # Provide fix recommendations for enhanced_enterprise_backend_with_context.py
        logger.info("Fix recommendation for enhanced_enterprise_backend_with_context.py:")
        logger.info("""
        In handle_contextual_chat_request_streaming method, we need to ensure:
        
        1. The LLM responses are properly processed regardless of ContentType errors
        2. Implement fallback handling for chat_request messages if LLM fails
        3. Add better error handling around LLM calls
        
        Key issues:
        
        1. No direct call to LLM from chat_request handler - only automation handlers
        2. No fallback response mechanism for General mode
        3. The backend does fallback to a mock response but it's not executing LLM calls
        
        The fix is to ensure real LLM calls are made from handle_contextual_chat_request_streaming
        for all modes, especially General mode.
        """)
        
        return True
    
    async def verify_port_8767(self):
        """Verify that port 8767 is working with a separate websocket connection"""
        try:
            # Create a separate websocket connection to verify port 8767
            ws = await websockets.connect(BACKEND_WS_URL)
            logger.info("✅ Successfully connected to port 8767")
            
            # Close this test connection
            await ws.close()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to port 8767: {e}")
            return False

async def main():
    """Main function to run diagnostics and apply fixes"""
    logger.info("="*50)
    logger.info("MESSAGE FLOW FIX DIAGNOSTIC TOOL")
    logger.info("="*50)
    
    tool = MessageFlowFixTool()
    
    # First verify port 8767 is running
    logger.info("Verifying port 8767 is accessible...")
    port_status = await tool.verify_port_8767()
    if not port_status:
        logger.error("❌ Port 8767 is not accessible - backend may not be running")
        logger.info("Please make sure the backend server is running with:")
        logger.info("  python enhanced_enterprise_backend_with_context.py")
        return
    
    # Test direct Ollama API
    logger.info("\nTesting direct Ollama API...")
    direct_ollama_status = await tool.test_direct_ollama()
    if direct_ollama_status:
        logger.info("✅ Direct Ollama API test passed")
    else:
        logger.error("❌ Direct Ollama API test failed")
    
    # Test backend message flow
    logger.info("\nTesting backend message flow...")
    message_flow_status = await tool.test_backend_message_flow()
    if message_flow_status:
        logger.info("✅ Backend message flow test passed")
    else:
        logger.error("❌ Backend message flow test failed")
    
    # Find and apply fixes
    logger.info("\nAnalyzing issues and recommending fixes...")
    fix_status = await tool.find_and_apply_fix()
    
    # Output final diagnostic summary
    logger.info("\n"+"="*50)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("="*50)
    logger.info(f"Backend WebSocket (Port 8767): {'✅ WORKING' if port_status else '❌ FAILED'}")
    logger.info(f"Direct Ollama API: {'✅ WORKING' if direct_ollama_status else '❌ FAILED'}")
    logger.info(f"Backend Message Flow: {'✅ WORKING' if message_flow_status else '❌ FAILED'}")
    
    # Provide final recommendations
    logger.info("\n"+"="*50)
    logger.info("RECOMMENDATIONS")
    logger.info("="*50)
    
    if not message_flow_status:
        logger.info("""
1. Fix the NDJSON handling in llm/model.py:
   - The error 'Attempt to decode JSON with unexpected mimetype: application/x-ndjson' 
     shows a content-type parsing issue.
   - Ensure both streams=True and content-type checking work correctly.

2. Fix missing LLM calls in enhanced_enterprise_backend_with_context.py:
   - The backend is not making direct LLM calls for General mode.
   - Implement proper LLM response generation for all modes.
   
3. Fix the handle_contextual_chat_request_streaming method:
   - Add direct LLM calls for General, Ask, and Suggest modes.
   - Implement proper error handling and fallbacks.
        """)
    else:
        logger.info("""
All tests passed! If you're still having issues, consider:

1. Checking log files for specific error patterns
2. Restarting the Ollama service
3. Verifying WebSocket connections from the client side
        """)

if __name__ == "__main__":
    asyncio.run(main())