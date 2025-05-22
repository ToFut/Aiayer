#!/usr/bin/env python3
"""
Test Context-Aware LLM Integration
Tests the enhanced context memory with LLM responses.
"""
import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def send_message(websocket, message_type, payload=None):
    """Send a message to the websocket server"""
    if payload is None:
        payload = {}
    
    message = {
        "type": message_type,
        "payload": payload,
        "timestamp": datetime.now().isoformat()
    }
    
    await websocket.send(json.dumps(message))
    print(f"Sent {message_type} message")

async def test_context_integration():
    """Test the context integration with LLM"""
    # Connect to bridge server
    bridge_uri = "ws://localhost:8767"
    
    try:
        print(f"Connecting to bridge server at {bridge_uri}...")
        async with websockets.connect(bridge_uri) as websocket:
            print("Connected to bridge server")
            
            # Send identification
            await send_message(websocket, "connection_established", {
                "client": "test_client",
                "version": "1.0.0",
                "capabilities": ["testing"]
            })
            
            # Wait for server_ready message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data['type']}")
            
            # Wait to ensure the system has received sensor data
            print("Waiting for sensors to send data...")
            await asyncio.sleep(5)
            
            # Send LLM request
            test_query = input("Enter a query to test the LLM with context (or press Enter for default): ")
            if not test_query:
                test_query = "What am I currently doing on my computer? Please provide specific details about my current activity."
            
            print(f"Sending LLM request: {test_query}")
            await send_message(websocket, "llm_request", {
                "query": test_query,
                "conversation_id": "test_conversation",
                "request_id": "test_1"
            })
            
            # Wait for response
            print("Waiting for LLM response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data['type'] == 'llm_response':
                llm_response = response_data['payload']
                print("\n===== LLM RESPONSE =====")
                print(f"Model: {llm_response.get('model', 'unknown')}")
                print(f"Context used: {llm_response.get('context_used', False)}")
                print(f"Enhanced context used: {llm_response.get('enhanced_context_used', False)}")
                print(f"Processing time: {llm_response.get('processing_time', 0):.2f}s")
                print("\nResponse:")
                print(llm_response.get('response', 'No response received'))
                print("=======================\n")
            else:
                print(f"Unexpected response type: {response_data['type']}")
                print(response_data)
                
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

async def test_context_memory_server():
    """Test the context memory server directly"""
    context_uri = "ws://localhost:8769"
    
    try:
        print(f"Connecting to context memory server at {context_uri}...")
        async with websockets.connect(context_uri) as websocket:
            print("Connected to context memory server")
            
            # Send identification
            await send_message(websocket, "connection_established", {
                "client": "test_client",
                "version": "1.0.0",
                "capabilities": ["testing"]
            })
            
            # Wait for server_ready message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data['type']}")
            
            # Get enhanced context
            print("Requesting enhanced context...")
            await send_message(websocket, "get_enhanced_context")
            
            # Wait for response
            response = await websocket.recv()
            context_data = json.loads(response)
            
            if context_data['type'] == 'enhanced_context':
                context = context_data['payload']
                print("\n===== ENHANCED CONTEXT =====")
                
                # Display application context
                if "current_application" in context and context["current_application"]:
                    app = context["current_application"]
                    print("Application Context:")
                    print(f"  Name: {app.get('name', 'unknown')}")
                    print(f"  Window: {app.get('window', '')}")
                    print(f"  View: {app.get('view', '')}")
                    print(f"  User Task: {app.get('workflow', '')}")
                
                # Display screen context
                if "screen_context" in context and context["screen_context"]:
                    screen = context["screen_context"]
                    print("\nScreen Context:")
                    if "visual_description" in screen:
                        desc = screen["visual_description"]
                        if len(desc) > 200:
                            desc = desc[:200] + "..."
                        print(f"  Description: {desc}")
                    if "ui_elements" in screen and screen["ui_elements"]:
                        print("  UI Elements:")
                        for elem in screen["ui_elements"][:3]:
                            print(f"    - {elem.get('name', '')} ({elem.get('type', 'unknown')})")
                
                # Display recent activities
                if "recent_activities" in context and context["recent_activities"]:
                    print("\nRecent Activities:")
                    for activity in context["recent_activities"][:3]:
                        print(f"  - {activity.get('action', 'unknown')} in {activity.get('application', 'unknown')}")
                
                print("=============================\n")
            else:
                print(f"Unexpected response type: {context_data['type']}")
                print(context_data)
                
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "context":
        # Test only the context memory server
        success = await test_context_memory_server()
    else:
        # Test the full integration
        success = await test_context_integration()
    
    if success:
        print("Test completed successfully")
    else:
        print("Test failed")

if __name__ == "__main__":
    asyncio.run(main())