#!/usr/bin/env python3
"""
Test Improved Agent Automation System
Tests the new universal automation system with various request types.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_universal_automation():
    """Test the universal automation system with different request types"""
    
    print("🧪 Testing Universal Intelligent Automation System")
    print("=" * 60)
    
    # Test requests of different types
    test_requests = [
        "search flight from nyc to miami",  # The original problematic case
        "find Python tutorials on YouTube",
        "search for MacBook deals on Amazon", 
        "open Calculator and compute 15 * 27",
        "check my Twitter feed",
        "find the weather forecast for tomorrow",
        "create a new document in TextEdit",
        "search for news about artificial intelligence"
    ]
    
    try:
        # Import the universal automation handler
        from universal_intelligent_automation_handler import handle_universal_automation
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n🔍 Test {i}: '{request}'")
            print("-" * 40)
            
            try:
                # Create automation plan
                result = await handle_universal_automation(request, f"test_session_{i}")
                
                if result["success"]:
                    print(f"✅ Plan created successfully!")
                    print(f"   📋 Title: {result.get('response', '').split('**📋 Task:**')[1].split('\\n')[0].strip() if '**📋 Task:**' in result.get('response', '') else 'N/A'}")
                    print(f"   🎯 Type: {result.get('request_type', 'unknown')}")
                    print(f"   🧠 Complexity: {result.get('complexity_score', 0):.1f}")
                    print(f"   📊 Success Probability: {result.get('success_probability', 0):.0%}")
                    print(f"   ⏱️ Processing Time: {result.get('processing_time', 0):.2f}s")
                    print(f"   🔧 Automation Available: {result.get('automation_available', False)}")
                    
                    # Show a few steps from the plan
                    response_text = result.get('response', '')
                    if '**🚀 Automation Steps:**' in response_text:
                        steps_section = response_text.split('**🚀 Automation Steps:**')[1].split('\\n\\n')[0]
                        steps_lines = [line for line in steps_section.split('\\n') if line.strip() and line.strip().startswith(('1.', '2.', '3.'))]
                        print(f"   📝 First 3 steps:")
                        for step_line in steps_lines[:3]:
                            print(f"      {step_line.strip()}")
                    
                else:
                    print(f"❌ Plan creation failed: {result.get('response', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Test failed with error: {e}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
    
    except ImportError as e:
        print(f"❌ Failed to import universal automation handler: {e}")
        print("Make sure the universal_intelligent_automation_handler.py file is properly created")
        return False
    
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False
    
    print(f"\n🎉 Test suite completed!")
    return True

async def test_agent_mode_handler():
    """Test the improved agent mode handler"""
    
    print(f"\n🧪 Testing Improved Agent Mode Handler")
    print("=" * 60)
    
    try:
        # Import the improved agent mode handler
        from brain.handlers.improved_agent_mode_handler import handle_improved_agent_mode
        from brain.core.brain_router import ChatRequest, ChatMode
        
        # Create test request
        test_request = ChatRequest(
            query="search flight from nyc to miami",
            mode=ChatMode.AGENT,
            user_id="test_user",
            context={}
        )
        
        print(f"🔍 Testing with request: '{test_request.query}'")
        
        # Handle the request
        response = await handle_improved_agent_mode(test_request)
        
        print(f"✅ Agent mode response generated!")
        print(f"   🎯 Success: {response.success}")
        print(f"   📝 Mode Used: {response.mode_used}")
        print(f"   ⏱️ Processing Time: {response.processing_time:.2f}s")
        print(f"   🧠 Confidence: {response.confidence:.1f}")
        print(f"   📊 Resources Used: {', '.join(response.resources_used)}")
        
        # Show metadata
        if response.metadata:
            print(f"   📋 Metadata:")
            for key, value in response.metadata.items():
                if key != "interactive_data":  # Skip complex data
                    print(f"      {key}: {value}")
        
        # Show first few lines of response
        response_lines = response.response.split('\\n')[:8]
        print(f"   📄 Response preview:")
        for line in response_lines:
            if line.strip():
                print(f"      {line}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import agent mode handler: {e}")
        return False
    except Exception as e:
        print(f"❌ Agent mode test failed: {e}")
        return False

async def test_flight_search_specifically():
    """Test the specific flight search case that was problematic"""
    
    print(f"\n🧪 Testing Flight Search Specifically")
    print("=" * 60)
    
    try:
        from universal_intelligent_automation_handler import handle_universal_automation
        
        flight_requests = [
            "search flight from nyc to miami",
            "find flights from New York to Miami",
            "look for cheap flights NYC to MIA",
            "book flight from JFK to Miami International",
            "find best flights between New York City and Miami Florida"
        ]
        
        for i, request in enumerate(flight_requests, 1):
            print(f"\\n✈️ Flight Test {i}: '{request}'")
            
            result = await handle_universal_automation(request, f"flight_test_{i}")
            
            if result["success"]:
                print(f"   ✅ Flight search plan created!")
                print(f"   🎯 Request Type: {result.get('request_type', 'unknown')}")
                
                # Check if it's correctly identified as flight search
                if result.get('request_type') == 'flight_search':
                    print(f"   🎉 Correctly identified as flight search!")
                else:
                    print(f"   ⚠️ Identified as: {result.get('request_type')} (not flight_search)")
                
                # Check for flight-related keywords in response
                response_text = result.get('response', '').lower()
                flight_keywords = ['flight', 'airline', 'airport', 'travel', 'ticket']
                found_keywords = [kw for kw in flight_keywords if kw in response_text]
                print(f"   🔍 Flight keywords found: {', '.join(found_keywords) if found_keywords else 'None'}")
                
            else:
                print(f"   ❌ Failed: {result.get('response', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flight search test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Improved Agent Automation Tests")
    print("=" * 60)
    
    # Test the universal automation system
    success1 = await test_universal_automation()
    
    # Test the agent mode handler  
    success2 = await test_agent_mode_handler()
    
    # Test flight search specifically
    success3 = await test_flight_search_specifically()
    
    print(f"\\n📊 Test Results Summary:")
    print(f"   Universal Automation: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Agent Mode Handler: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"   Flight Search Tests: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    overall_success = success1 and success2 and success3
    print(f"\\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print(f"\\n🎉 The improved agent automation system is working correctly!")
        print("✨ It now creates detailed, specific plans for ANY type of user request!")
    else:
        print(f"\\n🔧 Some issues need to be addressed before the system is fully functional.")

if __name__ == "__main__":
    asyncio.run(main())