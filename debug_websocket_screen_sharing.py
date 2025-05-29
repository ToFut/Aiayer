
# Add this to your backend WebSocket message handler

async def handle_screen_sharing_request(websocket, data):
    """Handle screen sharing requests with debug logging."""
    print(f"🖥️  Screen sharing request received: {data}")
    
    try:
        # Import screen capture functionality
        from realtime_screen_tcp_server import RealtimeScreenTCPServer
        
        # Create or get screen server instance
        if not hasattr(websocket, 'screen_server'):
            websocket.screen_server = RealtimeScreenTCPServer()
            await websocket.screen_server.start()
        
        # Get compressed frame data
        frame_data = websocket.screen_server.get_compressed_frame_data()
        
        if frame_data:
            # Send frame to client
            await websocket.send(json.dumps(frame_data))
            print(f"✅ Screen frame sent: {frame_data['width']}x{frame_data['height']}")
        else:
            print("⚠️  No screen frame data available")
            await websocket.send(json.dumps({
                "type": "screen_sharing_error",
                "message": "No screen data available"
            }))
            
    except Exception as e:
        print(f"❌ Screen sharing error: {e}")
        await websocket.send(json.dumps({
            "type": "screen_sharing_error", 
            "message": str(e)
        }))

# Add to your WebSocket message router:
if message_type == "start_screen_sharing":
    await handle_screen_sharing_request(websocket, data)
