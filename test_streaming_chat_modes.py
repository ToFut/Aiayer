#!/usr/bin/env python3
"""
Test streaming chat modes with llama3.2:1b
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

class StreamingChatTester:
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        
    async def test_streaming_mode(self, mode, message):
        """Test a single mode with streaming response handling"""
        print(f"\n{'='*70}")
        print(f"TESTING {mode.upper()} MODE WITH STREAMING")
        print(f"{'='*70}")
        print(f"Query: {message}")
        print("-" * 70)
        
        try:
            async with websockets.connect(self.backend_url) as websocket:
                # Wait for connection established
                connection_msg = await websocket.recv()
                connection_data = json.loads(connection_msg)
                print(f"✅ Connected: {connection_data.get('message', 'OK')}")
                
                # Send chat request
                start_time = time.time()
                request = {
                    "type": "chat_request",
                    "mode": mode,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                print(f"📤 Request sent, waiting for streaming response...")
                
                # Collect streaming response
                full_response = ""
                chunks_received = 0
                first_chunk_time = None
                
                while True:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                        response_data = json.loads(response)
                        response_type = response_data.get("type")
                        
                        if response_type == "chat_response_start":
                            print(f"🚀 {response_data.get('message', 'Starting...')}")
                            
                        elif response_type == "chat_response_chunk":
                            chunk = response_data.get("chunk", "")
                            full_response += chunk
                            chunks_received += 1
                            
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                print(f"⚡ First chunk received in {first_chunk_time - start_time:.1f}s")
                            
                            # Print chunk with some visual feedback
                            print(chunk, end="", flush=True)
                            
                        elif response_type == "chat_response_complete":
                            end_time = time.time()
                            final_response = response_data.get("full_response", full_response)
                            print(f"\n\n✅ Response complete!")
                            print(f"📊 Statistics:")
                            print(f"   Total time: {end_time - start_time:.1f}s")
                            print(f"   First chunk: {first_chunk_time - start_time:.1f}s" if first_chunk_time else "   No chunks received")
                            print(f"   Chunks received: {chunks_received}")
                            print(f"   Words: {len(final_response.split())}")
                            print(f"   AI powered: {response_data.get('ai_powered', False)}")
                            
                            return {
                                "success": True,
                                "mode": mode,
                                "query": message,
                                "response": final_response,
                                "total_time": end_time - start_time,
                                "first_chunk_time": first_chunk_time - start_time if first_chunk_time else 0,
                                "chunks_received": chunks_received,
                                "word_count": len(final_response.split()),
                                "ai_powered": response_data.get("ai_powered", False)
                            }
                            
                        elif response_type == "chat_response_metadata":
                            context_metrics = response_data.get("context_metrics", {})
                            print(f"🧠 Context: {context_metrics.get('memories_used', 0)} memories, "
                                  f"{context_metrics.get('confidence_score', 0):.1%} confidence")
                            
                        elif response_type == "chat_response_error":
                            error_msg = response_data.get("error", "Unknown error")
                            print(f"❌ Error: {error_msg}")
                            return {
                                "success": False,
                                "mode": mode,
                                "query": message,
                                "error": error_msg
                            }
                        
                    except asyncio.TimeoutError:
                        print(f"\n❌ Timeout waiting for response")
                        return {
                            "success": False,
                            "mode": mode,
                            "query": message,
                            "error": "Timeout"
                        }
                        
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return {
                "success": False,
                "mode": mode,
                "query": message,
                "error": str(e)
            }

    def analyze_response_quality(self, response, mode):
        """Quick quality analysis for responses"""
        if not response:
            return 0
        
        score = 0
        response_lower = response.lower()
        word_count = len(response.split())
        
        # Length scoring (3 points)
        if 50 <= word_count <= 300:
            score += 3
        elif 30 <= word_count <= 400:
            score += 2
        elif word_count >= 20:
            score += 1
        
        # Mode-specific content analysis (4 points)
        if mode == "ask":
            keywords = ["explain", "definition", "means", "because", "answer"]
            score += min(4, sum(2 for kw in keywords if kw in response_lower))
            
        elif mode == "agent":
            keywords = ["step", "first", "next", "plan", "process", "task"]
            score += min(4, sum(1 for kw in keywords if kw in response_lower))
            
        elif mode == "suggest":
            keywords = ["suggest", "recommend", "consider", "try", "could", "advice"]
            score += min(4, sum(1 for kw in keywords if kw in response_lower))
            
        elif mode == "general":
            # Check for coherent explanation
            sentences = len([s for s in response.split('.') if s.strip()])
            score += min(4, sentences)
        
        # Structure and usefulness (3 points)
        if '.' in response and len(response.split('.')) >= 2:
            score += 2
        if any(word in response_lower for word in ["however", "therefore", "because", "for example"]):
            score += 1
        
        return min(10, score)

    async def run_comprehensive_test(self):
        """Test all modes with streaming"""
        
        test_cases = [
            ("ask", "What is machine learning and how does it work?"),
            ("ask", "Explain how WebSockets differ from HTTP requests"),
            ("agent", "Help me plan a website redesign project step by step"),
            ("agent", "I need to debug a slow web application. Guide me through the process"),
            ("suggest", "What technologies should I learn for modern web development?"),
            ("suggest", "How can I improve my team's code review process?"),
            ("general", "Tell me about the benefits and challenges of microservices"),
            ("general", "What are the current trends in AI and machine learning?")
        ]
        
        print("COMPREHENSIVE STREAMING CHAT MODES TEST")
        print("Model: llama3.2:1b with streaming responses")
        print("=" * 80)
        
        results = []
        total_tests = len(test_cases)
        successful_tests = 0
        total_response_time = 0
        total_first_chunk_time = 0
        total_quality_score = 0
        
        for i, (mode, message) in enumerate(test_cases):
            print(f"\n[{i+1}/{total_tests}] Starting test...")
            result = await self.test_streaming_mode(mode, message)
            
            if result["success"]:
                # Analyze quality
                quality_score = self.analyze_response_quality(result["response"], mode)
                result["quality_score"] = quality_score
                
                successful_tests += 1
                total_response_time += result["total_time"]
                total_first_chunk_time += result["first_chunk_time"]
                total_quality_score += quality_score
                
                print(f"🎯 Quality Score: {quality_score:.1f}/10")
            
            results.append(result)
            
            # Pause between tests
            if i < total_tests - 1:
                print(f"\n⏳ Waiting 3 seconds before next test...")
                await asyncio.sleep(3)
        
        # Generate comprehensive report
        self.generate_final_report(results, total_tests, successful_tests, 
                                 total_response_time, total_first_chunk_time, total_quality_score)
        
        # Save results
        with open("streaming_chat_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": "llama3.2:1b",
                "streaming": True,
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": (successful_tests / total_tests) * 100,
                    "avg_total_time": total_response_time / successful_tests if successful_tests > 0 else 0,
                    "avg_first_chunk_time": total_first_chunk_time / successful_tests if successful_tests > 0 else 0,
                    "avg_quality_score": total_quality_score / successful_tests if successful_tests > 0 else 0
                },
                "results": results
            }, f, indent=2)
        
        return results

    def generate_final_report(self, results, total_tests, successful_tests, 
                            total_response_time, total_first_chunk_time, total_quality_score):
        """Generate comprehensive final report"""
        
        print(f"\n{'='*80}")
        print("FINAL STREAMING TEST REPORT")
        print("=" * 80)
        
        success_rate = (successful_tests / total_tests) * 100
        avg_total_time = total_response_time / successful_tests if successful_tests > 0 else 0
        avg_first_chunk = total_first_chunk_time / successful_tests if successful_tests > 0 else 0
        avg_quality = total_quality_score / successful_tests if successful_tests > 0 else 0
        
        print(f"📊 OVERALL PERFORMANCE:")
        print(f"   Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"   Avg Total Time: {avg_total_time:.1f}s")
        print(f"   Avg First Chunk: {avg_first_chunk:.1f}s")
        print(f"   Avg Quality: {avg_quality:.1f}/10")
        
        # Mode breakdown
        modes = ["ask", "agent", "suggest", "general"]
        print(f"\n📋 MODE BREAKDOWN:")
        print("-" * 60)
        print(f"{'Mode':<10} {'Status':<12} {'Success':<8} {'Avg Time':<10} {'Quality':<8}")
        print("-" * 60)
        
        for mode in modes:
            mode_results = [r for r in results if r.get("mode") == mode]
            mode_successful = [r for r in mode_results if r["success"]]
            
            if mode_successful:
                avg_time = sum(r["total_time"] for r in mode_successful) / len(mode_successful)
                avg_qual = sum(r.get("quality_score", 0) for r in mode_successful) / len(mode_successful)
                status = "✅ WORKING" if len(mode_successful) == len(mode_results) else "⚠️ PARTIAL"
            else:
                avg_time = 0
                avg_qual = 0
                status = "❌ FAILING"
            
            success_ratio = f"{len(mode_successful)}/{len(mode_results)}"
            print(f"{mode.upper():<10} {status:<12} {success_ratio:<8} {avg_time:<10.1f} {avg_qual:<8.1f}")
        
        # Performance assessment
        print(f"\n🚀 STREAMING PERFORMANCE:")
        if avg_first_chunk < 5:
            chunk_assessment = "Excellent - Very responsive"
        elif avg_first_chunk < 10:
            chunk_assessment = "Good - Acceptable responsiveness"
        elif avg_first_chunk < 20:
            chunk_assessment = "Fair - Noticeable delay"
        else:
            chunk_assessment = "Poor - Slow to start"
        
        print(f"   First chunk time: {chunk_assessment}")
        
        if avg_total_time < 30:
            total_assessment = "Excellent - Fast completion"
        elif avg_total_time < 60:
            total_assessment = "Good - Reasonable completion time"
        else:
            total_assessment = "Slow - Consider optimizations"
        
        print(f"   Total completion: {total_assessment}")
        
        # Final recommendation
        print(f"\n🎯 RECOMMENDATION:")
        if success_rate >= 90 and avg_first_chunk < 20:
            recommendation = "🎉 PRODUCTION READY - Streaming works excellently across all modes"
        elif success_rate >= 75 and avg_first_chunk < 30:
            recommendation = "✅ GOOD FOR PRODUCTION - Minor optimizations recommended"
        elif success_rate >= 50:
            recommendation = "⚠️ NEEDS IMPROVEMENT - Some modes failing or too slow"
        else:
            recommendation = "❌ NOT READY - Significant issues need addressing"
        
        print(f"   {recommendation}")
        
        print(f"\n💾 Results saved to: streaming_chat_test_results.json")

if __name__ == "__main__":
    tester = StreamingChatTester()
    asyncio.run(tester.run_comprehensive_test())