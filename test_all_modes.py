#!/usr/bin/env python3
"""
Test All Chat Modes
Tests Ask, Agent, Suggest, and General modes with the enhanced system
"""

import asyncio
import json
import websockets
import time
import sys

# Test messages for each mode
TEST_MESSAGES = {
    "Ask": "What applications are currently running on my computer?",
    "Agent": "Open Safari and search for 'Python programming'",
    "Suggest": "Can you suggest how to be more productive with my current tasks?",
    "General": "Hello, how are you today?"
}

async def test_chat_mode(mode, message):
    """Test a specific chat mode"""
    print(f"\n{'='*50}")
    print(f"TESTING {mode.upper()} MODE")
    print(f"{'='*50}")
    print(f"Message: {message}")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect('ws://localhost:8767') as websocket:
            # Register with server
            await websocket.send(json.dumps({
                "type": "register",
                "client_type": "test_client"
            }))
            
            # Wait for registration response
            response = await websocket.recv()
            print(f"Registration: {json.loads(response)['type']}")
            
            # Send chat request
            await websocket.send(json.dumps({
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "session_id": f"test_session_{int(time.time())}",
                "client_id": f"test_client_{int(time.time())}"
            }))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                response_data = json.loads(response)
                
                print(f"\nRESPONSE TYPE: {response_data.get('type', 'unknown')}")
                print(f"MODE USED: {response_data.get('mode', 'unknown')}")
                
                # Extract and display important fields
                ai_powered = response_data.get('ai_powered', False)
                brain_router_used = response_data.get('brain_router_used', False)
                real_automation_used = response_data.get('real_automation_used', False)
                interactive_mode = response_data.get('interactive_mode', False)
                
                print(f"\nAI POWERED: {ai_powered}")
                print(f"BRAIN ROUTER USED: {brain_router_used}")
                print(f"REAL AUTOMATION USED: {real_automation_used}")
                print(f"INTERACTIVE MODE: {interactive_mode}")
                
                # Display metadata if available
                if 'metadata' in response_data:
                    print("\nMETADATA:")
                    for key, value in response_data['metadata'].items():
                        print(f"  {key}: {value}")
                
                # Show the actual response
                print("\nRESPONSE CONTENT:")
                print(f"{response_data.get('response', 'No response content')}")
                
                # Check for success
                return True, response_data.get('response', '')
                
            except asyncio.TimeoutError:
                print("ERROR: Response timed out after 20 seconds")
                return False, "Timeout"
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, str(e)

async def main():
    """Test all chat modes"""
    print("TESTING ALL CHAT MODES WITH THE ENHANCED SYSTEM")
    print("==============================================")
    
    results = {}
    
    # Test each mode
    for mode, message in TEST_MESSAGES.items():
        success, response = await test_chat_mode(mode, message)
        results[mode] = {
            "success": success,
            "response_snippet": response[:100] + "..." if len(response) > 100 else response
        }
    
    # Print summary
    print("\n\nTEST RESULTS SUMMARY")
    print("===================")
    
    all_successful = True
    for mode, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"{mode} Mode: {status}")
        if not result["success"]:
            all_successful = False
    
    if all_successful:
        print("\n✅ ALL MODES WORKING SUCCESSFULLY!")
        return 0
    else:
        print("\n⚠️ SOME MODES FAILED - CHECK LOGS")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)