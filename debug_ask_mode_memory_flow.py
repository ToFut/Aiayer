#!/usr/bin/env python3
"""
Debug ASK Mode Memory Flow

This script analyzes why ASK/Suggest modes aren't giving contextual answers
by testing each component in the memory retrieval pipeline.
"""

import asyncio
import json
import os
import sys
import websockets
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_memory_retrieval_directly():
    """Test memory retrieval directly without websocket"""
    print("🔍 Testing Memory Retrieval Components")
    print("=" * 50)
    
    try:
        # Test 1: Check if memory file exists and is readable
        memory_file = "memory/memory_state.json"
        print(f"📁 Memory file: {memory_file}")
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
            
            print(f"✅ Memory file loaded successfully")
            print(f"   - Version: {memory_data.get('version', 'unknown')}")
            print(f"   - Last update: {memory_data.get('last_update', 'unknown')}")
            print(f"   - Short-term memories: {len(memory_data.get('short_term', []))}")
            print(f"   - Long-term memories: {len(memory_data.get('long_term', []))}")
            
            # Test 2: Check memory content quality
            short_term = memory_data.get('short_term', [])
            if short_term:
                latest_memory = short_term[-1]
                print(f"\n📝 Latest memory sample:")
                print(f"   - Type: {latest_memory.get('memory_type')}")
                print(f"   - Timestamp: {latest_memory.get('timestamp')}")
                
                if 'user_activity' in latest_memory:
                    activity = latest_memory['user_activity']
                    print(f"   - Activity: {activity.get('primary_activity')}")
                    print(f"   - Application: {activity.get('application_used')}")
                    print(f"   - Productivity: {activity.get('productivity_score')}")
                
                if 'insights' in latest_memory:
                    insights = latest_memory['insights']
                    print(f"   - Insights: {insights}")
            
            # Test 3: Check if memory contains development-related content
            dev_keywords = ['development', 'coding', 'cursor', 'software', 'programming']
            dev_content_found = False
            
            for memory in short_term:
                memory_str = json.dumps(memory).lower()
                if any(keyword in memory_str for keyword in dev_keywords):
                    dev_content_found = True
                    break
            
            print(f"\n💻 Development content found: {'✅ Yes' if dev_content_found else '❌ No'}")
            
        else:
            print(f"❌ Memory file not found: {memory_file}")
            return False
        
        # Test 4: Test ASK mode handler import
        print(f"\n🧠 Testing ASK Mode Handler Import")
        try:
            from brain.handlers.ask_mode_handler import RealMemoryRetriever, QueryAnalyzer, RealResponseGenerator
            print("✅ ASK mode handler components imported successfully")
            
            # Test 5: Test memory retriever initialization
            memory_retriever = RealMemoryRetriever()
            print(f"✅ RealMemoryRetriever initialized")
            print(f"   - Memory file path: {memory_retriever.memory_file}")
            
            # Test 6: Test actual memory retrieval
            print(f"\n🔄 Testing Memory Context Retrieval")
            test_query = "What development activities have I been doing?"
            context = await memory_retriever.retrieve_context(test_query, "test_user", "test_session")
            
            print(f"✅ Memory context retrieved")
            print(f"   - Confidence: {context.confidence_score}")
            print(f"   - Recent conversations: {len(context.recent_conversations)}")
            print(f"   - Relevant knowledge: {len(context.relevant_knowledge)}")
            print(f"   - User patterns keys: {list(context.user_patterns.keys())}")
            print(f"   - System state keys: {list(context.system_state.keys())}")
            
            # Test 7: Check relevance of retrieved knowledge
            if context.relevant_knowledge:
                print(f"\n📊 Knowledge Relevance Analysis:")
                for i, item in enumerate(context.relevant_knowledge[:3]):
                    print(f"   Item {i+1}:")
                    print(f"     - Type: {item.get('type')}")
                    print(f"     - Relevance: {item.get('relevance', 0):.3f}")
                    print(f"     - Memory type: {item.get('memory_type')}")
            
            # Test 8: Test query analysis
            print(f"\n🔍 Testing Query Analysis")
            query_analyzer = QueryAnalyzer()
            analysis = await query_analyzer.analyze_query(test_query, context)
            
            print(f"✅ Query analyzed")
            print(f"   - Intent: {analysis.intent}")
            print(f"   - Entities: {analysis.entities}")
            print(f"   - Keywords: {analysis.keywords}")
            print(f"   - Time context: {analysis.time_context}")
            print(f"   - Scope: {analysis.scope}")
            print(f"   - Complexity: {analysis.complexity}")
            
            # Test 9: Test response generation
            print(f"\n💬 Testing Response Generation")
            response_generator = RealResponseGenerator()
            response = await response_generator.generate_response(analysis, context, test_query)
            
            print(f"✅ Response generated")
            print(f"   Response: {response}")
            
            # Check if response contains real data
            real_data_indicators = ['cursor', 'development', 'coding', 'productivity', 'activity']
            contains_real_data = any(indicator.lower() in response.lower() for indicator in real_data_indicators)
            print(f"   Contains real data: {'✅ Yes' if contains_real_data else '❌ No'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing ASK mode handler: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error in memory retrieval test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_websocket_ask_mode():
    """Test ASK mode through websocket to see what's different"""
    print(f"\n🌐 Testing ASK Mode via WebSocket")
    print("=" * 50)
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            
            # Register
            register_msg = {"type": "register", "client_type": "debug_test", "client_id": "debug_ask"}
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            registration = json.loads(response)
            print(f"✅ Registered: {registration.get('connection_id')}")
            
            # Send ASK mode request
            test_query = "What development activities have I been doing recently?"
            message = {
                "type": "chat_request",
                "message": test_query,
                "mode": "Ask"
            }
            
            print(f"📤 Sending ASK request: {test_query}")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            start_time = time.time()
            response = await websocket.recv()
            response_time = time.time() - start_time
            
            response_data = json.loads(response)
            print(f"📥 Response received in {response_time:.2f}s")
            print(f"   Type: {response_data.get('type')}")
            print(f"   Success: {response_data.get('success', 'unknown')}")
            print(f"   Response: {response_data.get('response', 'NO RESPONSE')}")
            print(f"   Brain Router Used: {response_data.get('brain_router_used', False)}")
            print(f"   AI Powered: {response_data.get('ai_powered', False)}")
            
            # Check metadata
            if 'metadata' in response_data:
                metadata = response_data['metadata']
                print(f"   Metadata:")
                for key, value in metadata.items():
                    print(f"     - {key}: {value}")
            
            return response_data
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return None

async def diagnose_memory_blocking_issues():
    """Diagnose what's blocking memory integration"""
    print(f"\n🔧 Diagnosing Memory Integration Issues")
    print("=" * 50)
    
    # Check 1: Backend routing
    print("1. Checking backend routing logic...")
    
    try:
        # Read backend file to check ASK mode routing
        backend_file = "real_llm_backend_8767.py"
        with open(backend_file, 'r') as f:
            backend_content = f.read()
        
        # Check for ASK mode handling
        if 'mode == "Ask"' in backend_content:
            print("✅ ASK mode routing found in backend")
        else:
            print("❌ ASK mode routing not found in backend")
        
        # Check for brain router usage
        if 'brain_router_used' in backend_content:
            print("✅ Brain router integration found")
        else:
            print("❌ Brain router integration not found")
        
        # Check for ASK handler initialization  
        if 'ask_handler' in backend_content:
            print("✅ ASK handler initialization found")
        else:
            print("❌ ASK handler initialization not found")
            
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
    
    # Check 2: Brain router availability
    print(f"\n2. Checking brain router availability...")
    try:
        from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode
        print("✅ Brain router imports working")
        
        # Check if BRAIN_ROUTER_AVAILABLE flag exists
        if 'BRAIN_ROUTER_AVAILABLE' in backend_content:
            print("✅ BRAIN_ROUTER_AVAILABLE flag found")
        else:
            print("❌ BRAIN_ROUTER_AVAILABLE flag not found")
            
    except Exception as e:
        print(f"❌ Brain router import failed: {e}")
    
    # Check 3: File paths
    print(f"\n3. Checking file paths...")
    memory_file = "memory/memory_state.json"
    conversation_file = "memory/conversation_history.json" 
    
    print(f"   Memory file exists: {'✅' if os.path.exists(memory_file) else '❌'}")
    print(f"   Conversation file exists: {'✅' if os.path.exists(conversation_file) else '❌'}")
    
    # Check 4: Log the exact brain router initialization
    print(f"\n4. Checking initialization flags...")
    if 'BRAIN_ROUTER_AVAILABLE = True' in backend_content:
        print("✅ Brain router enabled")
    elif 'BRAIN_ROUTER_AVAILABLE = False' in backend_content:
        print("❌ Brain router disabled") 
    else:
        print("⚠️ Brain router availability unclear")

async def main():
    """Main execution"""
    print("🚀 Debugging ASK/Suggest Mode Memory Integration")
    print("=" * 60)
    
    # Test memory retrieval components
    memory_test_success = await test_memory_retrieval_directly()
    
    if memory_test_success:
        print(f"\n✅ Memory retrieval components working correctly!")
    else:
        print(f"\n❌ Memory retrieval components have issues")
        return
    
    # Test websocket integration  
    websocket_response = await test_websocket_ask_mode()
    
    if websocket_response:
        if websocket_response.get('brain_router_used'):
            print(f"\n✅ Brain router is being used via WebSocket")
        else:
            print(f"\n❌ Brain router not being used via WebSocket")
    
    # Diagnose issues
    await diagnose_memory_blocking_issues()
    
    print(f"\n🎯 Summary:")
    print("The ASK mode handler is properly integrated with real memory,")
    print("but there may be routing or initialization issues preventing")
    print("the brain router from being called correctly.")

if __name__ == "__main__":
    asyncio.run(main())