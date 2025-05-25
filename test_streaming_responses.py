#!/usr/bin/env python3
"""
Test streaming responses with instant acknowledgment for both models
"""

import asyncio
import json
import time
import requests
from typing import AsyncGenerator

async def test_streaming_model(model_name: str, prompt: str = "what is nye?") -> dict:
    """Test streaming response for a model"""
    print(f"\n🧪 Testing Streaming: {model_name}")
    print("="*60)
    
    # Instant acknowledgment
    print(f"⚡ Instant: Processing your request with {model_name}...")
    start_time = time.time()
    
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,  # Enable streaming
            "options": {
                "temperature": 0.7,
                "max_tokens": 200  # Reasonable limit for testing
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            stream=True,  # Enable streaming on client side
            timeout=60
        )
        
        if response.status_code != 200:
            return {
                "model": model_name,
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
        
        # Process streaming response
        full_response = ""
        first_token_time = None
        token_count = 0
        
        print(f"🔄 Streaming response:")
        print("   ", end="", flush=True)
        
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    
                    if token and first_token_time is None:
                        first_token_time = time.time()
                        time_to_first_token = first_token_time - start_time
                        print(f"\n⚡ First token in: {time_to_first_token:.2f}s")
                        print("   ", end="", flush=True)
                    
                    if token:
                        print(token, end="", flush=True)
                        full_response += token
                        token_count += 1
                    
                    if chunk.get("done", False):
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n\n✅ Streaming completed!")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"⚡ Time to first token: {first_token_time - start_time if first_token_time else 'N/A':.2f}s")
        print(f"🎯 Tokens: {token_count}")
        print(f"📝 Length: {len(full_response)} characters")
        
        # Analyze quality
        quality_score = analyze_response_quality(full_response, prompt)
        print(f"📊 Quality: {quality_score:.1f}/10")
        
        return {
            "model": model_name,
            "success": True,
            "total_time": total_time,
            "time_to_first_token": first_token_time - start_time if first_token_time else None,
            "token_count": token_count,
            "response_length": len(full_response),
            "quality_score": quality_score,
            "response": full_response,
            "streaming": True
        }
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"\n❌ Error after {error_time:.2f}s: {e}")
        return {
            "model": model_name,
            "success": False,
            "error": str(e),
            "error_time": error_time
        }

def analyze_response_quality(response: str, prompt: str) -> float:
    """Analyze response quality on a scale of 1-10"""
    score = 0.0
    
    # Length appropriateness (0-2 points)
    if 50 <= len(response) <= 500:
        score += 2.0
    elif 20 <= len(response) < 50 or 500 < len(response) <= 1000:
        score += 1.5
    elif len(response) >= 20:
        score += 1.0
    
    # Relevance to question (0-4 points)
    prompt_lower = prompt.lower()
    response_lower = response.lower()
    
    if "nye" in prompt_lower:
        if "new year" in response_lower and "eve" in response_lower:
            score += 4.0
        elif any(term in response_lower for term in ["new year", "december", "celebration"]):
            score += 3.0
        elif any(term in response_lower for term in ["year", "eve", "party"]):
            score += 2.0
        elif "nye" in response_lower:
            score += 1.0
    
    # Coherence and structure (0-2 points)
    sentences = response.split('.')
    if len(sentences) >= 3:
        score += 2.0
    elif len(sentences) >= 2:
        score += 1.0
    
    # Completeness (0-2 points)
    if response.strip() and not response.endswith('...'):
        score += 2.0
    elif response.strip():
        score += 1.0
    
    return min(score, 10.0)

async def compare_streaming_models():
    """Compare streaming performance of both models"""
    print("🚀 STREAMING RESPONSE TEST - INSTANT ACKNOWLEDGMENT + REAL-TIME STREAMING")
    print("="*80)
    
    models = ["llama3.2:1b", "llama3.2:latest"]
    results = []
    
    for model in models:
        result = await test_streaming_model(model)
        results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    print("\n" + "="*80)
    print("📊 STREAMING COMPARISON RESULTS")
    print("="*80)
    
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        print(f"\n{'Model':<20} {'First Token':<12} {'Total Time':<12} {'Quality':<8} {'Tokens':<8}")
        print("-" * 70)
        
        for result in successful_results:
            first_token = f"{result.get('time_to_first_token', 0):.1f}s" if result.get('time_to_first_token') else "N/A"
            total_time = f"{result['total_time']:.1f}s"
            quality = f"{result['quality_score']:.1f}/10"
            tokens = str(result.get('token_count', 0))
            
            print(f"{result['model']:<20} {first_token:<12} {total_time:<12} {quality:<8} {tokens:<8}")
        
        # Recommendation
        best_model = min(successful_results, key=lambda x: x.get('time_to_first_token', float('inf')))
        print(f"\n🏆 BEST FOR STREAMING: {best_model['model']}")
        print(f"   ⚡ First response in: {best_model.get('time_to_first_token', 0):.1f}s")
        print(f"   📊 Quality: {best_model['quality_score']:.1f}/10")
        
        print(f"\n🎯 USER EXPERIENCE:")
        print(f"   • Instant acknowledgment: 'Processing...'")
        print(f"   • First words appear: {best_model.get('time_to_first_token', 0):.1f}s")
        print(f"   • Complete response: {best_model['total_time']:.1f}s")
        print(f"   • Perceived speed: MUCH FASTER! ⚡")
    
    # Show failures
    failed_results = [r for r in results if not r["success"]]
    if failed_results:
        print(f"\n❌ Failed Models:")
        for result in failed_results:
            print(f"   {result['model']}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(compare_streaming_models())