#!/usr/bin/env python3
"""
Test script to verify that the bridge server properly forwards screen sharing requests
"""
import asyncio
import websockets
import json
import time
import os
import base64
import io
from PIL import Image

async def test_bridge_screen_sharing():
    print("Connecting to bridge server on port 8766...")
    
    try:
        async with websockets.connect("ws://localhost:8766") as bridge_ws:
            print("Connected to bridge server successfully")
            
            # Register with the bridge server
            await bridge_ws.send(json.dumps({
                "type": "register",
                "payload": {
                    "client_type": "ui",
                    "client_id": "test_bridge_client",
                    "capabilities": ["screen_sharing"],
                    "timestamp": time.time() * 1000
                }
            }))
            
            # Wait for bridge server to respond
            try:
                response = await asyncio.wait_for(bridge_ws.recv(), timeout=5)
                print(f"Registration response: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No registration response received")
            
            # Request screen sharing (with nested payload as used by bridge.js)
            await bridge_ws.send(json.dumps({
                "type": "start_screen_sharing",
                "payload": {
                    "resolution": "auto",
                    "fps": 5,
                    "compression": 80,
                    "client_id": "test_bridge_client",
                    "timestamp": time.time() * 1000
                }
            }))
            
            print("Screen sharing request sent via bridge")
            
            # Create directory for saving frames
            os.makedirs("test_bridge_frames", exist_ok=True)
            
            # Listen for responses for 10 seconds
            print("Waiting for screen frames via bridge...")
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(bridge_ws.recv(), timeout=1)
                    data = json.loads(response)
                    message_type = data.get("type", "")
                    
                    print(f"Received message type: {message_type}")
                    
                    if message_type == "screen_frame":
                        frame_count += 1
                        frame_data = data.get("data", "")
                        width = data.get("width", 0)
                        height = data.get("height", 0)
                        
                        print(f"✅ Screen frame #{frame_count} received: {width}x{height}, size: {len(frame_data) // 1024}KB")
                        
                        # Save first frame
                        if frame_count == 1:
                            try:
                                # Decode base64 image
                                img_data = base64.b64decode(frame_data)
                                img = Image.open(io.BytesIO(img_data))
                                
                                # Save image
                                frame_path = f"test_bridge_frames/bridge_frame_{int(time.time())}.jpg"
                                img.save(frame_path)
                                print(f"Saved frame to {frame_path}")
                            except Exception as e:
                                print(f"Error saving frame: {e}")
                    
                    elif message_type == "screen_sharing_started":
                        print(f"✅ Screen sharing started via bridge")
                    
                except asyncio.TimeoutError:
                    print("Waiting for response...")
            
            # Stop screen sharing
            await bridge_ws.send(json.dumps({
                "type": "stop_screen_sharing",
                "payload": {}
            }))
            
            print("Screen sharing stop request sent")
            
            try:
                stop_response = await asyncio.wait_for(bridge_ws.recv(), timeout=2)
                print(f"Stop response: {stop_response[:100]}...")
            except asyncio.TimeoutError:
                print("No stop response received")
            
            print("\nTest Results:")
            print(f"Frames received: {frame_count}")
            
            if frame_count > 0:
                print("✅ BRIDGE SCREEN SHARING IS WORKING!")
                return True
            else:
                print("❌ BRIDGE SCREEN SHARING FAILED - No frames received")
                return False
    
    except Exception as e:
        print(f"Error connecting to bridge server: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bridge_screen_sharing())