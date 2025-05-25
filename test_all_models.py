#!/usr/bin/env python3
"""
Test all available Ollama models for speed and response quality
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any

async def test_model(model_name: str, prompt: str = "what is nye?") -> Dict[str, Any]:
    """Test a specific model for speed and response quality"""
    print(f"\n🧪 Testing Model: {model_name}")
    print("="*50)
    
    start_time = time.time()
    
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 300  # Limit for speed comparison
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=90  # Allow more time for accurate testing
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "").strip()
            
            # Analyze response quality
            quality_score = analyze_response_quality(ai_response, prompt)
            
            print(f"⏱️  Response Time: {response_time:.2f} seconds")
            print(f"📊 Quality Score: {quality_score}/10")
            print(f"📝 Response Length: {len(ai_response)} characters")
            print(f"💬 Response Preview: {ai_response[:150]}...")
            
            return {
                "model": model_name,
                "success": True,
                "response_time": response_time,
                "quality_score": quality_score,
                "response_length": len(ai_response),
                "response": ai_response,
                "speed_rating": get_speed_rating(response_time),
                "overall_rating": (quality_score + get_speed_score(response_time)) / 2
            }
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                "model": model_name,
                "success": False,
                "error": f"HTTP {response.status_code}",
                "response_time": response_time
            }
            
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        print(f"⏰ Timeout after {response_time:.2f} seconds")
        return {
            "model": model_name,
            "success": False,
            "error": "Timeout",
            "response_time": response_time
        }
    except Exception as e:
        response_time = time.time() - start_time
        print(f"❌ Error: {e}")
        return {
            "model": model_name,
            "success": False,
            "error": str(e),
            "response_time": response_time
        }

def analyze_response_quality(response: str, prompt: str) -> float:
    """Analyze response quality on a scale of 1-10"""
    score = 0.0
    
    # Length appropriateness (1-2 points)
    if 50 <= len(response) <= 1000:
        score += 2.0
    elif 20 <= len(response) < 50 or 1000 < len(response) <= 2000:
        score += 1.0
    
    # Relevance to question (1-3 points)
    prompt_lower = prompt.lower()
    response_lower = response.lower()
    
    if "nye" in prompt_lower:
        if any(term in response_lower for term in ["new year", "december", "celebration"]):
            score += 3.0
        elif any(term in response_lower for term in ["year", "eve", "party"]):
            score += 2.0
        elif "nye" in response_lower:
            score += 1.0
    
    # Structure and coherence (1-3 points)
    sentences = response.split('.')
    if len(sentences) >= 3:
        score += 2.0
    elif len(sentences) >= 2:
        score += 1.0
    
    # Completeness (1-2 points)
    if not response.endswith('...') and len(response) > 100:
        score += 2.0
    elif len(response) > 50:
        score += 1.0
    
    return min(score, 10.0)

def get_speed_rating(response_time: float) -> str:
    """Get speed rating based on response time"""
    if response_time <= 5:
        return "⚡ Excellent"
    elif response_time <= 15:
        return "🚀 Good"
    elif response_time <= 30:
        return "⏳ Acceptable"
    elif response_time <= 60:
        return "🐌 Slow"
    else:
        return "❌ Too Slow"

def get_speed_score(response_time: float) -> float:
    """Convert response time to score (1-10)"""
    if response_time <= 5:
        return 10.0
    elif response_time <= 10:
        return 8.0
    elif response_time <= 20:
        return 6.0
    elif response_time <= 40:
        return 4.0
    elif response_time <= 60:
        return 2.0
    else:
        return 1.0

async def main():
    """Test all available models"""
    print("🔍 Testing All Available Ollama Models")
    print("="*60)
    print("Criteria: Speed + Response Quality + Comprehensiveness")
    print("="*60)
    
    # Get available models
    models = ["mistral:latest", "llava:latest", "llama3.2:latest", "llama3:latest"]
    
    results = []
    
    for model in models:
        result = await test_model(model)
        results.append(result)
        await asyncio.sleep(2)  # Brief pause between tests
    
    # Sort by overall rating
    successful_results = [r for r in results if r["success"]]
    successful_results.sort(key=lambda x: x["overall_rating"], reverse=True)
    
    print("\n" + "="*60)
    print("📊 RANKING: Best Models for Real-time Chat")
    print("="*60)
    
    for i, result in enumerate(successful_results, 1):
        print(f"\n{i}. {result['model']}")
        print(f"   ⏱️  Speed: {result['response_time']:.1f}s ({result['speed_rating']})")
        print(f"   📊 Quality: {result['quality_score']:.1f}/10")
        print(f"   🎯 Overall: {result['overall_rating']:.1f}/10")
    
    # Show failed models
    failed_results = [r for r in results if not r["success"]]
    if failed_results:
        print(f"\n❌ Failed Models:")
        for result in failed_results:
            print(f"   {result['model']}: {result['error']}")
    
    # Recommendation
    if successful_results:
        best_model = successful_results[0]
        print(f"\n🏆 RECOMMENDATION: {best_model['model']}")
        print(f"   Best balance of speed ({best_model['response_time']:.1f}s) and quality ({best_model['quality_score']:.1f}/10)")
        
        # Show if it needs timeout adjustment
        if best_model['response_time'] > 45:
            print(f"   ⚠️  Requires backend timeout increase to {int(best_model['response_time'] + 10)}+ seconds")
        else:
            print(f"   ✅ Works with current 45s timeout")

if __name__ == "__main__":
    asyncio.run(main())