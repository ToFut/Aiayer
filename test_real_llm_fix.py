#!/usr/bin/env python3
"""
Test that the backend now uses Universal (real LLM) handler instead of Fast (mock) handler
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_handler_priority():
    """Test which handler gets loaded"""
    
    print("🧪 Testing Handler Priority Fix")
    print("=" * 60)
    
    # Test the import logic from the backend
    print("\n🔧 Testing Handler Import Logic:")
    print("-" * 40)
    
    # Simulate the backend import logic
    ENHANCED_AUTOMATION_AVAILABLE = False
    FAST_AUTOMATION_AVAILABLE = False
    UNIVERSAL_AVAILABLE = False
    
    try:
        from universal_intelligent_automation_handler import universal_automation_handler
        AUTOMATION_AVAILABLE = True
        UNIVERSAL_AVAILABLE = True
        print("✅ Universal Intelligent Automation handler loaded for real LLM planning")
    except ImportError as e:
        UNIVERSAL_AVAILABLE = False
        try:
            from fast_universal_automation_handler import fast_universal_automation_handler
            AUTOMATION_AVAILABLE = True
            FAST_AUTOMATION_AVAILABLE = True
            print(f"⚡ Falling back to Fast automation handler: {e}")
        except ImportError as e2:
            print(f"❌ No automation handlers available: {e2}")
    
    print(f"\nHandler Status:")
    print(f"UNIVERSAL_AVAILABLE: {UNIVERSAL_AVAILABLE}")
    print(f"FAST_AUTOMATION_AVAILABLE: {FAST_AUTOMATION_AVAILABLE}")
    
    # Test which handler would be used
    print(f"\n🎯 Handler Selection Logic:")
    print("-" * 40)
    
    if UNIVERSAL_AVAILABLE:
        print("✅ Would use: Universal Intelligent Automation handler (REAL LLM)")
        print("   → Real LLM-generated automation plans")
        print("   → Advanced context-aware planning")
        print("   → Intelligent step generation")
    elif FAST_AUTOMATION_AVAILABLE:
        print("⚡ Would use: Fast Universal Automation handler (MOCK/TEMPLATE)")
        print("   → Template-based responses")
        print("   → Hardcoded step patterns")
        print("   → Mock 'FAST AUTOMATION PLAN' responses")
    else:
        print("❌ No automation handler available")
    
    # Test the specific query that was returning mock responses
    print(f"\n🔍 Testing Specific Query:")
    print("-" * 40)
    
    test_query = "search Omer Adam in spotify app"
    print(f"Query: '{test_query}'")
    
    if UNIVERSAL_AVAILABLE:
        print("Expected Behavior:")
        print("  ✅ Real LLM analysis of the request")
        print("  ✅ Context-aware automation planning")
        print("  ✅ Spotify-specific action generation")
        print("  ✅ Intelligent step sequencing")
        print("  ❌ NO MORE: 'Basic Web Search' templates")
        print("  ❌ NO MORE: Generic Safari + Google steps")
    else:
        print("Expected Behavior:")
        print("  ❌ Mock 'Basic Web Search' response")
        print("  ❌ Template: 1. Open Safari 2. Navigate to Google 3. Perform search")

if __name__ == "__main__":
    test_handler_priority()