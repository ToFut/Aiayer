#!/usr/bin/env python3
"""
Simple test script for the Neural UI Detector WebSocket server
"""
import asyncio
import websockets
import json
import sys
import time

async def test_detector(port=8768):
    """Test the Neural UI Detector WebSocket server"""
    print(f"Connecting to Neural UI Detector WebSocket server on port {port}...")
    
    try:
        async with websockets.connect(f"ws://localhost:{port}") as websocket:
            print("Connected!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"Received welcome message: {welcome_data}")
            
            # Send detect request
            print("\nSending detect request...")
            detect_request = {
                "action": "detect",
                "refresh": True  # Force a fresh detection
            }
            await websocket.send(json.dumps(detect_request))
            
            # Wait for response with timeout
            print("Waiting for response (timeout: 30s)...")
            start_time = time.time()
            response = await websocket.recv()
            response_time = time.time() - start_time
            
            print(f"Response received in {response_time:.2f} seconds")
            response_data = json.loads(response)
            
            if response_data.get("type") == "detection_result":
                print("\nDetection Results:")
                print(f"Timestamp: {response_data.get('timestamp')}")
                print(f"Elements found: {response_data.get('count')}")
                print(f"Detection methods: {response_data.get('methods')}")
                print(f"Execution time: {response_data.get('execution_time')}s")
                
                # Print details of detected elements
                elements = response_data.get("elements", [])
                if elements:
                    print("\nDetected Elements:")
                    for i, elem in enumerate(elements, 1):
                        print(f"\nElement {i}:")
                        print(f"  Type: {elem.get('element_type')}")
                        print(f"  Confidence: {elem.get('confidence'):.2f}")
                        print(f"  Text: {elem.get('text', 'N/A')}")
                        print(f"  Bounding Box: {elem.get('bounding_box')}")
                        print(f"  Center: {elem.get('center')}")
                        print(f"  Detection Method: {elem.get('detection_method')}")
            else:
                print(f"Unexpected response type: {response_data.get('type')}")
                print(f"Response data: {response_data}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Use port from command line argument if provided
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8768
    asyncio.run(test_detector(port))