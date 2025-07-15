#!/usr/bin/env python3
"""
Test direct LLM streaming responses
"""

import asyncio
import time
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.llm_service import LLMService

async def test_direct_streaming():
    """Test direct LLM streaming"""
    print("🧪 Testing Direct LLM Streaming")
    print("=" * 50)
    
    llm = LLMService()
    
    # Test 1: Simple prompt with streaming
    print("\n📝 Test 1: Simple prompt with streaming")
    print("-" * 40)
    
    messages = [{"role": "user", "content": "What is 2+2? Answer in one sentence."}]
    
    start_time = time.time()
    print("🔄 Streaming response:")
    
    try:
        async for chunk in llm.llm_client.generate_response_stream(messages):
            print(f"  📄 Chunk: {chunk}")
        
        elapsed = time.time() - start_time
        print(f"⏱️  Total time: {elapsed:.2f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Plan generation with streaming
    print("\n📝 Test 2: Plan generation with streaming")
    print("-" * 40)
    
    plan_prompt = "Create a simple automation plan for: open browser. Return as JSON with steps and apps."
    messages = [
        {"role": "system", "content": "You are an expert Mac automation planner."},
        {"role": "user", "content": plan_prompt}
    ]
    
    start_time = time.time()
    print("🔄 Streaming response:")
    
    try:
        full_response = ""
        async for chunk in llm.llm_client.generate_response_stream(messages):
            print(f"  📄 Chunk: {chunk}")
            full_response += chunk
        
        elapsed = time.time() - start_time
        print(f"⏱️  Total time: {elapsed:.2f}s")
        print(f"📋 Full response: {full_response[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_streaming()) 