#!/usr/bin/env python3
"""
Test the optimized LLM-only plan creator (no fallbacks)
"""

import asyncio
import json
import time
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_plan_creator import plan_creator

async def test_optimized_llm_only():
    """Test the optimized LLM-only plan creator"""
    print("🧪 Testing Optimized LLM-Only Plan Creator (No Fallbacks)")
    print("=" * 60)
    
    test_prompts = [
        "open browser",
        "open finder", 
        "open terminal",
        "open notes",
        "open calculator",
        "open mail",
        "open messages",
        "open calendar",
        "open photos",
        "open music"
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}/10: '{prompt}'")
        print("-" * 40)
        
        try:
            start_time = time.time()
            plan = await plan_creator.create_plan(prompt)  # Add await here
            elapsed = time.time() - start_time
            
            print(f"⏱️  Response time: {elapsed:.2f}s")
            print(f"✅ Plan created successfully")
            print(f"📋 Steps: {len(plan.get('steps', []))}")
            print(f"📱 Apps: {plan.get('apps', [])}")
            
            # Show plan details
            for j, step in enumerate(plan.get('steps', []), 1):
                print(f"  {j}. {step.get('description', 'Unknown')}")
                print(f"     Action: {step.get('action', 'Unknown')}")
                if 'app' in step:
                    print(f"     App: {step['app']}")
            
            results.append({
                'prompt': prompt,
                'success': True,
                'time': elapsed,
                'plan': plan
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'prompt': prompt,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/10")
    print(f"❌ Failed: {len(failed)}/10")
    
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        print(f"⏱️  Average response time: {avg_time:.2f}s")
    
    if failed:
        print("\n❌ Failed prompts:")
        for result in failed:
            print(f"  - {result['prompt']}: {result['error']}")
    
    print("\n🎯 Conclusion:")
    if len(successful) >= 8:
        print("✅ LLM-only approach is working well!")
    elif len(successful) >= 5:
        print("⚠️  LLM-only approach has some issues but mostly works")
    else:
        print("❌ LLM-only approach needs improvement")

if __name__ == "__main__":
    asyncio.run(test_optimized_llm_only()) 