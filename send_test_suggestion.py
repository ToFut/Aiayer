#!/usr/bin/env python3
"""
send_test_suggestion.py - Sends a test suggestion to the NextGen overlay

This script sends a test suggestion to the WebSocket server on port 8765,
which will then be displayed in the NextGen overlay with sound notification.

Usage:
    python3 send_test_suggestion.py [title] [message]
    
    If title and message are not provided, default test values will be used.
"""

import asyncio
import websockets
import json
import time
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_suggestion")

# Default suggestion content
DEFAULT_TITLE = "Test Suggestion"
DEFAULT_MESSAGE = "This is a test suggestion to verify notification sound and display"

async def send_test_suggestion(title, message):
    """Sends a test suggestion to the WebSocket server"""
    try:
        # Connect to WebSocket server
        logger.info("Connecting to WebSocket server at ws://localhost:8765...")
        async with websockets.connect('ws://localhost:8765') as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"Received welcome message: {welcome_data.get('type', 'unknown')}")
            
            # Create suggestion payload with notification flags
            suggestion = {
                "success": True,
                "response": f"💡 {title}: {message}",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "notification": True,  # Important: This flag enables notification display
                "play_sound": True,    # Important: This flag ensures sound is played
                "sound_type": "notification", # Use the notification sound file
                "importance": "high",  # Mark as high importance to ensure visibility
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
                "interactive": True,
                "plan_id": f"test_{int(time.time())}",
                "timestamp": time.time()
            }
            
            # Send suggestion
            suggestion_json = json.dumps(suggestion)
            logger.info(f"Sending suggestion: {title} - {message}")
            await ws.send(suggestion_json)
            
            # Wait for potential response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Received response from server")
            except asyncio.TimeoutError:
                logger.info("No response received (this is normal)")
            
            logger.info("Suggestion sent successfully! Check the NextGen overlay for notification")
            return True
            
    except Exception as e:
        logger.error(f"Error sending suggestion: {str(e)}")
        return False

async def send_mode_transition(plan_id):
    """Simulates the transition to Agent mode after suggestion acceptance"""
    try:
        # Connect to WebSocket server
        logger.info("Connecting to WebSocket server to send mode transition...")
        async with websockets.connect('ws://localhost:8765') as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            
            # Create agent mode transition payload
            agent_payload = {
                "success": True,
                "response": f"🤖 Ready to execute plan",
                "mode": "Agent",
                "processing_time": 0.3,
                "enterprise_validated": True,
                "notification": False,
                "plan_id": plan_id,
                "buttons": [
                    {
                        "id": "execute_plan",
                        "text": "Execute Now",
                        "action": "execute_plan",
                        "style": "success"
                    },
                    {
                        "id": "cancel",
                        "text": "Cancel",
                        "action": "cancel",
                        "style": "danger"
                    }
                ],
                "interactive": True,
                "requires_approval": True,
                "plan": {
                    "id": plan_id,
                    "title": "Test Plan",
                    "steps": [
                        {"description": "Step 1: Analyze current pattern", "type": "analysis"},
                        {"description": "Step 2: Implement automation", "type": "action"},
                        {"description": "Step 3: Verify completion", "type": "verification"}
                    ],
                    "estimated_duration": "30 seconds",
                    "risk_level": "low"
                }
            }
            
            # Send agent mode transition
            agent_json = json.dumps(agent_payload)
            logger.info(f"Sending Agent mode transition for plan: {plan_id}")
            await ws.send(agent_json)
            
            logger.info("Agent mode transition sent! Check the NextGen overlay")
            return True
            
    except Exception as e:
        logger.error(f"Error sending mode transition: {str(e)}")
        return False

async def main():
    """Main entry point"""
    # Get title and message from command line arguments or use defaults
    title = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TITLE
    message = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MESSAGE
    
    # Send suggestion
    success = await send_test_suggestion(title, message)
    
    if success:
        # Ask if user wants to simulate mode transition
        print("\nDo you want to simulate mode transition to Agent? (y/n)")
        answer = input().strip().lower()
        
        if answer == 'y':
            plan_id = f"test_{int(time.time())}"
            await send_mode_transition(plan_id)
    
    return success

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)