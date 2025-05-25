#!/usr/bin/env python3
"""
Fixed chat mode test - properly handles WebSocket message sequence
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_single_chat(mode, message):
    """Test a single chat request properly handling message sequence"""
    print(f"\n=== Testing {mode.upper()} mode ===")
    print(f"Query: {message}")
    print("-" * 50)
    
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection established message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"Connected: {connection_data.get('message', 'OK')}")
            
            # Send chat request
            start_time = time.time()
            request = {
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(request))
            print(f"Request sent, waiting for response...")
            
            # Wait for chat response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=90.0)
                end_time = time.time()
                
                response_data = json.loads(response)
                response_time = end_time - start_time
                
                print(f"✅ Response received in {response_time:.1f}s")
                print(f"Response type: {response_data.get('type')}")
                
                if response_data.get("type") == "chat_response":
                    ai_response = response_data.get("response", "")
                    word_count = len(ai_response.split())
                    
                    print(f"AI Response ({word_count} words):")
                    print(f"{'='*60}")
                    print(ai_response)
                    print(f"{'='*60}")
                    
                    # Quality analysis
                    quality_score = analyze_quality(ai_response, mode)
                    print(f"Quality Score: {quality_score:.1f}/10")
                    
                    return {
                        "success": True,
                        "mode": mode,
                        "query": message,
                        "response": ai_response,
                        "response_time": response_time,
                        "word_count": word_count,
                        "quality_score": quality_score
                    }
                elif response_data.get("type") == "error":
                    error_msg = response_data.get("error", "Unknown error")
                    print(f"❌ Server error: {error_msg}")
                    return {"success": False, "error": error_msg}
                else:
                    print(f"❌ Unexpected response type: {response_data.get('type')}")
                    return {"success": False, "error": "Unexpected response type"}
                    
            except asyncio.TimeoutError:
                print("❌ Response timeout (90s)")
                return {"success": False, "error": "Timeout"}
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return {"success": False, "error": str(e)}

def analyze_quality(response, mode):
    """Quick quality analysis"""
    if not response:
        return 0
    
    score = 0
    word_count = len(response.split())
    
    # Length scoring (3 points)
    if 50 <= word_count <= 300:
        score += 3
    elif 30 <= word_count < 50 or 300 < word_count <= 500:
        score += 2
    elif word_count >= 20:
        score += 1
    
    # Mode-specific content (3 points)
    response_lower = response.lower()
    
    if mode == "ask":
        if any(word in response_lower for word in ["explanation", "define", "means", "is", "are"]):
            score += 3
        elif any(word in response_lower for word in ["help", "answer", "question"]):
            score += 2
    elif mode == "agent":
        if any(word in response_lower for word in ["step", "plan", "first", "next", "process"]):
            score += 3
        elif any(word in response_lower for word in ["help", "assist", "recommend"]):
            score += 2
    elif mode == "suggest":
        if any(word in response_lower for word in ["suggest", "recommend", "consider", "try", "could"]):
            score += 3
        elif any(word in response_lower for word in ["advice", "tip", "idea"]):
            score += 2
    elif mode == "general":
        if len(response_lower.split('.')) >= 2:
            score += 3
        else:
            score += 1
    
    # Structure and coherence (2 points)
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    if len(sentences) >= 3:
        score += 2
    elif len(sentences) >= 2:
        score += 1
    
    # Usefulness indicators (2 points)
    useful_words = ["because", "however", "therefore", "for example", "such as", "including"]
    found_useful = sum(1 for word in useful_words if word in response_lower)
    score += min(2, found_useful * 0.5)
    
    return min(10, score)

async def main():
    """Run comprehensive test of all modes"""
    
    test_cases = [
        ("ask", "What is machine learning and how does it work?"),
        ("ask", "How do I center a div with CSS flexbox?"),
        ("agent", "Help me plan a website redesign project with timeline"),
        ("agent", "I need to optimize my web application performance step by step"),
        ("suggest", "What programming languages should I learn next for web development?"),
        ("suggest", "How can I improve my team's code review process?"),
        ("general", "Explain the benefits and challenges of microservices architecture"),
        ("general", "What are the current trends in artificial intelligence and machine learning?")
    ]
    
    print("COMPREHENSIVE CHAT MODES TEST WITH LLAMA3.2:1B")
    print("=" * 80)
    print("Testing all modes for meaningful responses...")
    print("=" * 80)
    
    results = []
    successful_tests = 0
    total_response_time = 0
    total_quality = 0
    
    for i, (mode, message) in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] Testing...")
        result = await test_single_chat(mode, message)
        results.append(result)
        
        if result["success"]:
            successful_tests += 1
            total_response_time += result["response_time"]
            total_quality += result["quality_score"]
        
        # Pause between tests to avoid overwhelming the system
        if i < len(test_cases) - 1:
            print(f"\nWaiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    # Generate summary
    print(f"\n{'='*80}")
    print("SUMMARY REPORT")
    print("=" * 80)
    
    success_rate = (successful_tests / len(test_cases)) * 100
    avg_response_time = total_response_time / successful_tests if successful_tests > 0 else 0
    avg_quality = total_quality / successful_tests if successful_tests > 0 else 0
    
    print(f"Total tests: {len(test_cases)}")
    print(f"Successful: {successful_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Average response time: {avg_response_time:.1f}s")
    print(f"Average quality score: {avg_quality:.1f}/10")
    
    # Mode breakdown
    modes = ["ask", "agent", "suggest", "general"]
    print(f"\nMODE BREAKDOWN:")
    print("-" * 40)
    
    for mode in modes:
        mode_results = [r for r in results if r.get("mode") == mode and r["success"]]
        mode_total = len([r for r in results if r.get("mode") == mode])
        mode_success = len(mode_results)
        
        if mode_results:
            mode_avg_time = sum(r["response_time"] for r in mode_results) / len(mode_results)
            mode_avg_quality = sum(r["quality_score"] for r in mode_results) / len(mode_results)
            status = "✅ WORKING" if mode_success == mode_total else "⚠️ PARTIAL"
        else:
            mode_avg_time = 0
            mode_avg_quality = 0
            status = "❌ FAILING"
        
        print(f"{mode.upper():8} | {status:12} | {mode_success}/{mode_total} | {mode_avg_time:5.1f}s | {mode_avg_quality:4.1f}/10")
    
    # Show best responses
    if successful_tests > 0:
        print(f"\nBEST RESPONSES BY MODE:")
        print("-" * 50)
        
        for mode in modes:
            mode_results = [r for r in results if r.get("mode") == mode and r["success"]]
            if mode_results:
                best = max(mode_results, key=lambda x: x["quality_score"])
                preview = best["response"][:150] + "..." if len(best["response"]) > 150 else best["response"]
                print(f"\n{mode.upper()} (Quality: {best['quality_score']:.1f}/10):")
                print(f"Q: {best['query']}")
                print(f"A: {preview}")
    
    # Final assessment
    print(f"\n{'='*80}")
    print("FINAL ASSESSMENT")
    print("=" * 80)
    
    if success_rate >= 90:
        assessment = "🎉 EXCELLENT - All modes working reliably"
    elif success_rate >= 75:
        assessment = "✅ GOOD - Most modes working well"
    elif success_rate >= 50:
        assessment = "⚠️ FAIR - Some modes need improvement"
    else:
        assessment = "❌ POOR - Significant issues detected"
    
    print(f"Overall Assessment: {assessment}")
    
    if avg_response_time < 20:
        speed_assessment = "🚀 Fast response times"
    elif avg_response_time < 40:
        speed_assessment = "⏱️ Acceptable response times"
    else:
        speed_assessment = "🐌 Slow response times - consider optimizations"
    
    print(f"Speed Assessment: {speed_assessment}")
    
    if avg_quality >= 7:
        quality_assessment = "🌟 High quality responses"
    elif avg_quality >= 5:
        quality_assessment = "👍 Good quality responses"
    else:
        quality_assessment = "👎 Quality needs improvement"
    
    print(f"Quality Assessment: {quality_assessment}")
    
    # Save detailed results
    with open("comprehensive_chat_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "llama3.2:1b",
            "summary": {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "avg_quality_score": avg_quality,
                "total_tests": len(test_cases),
                "successful_tests": successful_tests
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: comprehensive_chat_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())