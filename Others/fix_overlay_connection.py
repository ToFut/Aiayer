#!/usr/bin/env python3
"""
Fix for the overlay connection issue with the LLM service.

This script inspects the current WebSocket connections and verifies
that the server is properly registering clients with the correct type.
"""

import asyncio
import json
import logging
import websockets
import uuid
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("overlay_connection_fix")

# WebSocket endpoint
WS_URL = "ws://localhost:8765"

async def test_client_registration():
    """Test client registration to verify server behavior."""
    try:
        logger.info(f"Connecting to {WS_URL} as a UI client...")
        
        # Connect to the WebSocket server as a UI client
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"Connected to {WS_URL}")
            
            # Register as a UI client
            register_message = {
                "type": "register",
                "payload": {
                    "client_type": "ui",
                    "version": "1.0.0",
                    "capabilities": ["chat", "context"]
                }
            }
            await websocket.send(json.dumps(register_message))
            logger.info(f"Sent registration message as UI client")
            
            # Wait for response
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Received welcome: {welcome_msg}")
                
                reg_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Received registration: {reg_msg}")
                
                # Analyze registration response
                try:
                    reg_data = json.loads(reg_msg)
                    if reg_data.get('type') == 'registration_confirmed':
                        client_type = reg_data.get('payload', {}).get('client_type')
                        logger.info(f"Server recognized client as type: {client_type}")
                        
                        # Check if the client type is incorrect
                        if client_type != 'ui':
                            logger.warning(f"Server registered client as {client_type} instead of 'ui'")
                            logger.warning("This may be causing the disconnect issue in the overlay app")
                            return False
                    else:
                        logger.warning(f"Expected 'registration_confirmed' but got {reg_data.get('type')}")
                        return False
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in registration response: {reg_msg[:100]}...")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error("Timed out waiting for server response")
                return False
                
            logger.info("Client registration test completed successfully")
            return True
                
    except Exception as e:
        logger.error(f"Client registration test failed: {e}")
        return False

async def test_llm_service_registration():
    """Test registration as an LLM service."""
    try:
        logger.info(f"Connecting to {WS_URL} as an LLM service...")
        
        # Connect to the WebSocket server as an LLM service
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"Connected to {WS_URL}")
            
            # Register as an LLM service
            register_message = {
                "type": "register",
                "client_type": "llm",
                "version": "1.0.0",
                "capabilities": ["context", "chat"]
            }
            await websocket.send(json.dumps(register_message))
            logger.info(f"Sent registration message as LLM service")
            
            # Wait for response
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Received welcome: {welcome_msg}")
                
                reg_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Received registration: {reg_msg}")
                
                # Check if we're properly registered
                try:
                    reg_data = json.loads(reg_msg)
                    if reg_data.get('type') == 'registration_confirmed':
                        logger.info("LLM service registration successful")
                        return True
                    else:
                        logger.warning(f"Expected 'registration_confirmed' but got {reg_data.get('type')}")
                        return False
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in registration response: {reg_msg[:100]}...")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error("Timed out waiting for server response")
                return False
                
    except Exception as e:
        logger.error(f"LLM service registration test failed: {e}")
        return False

async def main():
    """Main function to run the diagnostics and fixes."""
    logger.info("Starting overlay connection diagnostics")
    
    # Run tests
    ui_test = await test_client_registration()
    llm_test = await test_llm_service_registration()
    
    # Analyze results
    if ui_test and llm_test:
        logger.info("All tests passed successfully!")
        logger.info("The WebSocket server is functioning correctly.")
        logger.info("\nProblem diagnosis: The issue is likely in how the overlay app processes registration responses.")
        logger.info("\nRecommended fixes:")
        logger.info("1. Verify that the overlay app is correctly processing the 'registration_confirmed' message")
        logger.info("2. Check if the overlay app is correctly updating connection status after registration")
        logger.info("3. Modify the EnhancedNextGenChat.svelte component to correctly handle connection status")
        logger.info("\nSpecific code fix in EnhancedNextGenChat.svelte:")
        logger.info("In the registration handling code, look for:")
        logger.info('if (data.type === "registration_confirmed") { ... }')
        logger.info("And make sure connectionStatus is set to 'connected' there.")
    else:
        logger.warning("Tests failed. The WebSocket server may not be functioning correctly.")
        if not ui_test:
            logger.warning("UI client registration test failed")
        if not llm_test:
            logger.warning("LLM service registration test failed")

if __name__ == "__main__":
    logger.info("Running overlay connection fix tool")
    asyncio.run(main())