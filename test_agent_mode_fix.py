#!/usr/bin/env python3
"""
Test Agent Mode Fix
Verifies that Agent Mode now uses Real Agent Automation Handler
and generates proper execution plans instead of conversational responses
"""

import asyncio
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_import_status():
    """Test if Real Agent Automation Handler is properly imported"""
    
    print("🔍 Testing Import Status...")
    
    try:
        from real_agent_automation_handler import RealAgentAutomationHandler
        print("✅ Real Agent Automation Handler imported successfully")
        
        # Test instantiation
        handler = RealAgentAutomationHandler()
        print("✅ Real Agent Automation Handler instantiated")
        
        # Test method availability
        if hasattr(handler, 'handle_agent_request'):
            print("✅ handle_agent_request method available")
        else:
            print("❌ handle_agent_request method missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Handler error: {e}")
        return False

async def test_backend_flags():
    """Test backend automation flags"""
    
    print("\n🏁 Testing Backend Flags...")
    
    try:
        from enhanced_enterprise_backend_with_context import (
            REAL_AGENT_AUTOMATION_AVAILABLE,
            ENHANCED_AUTOMATION_AVAILABLE,
            UNIVERSAL_AVAILABLE,
            FAST_AUTOMATION_AVAILABLE,
            AUTOMATION_AVAILABLE
        )
        
        print(f"🎯 REAL_AGENT_AUTOMATION_AVAILABLE: {REAL_AGENT_AUTOMATION_AVAILABLE}")
        print(f"🔧 ENHANCED_AUTOMATION_AVAILABLE: {ENHANCED_AUTOMATION_AVAILABLE}")
        print(f"🌍 UNIVERSAL_AVAILABLE: {UNIVERSAL_AVAILABLE}")
        print(f"⚡ FAST_AUTOMATION_AVAILABLE: {FAST_AUTOMATION_AVAILABLE}")
        print(f"✅ AUTOMATION_AVAILABLE: {AUTOMATION_AVAILABLE}")
        
        if REAL_AGENT_AUTOMATION_AVAILABLE:
            print("✅ Real Agent Automation is properly enabled")
            return True
        else:
            print("❌ Real Agent Automation is NOT enabled")
            return False
            
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
        return False

async def test_handler_directly():
    """Test the Real Agent Automation Handler directly"""
    
    print("\n🧪 Testing Handler Directly...")
    
    try:
        from real_agent_automation_handler import RealAgentAutomationHandler
        
        handler = RealAgentAutomationHandler()
        test_message = "search Omer Adam in Spotify"
        session_id = "test_session"
        
        print(f"📝 Testing with message: '{test_message}'")
        
        result = await handler.handle_agent_request(test_message, session_id)
        
        print(f"📊 Handler Result:")
        print(f"   ✅ Success: {result.get('success', False)}")
        print(f"   🎮 Interactive: {result.get('interactive', False)}")
        print(f"   🔘 Has Buttons: {bool(result.get('buttons', []))}")
        print(f"   🆔 Plan ID: {result.get('plan_id', 'None')}")
        print(f"   🤖 AI Powered: {result.get('ai_powered', False)}")
        
        response_preview = result.get('response', '')[:100] + "..." if len(result.get('response', '')) > 100 else result.get('response', '')
        print(f"   💬 Response: '{response_preview}'")
        
        # Check if it's a proper execution plan
        is_execution_plan = result.get('success', False) and (
            result.get('interactive', False) or 
            bool(result.get('buttons', [])) or 
            result.get('plan_id', '')
        )
        
        if is_execution_plan:
            print("✅ Handler generates proper execution plans!")
            return True
        else:
            print("❌ Handler not generating proper execution plans")
            return False
        
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    print("🚀 Agent Mode Fix Verification")
    print("=" * 60)
    
    # Test import status
    import_ok = await test_import_status()
    
    # Test backend flags
    flags_ok = await test_backend_flags()
    
    # Test handler directly
    handler_ok = await test_handler_directly()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS:")
    print(f"   📦 Import Status: {'✅ OK' if import_ok else '❌ FAILED'}")
    print(f"   🏁 Backend Flags: {'✅ OK' if flags_ok else '❌ FAILED'}")
    print(f"   🎯 Handler Test: {'✅ OK' if handler_ok else '❌ FAILED'}")
    
    all_ok = import_ok and flags_ok and handler_ok
    
    if all_ok:
        print("\n🎉 SUCCESS! Agent Mode fix is complete!")
        print("🔄 The backend should now generate execution plans")
        print("🎯 Test with: 'search Omer Adam in Spotify' in Agent Mode")
        print("🔘 Should show DO/DISMISS/ADJUST buttons instead of conversational response")
    else:
        print("\n🚨 FAILURE! Agent Mode still has issues!")
        print("🔧 Check the import errors and backend configuration")
        
        if not import_ok:
            print("💡 Fix: Check if real_agent_automation_handler.py exists and has correct syntax")
        if not flags_ok:
            print("💡 Fix: Check backend import configuration")
        if not handler_ok:
            print("💡 Fix: Check handler logic and LLM availability")
    
    return all_ok

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        exit(1)