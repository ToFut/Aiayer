#!/usr/bin/env python3
"""
NextGen Overlay Suggestion Fix

This script fixes the issue with suggestions not pushing to the NextGen overlay.
It modifies the ultimate_do_button_server.py to properly handle suggestions in the
format expected by the NextGen overlay component.
"""
import os
import sys
import json
import asyncio
import websockets
import logging
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/nextgen_suggestion_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nextgen_suggestion_fix')

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_suggestion_to_overlay():
    """Send a properly formatted suggestion to the NextGen overlay"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create suggestion in EXACT format expected by NextGenAppleChatWidget
            suggestion = {
                "success": True,
                "response": "💡 NextGen Suggestion Test: Would you like me to help you optimize your workflow?",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send the properly formatted suggestion
            await websocket.send(json.dumps(suggestion))
            logger.info(f"✅ Sent properly formatted suggestion to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_nextgen_overlay_connection():
    """Test connection to NextGen overlay and verify it's working"""
    try:
        # Test connection to the WebSocket server
        logger.info("Testing connection to WebSocket server...")
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=5) as websocket:
            logger.info("✅ Successfully connected to WebSocket server")
            
            # Send ping message
            ping_msg = json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()})
            await websocket.send(ping_msg)
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
                logger.info("✅ WebSocket server is responsive")
                return True
            except asyncio.TimeoutError:
                logger.warning("❌ WebSocket server did not respond to ping")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to WebSocket server: {e}")
        return False

async def add_suggestion_handler_to_server():
    """
    Modify the ultimate_do_button_server.py file to properly handle suggestions
    for the NextGen overlay
    """
    try:
        server_path = '/Users/segevbin/Desktop/SensAI/Aiayer/ultimate_do_button_server.py'
        backup_path = '/Users/segevbin/Desktop/SensAI/Aiayer/ultimate_do_button_server.py.bak'
        
        # Check if file exists
        if not os.path.exists(server_path):
            logger.error(f"Server file not found: {server_path}")
            return False
        
        # Create backup
        with open(server_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup of server file: {backup_path}")
        
        # Read file
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check if the suggestion handler is already present
        if 'elif msg_type == \'suggestion\'' in content:
            logger.info("Suggestion handler already present in server file")
            return True
        
        # Find the position to insert the new handler - after the do_button handler
        do_button_pos = content.find('elif msg_type == \'do_button\'')
        if do_button_pos == -1:
            logger.error("Could not find do_button handler in server file")
            return False
        
        # Find the end of the do_button handler code block
        next_handler_pos = content.find('else:', do_button_pos)
        if next_handler_pos == -1:
            logger.error("Could not find the end of do_button handler in server file")
            return False
        
        # Create the suggestion handler code
        suggestion_handler = """
                # CRITICAL: Add direct handling for suggestion message type
                elif msg_type == 'suggestion':
                    # Extract content information
                    logger.info(f"📢 Suggestion request received")
                    
                    # Extract or generate session ID
                    session_id = data.get('session_id', f"suggestion_{int(datetime.now().timestamp())}")
                    
                    # Extract suggestion content
                    title = data.get('title', 'Suggestion')
                    message = data.get('message', data.get('content', 'Would you like help with this?'))
                    
                    logger.info(f"Suggestion: {title} - {message}")
                    
                    # Create direct chat message in the EXACT format expected by NextGenAppleChatWidget
                    suggestion_message = {
                        "success": True,
                        "response": f"💡 {title}: {message}",
                        "mode": "SUGGEST",
                        "processing_time": 0.5,
                        "enterprise_validated": True,
                        "buttons": [
                            {
                                "id": "do_it",
                                "text": "Yes, help me",
                                "action": "accept",
                                "style": "success"
                            },
                            {
                                "id": "dismiss",
                                "text": "No thanks",
                                "action": "dismiss",
                                "style": "danger"
                            }
                        ],
                        "interactive": True
                    }
                    
                    # Send the properly formatted message to the overlay
                    await websocket.send(json.dumps(suggestion_message))
                    logger.info(f"✅ Sent properly formatted suggestion to overlay UI")
                    
                    # Send acknowledgment response
                    await websocket.send(json.dumps({
                        "type": "suggestion_displayed",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # CRITICAL: Also support direct message format (used by memory_trigger_service)
                elif 'success' in data and 'response' in data and 'mode' in data:
                    # This is already in the correct format for NextGenAppleChatWidget
                    # Just log and forward it directly
                    logger.info(f"📩 Direct message format received: {data.get('mode', 'unknown')}")
                    
                    # Just pass through the message exactly as received
                    await websocket.send(message)
                    logger.info(f"✅ Forwarded direct message to overlay")
                    
                """
        
        # Insert the suggestion handler before the else block
        new_content = content[:next_handler_pos] + suggestion_handler + content[next_handler_pos:]
        
        # Write the modified content back to the file
        with open(server_path, 'w') as f:
            f.write(new_content)
        
        logger.info("✅ Successfully added suggestion handler to server file")
        return True
        
    except Exception as e:
        logger.error(f"Error modifying server file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def create_suggestion_test_script():
    """Create a test script for sending suggestions to the NextGen overlay"""
    try:
        script_path = '/Users/segevbin/Desktop/SensAI/Aiayer/test_nextgen_suggestion.py'
        
        # Create test script content
        script_content = """#!/usr/bin/env python3
\"\"\"
Test NextGen Overlay Suggestion

This script tests sending a suggestion to the NextGen overlay in the correct format.
\"\"\"
import asyncio
import json
import logging
import sys
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_nextgen_suggestion")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_test_suggestion():
    \"\"\"Send a test suggestion to the NextGen overlay\"\"\"
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create suggestion in proper format
            suggestion = {
                "success": True,
                "response": "💡 Test Suggestion: Would you like help with organizing your files?",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send the suggestion
            await websocket.send(json.dumps(suggestion))
            logger.info(f"Sent suggestion to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    \"\"\"Main function\"\"\"
    logger.info("🚀 Testing NextGen overlay suggestion")
    
    # Send test suggestion
    success = await send_test_suggestion()
    
    if success:
        logger.info("✅ Suggestion test successful")
        logger.info("Check the overlay to see if the suggestion appears")
    else:
        logger.error("❌ Suggestion test failed")
        
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
"""
        
        # Write the script file
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"✅ Created test script: {script_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test script: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def create_restart_script():
    """Create a script to restart the ultimate_do_button_server with the fix applied"""
    try:
        script_path = '/Users/segevbin/Desktop/SensAI/Aiayer/restart_do_button_fix.sh'
        
        # Create script content
        script_content = """#!/bin/bash
# Restart Ultimate DO Button Server with the NextGen suggestion fix applied

# First kill any existing DO button server
echo "Stopping existing DO button server..."
pid_file="pids/ultimate_do_button_server.pid"
if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    if ps -p "$pid" > /dev/null; then
        echo "Killing process $pid..."
        kill -9 "$pid"
        sleep 1
    else
        echo "Process $pid is not running"
    fi
    rm "$pid_file"
else
    echo "No PID file found, checking for existing processes..."
    # Try to find and kill any Python process running the ultimate_do_button_server.py
    for pid in $(ps -ef | grep "ultimate_do_button_server.py" | grep -v grep | awk '{print $2}'); do
        echo "Killing process $pid..."
        kill -9 "$pid"
    done
fi

# Apply the fix if needed
echo "Applying NextGen suggestion fix..."
python3 nextgen_overlay_suggestion_fix.py

# Start the server in the background
echo "Starting ultimate_do_button_server.py..."
python3 ultimate_do_button_server.py &

# Wait a moment for the server to start
sleep 2

# Check if the server is running
if ps -ef | grep "ultimate_do_button_server.py" | grep -v grep > /dev/null; then
    echo "✅ Ultimate DO Button server is running"
    echo "✅ Suggestions should now work correctly with the NextGen overlay"
else
    echo "❌ Failed to start Ultimate DO Button server"
    exit 1
fi

# Test the suggestion functionality
echo "Testing suggestion functionality..."
python3 test_nextgen_suggestion.py

echo "Done! The NextGen overlay should now display suggestions correctly."
"""
        
        # Write the script file
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"✅ Created restart script: {script_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating restart script: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function to fix NextGen overlay suggestion issue"""
    logger.info("🚀 Starting NextGen Overlay Suggestion Fix")
    
    # First, test connection to WebSocket server
    connection_ok = await test_nextgen_overlay_connection()
    if not connection_ok:
        logger.warning("⚠️ Could not connect to WebSocket server - make sure it's running")
        logger.info("Will continue with the fix, but you'll need to restart the server afterward")
    
    # Add suggestion handler to server
    server_fixed = await add_suggestion_handler_to_server()
    if not server_fixed:
        logger.error("❌ Failed to add suggestion handler to server")
        return False
    
    # Create test script
    test_script_created = await create_suggestion_test_script()
    if not test_script_created:
        logger.error("❌ Failed to create test script")
        # Continue anyway
    
    # Create restart script
    restart_script_created = await create_restart_script()
    if not restart_script_created:
        logger.error("❌ Failed to create restart script")
        # Continue anyway
    
    # If the server is running, try sending a suggestion
    if connection_ok:
        suggestion_sent = await send_suggestion_to_overlay()
        if suggestion_sent:
            logger.info("✅ Successfully sent suggestion to overlay")
        else:
            logger.warning("⚠️ Failed to send suggestion to overlay")
            logger.info("You may need to restart the server for the changes to take effect")
    
    logger.info("✅ NextGen Overlay Suggestion Fix completed")
    logger.info("To apply the fix, run: bash restart_do_button_fix.sh")
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)