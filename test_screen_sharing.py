#!/usr/bin/env python3
"""
Test script to verify screen sharing functionality
"""
import asyncio
import websockets
import json
import time
import base64
import io
import os
import sys
from PIL import Image

async def test_screen_sharing():
    # Connect to the WebSocket server
    print("Connecting to WebSocket server...")
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Connected! Requesting screen sharing...")
        
        # Request screen sharing
        await websocket.send(json.dumps({
            "type": "start_screen_sharing",
            "resolution": "auto",
            "fps": 5,
            "compression": 80,
            "client_id": "test_client",
            "timestamp": time.time()
        }))
        
        # Create directory to save screenshots
        os.makedirs("test_screenshots", exist_ok=True)
        
        # Listen for incoming frames
        frame_count = 0
        start_time = time.time()
        
        print("Waiting for screen frames...")
        while time.time() - start_time < 10:  # Run test for 10 seconds
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                
                if data.get("type") == "screen_frame":
                    frame_count += 1
                    print(f"Received frame #{frame_count}: {data.get('width')}x{data.get('height')} ({len(data.get('data', '')) // 1024}KB)")
                    
                    # Save first and last frame
                    if frame_count == 1 or time.time() - start_time > 9:
                        # Decode base64 image
                        img_data = base64.b64decode(data.get('data', ''))
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Save image
                        filename = f"test_screenshots/frame_{frame_count}.jpg"
                        img.save(filename)
                        print(f"Saved frame to {filename}")
                
                elif data.get("type") == "screen_sharing_started":
                    print(f"Screen sharing started: FPS={data.get('fps')}, Quality={data.get('quality')}")
                    
                elif data.get("type") == "heartbeat":
                    print(f"Heartbeat: {data.get('screen_sharing_active')}, Clients: {data.get('screen_sharing_clients')}")
                    
            except asyncio.TimeoutError:
                print("No data received for 2 seconds")
                
        # Request to stop screen sharing
        print("Stopping screen sharing...")
        await websocket.send(json.dumps({
            "type": "stop_screen_sharing"
        }))
        
        # Wait for confirmation
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            data = json.loads(response)
            if data.get("type") == "screen_sharing_stopped":
                print("Screen sharing stopped successfully")
        except asyncio.TimeoutError:
            print("No stop confirmation received")
            
        print(f"Test completed. Received {frame_count} frames in {time.time() - start_time:.1f} seconds")

if __name__ == "__main__":
    asyncio.run(test_screen_sharing())