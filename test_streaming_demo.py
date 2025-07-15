#!/usr/bin/env python3
"""
Demo to show streaming vs non-streaming behavior of the LLM service.
"""

import asyncio
import time
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.llm.llm_service import LLMService

async def test_streaming_behavior():
    """Test to show streaming behavior"""
    print("🚀 Testing LLM Streaming Behavior...")
    print("=" * 50)
    
    # Initialize LLM service
    llm_service = LLMService()
    await llm_service.initialize()
    
    try:
        prompt = "open calculator"
        
        print(f"📝 Prompt: {prompt}")
        print("🔄 Starting streaming response...")
        print("-" * 30)
        
        start_time = time.time()
        chunk_count = 0
        total_chars = 0
        
        # Stream the response
        async for chunk in llm_service.generate_response_with_fallback(prompt):
            chunk_count += 1
            total_chars += len(chunk)
            elapsed = time.time() - start_time
            
            print(f"Chunk {chunk_count:2d} ({elapsed:6.2f}s): {repr(chunk)}")
            
            # Show first few chunks in detail
            if chunk_count <= 5:
                print(f"           Content: {chunk}")
        
        total_time = time.time() - start_time
        
        print("-" * 30)
        print(f"📊 Streaming Summary:")
        print(f"  Total chunks: {chunk_count}")
        print(f"  Total chars: {total_chars}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average chunk size: {total_chars/chunk_count:.1f} chars")
        print(f"  Chunks per second: {chunk_count/total_time:.1f}")
        
        # Now test non-streaming (collecting all chunks first)
        print("\n🔄 Testing non-streaming (collecting all chunks)...")
        print("-" * 30)
        
        start_time = time.time()
        llm_chunks = []
        
        async for chunk in llm_service.generate_response_with_fallback(prompt):
            llm_chunks.append(chunk)
        
        full_response = ''.join(llm_chunks)
        total_time = time.time() - start_time
        
        print(f"📊 Non-streaming Summary:")
        print(f"  Total response length: {len(full_response)} chars")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Response preview: {full_response[:200]}...")
        
    finally:
        await llm_service.cleanup()

if __name__ == "__main__":
    asyncio.run(test_streaming_behavior()) 