#!/usr/bin/env python3
"""
Simple test for chat modes with proper WebSocket handling
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_chat_mode(mode, message):
    """Test a single chat mode with a message"""
    print(f"\n=== Testing {mode.upper()} mode ===")
    print(f"Query: {message}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection established
            await asyncio.sleep(1)
            
            # Send chat request
            request = {
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Sending request: {json.dumps(request, indent=2)}")
            await websocket.send(json.dumps(request))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                end_time = time.time()
                
                response_data = json.loads(response)
                response_time = end_time - start_time
                
                print(f"✅ Response received in {response_time:.1f}s")
                print(f"Response type: {response_data.get('type')}")
                
                if response_data.get("type") == "chat_response":
                    ai_response = response_data.get("response", "")
                    print(f"Response: {ai_response}")
                    
                    # Quick quality check
                    word_count = len(ai_response.split())
                    quality = "Good" if word_count > 20 else "Short" if word_count > 5 else "Poor"
                    print(f"Quality: {quality} ({word_count} words)")
                    
                    return {
                        "success": True,
                        "response": ai_response,
                        "response_time": response_time,
                        "word_count": word_count
                    }
                else:
                    print(f"❌ Unexpected response: {response_data}")
                    return {"success": False, "error": "Unexpected response type"}
                    
            except asyncio.TimeoutError:
                print("❌ Response timeout (60s)")
                return {"success": False, "error": "Timeout"}
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return {"success": False, "error": str(e)}

async def run_comprehensive_test():
    """Run tests for all modes"""
    
    test_cases = [
        ("ask", "What is artificial intelligence?"),
        ("ask", "How do WebSockets work?"),
        ("agent", "Help me plan a web development project"),
        ("agent", "I need to improve my app's performance"),
        ("suggest", "What should I learn next in programming?"),
        ("suggest", "How can I make my code more efficient?"),
        ("general", "Explain the benefits of microservices"),
        ("general", "What are the latest trends in web development?")
    ]
    
    print("COMPREHENSIVE CHAT MODES TEST")
    print("Model: llama3.2:1b")
    print("=" * 80)
    
    results = []
    successful_tests = 0
    total_time = 0
    
    for mode, message in test_cases:
        result = await test_chat_mode(mode, message)
        results.append({
            "mode": mode,
            "message": message,
            **result
        })
        
        if result["success"]:
            successful_tests += 1
            total_time += result["response_time"]
        
        # Brief pause between tests
        await asyncio.sleep(3)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY REPORT")
    print("=" * 80)
    
    success_rate = (successful_tests / len(test_cases)) * 100
    avg_time = total_time / successful_tests if successful_tests > 0 else 0
    
    print(f"Total tests: {len(test_cases)}")
    print(f"Successful: {successful_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Average response time: {avg_time:.1f}s")
    
    # Mode-specific results
    modes = ["ask", "agent", "suggest", "general"]
    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        mode_success = sum(1 for r in mode_results if r["success"])
        print(f"{mode.upper()} mode: {mode_success}/{len(mode_results)} successful")
    
    # Show sample responses
    print(f"\nSAMPLE RESPONSES:")
    print("-" * 40)
    for result in results:
        if result["success"]:
            response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
            print(f"{result['mode'].upper()}: {response_preview}")
            break
    
    # Save results
    with open("simple_chat_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "llama3.2:1b",
            "success_rate": success_rate,
            "avg_response_time": avg_time,
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to simple_chat_test_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())