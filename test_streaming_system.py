#!/usr/bin/env python3
"""
Test system LLM streaming responses through plan creator
"""

import asyncio
import time
import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_plan_creator import plan_creator

async def test_system_streaming():
    """Test system LLM streaming through plan creator"""
    print("🧪 Testing System LLM Streaming (Plan Creator)")
    print("=" * 60)
    
    test_prompts = [
        "open browser",
        "open finder"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: '{prompt}'")
        print("-" * 40)
        
        try:
            start_time = time.time()
            print("🔄 Streaming response:")
            
            chunk_count = 0
            full_response = ""
            
            async for chunk in plan_creator.create_plan_streaming(prompt):
                chunk_count += 1
                if chunk.startswith("[DEBUG]"):
                    print(f"🔍 {chunk}")
                elif chunk.startswith("❌"):
                    print(f"❌ {chunk}")
                elif chunk.startswith("✅"):
                    print(f"✅ {chunk}")
                elif chunk.startswith("🔄"):
                    print(f"🔄 {chunk}")
                else:
                    # This is a raw chunk from LLM
                    full_response += chunk
                    if chunk_count <= 5:  # Show first 5 chunks
                        print(f"  📄 Chunk {chunk_count}: '{chunk}'")
                    elif chunk_count == 6:
                        print(f"  📄 ... (showing first 5 chunks only)")
            
            elapsed = time.time() - start_time
            print(f"⏱️  Total time: {elapsed:.2f}s")
            print(f"📋 Full response length: {len(full_response)} chars")
            if len(full_response) < 200:
                print(f"📝 Full response: {repr(full_response)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_system_streaming()) 