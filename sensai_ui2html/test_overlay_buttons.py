#!/usr/bin/env python3
"""
Test Overlay Buttons - Verify the overlay is receiving real button data
"""

import json
import requests
import time

def test_overlay_buttons():
    """Test that the overlay is receiving real button data"""
    print("🔍 Testing Overlay Button Data")
    print("=" * 50)
    
    try:
        # Test the backend API directly
        response = requests.get('http://localhost:8767/ui_context')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend API responding")
            print(f"📊 App: {data.get('app_name', 'Unknown')}")
            print(f"📊 UI Elements: {data.get('ui_elements_count', 0)}")
            print(f"📊 Buttons: {len(data.get('buttons', []))}")
            
            # Show some sample buttons
            buttons = data.get('buttons', [])
            if buttons:
                print(f"\n🔘 Sample Buttons Found:")
                for i, button in enumerate(buttons[:10]):
                    print(f"  {i+1}. {button.get('name', 'Unknown')} ({button.get('type', 'Unknown')})")
                
                if len(buttons) > 10:
                    print(f"  ... and {len(buttons) - 10} more buttons")
            else:
                print("❌ No buttons found in response")
        else:
            print(f"❌ Backend API error: {response.status_code}")
            
        # Test the WebSocket connection
        print(f"\n🔌 Testing WebSocket connection...")
        import websocket
        import threading
        
        received_messages = []
        
        def on_message(ws, message):
            received_messages.append(json.loads(message))
            print(f"📨 Received: {message[:100]}...")
        
        def on_error(ws, error):
            print(f"❌ WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("🔌 WebSocket connection closed")
        
        def on_open(ws):
            print("🔌 WebSocket connection opened")
            # Send a test message
            ws.send(json.dumps({
                "type": "query",
                "message": "What can I interact with?"
            }))
        
        # Connect to WebSocket
        ws = websocket.WebSocketApp(
            "ws://localhost:8767/ws",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run WebSocket in a thread
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for messages
        time.sleep(3)
        
        if received_messages:
            print(f"✅ WebSocket working - received {len(received_messages)} messages")
            for msg in received_messages:
                if msg.get('type') == 'response':
                    print(f"🤖 AI Response: {msg.get('message', '')[:100]}...")
        else:
            print("❌ No WebSocket messages received")
        
        ws.close()
        
    except Exception as e:
        print(f"❌ Error testing overlay: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_overlay_buttons() 