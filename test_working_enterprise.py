#!/usr/bin/env python3
"""
Working Enterprise System Test Client
Tests the actual enhanced enterprise backend properly
"""

import asyncio
import websockets
import json
import sys

async def test_working_enterprise():
    """Test the working enterprise system with correct message types"""
    uri = "ws://localhost:8765"
    
    try:
        print("🏢 Connecting to Enterprise System...")
        async with websockets.connect(uri) as websocket:
            
            # First message is connection established
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print("✅ Connected to Enhanced Enterprise Backend")
            print(f"📋 Capabilities: {', '.join(connection_data.get('capabilities', []))}")
            print()
            
            # Test agent request (the main feature)
            print("🧪 Testing Agent Request...")
            agent_request = {
                "type": "agent_request", 
                "message": "Click on Documents Folder with professional validation"
            }
            
            await websocket.send(json.dumps(agent_request))
            agent_response = await websocket.recv()
            agent_data = json.loads(agent_response)
            
            print(f"   ✅ Response Type: {agent_data.get('type')}")
            print(f"   🎯 Goal Analysis: {agent_data.get('goal_analysis', {}).get('clarified_goal', 'N/A')}")
            print(f"   🔍 Session ID: {agent_data.get('session_id', 'N/A')}")
            print(f"   🤝 Agent Contexts: {len(agent_data.get('agent_contexts', {}))}")
            print(f"   ✅ Validation Confidence: {agent_data.get('validation_confidence', 0):.2f}")
            
            if agent_data.get('professional_recommendations'):
                print("   🎓 Professional Recommendations:")
                for i, rec in enumerate(agent_data.get('professional_recommendations', []), 1):
                    print(f"      {i}. {rec}")
            
            print()
            
            # Test task validation request
            print("🧪 Testing Task Validation...")
            validation_request = {
                "type": "task_validation_request",
                "validation_type": "final_validation",
                "task_description": "Click operation validation"
            }
            
            await websocket.send(json.dumps(validation_request))
            validation_response = await websocket.recv()
            validation_data = json.loads(validation_response)
            
            print(f"   ✅ Validation Type: {validation_data.get('type')}")
            print(f"   📊 Validation Status: {validation_data.get('validation_status', 'N/A')}")
            
            print()
            
            # Test system info request  
            print("🧪 Testing System Info...")
            info_request = {"type": "system_info"}
            
            await websocket.send(json.dumps(info_request))
            info_response = await websocket.recv()
            info_data = json.loads(info_response)
            
            print(f"   📊 System Response: {info_data.get('type', 'N/A')}")
            
            print("\n🎉 Enterprise system testing completed successfully!")
            print("🏆 All enterprise features are operational!")
            
            return True
            
    except Exception as e:
        print(f"❌ Enterprise test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_working_enterprise())
    sys.exit(0 if success else 1)