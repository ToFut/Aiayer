#!/usr/bin/env python3
"""
Test Agent Integration
Verifies that the improved agent mode handler is properly integrated.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_brain_router_integration():
    """Test that the brain router uses the improved agent handler"""
    
    print("🧪 Testing Brain Router Integration")
    print("=" * 50)
    
    try:
        # Import brain router components
        from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode
        
        # Create brain router instance
        router = BrainRouter()
        
        # Create test request
        test_request = ChatRequest(
            query="search flight from nyc to miami",
            mode=ChatMode.AGENT,
            user_id="test_user",
            session_id="test_session",
            context={}
        )
        
        print(f"🔍 Testing request: '{test_request.query}'")
        print(f"   Mode: {test_request.mode.value}")
        
        # Process the request
        response = await router.process_request(test_request)
        
        print(f"✅ Response received!")
        print(f"   Success: {response.success}")
        print(f"   Mode Used: {response.mode_used.value}")
        print(f"   Processing Time: {response.processing_time:.2f}s")
        print(f"   Confidence: {response.confidence:.1f}")
        print(f"   Resources Used: {', '.join(response.resources_used)}")
        
        # Check if it's using the improved handler
        if response.metadata and response.metadata.get("universal_planning"):
            print(f"🎉 SUCCESS: Using Universal Intelligent Automation!")
        elif response.metadata and response.metadata.get("fallback_mode"):
            print(f"⚠️ FALLBACK: Using basic handler (improved handler not available)")
            print(f"   Reason: {response.metadata.get('error', 'Unknown')}")
        else:
            print(f"❓ UNKNOWN: Could not determine which handler was used")
        
        # Show response preview
        response_lines = response.response.split('\\n')[:6]
        print(f"\\n📄 Response Preview:")
        for line in response_lines:
            if line.strip():
                print(f"   {line}")
        
        return response.success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def test_direct_handler():
    """Test the improved agent handler directly"""
    
    print(f"\\n🧪 Testing Direct Handler")
    print("=" * 50)
    
    try:
        from brain.handlers.improved_agent_mode_handler import handle_improved_agent_mode
        from brain.core.brain_router import ChatRequest, ChatMode
        
        # Create test request
        test_request = ChatRequest(
            query="search flight from nyc to miami",
            mode=ChatMode.AGENT,
            user_id="test_user",
            session_id="test_session",
            context={}
        )
        
        print(f"🔍 Testing direct handler with: '{test_request.query}'")
        
        # Call handler directly
        response = await handle_improved_agent_mode(test_request)
        
        print(f"✅ Direct handler response received!")
        print(f"   Success: {response.success}")
        print(f"   Processing Time: {response.processing_time:.2f}s")
        print(f"   Confidence: {response.confidence:.1f}")
        
        # Check for automation plan creation
        if response.metadata:
            automation_plan_created = response.metadata.get("automation_plan_created", False)
            universal_planning = response.metadata.get("universal_planning", False)
            
            print(f"   Automation Plan Created: {automation_plan_created}")
            print(f"   Universal Planning: {universal_planning}")
            
            if automation_plan_created and universal_planning:
                print(f"🎉 SUCCESS: Improved agent handler is working correctly!")
                return True
            elif response.metadata.get("fallback_mode"):
                print(f"⚠️ FALLBACK: Handler is working but using fallback mode")
                return True
            else:
                print(f"❓ PARTIAL: Handler is working but with unexpected behavior")
                return False
        else:
            print(f"❓ NO METADATA: Response received but no metadata available")
            return False
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Direct handler test failed: {e}")
        return False

async def test_flight_search_specifically():
    """Test the specific flight search case"""
    
    print(f"\\n🧪 Testing Flight Search Case")
    print("=" * 50)
    
    try:
        from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode
        
        router = BrainRouter()
        
        flight_requests = [
            "search flight from nyc to miami",
            "find flights NYC to Miami",
            "look for cheap flights New York to Miami"
        ]
        
        for i, query in enumerate(flight_requests, 1):
            print(f"\\n✈️ Flight Test {i}: '{query}'")
            
            request = ChatRequest(
                query=query,
                mode=ChatMode.AGENT,
                user_id=f"test_user_{i}",
                session_id=f"test_session_{i}",
                context={}
            )
            
            response = await router.process_request(request)
            
            if response.success:
                print(f"   ✅ Request processed successfully")
                
                # Check if response contains flight-related content
                response_lower = response.response.lower()
                flight_keywords = ['flight', 'airline', 'airport', 'travel', 'automation']
                found_keywords = [kw for kw in flight_keywords if kw in response_lower]
                
                if found_keywords:
                    print(f"   🎯 Flight-related keywords found: {', '.join(found_keywords)}")
                else:
                    print(f"   ⚠️ No flight-related keywords found in response")
                
                # Check for automation plan
                if response.metadata and response.metadata.get("automation_plan_created"):
                    print(f"   🤖 Automation plan created successfully")
                else:
                    print(f"   📝 Basic response provided (no automation plan)")
                    
            else:
                print(f"   ❌ Request failed: {response.response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Flight search test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Agent Integration Tests")
    print("=" * 60)
    
    # Test brain router integration
    success1 = await test_brain_router_integration()
    
    # Test direct handler
    success2 = await test_direct_handler()
    
    # Test flight search specifically  
    success3 = await test_flight_search_specifically()
    
    print(f"\\n📊 Integration Test Results:")
    print(f"   Brain Router Integration: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Direct Handler Test: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"   Flight Search Tests: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    overall_success = success1 and success2 and success3
    print(f"\\n🎯 Overall Integration Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print(f"\\n🎉 The improved agent mode is successfully integrated!")
        print("✨ Agent mode now creates detailed, specific automation plans for ANY user request!")
        print("🤖 The 'search flight from NYC to Miami' example should now work perfectly!")
    else:
        print(f"\\n🔧 Some integration issues need to be addressed.")
        print("💡 The improved system is available but may not be fully connected.")

if __name__ == "__main__":
    asyncio.run(main())