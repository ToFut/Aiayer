#!/usr/bin/env python3
"""
Test Working Backend - Test both HTTP and WebSocket functionality
"""

import json
import requests
import time
import websocket
import threading

def test_working_backend():
    """Test the working backend with both HTTP and WebSocket."""
    print("🔍 Testing Working Backend")
    print("=" * 50)
    
    try:
        # Test HTTP API
        print("📡 Testing HTTP API...")
        response = requests.get('http://localhost:8768/ui_context', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP API working!")
            print(f"📊 App: {data.get('app_name', 'Unknown')}")
            print(f"📊 UI Elements: {data.get('element_count', 0)}")
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
                print("❌ No buttons found in HTTP response")
        else:
            print(f"❌ HTTP API error: {response.status_code}")
            
        # Test health endpoint
        print(f"\n🏥 Testing Health API...")
        health_response = requests.get('http://localhost:8768/health', timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health API working!")
            print(f"📊 Status: {health_data.get('status', 'Unknown')}")
            print(f"📊 UI Sensor Running: {health_data.get('ui_sensor_running', False)}")
            print(f"📊 Clients Connected: {health_data.get('clients_connected', 0)}")
        else:
            print(f"❌ Health API error: {health_response.status_code}")
            
        # Test WebSocket connection
        print(f"\n🔌 Testing WebSocket connection...")
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
    test_working_backend() 