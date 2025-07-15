#!/usr/bin/env python3
"""
Simple streaming test to debug the issue
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.llm_service import LLMService

async def test_simple_streaming():
    """Test simple streaming to see what's happening"""
    print("🧪 Testing Simple Streaming Debug")
    print("=" * 40)
    
    llm = LLMService()
    
    messages = [{"role": "user", "content": "Say hello in one word."}]
    
    print("🔄 Starting streaming...")
    chunk_count = 0
    full_response = ""
    
    try:
        async for chunk in llm.llm_client.generate_response_stream(messages, max_tokens=50):
            chunk_count += 1
            full_response += chunk
            print(f"📄 Chunk {chunk_count}: '{chunk}' (type: {type(chunk)})")
        
        print(f"\n✅ Completed: {chunk_count} chunks")
        print(f"📝 Full response: '{full_response}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_streaming()) 