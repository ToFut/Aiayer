#!/usr/bin/env python3
"""
Test WebSocket client for port 8765 to test agent_confirmation message handling
"""
import asyncio
import websockets
import json
import sys
import time
from datetime import datetime

async def test_agent_confirmation():
    """Connect to port 8765 and test agent_confirmation message"""
    try:
        uri = "ws://localhost:8765"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            welcome = await websocket.recv()
            print(f"Received welcome: {welcome}")
            
            # Create a session ID
            session_id = f"test_session_{int(time.time())}"
            
            # Send agent confirmation (DO button) message
            confirmation_msg = {
                "type": "agent_confirmation",
                "session_id": session_id,
                "action": "DO",
                "modifications": {},
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Sending agent confirmation: {confirmation_msg}")
            await websocket.send(json.dumps(confirmation_msg))
            
            # Receive multiple responses and process them
            for _ in range(5):  # Try to receive 5 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    print(f"\nReceived response: {response}")
                    
                    # Parse the response
                    data = json.loads(response)
                    
                    # Check if this is a progress or completion message
                    if data.get("type") == "agent_progress":
                        print(f"✅ Progress update received: {data.get('progress')}% - {data.get('message')}")
                    
                    if data.get("type") == "agent_execution_success":
                        print(f"✅ Execution success message received!")
                        print(f"Summary: {data.get('summary')}")
                        return True
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"Error receiving response: {e}")
                    break
            
            return False
            
    except Exception as e:
        print(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_agent_confirmation())
        if result:
            print("\n✅ TEST PASSED: Successfully tested agent_confirmation handling!")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Agent confirmation handling not working properly")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest error: {e}")
        sys.exit(1)