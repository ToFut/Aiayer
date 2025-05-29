#!/usr/bin/env python3

import websocket
import json
import time
import threading

def test_agent_mode_fix():
    """Test Agent mode with the original flight search request to verify real automation"""
    
    print("🧪 Testing Fixed Agent Mode - Flight Search Automation")
    print("=" * 60)
    
    response_received = False
    
    def on_message(ws, message):
        nonlocal response_received
        try:
            data = json.loads(message)
            print(f"\n📨 Response Type: {data.get('type', 'unknown')}")
            
            if data.get('type') == 'chat_response':
                response_received = True
                mode = data.get('mode', 'unknown')
                response = data.get('response', '')
                
                print(f"🤖 Mode: {mode}")
                print(f"💬 Response Preview: {response[:300]}...")
                
                # Check for automation indicators vs explanation indicators
                automation_keywords = [
                    'clicking', 'typing', 'opening', 'navigating', 'automating',
                    'executing', 'performing', 'controlling', 'step 1', 'step 2',
                    'automation plan', 'ui automation', 'screen control', 'browser',
                    'safari', 'chrome', 'website', 'navigate to'
                ]
                
                explanation_keywords = [
                    'i recommend', 'you should', 'consider visiting', 'suggests',
                    'would be to', 'here are some', 'you might want to',
                    'i can explain', 'let me explain', 'best practices'
                ]
                
                automation_score = sum(1 for keyword in automation_keywords if keyword.lower() in response.lower())
                explanation_score = sum(1 for keyword in explanation_keywords if keyword.lower() in response.lower())
                
                print(f"\n🔍 Analysis:")
                print(f"   Automation indicators: {automation_score}")
                print(f"   Explanation indicators: {explanation_score}")
                
                if automation_score > explanation_score:
                    print("✅ SUCCESS: Agent mode is providing REAL AUTOMATION!")
                elif automation_score == 0 and explanation_score > 0:
                    print("❌ FAILURE: Agent mode is still giving explanations")
                else:
                    print("⚠️  MIXED: Response contains both automation and explanation elements")
                    
                print(f"\n💬 Full Response:\n{response}")
                
            elif data.get('type') == 'execution_step':
                print(f"🔧 Execution Step: {data.get('step', '')}")
                print(f"   Status: {data.get('status', '')}")
                
        except Exception as e:
            print(f"❌ Error parsing message: {e}")
            print(f"Raw message: {message[:200]}...")

    def on_error(ws, error):
        print(f"❌ WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("🔌 WebSocket connection closed")

    def on_open(ws):
        print("✅ Connected to backend")
        
        # Send the same flight search request that was failing before
        test_message = {
            "type": "chat_request",
            "mode": "agent",
            "message": "search for best flights from nyc to miami",
            "client_id": "test_client_agent_fix"
        }
        
        print(f"\n📤 Sending Agent mode request:")
        print(f"   Mode: agent")
        print(f"   Message: '{test_message['message']}'")
        print(f"   Expected: Real UI automation (opening browser, navigating to flight sites, etc.)")
        print(f"   Previous Issue: Was giving explanations instead of automation")
        print("\n⏳ Waiting for response...")
        
        ws.send(json.dumps(test_message))

    try:
        ws = websocket.WebSocketApp("ws://localhost:8767/ws",
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        print("🔌 Connecting to Enhanced Backend...")
        
        # Run with timeout
        def run_with_timeout():
            ws.run_forever()
        
        thread = threading.Thread(target=run_with_timeout)
        thread.daemon = True
        thread.start()
        
        # Wait for response with timeout
        timeout = 20
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if response_received:
                print("\n✅ Test completed successfully!")
                break
            time.sleep(0.5)
        else:
            print("\n⏰ Test timed out - no response received")
            
        ws.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_agent_mode_fix()