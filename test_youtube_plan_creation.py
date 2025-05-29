#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_llm_automation_planner import enhanced_llm_planner

async def test_youtube_plan():
    """Test YouTube automation plan creation"""
    
    print("🧪 Testing YouTube automation plan creation...")
    print("=" * 50)
    
    # Test message
    message = "open youtube and search SEGEV"
    session_id = "test_session_123"
    
    try:
        # Create the plan
        print(f"📝 Creating plan for: '{message}'")
        plan = await enhanced_llm_planner.create_intelligent_plan(message, session_id)
        
        print(f"\n✅ Plan created successfully!")
        print(f"📋 Title: {plan.title}")
        print(f"📊 Steps: {len(plan.steps)}")
        print(f"⏱️ Duration: {plan.estimated_duration:.1f}s")
        print(f"🧠 LLM Generated: {plan.llm_generated}")
        print(f"🎯 Complexity: {plan.complexity_score:.2f}")
        
        print(f"\n📋 Detailed Steps:")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step.description}")
            print(f"     Type: {step.action_type}")
            if step.target:
                print(f"     Target: {step.target}")
            if step.value:
                print(f"     Value: {step.value}")
            print(f"     Confidence: {step.confidence:.2f}")
            print(f"     Duration: {step.estimated_duration:.1f}s")
            print()
        
        if len(plan.steps) == 0:
            print("❌ No steps were generated!")
            print("🔍 Let's analyze what went wrong...")
            
            # Test fallback analysis directly
            print("\n🔄 Testing fallback intent analysis...")
            analysis = await enhanced_llm_planner._fallback_intent_analysis(message)
            
            print(f"Intent Analysis:")
            print(f"  Primary Goal: {analysis['intent_analysis']['primary_goal']}")
            print(f"  Applications: {analysis['intent_analysis']['applications_needed']}")
            print(f"  Websites: {analysis['intent_analysis']['websites_needed']}")
            print(f"  Search Terms: {analysis['intent_analysis']['search_terms']}")
            print(f"  Complexity: {analysis['intent_analysis']['complexity_score']}")
            
            print(f"\nAutomation Steps:")
            for step in analysis['automation_steps']:
                print(f"  - {step['description']} ({step['action_type']})")
        
        return plan
        
    except Exception as e:
        print(f"❌ Error creating plan: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_youtube_plan())