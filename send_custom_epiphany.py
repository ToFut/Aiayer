#!/usr/bin/env python3
"""
Custom Epiphany Mode Test Script

This script sends a fully formatted suggestion with custom buttons and a detailed plan
to demonstrate the complete capabilities of the Epiphany mode.
"""

import asyncio
import websockets
import json
import time
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
logger = logging.getLogger("custom_epiphany")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_custom_epiphany(title="Automation Opportunity", message="I've detected a way to automate your workflow"):
    """Send a custom epiphany suggestion with buttons and a detailed plan"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome message")
            
            # Generate a unique suggestion ID
            suggestion_id = f"custom_sugg_{int(time.time())}"
            
            # Create a detailed suggestion with a complete plan
            suggestion = {
                "type": "suggestion",
                "suggestion_id": suggestion_id,
                "title": title,
                "message": message,
                "confidence": 0.92,
                "actions": [
                    {
                        "action_id": "approve",
                        "action_text": "Let's do it!",
                        "action_type": "primary"
                    },
                    {
                        "action_id": "learn_more",
                        "action_text": "Tell me more",
                        "action_type": "secondary"
                    },
                    {
                        "action_id": "dismiss",
                        "action_text": "No thanks",
                        "action_type": "danger"
                    }
                ],
                "plan": {
                    "task_id": f"plan_{int(time.time())}",
                    "title": title,
                    "description": message,
                    "request_type": "automation",
                    "steps": [
                        {
                            "id": "step_1",
                            "description": "Analyze your current workflow pattern",
                            "action_type": "analysis",
                            "target": None,
                            "value": None,
                            "coordinates": None
                        },
                        {
                            "id": "step_2",
                            "description": "Identify automation opportunities",
                            "action_type": "analysis",
                            "target": None,
                            "value": None,
                            "coordinates": None
                        },
                        {
                            "id": "step_3",
                            "description": "Create automation script/workflow",
                            "action_type": "create_file",
                            "target": "automation_script.py",
                            "value": "",
                            "coordinates": None
                        },
                        {
                            "id": "step_4",
                            "description": "Test the automation with your approval",
                            "action_type": "execute",
                            "target": "automation_script.py",
                            "value": "",
                            "coordinates": None
                        },
                        {
                            "id": "step_5",
                            "description": "Save the automation for future use",
                            "action_type": "finalize",
                            "target": None,
                            "value": None,
                            "coordinates": None
                        }
                    ],
                    "complexity_score": 0.6,
                    "estimated_duration": 15,
                    "risk_level": "low"
                }
            }
            
            # Send the suggestion
            await websocket.send(json.dumps(suggestion))
            logger.info(f"Custom Epiphany suggestion sent successfully!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received response: {response}")
            except asyncio.TimeoutError:
                logger.info("No immediate response received (this is normal)")
            
            # Wait a bit longer for any additional responses
            try:
                for _ in range(3):
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    logger.info(f"Received additional response: {response}")
            except asyncio.TimeoutError:
                pass
                
            return True
            
    except Exception as e:
        logger.error(f"Error sending custom epiphany: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Get custom message from command line if provided
    title = "Code Quality Opportunity"
    message = "I've noticed you might benefit from adding automated tests to your project. Would you like me to help set up a testing framework?"
    
    if len(sys.argv) > 1:
        title = sys.argv[1]
    if len(sys.argv) > 2:
        message = sys.argv[2]
    
    print("\n🧠 CUSTOM EPIPHANY MODE TEST\n")
    print(f"Title: {title}")
    print(f"Message: {message}")
    print("\nSending detailed suggestion with multiple buttons and a complete plan...\n")
    
    asyncio.run(send_custom_epiphany(title, message))
    
    print("\n✅ Custom Epiphany suggestion sent!")
    print("Check the overlay to see if it appears correctly.")