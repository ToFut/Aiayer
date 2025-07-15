#!/usr/bin/env python3
import asyncio
import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.model import LocalLLM

async def test_llm_direct():
    print("🧪 Testing LLM Service Directly...")
    
    try:
        # Initialize LLM
        llm = LocalLLM(model_name="llama3.2:1b")
        
        print("🔄 Starting LLM...")
        await llm.start()
        
        print("✅ LLM started successfully")
        
        # Test prompts
        prompts = [
            "What is 2+2? Answer in one word.",
            "Summarize the meaning of life in one sentence.",
            "List three colors.",
            "What is the capital of France?",
            "Write a short haiku about the ocean."
        ]
        
        for i, prompt in enumerate(prompts, 1):
            messages = [{"role": "user", "content": prompt}]
            print(f"\n📝 Prompt {i}: '{prompt}'")
            t0 = time.time()
            response = await llm.generate_response(messages, temperature=0.7, max_tokens=50)
            t1 = time.time()
            print(f"✅ Response received in {t1-t0:.2f} seconds")
            print(f"📄 Response: '{response}'")
        
        await llm.stop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_direct()) 