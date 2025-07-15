#!/usr/bin/env python3
"""
Test Final Backend - Simple WebSocket test
"""

import json
import time
import websocket
import threading

def test_final_backend():
    """Test the final backend with WebSocket only."""
    print("🔍 Testing Final Backend")
    print("=" * 50)
    
    try:
        # Test WebSocket connection
        print("🔌 Testing WebSocket connection...")
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
                elif msg.get('type') == 'ui_context_update':
                    payload = msg.get('payload', {})
                    print(f"📊 UI Update: {payload.get('app_name', 'Unknown')} with {len(payload.get('buttons', []))} buttons")
        else:
            print("❌ No WebSocket messages received")
        
        ws.close()
        
        print(f"\n🎉 Testing complete!")
        
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_backend() 