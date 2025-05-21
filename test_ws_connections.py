#!/usr/bin/env python3
"""
Test script to verify WebSocket connections to the bridge server and LLM service
"""
import asyncio
import websockets
import json
import sys

async def test_bridge_connection():
    """Test connection to bridge server"""
    bridge_uri = "ws://localhost:8768"
    
    try:
        print(f"Attempting to connect to bridge server at {bridge_uri}...")
        async with websockets.connect(bridge_uri) as websocket:
            print("Connected to bridge server!")
            
            # Send registration message (using one of the expected client types)
            await websocket.send(json.dumps({
                "type": "register",
                "client_type": "ui"  # Valid types: sensor, memory, llm, ui, application, other
            }))
            
            # Wait for response
            print("Waiting for bridge server response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"Received response: {response}")
                return True
            except asyncio.TimeoutError:
                print("Timeout waiting for bridge server response")
                return False
                
    except (ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
        print(f"Failed to connect to bridge server: {e}")
        return False

async def test_llm_connection():
    """Test connection to LLM service"""
    llm_uri = "ws://localhost:8770"
    
    try:
        print(f"Attempting to connect to LLM service at {llm_uri}...")
        async with websockets.connect(llm_uri) as websocket:
            print("Connected to LLM service!")
            
            # Wait for welcome message
            print("Waiting for LLM service welcome message...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"Received welcome message: {response}")
                
                # Send test message
                test_message = {
                    "type": "llm_request",
                    "message": "Hello, this is a test message"
                }
                
                print(f"Sending test message: {json.dumps(test_message)}")
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                print("Waiting for LLM response...")
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    print(f"Received LLM response: {response}")
                    return True
                except asyncio.TimeoutError:
                    print("Timeout waiting for LLM service response")
                    return False
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for LLM service welcome message")
                return False
                
    except (ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
        print(f"Failed to connect to LLM service: {e}")
        return False

async def main():
    """Run all tests"""
    print("=== Testing WebSocket Connections ===")
    
    # Test bridge server connection
    bridge_result = await test_bridge_connection()
    
    # Test LLM service connection
    llm_result = await test_llm_connection()
    
    # Print summary
    print("\n=== Test Results ===")
    print(f"Bridge Server: {'✅ CONNECTED' if bridge_result else '❌ FAILED'}")
    print(f"LLM Service:   {'✅ CONNECTED' if llm_result else '❌ FAILED'}")
    
    # Return exit code based on results
    if bridge_result and llm_result:
        print("\nAll connections successful!")
        return 0
    else:
        print("\nSome connections failed. Check error messages above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)