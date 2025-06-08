#!/usr/bin/env python3
"""
Test script for overlay screen sharing
This will simulate a frontend client and a bridge server message to verify screen sharing
"""
import asyncio
import websockets
import json
import time
import base64
import io
import os
from PIL import Image

async def test_overlay_screen_sharing():
    print("Connecting to automation WebSocket server on port 8765...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("Connected successfully")
            
            # Register as client
            await websocket.send(json.dumps({
                "type": "register",
                "client_id": "overlay_test_client",
                "client_type": "overlay_ui"
            }))
            
            # Wait for welcome message
            response = await websocket.recv()
            print(f"Received: {response[:100]}...")
            
            # Request screen sharing (in the format overlay bridge.js uses)
            await websocket.send(json.dumps({
                "type": "start_screen_sharing",
                "resolution": "auto",
                "fps": 5,
                "compression": 80,
                "client_id": "overlay_test_client",
                "timestamp": time.time()
            }))
            
            print("Requested screen sharing")
            
            # Create directory for test frames
            os.makedirs("test_overlay_frames", exist_ok=True)
            
            # Listen for screen frames
            print("Waiting for screen frames...")
            frame_count = 0
            start_time = time.time()
            
            while time.time() - start_time < 10:  # Run for 10 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "screen_frame":
                        frame_count += 1
                        print(f"✅ Received frame #{frame_count}: {data.get('width')}x{data.get('height')}, size: {len(data.get('data', '')) // 1024}KB")
                        
                        # Save first frame for verification
                        if frame_count == 1:
                            img_data = base64.b64decode(data.get('data', ''))
                            img = Image.open(io.BytesIO(img_data))
                            
                            frame_path = f"test_overlay_frames/overlay_frame_{int(time.time())}.jpg"
                            img.save(frame_path)
                            print(f"Saved frame to {frame_path}")
                    
                    elif data.get("type") == "screen_sharing_started":
                        print(f"Screen sharing started confirmation received - FPS: {data.get('fps')}, Quality: {data.get('quality')}")
                    
                    elif data.get("type") == "heartbeat":
                        print(f"Heartbeat received: Screen sharing active: {data.get('screen_sharing_active')}, Clients: {data.get('screen_sharing_clients')}")
                
                except asyncio.TimeoutError:
                    print("No data received for 2 seconds")
            
            # Stop screen sharing
            await websocket.send(json.dumps({
                "type": "stop_screen_sharing"
            }))
            
            # Wait for confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Stop sharing response: {response}")
            
            print(f"Test completed. Received {frame_count} screen frames in {time.time() - start_time:.1f} seconds")
            
            if frame_count > 0:
                print("✅ SCREEN SHARING IS WORKING CORRECTLY")
            else:
                print("❌ SCREEN SHARING FAILED - No frames received")
    
    except Exception as e:
        print(f"Error connecting to automation server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_overlay_screen_sharing())