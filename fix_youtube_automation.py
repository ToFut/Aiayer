#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def execute_youtube_automation():
    """Execute YouTube automation with manual step execution"""
    
    try:
        # Connect to backend
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Register
            register_payload = {
                "type": "register",
                "payload": {
                    "client_type": "youtube_fix_client",
                    "version": "1.0.0",
                    "capabilities": ["chat", "agent_execution", "automation"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration: {reg_data.get('type', 'unknown')}")
            
            # Send YouTube automation request
            session_id = str(uuid.uuid4())
            agent_payload = {
                "type": "chat_request",
                "mode": "agent",
                "message": "open youtube and search SEGEV",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🎬 Sending YouTube automation request...")
            await websocket.send(json.dumps(agent_payload))
            
            # Wait for the plan to be created
            plan_id = None
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    print(f"📦 Received: {data.get('type', 'unknown')}")
                    
                    if data.get("plan_id"):
                        plan_id = data["plan_id"]
                        print(f"📋 Got plan ID: {plan_id}")
                        
                        # Immediately click DO button to execute
                        button_payload = {
                            "type": "button_action",
                            "action": "execute_plan",
                            "plan_id": plan_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        print(f"🟢 Clicking DO button to execute automation...")
                        await websocket.send(json.dumps(button_payload))
                        
                    elif data.get("type") == "final_response":
                        response_text = data.get("response", "")
                        print(f"\n📋 Response: {response_text}")
                        
                        if "execution" in response_text.lower() or "completed" in response_text.lower():
                            print("✅ Automation executed!")
                        else:
                            print("❓ Automation may not have executed properly")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout - trying direct execution...")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            # If we couldn't execute through the system, run direct automation
            if plan_id is None:
                print("\n🔄 Running direct YouTube automation fallback...")
                await run_direct_youtube_automation()
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n🔄 Running direct YouTube automation fallback...")
        await run_direct_youtube_automation()

async def run_direct_youtube_automation():
    """Run direct YouTube automation using pyautogui"""
    try:
        import pyautogui
        import webbrowser
        import time
        
        print("🎬 Starting direct YouTube automation...")
        
        # Step 1: Open YouTube
        print("📱 Opening YouTube...")
        youtube_url = "https://www.youtube.com/results?search_query=SEGEV"
        webbrowser.open(youtube_url)
        
        print("✅ YouTube opened with search for 'SEGEV'!")
        
        # Alternative: Use the search workflow
        print("\n🔄 Alternative: Using search workflow...")
        time.sleep(2)
        
        # Open new tab for clean search
        pyautogui.hotkey('cmd', 't')
        time.sleep(1)
        
        # Go to YouTube
        pyautogui.typewrite('youtube.com')
        pyautogui.press('enter')
        time.sleep(3)
        
        # Use YouTube search shortcut
        pyautogui.press('/')
        time.sleep(0.5)
        
        # Type search term
        pyautogui.typewrite('SEGEV')
        pyautogui.press('enter')
        
        print("✅ YouTube search automation completed!")
        
    except Exception as e:
        print(f"❌ Direct automation failed: {e}")
        print("💡 Manual steps:")
        print("   1. Open your browser")
        print("   2. Go to youtube.com")
        print("   3. Search for 'SEGEV'")

if __name__ == "__main__":
    print("🎬 YouTube Automation Fix")
    print("=" * 30)
    asyncio.run(execute_youtube_automation())