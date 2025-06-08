#!/usr/bin/env python3
"""
Test script to send a mock suggestion to the Epiphany mode system
"""

import asyncio
import json
import websockets
import time

async def send_test_suggestion():
    """Connect to the WebSocket server and send a test suggestion"""
    try:
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Register as a test client
            await websocket.send(json.dumps({
                "type": "register",
                "client_type": "test_client",
                "client_id": f"test_{int(time.time())}"
            }))
            
            print("Registered as test client")
            await asyncio.sleep(1)
            
            # Send a test suggestion
            suggestion = {
                "type": "suggestion",
                "suggestion_id": f"test_sugg_{int(time.time())}",
                "title": "Automate File Organization",
                "message": "I've noticed you frequently create and move files between directories. Would you like me to create an automation script to organize your files by type?",
                "confidence": 0.85,
                "actions": [
                    {
                        "action_id": "approve",
                        "action_text": "Create Automation Script",
                        "action_type": "primary"
                    }
                ],
                "plan": {
                    "task_id": f"plan_{int(time.time())}",
                    "title": "File Organization Automation",
                    "description": "Create a script to automatically organize files by type",
                    "request_type": "automation",
                    "steps": [
                        {
                            "id": "step_1",
                            "description": "Create Python script",
                            "action_type": "create_file",
                            "target": "organize_files.py",
                            "value": "",
                            "coordinates": None
                        },
                        {
                            "id": "step_2",
                            "description": "Add categorization logic",
                            "action_type": "edit_file",
                            "target": "organize_files.py",
                            "value": "",
                            "coordinates": None
                        }
                    ],
                    "complexity_score": 0.4,
                    "estimated_duration": 10
                }
            }
            
            await websocket.send(json.dumps(suggestion))
            print("Test suggestion sent successfully!")
            
            # Wait for 5 seconds to see if there's a response
            for _ in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"Received response: {response}")
                except asyncio.TimeoutError:
                    pass
            
    except Exception as e:
        print(f"Error sending test suggestion: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_suggestion())