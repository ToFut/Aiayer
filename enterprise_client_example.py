#!/usr/bin/env python3
"""
Enterprise Client Example - Professional Agent Interaction
Demonstrates self-reflection and collaboration capabilities
"""

import asyncio
import websockets
import json

async def enterprise_demo():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        print("🏢 Connected to Enterprise Agent System")
        
        # Test professional agent request with self-reflection
        request = {
            "type": "agent_request",
            "message": "Click on Documents Folder with professional validation and agent collaboration"
        }
        
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        data = json.loads(response)
        
        print(f"📋 Response Type: {data.get('type')}")
        print(f"🎯 Goal Analysis: {data.get('goal_analysis', {}).get('clarified_goal')}")
        print(f"🔍 Session ID: {data.get('session_id')}")
        print(f"🤝 Agent Contexts: {len(data.get('agent_contexts', {}))}")
        print(f"✅ Professional Grade: {data.get('validation_confidence', 0):.2f}")
        
        print("\n🎓 Professional Recommendations:")
        for i, rec in enumerate(data.get('professional_recommendations', []), 1):
            print(f"  {i}. {rec}")

if __name__ == "__main__":
    asyncio.run(enterprise_demo())
