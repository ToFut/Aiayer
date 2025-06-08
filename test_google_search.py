#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def search_for_python():
    """Test script to search for Python on Google"""
    print("Connecting to automation server...")
    
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Connected to server")
        
        # Create a simple plan to search for Python on Google
        plan = {
            "title": "Search for Python on Google",
            "steps": [
                {
                    "type": "open_app",
                    "target": "Safari",
                    "description": "Open Safari browser"
                },
                {
                    "type": "wait",
                    "duration": 2,
                    "description": "Wait for Safari to open"
                },
                {
                    "type": "type_text",
                    "text": "google.com",
                    "description": "Type google.com"
                },
                {
                    "type": "press_key",
                    "key": "enter",
                    "description": "Press Enter to go to Google"
                },
                {
                    "type": "wait",
                    "duration": 2,
                    "description": "Wait for Google to load"
                },
                {
                    "type": "type_text",
                    "text": "Python programming",
                    "description": "Type search query: Python programming"
                },
                {
                    "type": "press_key",
                    "key": "enter",
                    "description": "Press Enter to search"
                }
            ]
        }
        
        # Store the plan
        session_id = f"test_{int(time.time())}"
        await websocket.send(json.dumps({
            "type": "plan_created",
            "plan": plan,
            "session_id": session_id
        }))
        
        print(f"Plan sent with session ID: {session_id}")
        
        # Wait for confirmation
        response = await websocket.recv()
        print(f"Server response: {response}")
        
        # Execute the plan
        await websocket.send(json.dumps({
            "type": "agent_confirmation",
            "action": "DO",
            "session_id": session_id
        }))
        
        print("Execution requested, waiting for updates...")
        
        # Listen for execution updates
        start_time = time.time()
        while time.time() - start_time < 30:  # Listen for 30 seconds max
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                
                if data.get("type") == "agent_progress":
                    print(f"Progress: {data.get('progress')}% - {data.get('message')}")
                
                elif data.get("type") == "agent_execution_success":
                    print(f"Execution completed: {data.get('summary')}")
                    print(f"Result: {json.dumps(data.get('result', {}), indent=2)}")
                    break
                    
            except asyncio.TimeoutError:
                continue

if __name__ == "__main__":
    asyncio.run(search_for_python())