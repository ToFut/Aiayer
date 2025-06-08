#\!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
from datetime import datetime
import argparse

async def send_overlay_notification(message, importance="high", play_sound=True, port=8766, custom_buttons=False):
    """Send a notification to the overlay"""
    ws_url = f"ws://localhost:{port}"
    
    try:
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            # Wait for welcome message
            try:
                await asyncio.wait_for(ws.recv(), timeout=2.0)
            except asyncio.TimeoutError:
                print(f"No welcome message received from port {port}, continuing anyway...")
            
            # Define buttons
            buttons = []
            if custom_buttons:
                buttons = [
                    {"text": "View Details", "value": "view", "style": "primary"},
                    {"text": "Take Action", "value": "action", "style": "success"},
                    {"text": "Dismiss", "value": "dismiss", "style": "danger"}
                ]
            else:
                buttons = [
                    {"text": "OK", "value": "ok", "style": "success"},
                    {"text": "Dismiss", "value": "dismiss", "style": "danger"}
                ]
            
            # Create notification - using the CORRECT format with type "suggestion"
            notification = {
                "type": "suggestion",  # This is critical - must be "suggestion", not "message"
                "response": message,   # Content goes in "response", not "message"
                "buttons": buttons,
                "importance": importance,
                "play_sound": play_sound,
                "plan_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Sending notification to port {port}: {json.dumps(notification)}")
            
            # Send notification
            await ws.send(json.dumps(notification))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Received response: {response}")
                return True
            except asyncio.TimeoutError:
                print("No response received within timeout")
                return False
    except Exception as e:
        print(f"Error connecting to port {port}: {e}")
        return False

async def try_all_ports(message, importance="high", play_sound=True, custom_buttons=False):
    """Try sending notification to all possible ports"""
    ports = [8765, 8766, 8767, 8768]
    
    for port in ports:
        print(f"Trying port {port}...")
        success = await send_overlay_notification(
            message, 
            importance=importance, 
            play_sound=play_sound, 
            port=port,
            custom_buttons=custom_buttons
        )
        if success:
            print(f"Successfully sent notification via port {port}")
            return True
        else:
            print(f"Failed to send notification via port {port}")
    
    print("Failed to send notification via any port")
    return False

def main():
    parser = argparse.ArgumentParser(description='Send a notification to the overlay')
    parser.add_argument('--message', type=str, required=True, help='Notification message')
    parser.add_argument('--importance', type=str, default='high', choices=['high', 'medium', 'low'], 
                        help='Importance level (high, medium, low)')
    parser.add_argument('--no-sound', action='store_true', help='Disable notification sound')
    parser.add_argument('--port', type=int, default=8766, help='WebSocket port (use 0 to try all ports)')
    parser.add_argument('--custom-buttons', action='store_true', help='Use custom buttons')
    
    args = parser.parse_args()
    
    play_sound = not args.no_sound
    
    if args.port == 0:
        asyncio.run(try_all_ports(args.message, args.importance, play_sound, args.custom_buttons))
    else:
        asyncio.run(send_overlay_notification(
            args.message, 
            args.importance, 
            play_sound, 
            args.port,
            args.custom_buttons
        ))

if __name__ == "__main__":
    main()
