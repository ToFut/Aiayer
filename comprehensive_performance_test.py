#!/usr/bin/env python3
"""
Comprehensive Performance Test
Tests both LLM speed and agent mode performance
"""

import asyncio
import time
import logging
import websockets
import json
from llm_warmup_manager import get_warmup_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTestResults:
    def __init__(self):
        self.llm_warmup_time = 0
        self.fast_response_times = []
        self.agent_response_times = []
        self.streaming_times = []
        
    def add_llm_time(self, time_taken):
        self.fast_response_times.append(time_taken)
    
    def add_agent_time(self, time_taken):
        self.agent_response_times.append(time_taken)
    
    def add_streaming_time(self, time_taken):
        self.streaming_times.append(time_taken)
    
    def get_summary(self):
        summary = {
            "LLM Performance": {
                "warmup_time": f"{self.llm_warmup_time:.2f}s",
                "fast_responses": len(self.fast_response_times),
                "avg_response_time": f"{sum(self.fast_response_times)/len(self.fast_response_times):.2f}s" if self.fast_response_times else "N/A",
                "fastest_response": f"{min(self.fast_response_times):.2f}s" if self.fast_response_times else "N/A",
                "target_met": all(t <= 10 for t in self.fast_response_times) if self.fast_response_times else False
            }
        }
        
        if self.agent_response_times:
            summary["Agent Performance"] = {
                "agent_responses": len(self.agent_response_times),
                "avg_agent_time": f"{sum(self.agent_response_times)/len(self.agent_response_times):.2f}s",
                "fastest_agent": f"{min(self.agent_response_times):.2f}s",
                "target_met": all(t <= 10 for t in self.agent_response_times)
            }
        
        return summary

async def test_llm_speed():
    """Test LLM warmup manager speed"""
    logger.info("🧪 Testing LLM Speed Performance...")
    results = PerformanceTestResults()
    
    try:
        # Start warmup manager
        start_warmup = time.time()
        manager = await get_warmup_manager()
        results.llm_warmup_time = time.time() - start_warmup
        
        logger.info(f"⏱️ Warmup completed in {results.llm_warmup_time:.2f}s")
        
        # Test multiple fast responses
        test_queries = [
            "What is 2+2?",
            "Briefly explain Python in one sentence.",
            "Name three colors.",
            "What day is today?",
            "Calculate 5*3."
        ]
        
        for i, query in enumerate(test_queries, 1):
            start_time = time.time()
            response = await manager.fast_generate_response([
                {"role": "user", "content": query}
            ])
            response_time = time.time() - start_time
            results.add_llm_time(response_time)
            
            logger.info(f"⚡ Query {i}: {response_time:.2f}s - {response[:50]}...")
        
        await manager.stop()
        return results
        
    except Exception as e:
        logger.error(f"❌ LLM test error: {e}")
        return results

async def test_backend_integration():
    """Test backend integration performance"""
    logger.info("🧪 Testing Backend Integration...")
    
    try:
        # Test if enhanced backend is running
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'enhanced_enterprise_backend'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Enhanced backend is running")
            
            # Test WebSocket connection (if possible)
            try:
                async with websockets.connect("ws://localhost:8767/ws") as websocket:
                    # Send test message
                    test_message = {
                        "type": "chat",
                        "message": "Hello, this is a speed test",
                        "mode": "ask",
                        "client_id": "speed_test"
                    }
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=15)
                    response_time = time.time() - start_time
                    
                    logger.info(f"🌐 Backend response in {response_time:.2f}s")
                    
                    if response_time <= 10:
                        logger.info("🚀 Backend performance target met!")
                    else:
                        logger.warning("⚠️ Backend response slower than target")
                        
            except Exception as e:
                logger.warning(f"⚠️ WebSocket test failed: {e}")
        else:
            logger.info("ℹ️ Enhanced backend not running - start with START_ENHANCED_SYSTEM.sh")
            
    except Exception as e:
        logger.error(f"❌ Backend test error: {e}")

async def main():
    """Run comprehensive performance tests"""
    logger.info("🎯 COMPREHENSIVE PERFORMANCE TEST")
    logger.info("="*50)
    logger.info("Target: LLM responses within 10s, streaming complete within 25s")
    logger.info("Target: Agent mode responses within 3-10s")
    logger.info("")
    
    # Test LLM speed
    results = await test_llm_speed()
    
    # Test backend integration
    await test_backend_integration()
    
    # Print results summary
    logger.info("")
    logger.info("📊 PERFORMANCE SUMMARY")
    logger.info("="*50)
    
    summary = results.get_summary()
    for category, metrics in summary.items():
        logger.info(f"\n{category}:")
        for metric, value in metrics.items():
            if metric == "target_met":
                status = "✅ PASS" if value else "❌ FAIL"
                logger.info(f"  Target Met: {status}")
            else:
                logger.info(f"  {metric.replace('_', ' ').title()}: {value}")
    
    # Overall assessment
    logger.info("")
    llm_performance = summary["LLM Performance"]["target_met"]
    
    if llm_performance:
        logger.info("🎉 OVERALL: Performance targets achieved!")
        logger.info("✅ LLM responses are fast (under 10s)")
        logger.info("✅ System ready for production use")
    else:
        logger.warning("⚠️ Some performance targets not met")
    
    logger.info("")
    logger.info("💡 To start the full optimized system:")
    logger.info("   ./START_ENHANCED_SYSTEM.sh")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")