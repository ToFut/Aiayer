#!/usr/bin/env python3
"""
Test all chat modes with the fixed streaming backend
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_mode(mode, message):
    """Test a specific mode"""
    print(f"\n{'='*60}")
    print(f"TESTING {mode.upper()} MODE")
    print(f"{'='*60}")
    print(f"Query: {message}")
    print("-" * 60)
    
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            
            # Send request
            request = {
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(request))
            print("🚀 Request sent, waiting for streaming response...")
            
            # Collect response
            full_response = ""
            chunks_received = 0
            start_time = None
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=90.0)
                    response_data = json.loads(response)
                    response_type = response_data.get("type")
                    
                    if response_type == "chat_response_start":
                        start_time = datetime.now()
                        print(f"⚡ Started processing...")
                        
                    elif response_type == "chat_response_chunk":
                        chunk = response_data.get("chunk", "")
                        full_response += chunk
                        chunks_received += 1
                        print(chunk, end="", flush=True)
                        
                    elif response_type == "chat_response_complete":
                        end_time = datetime.now()
                        final_response = response_data.get("full_response", full_response)
                        ai_powered = response_data.get("ai_powered", False)
                        
                        print(f"\n\n✅ {mode.upper()} MODE SUCCESS!")
                        print(f"📊 Stats: {chunks_received} chunks, AI-powered: {ai_powered}")
                        if start_time:
                            duration = (end_time - start_time).total_seconds()
                            print(f"⏱️ Duration: {duration:.1f}s")
                        
                        # Check if it's a real response (not mock)
                        is_real = not ("💭 💭 Let me help you understand" in final_response)
                        print(f"🤖 Real AI Response: {'✅ YES' if is_real else '❌ NO (Mock)'}")
                        
                        return {
                            "success": True,
                            "mode": mode,
                            "response": final_response,
                            "chunks": chunks_received,
                            "ai_powered": ai_powered,
                            "is_real_response": is_real,
                            "duration": duration if start_time else 0
                        }
                        
                    elif response_type == "chat_response_error":
                        error = response_data.get("error", "Unknown error")
                        print(f"\n❌ ERROR: {error}")
                        return {
                            "success": False,
                            "mode": mode,
                            "error": error
                        }
                        
                except asyncio.TimeoutError:
                    print(f"\n❌ TIMEOUT for {mode} mode")
                    return {
                        "success": False,
                        "mode": mode,
                        "error": "Timeout"
                    }
            
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
        return {
            "success": False,
            "mode": mode,
            "error": str(e)
        }

async def main():
    """Test all modes"""
    test_cases = [
        ("ask", "What is machine learning?"),
        ("agent", "Help me plan a website project step by step"),
        ("suggest", "What should I learn for web development?"),
        ("general", "Tell me about AI trends")
    ]
    
    print("COMPREHENSIVE REAL AI RESPONSE TEST")
    print("Model: llama3.2:1b with streaming")
    print("=" * 80)
    
    results = []
    successful_modes = 0
    real_ai_responses = 0
    
    for mode, message in test_cases:
        result = await test_mode(mode, message)
        results.append(result)
        
        if result["success"]:
            successful_modes += 1
            if result.get("is_real_response", False):
                real_ai_responses += 1
        
        # Brief pause between tests
        await asyncio.sleep(3)
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print("=" * 80)
    
    total_modes = len(test_cases)
    success_rate = (successful_modes / total_modes) * 100
    real_ai_rate = (real_ai_responses / total_modes) * 100
    
    print(f"📊 SUMMARY:")
    print(f"   Total modes tested: {total_modes}")
    print(f"   Successful responses: {successful_modes} ({success_rate:.1f}%)")
    print(f"   Real AI responses: {real_ai_responses} ({real_ai_rate:.1f}%)")
    print(f"   Mock responses: {successful_modes - real_ai_responses}")
    
    print(f"\n📋 MODE BREAKDOWN:")
    for result in results:
        mode = result["mode"].upper()
        if result["success"]:
            status = "✅ REAL AI" if result.get("is_real_response") else "⚠️ MOCK"
            duration = result.get("duration", 0)
            print(f"   {mode:<8} | {status:<10} | {duration:.1f}s")
        else:
            print(f"   {mode:<8} | ❌ FAILED   | {result.get('error', 'Unknown')}")
    
    # Overall assessment
    if real_ai_rate == 100:
        assessment = "🎉 PERFECT - All modes using real AI!"
    elif real_ai_rate >= 75:
        assessment = "✅ EXCELLENT - Most modes working with real AI"
    elif real_ai_rate >= 50:
        assessment = "⚠️ PARTIAL - Some modes still using mock responses"
    else:
        assessment = "❌ PROBLEM - Most modes still using mock responses"
    
    print(f"\n🎯 FINAL ASSESSMENT: {assessment}")
    
    # Save results
    with open("all_modes_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "llama3.2:1b",
            "summary": {
                "total_modes": total_modes,
                "successful_modes": successful_modes,
                "real_ai_responses": real_ai_responses,
                "success_rate": success_rate,
                "real_ai_rate": real_ai_rate
            },
            "results": results
        }, f, indent=2)
    
    print(f"💾 Results saved to: all_modes_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())