#!/usr/bin/env python3
"""
End-to-end test script for the guaranteed WebSocket server solution
"""
import asyncio
import websockets
import json
import logging
import sys
import os
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/test_guaranteed_solution.log')
    ]
)
logger = logging.getLogger('test_guaranteed_solution')

async def test_connection_and_agent_confirmation():
    """Test connection to WebSocket server and agent_confirmation handling"""
    ws_url = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to WebSocket server: {ws_url}")
        async with websockets.connect(ws_url) as websocket:
            logger.info("✅ Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome)
            logger.info(f"Received welcome message: {welcome_data.get('message', '')}")
            
            # Create test session ID
            session_id = f"test_session_{int(datetime.now().timestamp())}"
            
            # Send agent_confirmation message (DO button press)
            logger.info("Sending agent_confirmation message (DO button press)")
            confirmation_message = {
                "type": "agent_confirmation",
                "session_id": session_id,
                "action": "DO",
                "modifications": {},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(confirmation_message))
            logger.info("✅ Agent confirmation message sent")
            
            # Wait for responses
            received_progress = False
            received_success = False
            timeout = 10.0  # Total timeout
            start_time = asyncio.get_event_loop().time()
            
            logger.info("Waiting for responses...")
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    response = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                    response_data = json.loads(response)
                    
                    msg_type = response_data.get('type', 'unknown')
                    logger.info(f"Received message type: {msg_type}")
                    
                    # Check for progress messages
                    if msg_type == 'agent_progress':
                        received_progress = True
                        progress = response_data.get('progress', 0)
                        step = response_data.get('step', 0)
                        message = response_data.get('message', '')
                        logger.info(f"Progress update: Step {step}, {progress}% - {message}")
                    
                    # Check for success message
                    elif msg_type == 'agent_execution_success':
                        received_success = True
                        summary = response_data.get('summary', '')
                        logger.info(f"Success message received: {summary}")
                        break  # We got what we needed
                    
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for more responses")
                    break
            
            # Verify we received the expected messages
            if received_progress and received_success:
                logger.info("✅ Test PASSED! Received both progress and success messages")
                return True
            else:
                logger.error(f"❌ Test FAILED! Missing messages: Progress={received_progress}, Success={received_success}")
                return False
    
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def ensure_server_running():
    """Ensure the WebSocket server is running, start if needed"""
    try:
        # Check if server is already running
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('localhost', 8765))
        s.close()
        
        if result == 0:
            logger.info("WebSocket server is already running on port 8765")
            return True
        
        # Start the server
        logger.info("WebSocket server is not running, starting it...")
        server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "start_guaranteed_ws_8765.sh")
        
        subprocess.Popen(["/bin/bash", server_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        for _ in range(5):  # Try 5 times
            await asyncio.sleep(1)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = s.connect_ex(('localhost', 8765))
            s.close()
            if result == 0:
                logger.info("✅ WebSocket server started successfully")
                return True
        
        logger.error("❌ Failed to start WebSocket server")
        return False
        
    except Exception as e:
        logger.error(f"Error ensuring server is running: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("=== STARTING END-TO-END TEST OF GUARANTEED SOLUTION ===")
    
    # Ensure server is running
    server_running = await ensure_server_running()
    if not server_running:
        logger.error("Cannot proceed with test, server is not running")
        return False
    
    # Run the test
    return await test_connection_and_agent_confirmation()

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Run the test
        result = asyncio.run(main())
        
        if result:
            logger.info("✅ END-TO-END TEST PASSED!")
            sys.exit(0)
        else:
            logger.error("❌ END-TO-END TEST FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)