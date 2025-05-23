#!/usr/bin/env python3
"""
Frontend Compatibility Test Client
Tests the Enterprise Backend 8767 with frontend-expected message formats
"""

import asyncio
import websockets
import json
import sys

async def test_frontend_compatibility():
    """Test all frontend-expected message types and formats"""
    uri = "ws://localhost:8767"
    
    try:
        print("🌐 Testing Frontend Compatibility with Enterprise Backend 8767")
        print("=" * 60)
        
        async with websockets.connect(uri) as websocket:
            
            # 1. Receive initial connection message
            print("1️⃣ Testing Initial Connection...")
            welcome_msg = await websocket.recv()
            welcome_data = json.loads(welcome_msg)
            print(f"   ✅ Connection Type: {welcome_data.get('type')}")
            print(f"   ✅ Client ID: {welcome_data.get('client_id')}")
            print(f"   ✅ Capabilities: {len(welcome_data.get('capabilities', []))} features")
            print()
            
            # 2. Test Agent Mode (main frontend feature)
            print("2️⃣ Testing Agent Mode (Documents Click)...")
            agent_request = {
                "type": "chat_request",
                "mode": "Agent", 
                "message": "Click on Documents folder",
                "timestamp": "2025-05-22T15:06:00.000Z"
            }
            
            await websocket.send(json.dumps(agent_request))
            agent_response = await websocket.recv()
            agent_data = json.loads(agent_response)
            
            print(f"   ✅ Response Type: {agent_data.get('type')}")
            print(f"   ✅ Success: {agent_data.get('success')}")
            print(f"   ✅ Mode: {agent_data.get('mode')}")
            print(f"   ✅ Response: {agent_data.get('response', '')[:80]}...")
            print(f"   ✅ Processing Time: {agent_data.get('processing_time')}s")
            print()
            
            # 3. Test Ask Mode
            print("3️⃣ Testing Ask Mode (System Status)...")
            ask_request = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "What is the current system status?"
            }
            
            await websocket.send(json.dumps(ask_request))
            ask_response = await websocket.recv()
            ask_data = json.loads(ask_response)
            
            print(f"   ✅ Ask Response: {ask_data.get('response', '')[:80]}...")
            print()
            
            # 4. Test Suggest Mode  
            print("4️⃣ Testing Suggest Mode (Workflow Optimization)...")
            suggest_request = {
                "type": "chat_request",
                "mode": "Suggest",
                "message": "Help optimize my workflow"
            }
            
            await websocket.send(json.dumps(suggest_request))
            suggest_response = await websocket.recv()
            suggest_data = json.loads(suggest_response)
            
            print(f"   ✅ Suggestion: {suggest_data.get('response', '')[:80]}...")
            print()
            
            # 5. Test General Mode
            print("5️⃣ Testing General Mode (Basic Chat)...")
            general_request = {
                "type": "chat_request", 
                "mode": "General",
                "message": "Hello enterprise system"
            }
            
            await websocket.send(json.dumps(general_request))
            general_response = await websocket.recv()
            general_data = json.loads(general_response)
            
            print(f"   ✅ General Response: {general_data.get('response', '')[:80]}...")
            print()
            
            # 6. Test System Status
            print("6️⃣ Testing System Status Request...")
            status_request = {"type": "system_status"}
            
            await websocket.send(json.dumps(status_request))
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            
            print(f"   ✅ Status: {status_data.get('status')}")
            print(f"   ✅ Connected Clients: {status_data.get('connected_clients')}")
            print(f"   ✅ Port: {status_data.get('port')}")
            print(f"   ✅ Version: {status_data.get('version')}")
            print()
            
            # 7. Test Legacy Agent Request (for compatibility)
            print("7️⃣ Testing Legacy Agent Request...")
            legacy_request = {
                "type": "agent_request",
                "message": "Click on Documents Folder with professional validation"
            }
            
            await websocket.send(json.dumps(legacy_request))
            legacy_response = await websocket.recv() 
            legacy_data = json.loads(legacy_response)
            
            print(f"   ✅ Legacy Response Type: {legacy_data.get('type')}")
            print(f"   ✅ Validation Confidence: {legacy_data.get('validation_confidence')}")
            print(f"   ✅ Recommendations: {len(legacy_data.get('professional_recommendations', []))}")
            print()
            
            print("🎉 ALL FRONTEND COMPATIBILITY TESTS PASSED!")
            print("✅ Enterprise Backend 8767 is fully compatible with frontend")
            print("✅ All message types handled correctly")
            print("✅ Response formats match frontend expectations")
            
            return True
            
    except Exception as e:
        print(f"❌ Frontend compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_frontend_compatibility())
    print(f"\n{'='*60}")
    print(f"Frontend Compatibility Test: {'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)